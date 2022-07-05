from palliate_codegen.generator import generator
from palliate_codegen.log import logger, set_min_level

import click
from pathlib import Path
import sys

def handle_exception(type, value, trace):
    logger.error("Exception occured: ", exc_info=(type, value, trace))

sys.excepthook = handle_exception

@click.command()
@click.option('-c', '--config',
              help='Path to project configuration.',
              default=Path.cwd() / 'codegen.toml')
@click.option('-o', '--outpath',
              help='Build directory.',
              default=Path.cwd() / 'build')
@click.option('-v', '--verbosity',
              help='Log verbosity.',
              default=0)
def main(config, outpath, verbosity):
    '''This tool is used for code generation.'''
    set_min_level(verbosity)

    gen = generator(config, outpath)
    if gen.collect():
        outpath = Path(outpath).resolve().absolute()
        logger.debug(f'Config output path: {outpath}')
        outpath.mkdir(parents=True, exist_ok=True)

        gen.parse()
    else:
        logger.error("No configuration files found.")
