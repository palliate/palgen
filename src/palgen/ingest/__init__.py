#from dataclasses import dataclass
#from functools import cached_property

from pathlib import Path
from abc import abstractmethod
from typing import Iterable, Any
from palgen.util.filesystem import SuffixDict


class Ingest:
    @abstractmethod
    def ingest(self, files: Iterable[Path]) -> Iterable[tuple[Path, Any]]:
        raise NotImplementedError

        # sourcery skip: remove-unreachable-code; pylint: disable=unreachable
        yield # type: ignore [unreachable]

    def __call__(self, file_cache: SuffixDict) -> Iterable[tuple[Path, Any]]:
        yield from self.ingest(file_cache)

class Nothing(Ingest):
    def ingest(self, files: Iterable[Path]) -> Iterable[tuple[Path, Any]]:
        return
        # sourcery skip: remove-unreachable-code; pylint: disable=unreachable
        yield # type: ignore [unreachable]
