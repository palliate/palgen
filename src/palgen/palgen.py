# remove once 3.11 lands, required for self type type hints
from __future__ import annotations

import logging
from functools import cached_property
from pathlib import Path
from typing import Optional

import toml
from palgen.modules import Modules

from palgen.schemas.root import RootSettings
from palgen.schemas.project import ProjectSettings
from palgen.schemas.palgen import PalgenSettings

from palgen.util.filesystem import SuffixDict, gitignore

logger = logging.getLogger(__name__)


class Palgen:
    def __init__(self, config_file: str | Path):
        """Palgen project. Loads and verifies config_file

        Args:
            config_file (str | Path): Project configuration file

        Raises:
            ValidationError:   Incorrect or missing project configuration
            FileNotFoundError: Config file does not exist
        """
        # default to `palgen.toml` if no file name is given
        self.config_file = Path(config_file).resolve()
        if self.config_file.is_dir():
            self.config_file /= "palgen.toml"

        if not self.config_file.exists():
            raise FileNotFoundError("Config file does not exist")

        config = toml.load(self.config_file)
        self.settings = RootSettings.parse_obj(config)
        self.root = self.config_file.parent

        self.project = ProjectSettings.parse_obj(self.settings['project'])
        self.options = PalgenSettings.parse_obj(self.settings['palgen'])

        self.output = self._path_for(self.project.output) \
            if self.project.output else self.root

    @cached_property
    def files(self) -> SuffixDict:
        """ Representation of the source tree in the form of
            dict[suffix, dict[name, list[Path]]]

            First access to this can be slow, since it has to walk the entire
            source tree once. After that it'll be in cache.
        Returns:
            SuffixDict
        """
        discovered = SuffixDict()

        for folder in self.project.folders:
            path: Path = self._path_for(folder)
            if not path.exists():
                logger.warning("Folder not found: %s. Skipping.", path)
                continue

            discovered.walk(path, gitignore(self.root))
        return discovered

    @cached_property
    def modules(self) -> Modules:
        if not self.options.modules.extra_folders:
            # disable conan integration when extra dirs are provided

            from palgen.integrations.conan.dependencies import get_paths
            self.options.modules.extra_folders = get_paths(self.root)

        return Modules(self.options.modules, self.files)

    @cached_property
    def subprojects(self) -> dict[str, Palgen]:
        # TODO remove, unused
        subprojects_: dict[str, Palgen] = {}
        for file in self.files.by_name('palgen.toml'):
            loader = Palgen(file)
            if loader.project.name in subprojects_:
                logger.warning("Found project %s more than once.",
                               loader.project.name)
                continue

            subprojects_[loader.project.name] = loader

        return subprojects_

    def _path_for(self, folder: str | Path) -> Path:
        path = Path(folder)
        if path.is_absolute():
            return path

        return self.root / path

    def run(self):
        generated: list[Path] = []
        for template, settings in self.settings.items():
            if template not in self.modules.runnables:
                if template not in ('project', 'template'):
                    logger.warning("Module `%s` not found.", template)
                continue

            if parser := self.modules.runnables[template]:

                module = parser(self.root, self.output, settings)
                logger.info("Rendering template `%s`", module.name)
                try:
                    generated.extend(module.run(self.files))
                except Exception as exception:
                    logger.exception(
                        "Generating failed: %s: %s", type(
                            exception).__name__, exception
                    )
                    raise SystemExit(0) from exception

        logger.info("Generated %d files.", len(generated))

    def generate_manifest(self, basepath: Optional[Path] = None):
        modules = []
        for name, module in self.modules.exportables.items():
            path = module.path
            if basepath and module.path.is_relative_to(basepath):
                path = module.path.relative_to(basepath)

            modules.append({'name': name, 'path': str(path)})

        return toml.dumps({'modules': modules})

    def __eq__(self, other) -> bool:
        if isinstance(other, Path):
            return self.config_file == other.resolve()

        if isinstance(other, str):
            return str(self.config_file) == other

        if isinstance(other, Palgen):
            return self.config_file == other.config_file

        return False
