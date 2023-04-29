import timeit
def foo2(bar):
    for i in bar:
        yield 11 + i


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

from functools import reduce
from pprint import pprint

class Pipeline:
    def __init__(self, state=None):
        self.steps = [state] if state is not None else []

    def __rshift__(self, step):
        if isinstance(step, type):
            try:
                step = step()
            except TypeError as exc:
                raise ValueError("Type in pipeline is not default constructible") from exc

        self.steps.append(step)
        return self

    def __iter__(self):
        print(self)
        yield from reduce(lambda state, step: step(state), self.steps)

    def __call__(self, state):
        self.steps = [state, *self.steps]
        yield from self


def zoinkers(bar):
    for i in bar:
        yield i * 2

class Foinkers(Pipeline):
    def __call__(self, data):
        for i in data:
            if i > 4:
                yield i

def boinkers(bar):
    for i in bar:
        yield f'stringified:{str(i)}'

foo = Foinkers(range(10)) >> zoinkers >> Foinkers >> boinkers
pprint(list(foo))
