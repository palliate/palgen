import pytest
from palgen.ingest.filter import Filter, Pattern
from pathlib import Path
import re

class Identity:
    ...




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

    result = list(matcher(paths))
    assert len(expected) == len(result)

    for value in expected:
        assert Path(value) in result
