#pylint: disable=invalid-name

import fnmatch
import re
from pathlib import Path, PurePath
from typing import Any, Iterable, Optional


class Filter:
    __slots__ = ('needles',)

    def __init__(self, *needles: str | re.Pattern[str], regex: bool = False, unix: bool = False) -> None:
        """ Generic filter

        Args:
            *needles (str | re.Pattern[str]): list of strings or regex patterns
            regex (bool): if True, all needles will be interpreted as regex patterns
            unix (bool): if True, all needles will be interpreted as unix patterns

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
            files: input Iterable of files to filter
            attribute: attribute of the pathlib.Path object to check against

        Yields:
            Path: for every file that matches any of the needles
        """
        for file in files:
            assert isinstance(file, (Path, PurePath)), f"File isn't a Path object: {file}"
            if self.match_str(str(file)
                              if attribute is None
                              else getattr(file, attribute)):
                yield file

    def filter(self, files: Iterable[Path]) -> Iterable[Path]:
        """
        Args:
            files: input Iterable of files to filter

        Yields:
            Path: for every file that matches any of the needles
        """
        yield from self.match_files(files)

    def __call__(self, file_cache: Iterable[Path]) -> Iterable[Path]:
        """
        Args:
            file_cache: input Iterable of files to filter

        Yields:
            Path: for every file that matches any of the needles
        """
        yield from self.filter(file_cache)


class Pattern(Filter):
    __slots__ = ()

    def __init__(self, *patterns: str | re.Pattern[str], unix: bool = False) -> None:
        """ Filter by regex or unix pattern. Equivalent to Filter(..., regex=True)

        Args:
            patterns: Iterable of strings or regex patterns
            unix: if True, all needles will be interpreted as unix patterns
        """
        super().__init__(*patterns, regex=True, unix=unix)


class Folder(Filter):
    __slots__ = ()

    def filter(self, files: Iterable[Path]) -> Iterable[Path]:
        """Filters by folder name. This will match folder names at any level

        Args:
            files (Iterable[Path]): input Iterable of files to filter

        Yields:
            Path: for every file that matches any of the needles
        """
        for file in files:
            if any(self.match_str(part) for part in file.parts):
                yield file


class Suffix(Filter):
    __slots__ = ()

    def filter(self, files: Iterable[Path]) -> Iterable[Path]:
        """Filters by suffix with leading dot. Unlike Python's default behavior this
        concatenates all suffixes.

        ie while pathlib.Path.suffix for `foo.tar.gz` would only be `.gz`,
        this will instead check against `.tar.gz`.

        Args:
            files (Iterable[Path]): input Iterable of files to filter

        Yields:
            Path: for every file that matches any of the needles
        """
        for file in files:
            suffix = ''.join(file.suffixes)

            if self.match_str(suffix):
                yield file


class Suffixes(Filter):
    __slots__ = ('position',)

    def __init__(self, *needles: str | re.Pattern[str], regex: bool = False,
                 unix: bool = False, position: Optional[int] = None) -> None:
        """ Multiple suffixes filter

        Args:
            *needles (str | re.Pattern[str]): list of strings or regex patterns
            regex (bool): if True, all needles will be interpreted as regex patterns
            unix (bool): if True, all needles will be interpreted as unix patterns
            position (Optional[int]): Check against the suffix at position `position` only.
                                      Tries all parts of the suffix if this is `None`.
        """
        self.position = position
        super().__init__(*needles, regex=regex, unix=unix)

    def filter(self, files: Iterable[Path]) -> Iterable[Path]:
        """Filters by suffix

        Args:
            files (Iterable[Path]): input Iterable of files to filter

        Yields:
            Path: for every file that matches any of the needles
        """
        for file in files:
            if self.position is None:
                if any(self.match_str(part) for part in file.suffixes):
                    yield file
            else:
                if len(file.suffixes) < self.position + 1:
                    continue

                if self.match_str(file.suffixes[self.position]):
                    yield file


class Stem(Filter):
    __slots__ = ()

    def filter(self, files: Iterable[Path]) -> Iterable[Path]:
        """Filters by stem (file's name without extension(s))
        ie the stem of `foobar.tar.gz` is `foobar`

        Args:
            files (Iterable[Path]): input Iterable of files to filter

        Yields:
            Path: for every file that matches any of the needles
        """
        yield from self.match_files(files, 'stem')


class Name(Filter):
    __slots__ = ()

    def filter(self, files: Iterable[Path]) -> Iterable[Path]:
        """Filters by name

        Args:
            files (Iterable[Path]): input Iterable of files to filter

        Yields:
            Path: for every file that matches any of the needles
        """
        yield from self.match_files(files, 'name')


def Passthrough(data: Iterable[Any]) -> Iterable[Any]:
    """No-op, yields everything from the input Iterable

    Args:
        files (Iterable[Any]): any Iterable

    Yields:
        Path: for every file that matches any of the needles
    """
    yield from data


def Nothing(data: Iterable[Any]) -> Iterable[Any]:
    """Consumes the input iterable but does not yield anything

    Args:
        files (Iterable[Any]): any Iterable

    Yields:
        Nothing whatsoever.
    """
    list(data)  # Consume the Iterable

    return
    # sourcery skip: remove-unreachable-code; pylint: disable=unreachable
    yield from data  # type: ignore [unreachable]
