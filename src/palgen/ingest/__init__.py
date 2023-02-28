#from dataclasses import dataclass
#from functools import cached_property

from pathlib import Path
from abc import abstractmethod
from typing import Iterable, Any, Optional
from palgen.util.filesystem import SuffixDict


"""
@dataclass
class Meta:
    qualname: list[str]
    source: Path

    @cached_property
    def name(self):
        assert self.qualname
        return self.qualname[0]

    @cached_property
    def namespace(self):
        assert self.qualname
        return self.qualname[:-1]"""

class Filter:
    def __init__(self, name: Optional[str] = None, extension: Optional[str] = None):
        # TODO: wildcards
        self.name = name or ""
        self.extension = extension or ""

        assert self.name or self.extension

    def __call__(self, file_cache: SuffixDict) -> Iterable[Path]:
        if not self.name:
            for _, path in file_cache.by_extension(self.extension).items():
                yield from path
            return

        yield from file_cache.by_name(f"{self.name}{self.extension}")

class Ingest:
    def __init__(self, filter_: Filter):
        self.filter = filter_

    @abstractmethod
    def ingest(self, files: Iterable[Path]) -> Iterable[tuple[Path, Any]]:
        raise NotImplementedError

        # sourcery skip: remove-unreachable-code; pylint: disable=unreachable
        yield # type: ignore [unreachable]

    def __call__(self, file_cache: SuffixDict) -> Iterable[tuple[Path, Any]]:
        return self.ingest(self.filter(file_cache))

class Nothing(Ingest):
    def ingest(self, files: Iterable[Path]) -> Iterable[tuple[Path, Any]]:
        return
        # sourcery skip: remove-unreachable-code; pylint: disable=unreachable
        yield # type: ignore [unreachable]
