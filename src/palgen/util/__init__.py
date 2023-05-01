from functools import reduce
from typing import Any, Iterable, Optional


class Pipeline:
    def __init__(self, state: Optional[Any] = None):
        self.steps = [state] if state is not None else []

    def __rshift__(self, step) -> 'Pipeline':
        if isinstance(step, type):
            try:
                step = step()
            except TypeError as exc:
                raise ValueError("Type in pipeline is not default constructible") from exc

        self.steps.append(step)
        return self

    def __iter__(self) -> Iterable[Any]:
        yield from reduce(lambda state, step: step(state), self.steps)


def setattr_default(cls: type, name: str, default: Any):
    if not hasattr(cls, name):
        setattr(cls, name, default)
