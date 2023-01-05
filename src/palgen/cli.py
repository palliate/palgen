import logging
from pathlib import Path

import click

from palgen.loader import Loader
from palgen.log import set_min_level

logger = logging.getLogger(__name__)


@click.group()
@click.option('--debug/--no-debug', default=False)
@click.option("-c", "--config",
              help="Path to project configuration.",
              default=Path.cwd() / "palgen.toml")
@click.pass_context
def main(ctx, debug, config):
    if debug:
        set_min_level(0)

    config = Path(config)
    if config.is_dir():
        config /= "palgen.toml"

    ctx.obj = Loader(config)


@main.command()
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

@main.command()
@click.option("-o", "--outpath",
              help="Relative path to output folder",
              default=Path.cwd() / "build")
@click.option("-d", "--dry", help="Dry run. Do not write any generated files to disk.")
@click.argument("tables", nargs=-1)
@click.pass_context
def run(ctx, outpath, dry, tables):
    """Run codegen"""
    ctx.obj.run(*tables)


'''project.load()
    gen = Generator(project, outpath, tables)
    gen.collect()

    outpath = Path(outpath).resolve().absolute()
    logger.debug("Config output path: %s", outpath)
    outpath.mkdir(parents=True, exist_ok=True)
    gen.parse()
'''
