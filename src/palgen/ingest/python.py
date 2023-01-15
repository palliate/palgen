from pathlib import Path
from palgen.ingest import Ingest

class Python(Ingest):
    extension = '.py'

    @classmethod
    def template(cls, path: Path):
        ...
