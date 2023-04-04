import logging
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import toml
from pydantic import BaseModel

from palgen.ingest import Filter
from palgen.loaders import Loader
from palgen.loaders.python import Python
from palgen.util.filesystem import SuffixDict

if TYPE_CHECKING:
    from palgen.modules import Modules


logger = logging.getLogger(__name__)


class ManifestSchema(BaseModel):
    __root__: dict[str, str]

    def items(self):
        return self.__root__.items()


class Manifest(Loader):

    @staticmethod
    def ingest(sources: SuffixDict | list[Path]):
        if isinstance(sources, list):
            for source in sources:
                assert isinstance(source, Path)

                if not source.is_dir():
                    continue

                for path in source.glob('**/palgen.manifest'):
                    yield from Manifest.load(Path(path))

        elif isinstance(sources, SuffixDict):
            files = Filter('palgen', '.manifest')(sources)
            for file in files:
                yield from Manifest.load(file)

    @staticmethod
    def load(path: Path):
        if not path.exists():
            logger.warning("Could not find %s", path)
            return

        file = toml.load(path)
        manifest = ManifestSchema.parse_obj(file)
        logger.debug("Loading from `%s`", path)

        for name, path_str in manifest.items():
            path = Path(path_str)
            if not path.is_absolute():
                path = path.parent / path

            yield from Python.load(path, import_name=name)

    @staticmethod
    def generate(modules: 'Modules', basepath: Optional[Path] = None):
        modules_out: dict[str, str] = {}

        for module in modules.exportables.values():
            path = module.path
            if basepath and module.path.is_relative_to(basepath):
                path = module.path.relative_to(basepath)

            modules_out[module.module] = str(path)

        return toml.dumps(modules_out)
