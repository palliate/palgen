import fnmatch
import re
from pathlib import Path
from typing import Iterable


class Filter:
    needles: list[str | re.Pattern[str]]

    def __init__(self, *needles: str | re.Pattern[str], regex: bool = False, unix: bool = False) -> None:
        """ Generic filter
        Args:
            needles: list of strings or regex patterns
            regex: if True, all needles will be interpreted as regex patterns
            unix: if True, all needles will be interpreted as unix patterns

        Important:
            Needles that start with `^` or end with `$` are always converted to regex patterns.
        """
        self.needles: list[str | re.Pattern[str]] = []

        for needle in needles:
            assert isinstance(needle, (str, re.Pattern)), \
                f"Expected str or Pattern, got {type(needle)}"

            if isinstance(needle, re.Pattern):
                self.needles.append(needle)
            elif regex or unix:
                self.needles.append(re.compile(fnmatch.translate(needle)
                                               if unix else needle))
            elif needle.startswith('^') or needle.endswith('$'):
                self.needles.append(re.compile(needle))
            else:
                self.needles.append(needle)

    def match_str(self, other: str):
        """
        Args:
            other: string to check against

        Returns:
            True if `other` matches any of the needles
        """
        return any(re.match(needle, other)
                   if isinstance(needle, re.Pattern)
                   else needle == other
                   for needle in self.needles)

    def match_files(self, files: Iterable[Path], attribute=None):
        """
        Args:
            files: iterable of files to check against
            attribute: attribute of the pathlib.Path object to check against

        Yields:
            Path: for every file that matches any of the needles
        """
        for file in files:
            assert isinstance(file, Path), f"File isn't a Path object: {file}"
            if self.match_str(str(file)
                              if attribute is None
                              else getattr(file, attribute)):
                yield file

    def filter(self, files: Iterable[Path]) -> Iterable[Path]:
        """
        Args:
            files: list of files to check against

        Yields:
            Path: for every file that matches any of the needles
        """
        yield from self.match_files(files)

    def __call__(self, file_cache: Iterable[Path]) -> Iterable[Path]:
        """
        Args:
            file_cache: list of files to check against

        Yields:
            Path: for every file that matches any of the needles
        """
        yield from self.filter(file_cache)


class Pattern(Filter):
    def __init__(self, *patterns: str | re.Pattern[str], unix: bool = False) -> None:
        """ Filter by regex or unix pattern. Equivalent to Filter(..., regex=True)
        Args:
            patterns: iterable of strings or regex patterns
            unix: if True, all needles will be interpreted as unix patterns
        """
        super().__init__(*patterns, regex=True, unix=unix)


class Extension(Filter):
    def filter(self, files: Iterable[Path]) -> Iterable[Path]:
        """Filters by name

        Args:
            files (Iterable[Path]): list of files to check against

        Yields:
            Path: for every file that matches any of the needles
        """
        yield from self.match_files(files, 'suffix')


class Stem(Filter):
    def filter(self, files: Iterable[Path]) -> Iterable[Path]:
        """Filters by stem (file's name without extension(s))
        ie the stem of `foobar.tar.gz` is `foobar`

        Args:
            files (Iterable[Path]): list of files to check against

        Yields:
            Path: for every file that matches any of the needles
        """
        yield from self.match_files(files, 'stem')


class Name(Filter):
    def filter(self, files: Iterable[Path]) -> Iterable[Path]:
        """Filters by name

        Args:
            files (Iterable[Path]): list of files to check against

        Yields:
            Path: for every file that matches any of the needles
        """
        yield from self.match_files(files, 'name')