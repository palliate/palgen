from palgen.ingest.filter import Pattern
from pathlib import Path


def test_pattern():
    paths = [Path(p) for p in ["/foo/bar", "/foo/bar.c", "/foo/bar.cpp", "/foo/bar.h",
             "/bar/foo.c", "/", "/f/o/o/bar.toml",
             r"C:\foo\bar.c", "C:/", r"\\foo\bar.h"]]
    matcher = Pattern(".*")
    result = list(matcher.ingest(paths))
    assert len(paths) == len(result)
