from functools import reduce
from typing import Any


class Pipeline:
    def __init__(self, state=None):
        self.steps = [state] if state is not None else []

    def __rshift__(self, step):
        self.steps.append(step)
        return self

    def __iter__(self):
        yield from reduce(lambda state, step: step(state), self.steps)


def setattr_default(cls: type, name: str, default: Any):
    if not hasattr(cls, name):
        setattr(cls, name, default)
