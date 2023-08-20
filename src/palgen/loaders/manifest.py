import logging
from pathlib import Path
from typing import Iterable

import toml
from pydantic import RootModel

from ..ingest.filter import Suffix
from .loader import Loader, ExtensionInfo
from .python import Python

_logger = logging.getLogger(__name__)


class ManifestSchema(RootModel):
    root: dict[str, str]

    def items(self):
        return self.root.items()


class Manifest(Loader):
    __slots__ = ('python_loader',)

    def __init__(self) -> None:
        """Loads palgen extensions from manifest files (palgen.manifest).
        """

        self.python_loader = Python()

    def ingest(self, sources: Iterable[Path]) -> Iterable[ExtensionInfo]:
        """Searches the given sources for palgen manifests and loads them.

        Args:
            sources (Iterable[Path]): An iterable of paths to input files

        Yields:
            tuple[str, Type[Extension]]: name and class of all discovered palgen extensions
        """

        for source in Suffix(".manifest", ".cache")(sources):
            assert isinstance(source, Path)
            yield from self.load(source)

    def load(self, source: Path) -> Iterable[ExtensionInfo]:
        """Attempt loading palgen extensions from manifest at the given path.

        Args:
            path (Path): Path to the manifest

        Yields:
            tuple[str, Type[Extension]]: name and class of all discovered palgen extensions
        """
        if not source.exists():
            _logger.warning("Could not find %s", source)
            return

        file = toml.load(source)
        manifest = ManifestSchema.model_validate(file)
        _logger.debug("Loading from `%s`", source)

        for name, path_str in manifest.items():
            source = Path(path_str)
            if not source.is_absolute():
                source = source.parent / source

            yield from self.python_loader.load(source, import_name=name)
