import importlib.metadata

from .application import check_direct_run, main, setup_logger
from .palgen import Palgen

__version__ = importlib.metadata.version('palgen')
__all__ = ['Palgen', 'main']

setup_logger()
check_direct_run()
