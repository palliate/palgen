import copy as _copy
from typing import Any, Callable, TypeVar


def setattr_default(cls: type, name: str, default: Any):
    if not hasattr(cls, name):
        setattr(cls, name, default)


T = TypeVar('T')


def copy_attrs(source: Any, target: Any, copy: bool = False, deepcopy: bool = False) -> None:
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

    operation: Callable[[Any], Any]
    if copy:
        operation = _copy.copy
    elif deepcopy:
        operation = _copy.deepcopy
    else:
        # pylint: disable-next=C3001
        operation = lambda obj: obj # noqa: E731

    for slot in getattr(source, '__slots__', ()):
        setattr(target, slot, operation(getattr(source, slot)))

    for attr, value in getattr(source, '__dict__', {}).items():
        setattr(target, attr, operation(value))
