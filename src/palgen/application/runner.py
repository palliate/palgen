import contextlib
import importlib
import itertools
import logging
import os
import sys
from functools import cached_property
from pathlib import Path
from pkgutil import walk_packages
from subprocess import check_call
from typing import Type

import click
from pydantic import BaseModel, RootModel, ValidationError

from ..ext import Extension
from ..loaders import AST, Python
from ..machinery import find_backwards
from .log import set_min_level
from ..palgen import Palgen
from .util import ListParam, pydantic_to_click


def init_context(ctx, config: str | Path = Path.cwd()):
    if isinstance(config, str):
        config = Path(config)

    if config.is_dir():
        config /= "palgen.toml"

    if not config.exists():
        raise FileNotFoundError("palgen.toml not found")

    ctx.obj = Palgen(config)


class CommandLoader(click.Group):
    def list_commands(self, ctx: click.Context) -> list[str]:
        commands = super().list_commands(ctx)
        commands.extend(self.builtins.keys())

        if not ctx.obj:
            # ? When running palgen --help, main() will not be called
            # ? hence the context has not yet been initialized

            # TODO look for arguments in sys.argv to find proper config etc

            ctx.obj = Palgen(Path.cwd())

        assert isinstance(ctx.obj, Palgen)
        commands.extend(ctx.obj.extensions.runnables)

        return commands

    def get_command(self, ctx: click.Context, cmd_name: str):
        cmd_name = cmd_name.lower()

        if from_group := super().get_command(ctx, cmd_name):
            # commands registered to the top level group
            return from_group

        if cmd_name in self.builtins:
            # built-in commands
            return self.builtins[cmd_name]

        assert isinstance(ctx.obj, Palgen)
        if cmd_name in ctx.obj.extensions.runnables:
            extension = ctx.obj.extensions.runnables[cmd_name]
            return getattr(extension, "cli", CommandLoader.generate_cli(extension, ctx.obj))

        return None

    @staticmethod
    def generate_cli(extension: Type[Extension], palgen: Palgen):
        key = extension.name.lower()

        @click.command(name=key,
                       help=extension.__doc__,
                       context_settings={'show_default': True})
        @click.pass_obj
        def wrapper(obj, **kwargs):
            nonlocal key
            obj.run(key, kwargs)

        if key in palgen.settings and extension.Settings is not None:
            assert issubclass(extension.Settings, (BaseModel, RootModel))

            try:
                extension.Settings.model_validate(palgen.settings[key])
            except ValidationError as exc:
                filtered = [error for error in exc.errors()
                            if error.get('type', None) != 'missing']

                if filtered:
                    raise

        for field, options in pydantic_to_click(extension.Settings):
            if key in palgen.settings and field in palgen.settings[key]:
                options["required"] = False
                options["default"] = palgen.settings[key][field]
            wrapper = click.option(f'--{field}', **options)(wrapper)

        return wrapper

    @cached_property
    def builtins(self):
        keys = set()
        builtins = {}
        for (name, attr) in itertools.chain(CommandLoader._load_from("palgen.application.commands"),
                                            CommandLoader._load_from("palgen.integrations")):
            if name in keys:
                logging.error(
                    "Duplicate command name `%s` found, skipping", name)
                continue

            keys.add(name)
            builtins[name] = attr
        return builtins

    @staticmethod
    def _load_builtin(name):
        with contextlib.suppress(ImportError):
            mod = importlib.import_module(name)

            skip_list = []

            for ident, attr in mod.__dict__.items():
                if ident.startswith('_'):
                    continue

                if isinstance(attr, click.core.Command):
                    if isinstance(attr, click.core.Group):
                        skip_list.extend(attr.commands.values())
                    elif attr in skip_list:
                        continue

                    yield getattr(attr, "name", ident), attr

    @staticmethod
    def _load_from(name: str):
        with contextlib.suppress(ImportError):
            pkg = importlib.import_module(name)
            for module in walk_packages(path=pkg.__path__, prefix=f"{name}."):
                if module.ispkg:
                    continue

                yield from CommandLoader._load_builtin(module.name)


@click.command(cls=CommandLoader, chain=True,
               invoke_without_command=True, context_settings={'show_default': True})
@click.option('-v', "--version", help="Show palgen version", is_flag=True)
@click.option('--debug/--no-debug', default=False)
@click.option('-j', '--jobs',
              help=f"Amount of parallel tasks to use. Defaults to {os.cpu_count()}",
              default=None, type=int)
@click.option("-c", "--config",
              help="Path to project configuration.",
              default=Path.cwd() / "palgen.toml")
@click.option("--extra-folders", default=[], type=ListParam[Path]())
@click.option("--dependencies", default=[], type=ListParam[Path]())
@click.pass_context
def main(ctx, debug: bool, version: bool, config: Path,
         extra_folders: ListParam[Path], dependencies: ListParam[Path], jobs: int):
    # pylint: disable=too-many-arguments

    if version:
        from palgen import __version__
        print(f"palgen {__version__}")
        return
    if debug:
        # logging.getLogger(__package__).setLevel(logging.DEBUG)
        set_min_level(0)

    ctx.obj = Palgen(config)

    assert isinstance(ctx.obj, Palgen)

    # override options
    if jobs is not None:
        ctx.obj.options.jobs = jobs

    if extra_folders:
        ctx.obj.options.extensions.folders.extend(extra_folders)

    if dependencies:
        ctx.obj.options.extensions.dependencies = list(dependencies)

    if ctx.invoked_subcommand is None:
        assert isinstance(ctx.obj, Palgen)

        # no subcommand - run all enabled templates
        ctx.obj.run_all()


def check_direct_run():
    """This hack allows running extensions directly
    """

    import __main__
    if not (importer := getattr(__main__, '__file__', None)):
        return

    importer = Path(importer)
    if importer.suffix == '.py' and Python.check_candidate(importer):
        _run_directly(importer)


def _run_directly(importer: Path):
    # when palgen is run directly the suffix will never be '.py'
    # however if you run an extension directly it'll correspond to the extension's file
    # ie `python test.py` => 'test.py'

    ast = AST.load(importer)
    extensions = list(ast.get_subclasses(Extension))
    args = sys.argv[1:]

    if '--debug' in args:
        # early check for `--debug` flag
        # by the time the extension gets loaded we will otherwise have already
        # missed debug messages during loading
        set_min_level(0)
        args.remove('--debug')

    if all(extension.name.lower() not in args for extension in extensions):
        if len(extensions) > 1:
            logging.error(
                "Module contains multiple extensions, please specify which one to run.")
            args = ['--help']
        else:
            args = [extensions[0].name.lower(), *args]

    # TODO investigate why running directly with >1 jobs hangs
    # if '--jobs' not in args and '-j' not in args:
    #    args = ['--jobs', '1', *args]
    # main(args=args)

    #! workaround
    check_call(["palgen", *args],
               cwd=find_backwards("palgen.toml", source_dir=importer.parent).parent)
