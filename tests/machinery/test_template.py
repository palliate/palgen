from pathlib import Path
from traceback import FrameSummary
from palgen.machinery.template import get_caller


def test_caller():
    def inner() -> FrameSummary:
        return get_caller()

    def outer() -> FrameSummary:
        return inner()

    assert outer().name == "outer"
    assert outer().line == "return inner()"
    assert outer().lineno == 11
    assert outer().filename == __file__
