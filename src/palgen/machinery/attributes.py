from typing import Any
import copy as _copy

def setattr_default(cls: type, name: str, default: Any):
    if not hasattr(cls, name):
        setattr(cls, name, default)

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
