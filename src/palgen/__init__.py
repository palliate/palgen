import importlib.metadata
from .application import main, setup_logger, check_direct_run, Palgen

__version__ = importlib.metadata.version('palgen')
__all__ = ['Palgen', 'main']

setup_logger()
check_direct_run()
