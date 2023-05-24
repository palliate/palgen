import pytest
from palgen.ingest.filter import Pattern
from pathlib import Path
import re


class Identity:
    ...


@pytest.mark.parametrize('patterns,unix,expected', [
    (['.*'],                False, Identity),
    (['*'],                 True,  Identity),
    ([re.compile('.*')],    True,  Identity),
    ([r".*\.h"],            False, ["/foo/bar.h", r"\\foo\bar.h"]),
    (["*.h"],               True,  ["/foo/bar.h", r"\\foo\bar.h"]),
    ([re.compile("C:")],    False, ["C:/", r"C:\foo\bar.c"]),
    ([re.compile("C:")],    True,  ["C:/", r"C:\foo\bar.c"]),
    ([".*.h", ".*.c"],              False,  ["/foo/bar.c", "/foo/bar.h", "/bar/foo.c",
                                             "/foo/bar.cpp", r"C:\foo\bar.c", r"\\foo\bar.h"]),
    ([r".*\.h$", r".*\.c$"],         False,  ["/foo/bar.c", "/foo/bar.h", "/bar/foo.c",
                                              r"C:\foo\bar.c", r"\\foo\bar.h"]),
    (["*.h", "*.c"],                 True,  ["/foo/bar.c", "/foo/bar.h", "/bar/foo.c",
                                             r"C:\foo\bar.c", r"\\foo\bar.h"]),
    ([re.compile(r".*\.h$"), "*.c"], True,  ["/foo/bar.c", "/foo/bar.h", "/bar/foo.c",
                                             r"C:\foo\bar.c", r"\\foo\bar.h"])
])
def test_pattern(patterns: list[str], unix: bool, expected: list | Identity):
    paths = [Path(p) for p in ["/foo/bar", "/foo/bar.c", "/foo/bar.cpp",
                               "/foo/bar.h", "/bar/foo.c", "/", "/f/o/o/bar.toml",
                               r"C:\foo\bar.c", "C:/", r"\\foo\bar.h"]]
    matcher = Pattern(*patterns, unix=unix)

    if expected is Identity:
        expected = paths

    result = list(matcher.ingest(paths))
    assert len(expected) == len(result)

    for value in expected:
        assert Path(value) in result
