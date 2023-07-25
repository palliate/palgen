from typing import Type
import pytest
from palgen.ingest.filter import Filter, Pattern
from pathlib import Path, PureWindowsPath, PurePosixPath
import re


class Identity:
    ...


W = PureWindowsPath
P = PurePosixPath


def test_init_str():
    needles = ['foo', 'bar', 'baz']
    filter_instance = Filter(*needles)
    assert filter_instance.needles == ['foo', 'bar', 'baz']

    for needle in filter_instance.needles:
        assert isinstance(needle, str)


def test_init_regex():
    filter_instance = Filter('^foo', 'bar$', 'baz', regex=True)
    for needle in filter_instance.needles:
        assert isinstance(needle, re.Pattern)

    filter_instance = Filter('^foo', 'bar$', '^baz$', regex=False)
    for needle in filter_instance.needles:
        assert isinstance(needle, re.Pattern)


def test_init_unix():
    needles = ['^foo', 'bar$', 'baz']
    filter_instance = Filter(*needles, unix=True)
    for needle in filter_instance.needles:
        assert isinstance(needle, re.Pattern)


def test_match_str():
    needles = ['foo', 'bar', 'baz']
    filter_instance = Filter(*needles)
    assert filter_instance.match_str('foo') is True
    assert filter_instance.match_str('bar') is True
    assert filter_instance.match_str('baz') is True
    assert filter_instance.match_str('foobar') is False


def test_match_files():
    files = [Path('foo.txt'), Path('bar.txt'), Path('foobar.txt')]
    needles = ['foo.txt', 'bar.txt', 'baz.txt']
    filter_instance = Filter(*needles)
    matched_files = list(filter_instance.match_files(files))
    assert matched_files == [Path('foo.txt'), Path('bar.txt')]


def test_call():
    files = [Path('foo.txt'), Path('bar.txt'), Path('foobar.txt')]
    needles = ['foo.txt', 'bar.txt', 'baz.txt']
    filter_instance = Filter(*needles)
    filtered_files = list(filter_instance(files))
    assert filtered_files == [Path('foo.txt'), Path('bar.txt')]


@pytest.mark.parametrize('patterns,unix,expected', [
    (['.*'],                False, Identity),
    (['*'],                 True,  Identity),
    ([re.compile('.*')],    True,  Identity),
    ([r".*\.h"],            False, [P("/foo/bar.h"), W("//foo/bar/baz.h")]),
    (["*.h"],               True,  [P("/foo/bar.h"), W("//foo/bar/baz.h")]),
    ([re.compile("C:")],    False, [W("C:\\"), W("C:\\foo\\bar.c")]),
    ([re.compile("C:")],    True,  [W("C:\\"), W("C:\\foo\\bar.c")]),
    ([".*.h", ".*.c"],              False,  [P("/foo/bar.c"), P("/foo/bar.h"), P("/bar/foo.c"),
                                             P("/foo/bar.cpp"), W("C:\\foo\\bar.c"), W("//foo/bar/baz.h")]),
    ([r".*\.h$", r".*\.c$"],         False,  [P("/foo/bar.c"), P("/foo/bar.h"), P("/bar/foo.c"),
                                              W("C:\\foo\\bar.c"), W("//foo/bar/baz.h")]),
    (["*.h", "*.c"],                 True,  [P("/foo/bar.c"), P("/foo/bar.h"), P("/bar/foo.c"),
                                             W("C:\\foo\\bar.c"), W("//foo/bar/baz.h")]),
    ([re.compile(r".*\.h$"), "*.c"], True,  [P("/foo/bar.c"), P("/foo/bar.h"), P("/bar/foo.c"),
                                             W("C:\\foo\\bar.c"), W("//foo/bar/baz.h")])
])
def test_pattern(patterns: list[str], unix: bool, expected: list | Type[Identity]):
    paths = [P("/foo/bar"), P("/foo/bar.c"), P("/foo/bar.cpp"),
             P("/foo/bar.h"), P("/bar/foo.c"), P("/"), P("/f/o/o/bar.toml"),
             W("C:\\foo\\bar.c"), W("C:\\"), W("//foo/bar/baz.h")]
    matcher = Pattern(*patterns, unix=unix)

    if expected is Identity:
        expected = paths
    assert isinstance(expected, list)

    result = list(matcher(paths))
    assert len(expected) == len(result)

    for value in expected:
        assert value in result
