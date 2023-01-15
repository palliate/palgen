from pathlib import Path

from palgen.ingest import Ingest, Meta


class Raw(Ingest):

    @classmethod
    def data(cls, path: Path):
        yield Meta(path.parts, path), path.read_bytes()
