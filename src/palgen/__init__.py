from pathlib import Path

import logging
import sys
import click

from palgen.generator import Generator
from palgen.log import set_min_level, setup_logger


setup_logger()


def handle_exception(type_, value, trace):
    """Global exception handler.
    Prints uncaught exceptions with the custom formatter.

    Args:
        type_: Exception type
        value: Exception value
        trace: Exception trace
    """
    logging.getLogger(__name__).error("Exception occured: ",
                                      exc_info=(type_, value, trace))


sys.excepthook = handle_exception


@click.command()
@click.option('-c', '--config',
              help='Path to project configuration.',
              default=Path.cwd() / 'palgen.toml')
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
    logger = logging.getLogger(__name__)

    gen = Generator(config, outpath, tables)
    gen.collect()
    outpath = Path(outpath).resolve().absolute()
    logger.debug("Config output path: %s", outpath)
    outpath.mkdir(parents=True, exist_ok=True)
    gen.parse()
