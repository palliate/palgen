import pytest

from palgen.util import Pipeline


def odd(data):
    for datum in data:
        if datum % 2 != 0:
            print(f"Odd:    yielding {datum}")
            yield datum


def square(data):
    for datum in data:
        print(f"Square: yielding {datum * datum}")
        yield datum * datum


class Even:
    def __call__(self, data):
        for datum in data:
            if datum % 2 == 0:
                yield datum


class MultiplyFactor:
    def __init__(self, factor: int | float):
        self.factor = factor

    def __call__(self, data):
        for datum in data:
            yield datum * self.factor


class ToOrd:
    def __call__(self, data):
        for datum in data:
            yield ord(datum)


class FromString(Pipeline):
    # TODO
    def __init__(self, string: str):
        self.string = string
        super().__init__()

    def __call__(self):
        for character in self.string:
            yield character


def test_function():
    pipe = Pipeline(range(10)) >> odd >> square
    # 0, 1, 2, 3, 4, 5, 6, 7, 8, 9
    # 1, 3, 5, 7, 9
    # 1, 9, 25, 49, 81
    result = list(pipe)
    assert result == [1, 9, 25, 49, 81]


def test_functor():
    pipe = Pipeline(range(10)) >> Even() >> MultiplyFactor(3)
    # 0, 1, 2, 3, 4, 5, 6, 7, 8, 9
    # 0, 2, 4, 6, 8
    # 0, 6, 12, 18, 24
    result = list(pipe)
    assert result == [0, 6, 12, 18, 24]


def test_mixed():
    pipe = Pipeline(range(10)) >> odd >> MultiplyFactor(3) >> square
    # 0, 1, 2, 3, 4, 5, 6, 7, 8, 9
    # 1, 3, 5, 7, 9
    # 3, 9, 15, 21, 27
    # 9, 81, 225, 441, 729
    result = list(pipe)
    assert result == [9, 81, 225, 441, 729]


def test_introducer():
    pipe = FromString("asdf") >> ToOrd() >> Even() >> MultiplyFactor(.5)
    # 'a' 'b' 'c' 'd'
    # 97 98 99 100
    # 98 100
    # 49 50
    result = list(pipe)
    assert result == [49, 50]
