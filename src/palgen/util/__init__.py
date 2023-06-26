from pathlib import Path
import traceback
from typing import Any
from palgen.util.pipeline import Pipeline
from palgen.util.filesystem import Sources
import copy as _copy

__all__ = ['Pipeline', 'Sources']


def setattr_default(cls: type, name: str, default: Any):
    if not hasattr(cls, name):
        setattr(cls, name, default)


def chain_with_args(*args, generators=None, **kwargs):
    if not generators:
        return
    print(f"{args=} {kwargs=} {generators=}")
    for generator in generators:
        yield from generator(*args, **kwargs)

def strip_quotes(string):
    if string[0] == string[-1] and string[0] in ('\'', '\"'):
        return string[1:-1]
    return string

def get_caller() -> traceback.FrameSummary:
    return traceback.extract_stack(limit=3)[-3]


def get_caller_path() -> Path:
    frame = traceback.extract_stack(limit=3)[-3]
    return Path(frame.filename)

class MockAttributes:
    __slots__ = ['_items']
    def __init__(self, **kwargs) -> None:
        self._items = kwargs

    def __getattribute__(self, name: str) -> Any:
        items = object.__getattribute__(self, '_items')
        if name in items:
            return items.get(name)

        return object.__getattribute__(self, name)

def copy_attrs(source: Any, target: Any, copy: bool = False, deepcopy: bool = False):
    """Copies attributes from one object to another.

    Notes:
        If neither copy nor deepcopy are set this will just update attribute references.

    Args:
        source (Any): The source object from which attributes will be copied.
        target (Any): The target object to which attributes will be copied.
        copy (bool, optional): Whether to perform a shallow copy. Defaults to False.
        deepcopy (bool, optional):  Whether to perform a deep copy. Defaults to False.

    """
    assert not (copy and deepcopy), "Expected either copy, deepcopy or neither but not both."

    operation = (_copy.copy if copy
                else _copy.deepcopy if deepcopy
                else lambda obj: obj)

    for slot in getattr(source, '__slots__', ()):
        setattr(target, slot, operation(getattr(source, slot)))

    for attr, value in getattr(source, '__dict__', {}).items():
        setattr(target, attr, operation(value))
