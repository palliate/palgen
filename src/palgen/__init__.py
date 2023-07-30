import importlib.metadata

from .application import Palgen, check_direct_run, main, setup_logger

__version__ = importlib.metadata.version('palgen')
__all__ = ['Palgen', 'main']

setup_logger()
check_direct_run()
