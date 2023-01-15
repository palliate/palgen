import logging
from pathlib import Path

import click

from palgen.util.log import set_min_level
from palgen.loader import Loader


logger = logging.getLogger(__name__)

class CommandLoader(click.Group):
    def get_command(self, ctx, name: str):
        name = name.lower()

        if from_group := super().get_command(ctx, name):
            # built-in commands

            #ctx.executed_commands.add(name)
            return from_group

        if name in ctx.executed_commands:
            logger.warning("Skipping `%s`. Module invoked more than once.", name)

            # return noop command
            return click.Command(name, callback=lambda: None)


        assert isinstance(ctx.obj, Loader)

        if name in ctx.obj.templates:
            print("found module %s" % name)
            meta = ctx.obj.templates[name]
            return meta.parser.cli

        print(ctx.obj)

@click.command(cls=CommandLoader, chain=True, invoke_without_command=True)
@click.option('--debug/--no-debug', default=False)
@click.option("-c", "--config",
              help="Path to project configuration.",
              default=Path.cwd() / "palgen.toml")
@click.pass_context
def cli(ctx, debug, config):
    ctx.executed_commands = set()

    if debug:
        logging.getLogger(__package__).setLevel(logging.DEBUG)

    config = Path(config)
    if config.is_dir():
        config /= "palgen.toml"

    ctx.obj = Loader(config)

    if ctx.invoked_subcommand is None:
        # no subcommand - run all enabled templates
        print("no subcommand")

@cli.command()
@click.option("-f", "--full", help="Search for templates and inputs.", is_flag=True)
@click.pass_context
def info(ctx, full):
    """Print project info and exit."""
    set_min_level(3)
    text = f"""\
Name:        {ctx.obj.name}
Description: {ctx.obj.description}
Version:     {ctx.obj.version}"""

    if full:
        text += f"""

Templates:   {list(ctx.obj.templates.keys())}
Enabled:     {list(ctx.obj.active_templates.keys())}
Subprojects: {list(ctx.obj.subprojects.keys())}"""

    print(text)

'''
@cli.command()
@click.option("-o", "--outpath",
              help="Relative path to output folder",
              default=Path.cwd() / "build")
@click.option("-d", "--dry", help="Dry run. Do not write any generated files to disk.")
@click.argument("tables", nargs=-1)
@click.pass_context
def run(ctx, outpath, dry, tables):
    """Run codegen"""
    ctx.obj.run(*tables)
'''

'''project.load()
    gen = Generator(project, outpath, tables)
    gen.collect()

    outpath = Path(outpath).resolve().absolute()
    logger.debug("Config output path: %s", outpath)
    outpath.mkdir(parents=True, exist_ok=True)
    gen.parse()
'''

