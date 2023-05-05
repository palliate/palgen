from functools import reduce, partial
from typing import Optional, Callable, Iterable, Any
from inspect import signature, ismethod, isfunction

StepType = Callable[[Iterable], Iterable]


class PipelineMeta(type):
    def __rshift__(cls, step: StepType):  # sourcery skip: instance-method-first-arg-name
        return cls().__rshift__(step)


class Pipeline(metaclass=PipelineMeta):

    def __init__(self, state=None):
        self.initial_state: Optional[Iterable] = state
        self.steps: list[StepType] = []

    def __rshift__(self, step: StepType | type) -> 'Pipeline':
        if isinstance(step, type):
            try:
                step = step()
            except TypeError as exc:
                raise ValueError(f"Type `{step}` in pipeline is not default constructible") from exc

        self.steps.append(step)
        return self

    def __iter__(self, state: Optional[Iterable] = None, obj: Any = None):
        assert state is not None or self.initial_state is not None, "No initial state"

        initial_state: Optional[Iterable] = state or self.initial_state
        assert initial_state is not None
        assert self.steps

        yield from reduce(lambda state, step: self._late_bind(step, obj)(state),  # type: ignore
                          [initial_state, *self.steps])

    def __call__(self, state: Iterable, obj: Any = None):
        yield from self.__iter__(state, obj)

    @staticmethod
    def _late_bind(fnc: Callable, obj: Any):
        if obj is None or ismethod(fnc):
            # skip if we don't have an object to bind
            # or fnc is already bound
            #? checking if fnc.__self__ is not None might be sufficient?
            return fnc

        if not isfunction(fnc) or not hasattr(fnc, "__qualname__"):
            return fnc

        qualname = f"{type(obj).__qualname__}." in fnc.__qualname__
        bases = any(f"{base.__qualname__}." in fnc.__qualname__
                    for base in type(obj).__bases__)

        if not qualname and not bases:
            # fnc is defined in an unrelated class
            # try binding anyway if it has a `self` parameter
            has_self = 'self' in signature(fnc).parameters

            if not has_self:
                return fnc

        return partial(fnc, obj)
