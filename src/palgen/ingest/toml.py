import logging
from pathlib import Path

import toml  # TODO do this lazily

from palgen.ingest import Meta, Ingest
from palgen.util.transformations import compress

logger = logging.getLogger(__name__)


class Toml(Ingest):
    extension = '.toml'

    @classmethod
    def data(cls, path: Path):
        data = toml.load(path)

        file_namespace = data.pop("namespace", None)
        if isinstance(file_namespace, str):
            file_namespace = file_namespace.split('.')

        for namespace, name, value in compress(data, file_namespace):
            yield Meta([*namespace, name], path), value
