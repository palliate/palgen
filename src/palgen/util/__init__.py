from typing import Any
from palgen.util.pipeline import Pipeline

__all__ = ['Pipeline']


def setattr_default(cls: type, name: str, default: Any):
    if not hasattr(cls, name):
        setattr(cls, name, default)


def chain_with_args(generators, *args, **kwargs):
    for generator in generators:
        yield from generator(*args, **kwargs)

def strip_quotes(string):
    if string[0] == string[-1] and string[0] in ('\'', '\"'):
        return string[1:-1]
    return string
