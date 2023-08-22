import logging
from abc import abstractmethod
from pathlib import Path
from typing import Any, Iterable

_logger = logging.getLogger(__name__)


class Ingest:
    """Ingest interface.
    """

    __slots__ = ()

    @abstractmethod
    def ingest(self, files: Iterable[Path]) -> Iterable[tuple[Path, Any]]:
        """Ingests files.

        Args:
            files (Iterable[Path]):  An iterable of Paths that should be ingested.

        Yields:
            tuple[Path, Any]: Tuple of a path to every ingested file and its content.
        """
        raise NotImplementedError

        # sourcery skip: remove-unreachable-code; pylint: disable=unreachable
        yield  # type: ignore [unreachable]

    def __call__(self, files: Iterable[Path]) -> Iterable[tuple[Path, Any]]:
        yield from self.ingest(files)


class Empty(Ingest):
    __slots__ = ()

    def ingest(self, files: Iterable[Path]) -> Iterable[tuple[Path, None]]:
        """Ingests files if they are empty. Warns if a file in the :code:`files` iterable
        is not empty.

        Args:
            files (Iterable[Path]):  An iterable of Paths that should be ingested.

        Yields:
            tuple[Path, None]: Tuple of a path to every ingested file and None.
        """
        for file in files:
            if not file.exists():
                continue

            if file.stat().st_size == 0:
                yield file, None
            else:
                _logger.warning("%s matches ingest configuration but is not empty.",
                                file)


class Raw(Ingest):
    __slots__ = ()

    def ingest(self, files: Iterable[Path]) -> Iterable[tuple[Path, bytes]]:
        """Ingests files as raw bytes.

        Args:
            files (Iterable[Path]):  An iterable of Paths that should be ingested.

        Yields:
            tuple[Path, byte]: Tuple of a path to every ingested file and its content.
        """
        for file in files:
            yield file, file.read_bytes()


class Text(Ingest):
    __slots__ = ('encoding',)

    def __init__(self, encoding='utf-8') -> None:
        """Text ingest.

        Args:
            encoding (str, optional): Encoding to use when reading files. Defaults to 'utf-8'.
        """
        self.encoding = encoding

    def ingest(self, files: Iterable[Path]) -> Iterable[tuple[Path, str]]:
        """Ingests files as text.

        Args:
            files (Iterable[Path]):  An iterable of Paths that should be ingested.

        Yields:
            tuple[Path, Any]: Tuple of a path to every ingested file and its content.
        """
        for file in files:
            yield file, file.read_text(self.encoding)


class Json(Ingest):
    __slots__ = ()

    def ingest(self, files: Iterable[Path]):
        """Ingests JSON files.

        Args:
            files (Iterable[Path]):  An iterable of Paths that should be ingested.

        Yields:
            tuple[Path, Any]: Tuple of a path to every ingested file and its content.
        """
        import json
        for path in files:
            yield path, json.loads(path.read_bytes())


class Toml(Ingest):
    __slots__ = ()

    def ingest(self, files: Iterable[Path]) -> Iterable[tuple[Path, dict[str, Any]]]:
        """Ingests TOML files. This uses Python's standard library tomllib if available.

        Args:
            files (Iterable[Path]):  An iterable of Paths that should be ingested.

        Yields:
            tuple[Path, dict[str, Any]]: Tuple of a path to every ingested file and its content.
        """
        import toml
        for path in files:
            try:
                yield path, toml.loads(path.read_text())
            except toml.TomlDecodeError as exc:
                _logger.warning("Could not load %s", path)
                _logger.warning("Reason: %s", exc.msg)
