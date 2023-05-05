from typing import Any
from palgen.util.pipeline import Pipeline

__all__ = ['Pipeline']

def setattr_default(cls: type, name: str, default: Any):
    if not hasattr(cls, name):
        setattr(cls, name, default)
