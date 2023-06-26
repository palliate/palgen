import logging
from pathlib import Path
from typing import Iterable, Optional, Type

import toml

from palgen.loaders import Manifest, Python
from palgen.module import Module
from palgen.schemas import ModuleSettings, ProjectSettings
from palgen.util.filesystem import discover, gitignore

_logger = logging.getLogger(__name__)


class Modules:
    def __init__(self, project: ProjectSettings, settings: ModuleSettings, files: Iterable[Path], root: Path) -> None:
        self.private: dict[str, Type[Module]] = {}
        self.public: dict[str, Type[Module]] = {}
        self.inherited: dict[str, Type[Module]] = {}
        self.root: Path = root

        module_paths = discover(settings.folders, gitignore(root), jobs=1)

        if settings.inherit:
            manifest_loader = Manifest()
            _logger.debug("Loading manifests")
            for name, module in manifest_loader.ingest(module_paths):
                self._append_checked(self.inherited, name, module)

            for name, module in manifest_loader.ingest(settings.dependencies):
                self._append_checked(self.inherited, name, module)

        if settings.python:
            python_loader = Python(project=project)
            _logger.debug("Loading Python modules")
            self._extend(python_loader.ingest(module_paths))

            if settings.inline:
                self._extend(python_loader.ingest(files))

    def _extend(self, modules: Iterable[tuple[str, Type[Module]]]):
        for name, module in modules:
            target = self.private if module.private else self.public
            self._append_checked(target, name, module)

    def _append_checked(self, target: dict[str, Type[Module]], name: str, module: Type[Module]):
        if name in target:
            other = target[name]
            _logger.warning("Module name collision: %s defined in files %s and %s. "
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

    def manifest(self, relative_to: Optional[Path] = None) -> str:
        """Returns exportable modules and their file paths as TOML-formatted string.

        Returns:
            str: TOML representation of exportable modules.
        """
        output = {}
        for module in self.exportables.values():
            path = module.path

            if relative_to and path.is_relative_to(relative_to):
                path = path.relative_to(relative_to)

            output[module.module] = str(path)

        return toml.dumps(output)
