import logging
import sys

from colorama import init

from palgen.palgen import Palgen
from palgen.integrations.conan.recipe import Conan
from palgen.util.log import setup_logger
from palgen.cli import cli as main

init()
setup_logger()


__all__ = ['Palgen', 'Conan', 'main']
globals()['Project'] = Palgen

def handle_exception(type_, value, trace):
    """Global exception handler.
    Prints uncaught exceptions with the custom formatter.

    Args:
        type_: Exception type
        value: Exception value
        trace: Exception trace
    """
    logger = logging.getLogger(__name__)
    if True:#logger.isEnabledFor(logging.DEBUG):
        logger.exception("Exception occured: ", exc_info=(type_, value, trace))
    else:
        logger.error("Exception occured: %s %s", type_.__name__, value)


sys.excepthook = handle_exception
