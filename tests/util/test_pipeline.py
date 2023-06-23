import pytest
from palgen.util import Pipeline
from palgen.util.pipeline import PipelineMeta


def passthrough(data):
    yield from data


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


def test_functor_type():
    pipe = Pipeline(range(10)) >> Even >> MultiplyFactor(3)
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


def test_mixed_lazy():
    pipe = Pipeline() >> odd >> MultiplyFactor(3) >> square
    pipe2 = Pipeline >> odd >> MultiplyFactor(3) >> square
    # 0, 1, 2, 3, 4, 5, 6, 7, 8, 9
    # 1, 3, 5, 7, 9
    # 3, 9, 15, 21, 27
    # 9, 81, 225, 441, 729
    for pipeline in pipe, pipe2:
        result = list(pipeline(range(10)))
        assert result == [9, 81, 225, 441, 729]


def test_string():
    pipe = Pipeline("abcd") >> ToOrd() >> Even() >> MultiplyFactor(2)
    # 'a' 'b' 'c' 'd'
    # 97 98 99 100
    # 98 100
    # 196 200
    result = list(pipe)
    assert result == [196, 200]


def test_methods():

    class Unrelated:
        def triple(self, data):
            assert not isinstance(self, Unrelated)

            for datum in data:
                yield datum * 3

    class Foo:
        def increment(self, data):
            for datum in data:
                yield datum + 1

    class Bar(Foo):
        def multiply(self, data):
            for datum in data:
                yield datum * 2
        pipeline = Pipeline >> Foo.increment >> multiply >> Unrelated.triple

        def run(self):
            return list(self.pipeline(range(10), self))

        def run_local(self):
            pipeline = Pipeline >> self.increment >> self.multiply >> Unrelated.triple
            return list(pipeline(range(10), self))

    bar = Bar()
    result = list(bar.pipeline(range(10), bar))

    # 0,  1,  2,  3,  4,  5,  6,  7,  8,  9
    # 1,  2,  3,  4,  5,  6,  7,  8,  9, 10
    # 2,  4,  6,  8, 10, 12, 13, 16, 18, 20
    # 6, 12, 18, 24, 30, 36, 42, 48, 54, 60
    assert result          == [6, 12, 18, 24, 30, 36, 42, 48, 54, 60]
    assert bar.run()       == [6, 12, 18, 24, 30, 36, 42, 48, 54, 60]
    assert bar.run_local() == [6, 12, 18, 24, 30, 36, 42, 48, 54, 60]


def test_nested():
    first = Pipeline >> odd >> MultiplyFactor(2)
    second = Pipeline >> first >> square

    result = list(second(range(10)))
    # 0, 1, 2, 3, 4, 5, 6, 7, 8, 9
    # 1, 3, 5, 7, 9
    # 2, 6, 10, 14, 18
    # 4, 36, 100, 196, 324
    assert result == [4, 36, 100, 196, 324]


@pytest.mark.parametrize("pipeline, meta_count, ctor_count, call_count",
                         [
                             ('Pipeline >> passthrough', 1, 1, 1),
                             ('Pipeline() >> passthrough', 0, 1, 1),
                             ('Pipeline', 0, 1, 0),
                             ('Pipeline()', 0, 1, 1)
                         ])
def test_identity(mocker, pipeline, meta_count, ctor_count, call_count):
    meta = mocker.spy(PipelineMeta, '__rshift__')
    iter_ = mocker.spy(Pipeline, '__iter__')
    ctor = mocker.spy(Pipeline, '__init__')
    call = mocker.spy(Pipeline, '__call__')

    empty = eval(pipeline)  # pylint: disable=eval-used
    assert meta.call_count == meta_count

    result = list(empty(range(5)))

    assert result == [0, 1, 2, 3, 4]
    assert ctor.call_count == ctor_count
    assert call.call_count == call_count
