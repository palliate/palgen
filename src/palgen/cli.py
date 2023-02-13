import importlib
import logging
from pathlib import Path

import click

from palgen.util.log import set_min_level
from palgen.palgen import Palgen

logger = logging.getLogger(__name__)


def init_context(ctx, config: str | Path = Path.cwd()):
    if isinstance(config, str):
        config = Path(config)

    if config.is_dir():
        config /= "palgen.toml"

    if not config.exists():
        return

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
            meta = ctx.obj.modules.runnables[cmd_name]
            return meta.cli

        return None


    @staticmethod
    def _load_builtin(name):
        try:
            mod = importlib.import_module(name)
            if hasattr(mod, "cli"):
                return mod.cli

        except ImportError:
            pass
        return None

@click.command(cls=CommandLoader, chain=True, invoke_without_command=True)
@click.option('--debug/--no-debug', default=False)
@click.option("-c", "--config",
              help="Path to project configuration.",
              default=Path.cwd() / "palgen.toml")
@click.option("--extra-folders", default="")
@click.pass_context
def cli(ctx, debug: bool, config: Path, extra_folders: str):
    if debug:
        # logging.getLogger(__package__).setLevel(logging.DEBUG)
        set_min_level(0)

    init_context(ctx, config)

    # override options
    if extra_folders:
        paths = [Path(path) for path in extra_folders.split(';')]
        ctx.obj.options.modules.extra_folders = paths

    if ctx.invoked_subcommand is None:
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
    manifest = ctx.obj.generate_manifest(output.parent.absolute() if relative else None)

    with open(output, 'w', encoding="utf-8") as file:
        file.write(manifest)
    logger.info("Written manifest file %s", output)
