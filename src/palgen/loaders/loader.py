from pathlib import Path
from abc import abstractmethod
from typing import Generator, Type

from palgen.module import Module

LoaderGenerator = Generator[tuple[str, Type[Module]], None, None]
class Loader:
    @abstractmethod
    def ingest(self, sources: list[Path]) -> LoaderGenerator:
        """Searches the given sources for ingestable modules and loads them.

        Args:
            sources (Iterable[Path]): An iterable of paths to input files

        Yields:
            tuple[str, Type[Module]]: name and class of all discovered palgen modules
        """

    @abstractmethod
    def load(self, path: Path) -> LoaderGenerator:
        """Attempt loading palgen modules from the given path.

        Args:
            path (Path): Target file

        Yields:
            tuple[str, Type[Module]]: name and class of all discovered palgen modules
        """
