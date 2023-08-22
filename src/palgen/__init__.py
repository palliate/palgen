import importlib.metadata

from pydantic import BaseModel as Model

from .application import check_direct_run, main, setup_logger
from .interface import Extension, max_jobs
from .machinery import Pipeline as Sources
from .palgen import Palgen

__version__ = importlib.metadata.version('palgen')
__all__ = ['Model', 'Sources', 'Extension', 'max_jobs',
           'Palgen', 'main']

setup_logger()
check_direct_run()
