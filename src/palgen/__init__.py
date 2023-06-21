import __main__
import importlib.metadata
import logging
from pathlib import Path
import sys

from colorama import init
from click import Context

from palgen.cli import cli as main
from palgen.loaders.python import Python
from palgen.palgen import Palgen
from palgen.util.log import setup_logger, set_min_level
from palgen.util.filesystem import find_backwards

init()
setup_logger()

logger = logging.getLogger(__name__)
__version__ = importlib.metadata.version('palgen')
__all__ = ['Palgen', 'main']


def handle_exception(type_, value, trace):
    """Global exception handler.
    Prints uncaught exceptions with the custom formatter.

    Args:
        type_: Exception type
        value: Exception value
        trace: Exception trace
    """
    logger = logging.getLogger(__name__)
    if logger.isEnabledFor(logging.DEBUG):
        logger.exception("Exception occured: ", exc_info=(type_, value, trace))
    else:
        logger.critical("Exception occured: %s %s", type_.__name__, value)


sys.excepthook = handle_exception


def run_directly(module_path):
    # TODO add proper command line interface
    # TODO add options
    set_min_level(0)

    # find palgen.toml
    config = find_backwards("palgen.toml", source_dir=module_path.parent)

    obj = Palgen(config)

    # TODO investigate why running with more than one job does not work in this mode
    obj.options.jobs = 1

    # load file to inspect modules
    module = dict(Python().load(module_path, project=obj.project))
    if len(module) > 1:
        logger.warning("Found multiple modules: %s", list(module.keys()))
        logger.warning("Cannot run directly, aborting.")
        sys.exit(0)

    for key, value in module.items():
        instance = value(obj.root, obj.root, obj.settings[key])
        generated = instance.run(obj.files, obj.options.jobs)
        logger.info("Generated %d files.", len(generated))


# This hack allows running modules directly
if _importer_path := getattr(__main__, '__file__', None):
    # when palgen is run directly the suffix will never be '.py'
    # however if you run a module directly it'll correspond to the module's file
    # ie `python test.py` => _module = 'test.py'
    if (_module := Path(_importer_path)).suffix == '.py':
        run_directly(_module)
