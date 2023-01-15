import logging
import sys

from colorama import init

from palgen.loader import Loader
from palgen.integrations.conan import Conan
from palgen.util.log import setup_logger
from palgen.cli import cli as main

init()
setup_logger()


__all__ = ['Loader', 'Conan', 'main']
globals()['Project'] = Loader

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
