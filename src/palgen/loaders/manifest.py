from pathlib import Path
from typing import Optional, TYPE_CHECKING

import toml
from pydantic import BaseModel

from palgen.ingest import Filter
from palgen.loaders import Loader
from palgen.loaders.python import Python
from palgen.schemas.project import ProjectSettings
from palgen.util.filesystem import SuffixDict

if TYPE_CHECKING:
    from palgen.modules import Modules

class ManifestEntry(BaseModel):
    name: str
    path: Path

class ManifestSchema(BaseModel):
    modules: list[ManifestEntry]

class Manifest(Loader):

    @staticmethod
    def ingest(project: ProjectSettings, source_tree: SuffixDict | list[Path]):
        if isinstance(source_tree, list):
            for source in source_tree:
                assert isinstance(source, Path)

                if not source.is_dir():
                    continue

                for path in source.glob('**/palgen.manifest'):
                    yield from Manifest.load(project, Path(path))
                    break

        elif isinstance(source_tree, SuffixDict):
            files = Filter('palgen', '.manifest')(source_tree)
            for file in files:
                yield from Manifest.load(project, file)

    @staticmethod
    def load(project: ProjectSettings, path: Path):
        file = toml.load(path)
        manifest = ManifestSchema.parse_obj(file)
        for entry in manifest.modules:
            assert not entry.path.is_absolute()

            yield from Python.load(project, path.parent / entry.path)

    @staticmethod
    def generate(modules: 'Modules', basepath: Optional[Path] = None):
        modules_out = []

        for name, module in modules.exportables.items():
            path = module.path
            if basepath and module.path.is_relative_to(basepath):
                path = module.path.relative_to(basepath)

            modules_out.append({'name': name, 'path': str(path)})

        #TODO namespaces

        return toml.dumps({'modules': modules_out})
