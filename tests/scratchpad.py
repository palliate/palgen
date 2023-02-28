import timeit
from functools import reduce


def foo1(bar):
    for i in bar:
        yield i + 1


def foo2(bar):
    for i in bar:
        yield 10 + i


def foo3(bar):
    for i in bar:
        yield 'foo3:' + str(i)


def wrap(f):
    return lambda: list(f())

LIMIT = 100000
RUNS = 100


def time(*funcs):
    for func in funcs:
        duration = timeit.Timer(wrap(func)).timeit(number=RUNS)
        avg_duration = duration/RUNS
        print(
            f'Average after {RUNS} runs: {func.__name__} {avg_duration} seconds')


class Pipeline:
    def __init__(self, state=None):
        self.steps = [state] if state is not None else []

    def __rshift__(self, step):
        self.steps.append(step)
        return self

    def __iter__(self):
        yield from reduce(lambda state, step: step(state), self.steps)


class Pipe:
    def __init__(self, step, next=None):
        self.step = step
        self.next = next

    def __rshift__(self, step):
        return Pipe(self, step)

    def __iter__(self):
        yield from self.next(self.step) if self.next is not None else self.step

class Pipelineable:
    def __init__(self, task):
        self.task = task

    def __rrshift__(self, x):
        return self.task(x)

def nested():
    yield from foo3(foo2(foo1(range(0, LIMIT))))

def reduced():
    yield from reduce(lambda state, step: step(state), [
        range(0, LIMIT),
        foo1,
        foo2,
        foo3
    ])

def pipelined():
    yield from (Pipeline(range(0, LIMIT))
                >> foo1
                >> foo2
                >> foo3
                >> list)

def piped():
    yield from (Pipe(range(0, LIMIT))
                >> foo1
                >> foo2
                >> foo3
                >> list)

def pipe3():
    yield from (
        range(LIMIT)
        >> Pipelineable(foo1)
        >> Pipelineable(foo2)
        >> Pipelineable(foo3)
    )

time(nested, reduced, pipelined, piped, pipe3)
