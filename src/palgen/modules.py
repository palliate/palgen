import logging
from typing import Type, Iterable

from palgen.loaders.manifest import Manifest
from palgen.loaders.python import Python
from palgen.module import Module
from palgen.schemas.palgen import ModuleSettings
from palgen.util.filesystem import SuffixDict

logger = logging.getLogger(__name__)


class Modules:
    def __init__(self, settings: ModuleSettings, file_cache: SuffixDict) -> None:
        self.private: dict[str, Type[Module]] = {}
        self.public: dict[str, Type[Module]] = {}

        if settings.inherit:
            logger.debug("Loading manifests")
            self._extend(Manifest.ingest(settings.extra_folders))

        if settings.python:
            logger.debug("Loading Python modules")
            self._extend(Python.ingest(file_cache))

    def _extend(self, modules: Iterable[tuple[str, Type[Module]]]):
        for name, module in modules:
            target = self.private if module.private else self.public
            self._append_checked(target, name, module)

    def _append_checked(self, target: dict[str, Type[Module]], name: str, module: Type[Module]):
        if name in target:
            other = target[name]
            logger.warning("Module name collision: %s defined in files %s and %s. "
                           "Ignoring the latter.",
                           name,
                           other.path,
                           module.path)
            return

        target[name] = module

    @property
    def runnables(self):
        return self.public | self.private

    @property
    def exportables(self):
        return self.public