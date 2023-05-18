# TODO

import fnmatch
import re
from pathlib import Path
from typing import Iterable

from palgen.util.filesystem import SuffixDict


class Filter:
    def __init__(self, *needles: str, regex: bool = False, unix: bool = False) -> None:
        super().__init__()
        self.needles: list[str | Pattern] = []

        for needle in needles:
            if regex or needle.startswith('^') or needle.endswith('$'):
                self.needles.append(re.compile(fnmatch.translate(needle)
                                               if unix else needle))
            else:
                self.needles.append(needle)

    def matches(self, other: str):
        for needle in self.needles:
            matches = re.match if isinstance(needle, Pattern) else str.__eq__
            if matches(needle, other):
                return True
        return False

    def ingest(self, files: Iterable[Path | str]) -> Iterable[Path]:
        if isinstance(files, SuffixDict):
            for needle in self.needles:
                yield from files.by_pattern(needle)
        else:
            for file in files:
                if self.matches(str(file)):
                    yield file

    def __call__(self, file_cache: Iterable[Path] | SuffixDict) -> Iterable[Path]:
        yield from self.ingest(file_cache)


class Pattern(Filter):
    def __init__(self, *patterns: str, unix: bool = False) -> None:
        super().__init__(*patterns, True, unix)


class Extension(Filter):
    def ingest(self, files: Iterable[Path] | SuffixDict) -> Iterable[Path]:
        if isinstance(files, SuffixDict):
            for needle in self.needles:
                yield from files.by_extension(needle)
        else:
            yield from super().ingest(file.suffix for file in files)


class Stem(Filter):
    def ingest(self, files: Iterable[Path]) -> Iterable[Path]:
        if isinstance(files, SuffixDict):
            for needle in self.needles:
                yield from files.by_stem(needle)
        else:
            yield from super().ingest(file.stem for file in files)


class Name(Filter):
    def ingest(self, files: Iterable[Path]) -> Iterable[Path]:
        if isinstance(files, SuffixDict):
            for needle in self.needles:
                yield from files.by_name(needle)
        else:
            yield from super().ingest(file.name for file in files)
