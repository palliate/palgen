import logging
from typing import Type, Iterable
from pathlib import Path

from palgen.loaders.manifest import Manifest
from palgen.loaders.python import Python
from palgen.module import Module
from palgen.schemas.palgen import ModuleSettings
from palgen.schemas.project import ProjectSettings
from palgen.util.filesystem import discover, gitignore

logger = logging.getLogger(__name__)


class Modules:
    def __init__(self, project: ProjectSettings, settings: ModuleSettings, files: Iterable[Path], root: Path) -> None:
        self.private: dict[str, Type[Module]] = {}
        self.public: dict[str, Type[Module]] = {}
        self.inherited: dict[str, Type[Module]] = {}

        module_paths = discover(settings.folders, gitignore(root), jobs=1)

        if settings.inherit:
            logger.info("Loading manifests")
            for name, module in Manifest.ingest(module_paths):
                self._append_checked(self.inherited, name, module)

            for name, module in Manifest.ingest(settings.dependencies):
                self._append_checked(self.inherited, name, module)

        if settings.python:
            logger.info("Loading Python modules")
            self._extend(Python.ingest(module_paths, project=project))

            if settings.inline:
                self._extend(Python.ingest(files, project=project))

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
    def runnables(self) -> dict[str, Type[Module]]:
        """Returns all runnable modules.
        Runnable modules are all private and public modules, including inherited ones.

        Returns:
            dict[str, Type[Module]]: Runnable modules
        """
        return self.public | self.private | self.inherited

    @property
    def exportables(self) -> dict[str, Type[Module]]:
        """Returns all exportable modules.
        Exportable modules are all public modules. Private and inherited ones are not exportable.

        Returns:
            dict[str, Type[Module]]: Runnable modules
        """
        return self.public
