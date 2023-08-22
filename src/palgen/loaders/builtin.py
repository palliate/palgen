import importlib
import logging
from pathlib import Path
from pkgutil import walk_packages
from types import ModuleType
from typing import Iterable, Optional

import click
from .loader import Kind, Loader, ExtensionInfo

_logger = logging.getLogger(__name__)

class Builtin(Loader):

    def ingest(self, sources: Iterable[str]) -> Iterable[ExtensionInfo]:
        for module in sources:
            yield from self.load(module)


    def _import(self, name: str) -> Optional[ModuleType]:
        try:
            return importlib.import_module(name)
        except ImportError:
            _logger.warning("Could not import `%s`.", name)

    def _load(self, module: ModuleType) -> Iterable[ExtensionInfo]:
        skip_list = []

        for ident, attr in module.__dict__.items():
            if ident.startswith('_'):
                continue

            if isinstance(attr, click.core.Command):
                if isinstance(attr, click.core.Group):
                    skip_list.extend(attr.commands.values())
                elif attr in skip_list:
                    continue

                assert module.__spec__
                assert module.__spec__.origin

                yield ExtensionInfo(attr, ident, Path(module.__spec__.origin), Kind.BUILTIN)

    def load(self, source: str) -> Iterable[ExtensionInfo]:
        if not (pkg := self._import(source)):
            return

        for module_info in walk_packages(path=pkg.__path__, prefix=f"{source}."):
            if module_info.ispkg:
                continue

            if module := self._import(module_info.name):
                yield from self._load(module)
