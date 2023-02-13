from pathlib import Path

import toml
from pydantic import BaseModel

from palgen.ingest import Filter
from palgen.loaders import Loader
from palgen.loaders.python import Python
from palgen.util.filesystem import SuffixDict


class ManifestEntry(BaseModel):
    name: str
    path: Path

class ManifestSchema(BaseModel):
    modules: list[ManifestEntry]

class Manifest(Loader):

    def generate(self):
        ...

    @staticmethod
    def ingest(source_tree: SuffixDict | list[Path]):
        if isinstance(source_tree, list):
            for source in source_tree:
                assert isinstance(source, Path)

                if not source.is_dir():
                    continue

                for path in source.glob('**/palgen.manifest'):
                    yield from Manifest.load(Path(path))
                    break

        elif isinstance(source_tree, SuffixDict):
            files = Filter('palgen', '.manifest')(source_tree)
            for file in files:
                yield from Manifest.load(file)

    @staticmethod
    def load(path: Path):
        file = toml.load(path)
        manifest = ManifestSchema.parse_obj(file)
        for entry in manifest.modules:
            assert not entry.path.is_absolute()

            yield from Python.load(path.parent / entry.path)
