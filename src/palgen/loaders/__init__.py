import importlib
from pathlib import Path
from typing import Type
from abc import abstractmethod

from palgen.util.filesystem import SuffixDict


class Loader:

    @staticmethod
    @abstractmethod
    def ingest(source_tree: SuffixDict):
        pass

    @staticmethod
    @abstractmethod
    def load(path: Path):
        pass


def get_loader(name: str) -> Type[Loader]:
    module = importlib.import_module(f"palgen.loaders.{name}")

    attrs = [getattr(module, name)
             for name in dir(module)
             if not name.startswith('_')]

    for attr in attrs:
        if issubclass(attr, Loader) and attr is not Loader:
            assert isinstance(attr, type)
            return attr

    raise ImportError