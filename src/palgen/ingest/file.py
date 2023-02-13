import logging
from pathlib import Path
from typing import Iterable

from palgen.ingest import Ingest

logger = logging.getLogger(__name__)


class Raw(Ingest):

    def ingest(self, files: Iterable[Path]) -> Iterable[tuple[Path, bytes]]:
        for file in files:
            yield file, file.read_bytes()


class Empty(Ingest):
    def ingest(self, files: Iterable[Path]) -> Iterable[tuple[Path, None]]:
        for file in files:
            if not file.exists():
                continue

            if file.stat().st_size == 0:
                yield file, None
            else:
                logger.warning("%s matches ingest configuration but is not empty.",
                               file)
