import contextlib
import importlib
import logging
from pathlib import Path
from typing import Optional

import click
from pydantic import BaseModel, ValidationError, validate_model
from pydantic.errors import MissingError

from palgen.module import Module
from palgen.palgen import Palgen
from palgen.util.cli import ListParam
from palgen.util.log import set_min_level
from palgen.util.schema import pydantic_to_click

logger = logging.getLogger(__name__)


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

        for subfolder in (Path(__file__).parent / "integrations").iterdir():
            if not subfolder.is_dir():
                continue

            name = f"palgen.integrations.{subfolder.name}.cli"
            if self._load_builtin(name) is not None:
                commands.append(subfolder.name)

        if not ctx.obj:
            init_context(ctx)

        if ctx.obj:
            assert isinstance(ctx.obj, Palgen)
            commands.extend(ctx.obj.modules.runnables)

        return commands

    def get_command(self, ctx: click.Context, cmd_name: str):
        cmd_name = cmd_name.lower()

        if from_group := super().get_command(ctx, cmd_name):
            # built-in commands
            return from_group

        if from_integrations := self._load_builtin(f"palgen.integrations.{cmd_name}.cli"):
            return from_integrations

        assert isinstance(ctx.obj, Palgen)
        if cmd_name in ctx.obj.modules.runnables:
            module = ctx.obj.modules.runnables[cmd_name]
            if hasattr(module, "cli"):
                return module.cli
            else:
                return CommandLoader._generate_cli(module, ctx.obj)

        return None

    @staticmethod
    def _generate_cli(module: Module, palgen: Palgen):
        key = module.name.lower()
        @click.command(name=key,
                       help=module.__doc__,
                       context_settings={'show_default': True})
        @click.pass_context
        def wrapper(ctx, **kwargs):
            nonlocal module
            parser = module(ctx.obj.root, ctx.obj.root, kwargs)
            parser.run(ctx.obj.files)

        if key in palgen.settings:
            assert issubclass(module.Settings, BaseModel)
            *_, errors = validate_model(module.Settings, palgen.settings[key])
            if errors:
                unfiltered = [error for error in errors.raw_errors
                            if not isinstance(error.exc, MissingError)]
                if unfiltered:
                    raise ValidationError(unfiltered, module.Settings)

        for field, options in pydantic_to_click(module.Settings):
            if key in palgen.settings and field in palgen.settings[key]:
                options["required"] = False
                options["default"] = palgen.settings[key][field]

            wrapper = click.option(f'--{field}', **options)(wrapper)

        return wrapper

    @staticmethod
    def _load_builtin(name):
        with contextlib.suppress(ImportError):
            mod = importlib.import_module(name)
            if hasattr(mod, "cli"):
                return mod.cli

        return None


@click.command(cls=CommandLoader, chain=True, invoke_without_command=True)
@click.option('--debug/--no-debug', default=False)
@click.option("-c", "--config",
              help="Path to project configuration.",
              default=Path.cwd() / "palgen.toml")
@click.option('-v', "--version", help="Show palgen version", is_flag=True)
@click.option("--extra-folders", default=[], type=ListParam[Path])
@click.option("--dependencies", default=None, type=Path)
@click.pass_context
def cli(ctx, debug: bool, version: bool, config: Path, extra_folders: str, dependencies: Optional[Path]):
    if version:
        print("TODO")
        return
    if debug:
        # logging.getLogger(__package__).setLevel(logging.DEBUG)
        set_min_level(0)

    init_context(ctx, config)

    # override options
    if extra_folders:
        ctx.obj.options.modules.extra_folders = extra_folders

    if dependencies:
        ctx.obj.options.modules.dependencies = dependencies

    if ctx.invoked_subcommand is None:
        assert isinstance(ctx.obj, Palgen)

        # no subcommand - run all enabled templates
        ctx.obj.run()


@cli.command()
@click.option("-f", "--full", help="Search for templates and inputs.", is_flag=True)
@click.pass_context
def info(ctx, full):
    """Print project info and exit."""
    set_min_level(3)
    text = f"""\
Name:        {ctx.obj.project.name}
Description: {ctx.obj.project.description}
Version:     {ctx.obj.project.version}"""

    if full:
        text += f"""

Templates:   {list(ctx.obj.modules.keys())}
Subprojects: {list(ctx.obj.subprojects.keys())}"""

    print(text)


@cli.command()
@click.option("-o", "--output", help="Output path", type=Path, required=True)
@click.option("-r", "--relative", help="Output relative paths instead of absolute ones.", is_flag=True)
@click.pass_context
def generate_manifest(ctx, output: Path, relative: bool):
    assert isinstance(ctx.obj, Palgen)

    if output.is_dir():
        output /= 'palgen.manifest'
    output.parent.mkdir(exist_ok=True)

    # TODO generate sane relative paths. I don't like the current way but it's fine for now
    manifest = ctx.obj.generate_manifest(
        output.parent.absolute() if relative else None)

    with open(output, 'w', encoding="utf-8") as file:
        file.write(manifest)
    logger.info("Written manifest file %s", output)
