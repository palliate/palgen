import logging
from pathlib import Path
from typing import Iterable

import toml

from palgen.ingest import Ingest
#from palgen.util.transformations import compress

logger = logging.getLogger(__name__)


class Toml(Ingest):
    def ingest(self, files: Iterable[Path]):
        for file in files:
            yield from self.parse(file)

    def parse(self, path: Path):
        data = toml.load(path)
        yield path, data

        #file_namespace = data.pop("namespace", None)
        #if isinstance(file_namespace, str):
        #    file_namespace = file_namespace.split('.')

        #for namespace, name, value in compress(data, file_namespace):
        #    yield path, ([namespace, name], value)
