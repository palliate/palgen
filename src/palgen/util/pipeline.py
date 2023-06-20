from functools import reduce, partial
import inspect
import logging
from multiprocessing import Pool
from typing import Generator, Optional, Callable, Iterable, Any
from inspect import isgenerator, signature, ismethod, isfunction
import typing

from palgen.util.typing import issubtype

_Step = Callable[[Iterable], Iterable] | Generator[Any, Any,
                                                   Any] | partial[Callable[[Iterable], Iterable] | Generator[Any, Any, Any]]
Step = _Step | partial[_Step]
Task = list[Step]


class PipelineMeta(type):
    def __rshift__(cls, step: Step):  # sourcery skip: instance-method-first-arg-name
        return cls().__rshift__(step)


class Pipeline(metaclass=PipelineMeta):
    __slots__ = ['initial_state', 'tasks']

    def __init__(self, state=None):
        self.initial_state: Optional[Iterable] = state
        self.tasks: list[Task] = [[]]

    def __rshift__(self, step: Step | type) -> 'Pipeline':
        if isinstance(step, type):
            try:
                step = step()
            except TypeError as exc:
                raise ValueError(
                    f"Type `{step}` in pipeline is not default constructible") from exc
        assert not isinstance(step, type)

        step_signature = inspect.signature(step
                                           if isfunction(step) and not isgenerator(step)
                                           else getattr(step, '__call__', step))

        if any(issubtype(parameter.annotation, (list, set, dict))
               for name, parameter in step_signature.parameters.items() if name != 'self'):
            self.tasks.append([])

        if isinstance(step, Pipeline) and step.initial_state is None:
            if not self.tasks[-1]:
                self.tasks = step.tasks
            else:
                self.tasks.extend(step.tasks)
        else:
            self.tasks[-1].append(step)
        return self

    def _run_task(self, state: Optional[Iterable] = None, obj: Any = None, task: Optional[list[Step]] = None):
        initial_state: Optional[Iterable] = state if state is not None else self.initial_state
        assert initial_state is not None, "No initial state"
        if task is None or not initial_state:
            return []

        return list(reduce(lambda state, step: self._bind_step(step, obj)(state),  # type: ignore
                           [initial_state, *task]))

    def __iter__(self, state: Optional[Iterable] = None, obj: Any = None):
        if not self.tasks:
            return

        for task in self.tasks:
            yield from self._run_task(task, state, obj)

    def __call__(self, state: list[Any], obj: Any = None, jobs: int = 1):
        output = state
        with Pool(jobs) as pool:
            # synchronize after every task
            for task in self.tasks:
                chunks = [output[i::jobs] for i in range(jobs)]  # partition
                output = []  # reset buffer
                for chunk in pool.imap(partial(self._run_task, task=task, obj=obj), chunks):
                    if not chunk:
                        continue

                    output.extend(chunk)
        return output

    def __repr__(self):
        def pretty(obj):
            if isinstance(obj, str):
                return obj
            return obj.__name__ if hasattr(obj, "__name__") else type(obj).__name__

        return f"{str(self.initial_state or '[object]')} >> " + \
            ' |>> '.join(' >> '.join(pretty(obj)
                                     for obj in task)
                         for task in self.tasks)

    __str__ = __repr__

    def _bind_step(self, fnc: Callable, obj: Any):
        if obj is None or ismethod(fnc):
            # skip if fnc is already bound
            # ? checking if fnc.__self__ is not None might be sufficient?
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
