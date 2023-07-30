from abc import abstractmethod
from pathlib import Path
from typing import Generator, Type

from ..ext import Extension

LoaderGenerator = Generator[tuple[str, Type[Extension]], None, None]
class Loader:
    @abstractmethod
    def ingest(self, sources: list[Path]) -> LoaderGenerator:
        """Searches the given sources for ingestable extensions and loads them.

        Args:
            sources (Iterable[Path]): An iterable of paths to input files

        Yields:
            tuple[str, Type[Extension]]: name and class of all discovered palgen extensions
        """

    @abstractmethod
    def load(self, path: Path) -> LoaderGenerator:
        """Attempt loading palgen extensions from the given path.

        Args:
            path (Path): Target file

        Yields:
            tuple[str, Type[Extension]]: name and class of all discovered palgen extensions
        """
