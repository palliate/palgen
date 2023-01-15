import timeit
from functools import reduce


def foo1(g):
    for i in g:
        yield i + 1


def foo2(g):
    for i in g:
        yield 10 + i


def foo3(g):
    for i in g:
        yield 'foo3:' + str(i)


LIMIT = 10000000


def wrap(f):
    return lambda: list(f())


def time(*funcs):
    for func in funcs:
        num_runs = 20
        duration = timeit.Timer(wrap(func)).timeit(number=num_runs)
        avg_duration = duration/num_runs
        print(
            f'Average after {num_runs} runs: {func.__name__} {avg_duration} seconds')


def pipeline(*steps):
    return reduce(lambda x, y: y(x), list(steps))


class Pipeline:
    def __init__(self, data):
        self.data = data
        self.functions = []

    def __rshift__(self, x):
        self.functions.append(x)
        return self
        # return self.task(Pipeline(x))

    def __iter__(self):
        x = self.data
        for function in self.functions:
            x = function(x)
        yield from x

    def d__iter__(self):
        yield from reduce(lambda x, y: y(x), self.functions)


def nested():
    yield from foo3(foo2(foo1(range(0, LIMIT))))

def pipelined():
    yield from reduce(lambda x, y: y(x), [
        range(0, LIMIT),
        foo1,
        foo2,
        foo3
    ])

def operator():
    yield from (Pipeline(range(0, LIMIT))
                >> foo1
                >> foo2
                >> foo3)


time(nested, pipelined, operator)

# print(list(operator()))
