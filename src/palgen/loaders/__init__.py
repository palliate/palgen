from pathlib import Path
from abc import abstractmethod


class Loader:
    @staticmethod
    @abstractmethod
    def ingest(sources: list[Path]):
        pass

    @staticmethod
    @abstractmethod
    def load(path: Path):
        pass
