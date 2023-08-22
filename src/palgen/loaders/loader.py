from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Iterable, Type

import click

from ..interface import Extension


class Kind(Enum):
    PRIVATE = auto()
    PUBLIC = auto()
    BUILTIN = auto()


@dataclass
class ExtensionInfo:
    extension: click.Command | click.Group | Type[Extension]
    module: str
    path: Path
    kind: Kind
    inherited: bool = False

    @property
    def name(self) -> str:
        if self.inherited:
            return self.module

        assert self.extension.name is not None, f"NO NAME: {self.extension}"
        return self.extension.name


class Loader:
    __slots__ = ()

    @abstractmethod
    def ingest(self, sources: Iterable[Path | str]) -> Iterable[ExtensionInfo]:
        """Searches the given sources for ingestable extensions and loads them.

        Args:
            sources (Iterable[Path | str]): An iterable of paths to input files or strings

        Yields:
            tuple[str, Type[Extension]]: name and class of all discovered palgen extensions
        """

    @abstractmethod
    def load(self, source: Path | str) -> Iterable[ExtensionInfo]:
        """Attempt loading palgen extensions from the given path or string.

        Args:
            source (Path | str): Source to load from

        Yields:
            tuple[str, Type[Extension]]: name and class of all discovered palgen extensions
        """
