from palgen.generator import Generator
from palgen.log import logger, set_min_level

import click
from pathlib import Path
import sys

def handle_exception(type, value, trace):
    logger.error("Exception occured: ", exc_info=(type, value, trace))

sys.excepthook = handle_exception

@click.command()
@click.option('-c', '--config',
              help='Path to project configuration.',
              default=Path.cwd() / 'project.toml')
@click.option('-o', '--outpath',
              help='Build directory.',
              default=Path.cwd() / 'build')
@click.option('-v', '--verbosity',
              help='Log verbosity.',
              default=0)
@click.argument('tables', nargs=-1)
def main(config, outpath, verbosity, tables):
    '''This tool is used for code generation.'''
    set_min_level(verbosity)

    gen = Generator(config, outpath, tables)
    gen.collect()
    outpath = Path(outpath).resolve().absolute()
    logger.debug(f'Config output path: {outpath}')
    outpath.mkdir(parents=True, exist_ok=True)
    gen.parse()
