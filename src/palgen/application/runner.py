import logging
import os
import sys
from gettext import gettext
from pathlib import Path
from subprocess import check_call
from typing import Iterable

import click
from click.core import Context
from click.formatting import HelpFormatter

from palgen.schemas.palgen import PalgenSettings

from ..interface import Extension
from ..loaders import AST, Python
from ..machinery import find_backwards
from ..palgen import Palgen
from .log import set_min_level
from .util import ListParam


class CommandLoader(click.Group):
    def ensure_palgen(self, ctx: click.Context):
        args = sys.argv[1:]
        args.remove("--help")

        parser = ctx.command.make_parser(ctx)
        options, arguments, _ = parser.parse_args(args)
        parsed = {parameter.name: parameter.consume_value(ctx, options)[0]
                  for parameter in ctx.command.get_params(ctx)}

        # TODO if arguments is nonempty print helptext for command

        if ctx.obj is None:
            # ? When running palgen --help, main() will not be called
            # ? hence the context has not yet been initialized

            if options.get('debug', False):
                set_min_level(0)

            settings = PalgenSettings()
            settings.jobs = int(options.get('jobs', 1))

            conv = ListParam[Path]()
            settings.extensions.dependencies = conv.convert(options.get('dependencies', []))
            settings.extensions.folders = conv.convert(options.get('extra_folders', []))

            ctx.obj = Palgen(config_file=Path(parsed['config']).resolve(), settings=settings)

    def list_commands(self, ctx: click.Context) -> list[str]:
        commands = super().list_commands(ctx)

        self.ensure_palgen(ctx)
        assert isinstance(ctx.obj, Palgen)
        commands.extend(ctx.obj.extensions.runnable)

        return commands

    def get_command(self, ctx: click.Context, cmd_name: str):
        cmd_name = cmd_name.lower()

        if from_group := super().get_command(ctx, cmd_name):
            # commands registered to the top level group
            return from_group

        assert isinstance(ctx.obj, Palgen)
        return ctx.obj.get_command(cmd_name)

    def format_commands(self, ctx: Context, formatter: HelpFormatter) -> None:
        self.ensure_palgen(ctx)
        palgen: Palgen = ctx.obj

        def get_commands(extensions: Iterable[str]):
            nonlocal ctx
            for name in extensions:
                cmd = self.get_command(ctx, name)
                if cmd is None:
                    continue

                if cmd.hidden:
                    continue
                yield name, cmd

        def format_section(section: str, extensions: Iterable[str]) -> None:
            nonlocal formatter
            commands = list(get_commands(extensions))
            # allow for 3 times the default spacing
            if not commands:
                return
            limit = formatter.width - 6 - max(len(cmd[0]) for cmd in commands)
            rows = [(subcommand, cmd.get_short_help_str(limit)) for subcommand, cmd in commands]

            if rows:
                with formatter.section(section):
                    formatter.write_dl(rows)

        format_section("Built-in Commands", [*super().list_commands(ctx), *palgen.extensions.builtin])
        format_section(f'{palgen.project.name} Commands', palgen.extensions.local)
        format_section('Inherited Commands', palgen.extensions.inherited)

    def format_options(self, ctx: Context, formatter: HelpFormatter) -> None:
        opts = []
        for param in self.get_params(ctx):
            rv = param.get_help_record(ctx)
            if rv is not None:
                opts.append(rv)

        if opts:
            with formatter.section(gettext("Options")):
                formatter.write_dl(opts)

        self.format_commands(ctx, formatter)

@click.command(cls=CommandLoader,
               chain=True,
               invoke_without_command=True,
               context_settings={'show_default': True})
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
@click.option("--output", help="Output path", default=Path("build"), type=Path)
@click.pass_context
def main(ctx, debug: bool, version: bool, config: Path,
         extra_folders: ListParam[Path], dependencies: ListParam[Path],
         jobs: int, output: Path):
    # pylint: disable=too-many-arguments
    if version:
        from palgen import __version__
        print(f"palgen {__version__}")
        return

    if debug:
        # logging.getLogger(__package__).setLevel(logging.DEBUG)
        set_min_level(0)

    if isinstance(ctx.obj, Palgen):
        return

    settings = PalgenSettings()
    if jobs is not None:
        settings.jobs = jobs
    settings.output = output

    settings.extensions.folders = list(extra_folders)
    settings.extensions.dependencies = list(dependencies)

    ctx.obj = Palgen(config, settings)

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
