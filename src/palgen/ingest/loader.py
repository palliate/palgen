import logging
from typing import Any, Iterable
from abc import abstractmethod
import sys
from pathlib import Path


_logger = logging.getLogger(__name__)


class Ingest:
    @abstractmethod
    def ingest(self, files: Iterable[Path]) -> Iterable[tuple[Path, Any]]:
        raise NotImplementedError

        # sourcery skip: remove-unreachable-code; pylint: disable=unreachable
        yield  # type: ignore [unreachable]

    def __call__(self, files: Iterable[Path]) -> Iterable[tuple[Path, Any]]:
        yield from self.ingest(files)


class Empty(Ingest):
    def ingest(self, files: Iterable[Path]) -> Iterable[tuple[Path, None]]:
        for file in files:
            if not file.exists():
                continue

            if file.stat().st_size == 0:
                yield file, None
            else:
                _logger.warning("%s matches ingest configuration but is not empty.",
                                file)


class Nothing(Ingest):
    def ingest(self, files: Iterable[Path]) -> Iterable[tuple[Path, Any]]:
        return
        # sourcery skip: remove-unreachable-code; pylint: disable=unreachable
        yield  # type: ignore [unreachable]


class Raw(Ingest):
    def ingest(self, files: Iterable[Path]) -> Iterable[tuple[Path, bytes]]:
        for file in files:
            yield file, file.read_bytes()


class Text(Ingest):
    def ingest(self, files: Iterable[Path]) -> Iterable[tuple[Path, str]]:
        for file in files:
            yield file, file.read_text()


class Json(Ingest):
    def ingest(self, files: Iterable[Path]):
        import json
        for path in files:
            yield path, json.loads(path.read_bytes())


class Toml(Ingest):
    def ingest(self, files: Iterable[Path]):
        if sys.version_info.minor >= 11:
            import tomllib as toml
        else:
            import toml

        for path in files:
            yield path, toml.loads(path.read_text())
