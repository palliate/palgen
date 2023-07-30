import inspect
import logging
from functools import partial, reduce
from inspect import isfunction, isgenerator, ismethod, signature
from multiprocessing import cpu_count
from multiprocessing.pool import Pool
from typing import Any, Callable, Generator, Iterable, Optional, Type

from .types import issubtype

_logger = logging.getLogger(__name__)


_Step = Callable[[Iterable], Iterable] | Generator[Any, Any, Any] | \
    partial[Callable[[Iterable], Iterable] | Generator[Any, Any, Any]]
Step = _Step | partial[_Step]


def get_name(obj):
    if isinstance(obj, str):
        return obj
    return obj.__name__ if hasattr(obj, "__name__") else type(obj).__name__


class PipelineMeta(type):
    __slots__ = ()

    def __rshift__(cls, step: Step | Type['Pipeline'] | Any) -> 'Pipeline':
        # sourcery skip: instance-method-first-arg-name

        return cls().__rshift__(step)


class Task:
    __slots__ = 'max_jobs', 'steps'

    def __init__(self, steps: Optional[list[Step]] = None, max_jobs: int = 0):
        self.steps: list[Step] = steps or []
        self.max_jobs = max_jobs

    def append(self, step) -> None:
        self.steps.append(step)

    def __str__(self) -> str:
        return ' >> '.join(get_name(obj) for obj in self.steps)

    def __repr__(self) -> str:
        return f'Task(steps={self.steps}, max_jobs={self.max_jobs})'

    def __bool__(self) -> bool:
        return bool(self.steps)


class Pipeline(metaclass=PipelineMeta):
    __slots__ = 'initial_state', 'tasks'

    def __init__(self, state=None):
        self.initial_state: Optional[Iterable] = state
        self.tasks: list[Task] = [Task()]

    def __rshift__(self, step: Step | Type['Pipeline'] | Any) -> 'Pipeline':
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

        wants_list = any(issubtype(parameter.annotation, list)
                         for name, parameter in step_signature.parameters.items()
                         if name != 'self')
        max_jobs = getattr(step, 'max_jobs', 1 if wants_list else 0)

        if wants_list or max_jobs != self.tasks[-1].max_jobs:
            self.tasks.append(Task(max_jobs=max_jobs))

        if isinstance(step, Pipeline) and step.initial_state is None:
            if not self.tasks[-1]:
                self.tasks = step.tasks
            else:
                self.tasks.extend(step.tasks)
        else:
            self.tasks[-1].append(step)
        return self

    def _run_task(self, state: Optional[Iterable] = None, obj: Any = None, task: Optional[Task] = None):
        initial_state: Optional[Iterable] = state if state is not None else self.initial_state
        assert initial_state is not None, "No initial state"
        if task is None or not initial_state:
            return []

        return list(reduce(lambda state, step: self._bind_step(step, obj)(state) or [],  # type: ignore
                           [initial_state, *task.steps]))

    def __iter__(self, state: Optional[Iterable] = None, obj: Any = None):
        if not self.tasks:
            return

        for task in self.tasks:
            yield from self._run_task(state=state, obj=obj, task=task)

    def __call__(self, state: list[Any], obj: Any = None, max_jobs: Optional[int] = None):
        output = state
        for task in self.tasks:
            if not output:
                break

            jobs = task.max_jobs or max_jobs or cpu_count()

            if jobs == 1:
                output = self._run_task(state=output, obj=obj, task=task)
                continue

            # synchronize after every task
            with Pool(processes=jobs) as pool:
                _logger.debug("Running with %d jobs", jobs)
                chunks = [output[i::jobs] for i in range(jobs)]  # partition
                output = []  # reset buffer
                for chunk in pool.imap(partial(self._run_task, obj=obj, task=task), chunks):
                    if not chunk:
                        continue

                    output.extend(chunk)
        return output

    run = __call__

    def __repr__(self):
        return f"{str(self.initial_state or '[object]')} " + \
            ' |'.join(f"{task.max_jobs or cpu_count()}>> {task}"
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
