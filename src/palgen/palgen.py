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
from palgen.loaders.manifest import Manifest
from palgen.util.filesystem import discover, gitignore


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

        if self.project.sources:
            self.project.sources = self._expand_paths(self.project.sources)

        if self.options.modules.folders:
            self.options.modules.folders = self._expand_paths(self.options.modules.folders)

        self.output = self._path_for(self.options.output) \
            if self.options.output else self.root

    @cached_property
    def files(self) -> list[Path]:
        """ List of all files considered as module imports. This is
            pre-filtered to exclude everything ignored through .gitignore files.

            First access to this can be slow, since it has to walk the entire
            source tree once. After that it'll be in cache.
        Returns:
            list[Path]
        """
        files: list[Path] = discover(self.project.sources, gitignore(self.root), jobs=self.options.jobs)
        if not files:
            logger.warning("No source files detected.")
        return files

    @cached_property
    def modules(self) -> Modules:
        return Modules(self.project, self.options.modules, self.files, self.root)

    """@cached_property
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

        return subprojects_"""

    def _path_for(self, folder: str | Path) -> Path:
        path = Path(folder)
        return path if path.is_absolute() else self.root / path

    def _expand_paths(self, folders: list[Path]) -> list[Path]:
        return [self._path_for(folder) for folder in folders]

    def run(self, name: str, settings: dict):
        if name not in self.modules.runnables:
            logger.warning("Module `%s` not found.", name)
            return []

        module = self.modules.runnables[name](self.root, self.output, settings)
        logger.info("Running module `%s` with %d jobs", module.name, self.options.jobs or 1)

        try:
            return module.run(self.files, self.options.jobs or 1)
        except Exception as exception:
            logger.exception("Running failed: %s: %s",
                             type(exception).__name__, exception)
            raise SystemExit(0) from exception

    def run_all(self):
        generated: list[Path] = []
        for name, settings in self.settings.items():

            if name not in self.modules.runnables:
                if  name not in ('palgen', 'project'):
                    logger.warning("Module `%s` not found.", name)
                continue

            generated.extend(self.run(name, settings))

        logger.info("Generated %d files.", len(generated))

    def generate_manifest(self, basepath: Optional[Path] = None):
        return Manifest.generate(self.modules, basepath)

    def __eq__(self, other) -> bool:
        if isinstance(other, Path):
            return self.config_file == other.resolve()

        if isinstance(other, str):
            return str(self.config_file) == other

        if isinstance(other, Palgen):
            return self.config_file == other.config_file

        return False
