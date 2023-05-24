from pathlib import Path
from traceback import FrameSummary
from palgen import util


def test_caller():
    def inner() -> FrameSummary:
        return util.get_caller()

    def outer() -> FrameSummary:
        return inner()

    assert outer().name == "outer"
    assert outer().line == "return inner()"
    assert outer().lineno == 11
    assert outer().filename == __file__


def test_caller_path():
    def inner() -> Path:
        return util.get_caller_path()

    def outer() -> Path:
        return inner()

    assert outer() == Path(__file__)
