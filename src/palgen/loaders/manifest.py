import logging
from pathlib import Path

import toml
from pydantic import BaseModel

from .loader import Loader, LoaderGenerator
from .python import Python

_logger = logging.getLogger(__name__)


class ManifestSchema(BaseModel):
    __root__: dict[str, str]

    def items(self):
        return self.__root__.items()


class Manifest(Loader):
    __slots__ = ['python_loader']
    def __init__(self) -> None:
        """Loads palgen extensions from manifest files (palgen.manifest).
        """

        self.python_loader = Python()

    def ingest(self, sources: list[Path]) -> LoaderGenerator:
        """Searches the given sources for palgen manifests and loads them.

        Args:
            sources (Iterable[Path]): An iterable of paths to input files

        Yields:
            tuple[str, Type[Extension]]: name and class of all discovered palgen extensions
        """

        for source in sources:
            assert isinstance(source, Path)

            if not source.is_dir():
                continue

            for path in source.glob('**/palgen.manifest'):
                yield from self.load(Path(path))

    def load(self, path: Path) -> LoaderGenerator:
        """Attempt loading palgen extensions from manifest at the given path.

        Args:
            path (Path): Path to the manifest

        Yields:
            tuple[str, Type[Extension]]: name and class of all discovered palgen extensions
        """
        if not path.exists():
            _logger.warning("Could not find %s", path)
            return

        file = toml.load(path)
        manifest = ManifestSchema.parse_obj(file)
        _logger.debug("Loading from `%s`", path)

        for name, path_str in manifest.items():
            path = Path(path_str)
            if not path.is_absolute():
                path = path.parent / path

            yield from self.python_loader.load(path, import_name=name)
