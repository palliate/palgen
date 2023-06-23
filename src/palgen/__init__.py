import importlib.metadata
import logging
import sys

from colorama import init

from palgen.cli.package import main
from palgen.cli.direct import check_direct_run
from palgen.palgen import Palgen
from palgen.util.log import setup_logger


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
    if logger.isEnabledFor(logging.DEBUG):
        logger.exception("Exception occured: ", exc_info=(type_, value, trace))
    else:
        logger.critical("Exception occured: %s %s", type_.__name__, value)


sys.excepthook = handle_exception

check_direct_run()
