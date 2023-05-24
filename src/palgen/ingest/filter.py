import fnmatch
import re
from pathlib import Path
from typing import Iterable


class Filter:
    def __init__(self, *needles: str | re.Pattern, regex: bool = False, unix: bool = False) -> None:
        self.needles: list[str | re.Pattern] = []

        for needle in needles:
            assert isinstance(needle, (str, re.Pattern)), \
                f"Expected str or Pattern, got {type(needle)}"

            if isinstance(needle, re.Pattern):
                self.needles.append(needle)
            elif regex or unix or needle.startswith('^') or needle.endswith('$'):
                self.needles.append(re.compile(fnmatch.translate(needle)
                                               if unix else needle))
            else:
                self.needles.append(needle)

    def match_str(self, other: str):
        for needle in self.needles:
            matches = re.match \
                if isinstance(needle, re.Pattern) else str.__eq__
            print(needle)
            if matches(needle, other):
                return True
        return False

    def match_files(self, files: Iterable[Path], attribute=None):
        for file in files:
            assert isinstance(file, Path), f"File isn't a Path object: {file}"
            if self.match_str(str(file)
                              if attribute is None
                              else getattr(file, attribute)):
                yield file

    def ingest(self, files: Iterable[Path | str]) -> Iterable[Path]:
        yield from self.match_files(files)

    def __call__(self, file_cache: Iterable[Path]) -> Iterable[Path]:
        yield from self.ingest(file_cache)


class Pattern(Filter):
    def __init__(self, *patterns: str, unix: bool = False) -> None:
        super().__init__(*patterns, regex=True, unix=unix)


class Extension(Filter):
    def ingest(self, files: Iterable[Path]) -> Iterable[Path]:
        yield from self.match_files(files, 'suffix')


class Stem(Filter):
    def ingest(self, files: Iterable[Path]) -> Iterable[Path]:
        yield from self.match_files(files, 'stem')


class Name(Filter):
    def ingest(self, files: Iterable[Path]) -> Iterable[Path]:
        yield from self.match_files(files, 'name')
