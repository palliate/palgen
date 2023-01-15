# remove once 3.11 lands, required for self type type hints
from __future__ import annotations

import logging
from functools import cached_property
from pathlib import Path
from typing import Any, Optional

import toml
from pydantic import BaseModel, root_validator

from palgen.project import Project
from palgen.template import Template
from palgen.templates import TemplateMeta, Templates
from palgen.util.filesystem import SuffixDict, gitignore

logger = logging.getLogger(__name__)


class Loader:
    class Settings(BaseModel):
        __root__: dict[Any, Any]

        @root_validator(pre=True)
        @classmethod
        def validate(cls, values):
            settings = values.get("__root__")
            assert "project" in settings, "Missing project table."
            settings.setdefault("templates", {})

            for key, value in settings.items():
                assert isinstance(value, dict), \
                    f"Setting {key} is not a table."

            return values

        # region boilerplate
        def get(self, key, default = None):
            return self.__root__.get(key, default)

        def __iter__(self):
            return iter(self.__root__)

        def __getitem__(self, item):
            return self.__root__[item]

        def keys(self):
            return self.__root__.keys()

        def items(self):
            return self.__root__.items()
        # endregion

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
        self.settings = Loader.Settings.parse_obj(config)
        self.root = self.config_file.parent

        self.project = Project.parse_obj(self.settings['project'])
        self.active_templates: dict[str, Template] = {} #?

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
    def templates(self) -> Templates:
        templates_ = Templates.parse_obj(self.settings['templates'])

        for files in self.files.by_extension('.py').values():
            for file in files:
                templates_.from_py(file)

        for file in self.files.by_name('template.toml'):
            templates_.from_toml(file)

        for project in templates_.inherit:
            if project in self.subprojects:
                templates_.inherit_templates(self.subprojects[project].templates)
            # TODO load templates from repos or through conan

        return templates_

    @cached_property
    def subprojects(self) -> dict[str, Loader]:
        subprojects_: dict[str, Loader] = {}
        for file in self.files.by_name('palgen.toml'):
            loader = Loader(file)
            if loader.project.name in subprojects_:
                logger.warning("Found project %s more than once.",
                               loader.name)
                continue

            subprojects_[loader.project.name] = loader

        return subprojects_

    def _path_for(self, folder: str | Path) -> Path:
        path = Path(folder)
        if path.is_absolute():
            return path

        return self.root / path


    def run(self, *templates: str):
        templates_ = set(templates)
        generated: list[Path] = []
        # TODO get enabled from config file

        for template in templates_:
            if template not in self.templates:
                logger.warning("Module `%s` not found.", template)
                continue

            if parser := self.templates[template]:
                settings = self.settings[template] \
                    if template in self.settings else {}

                module = parser(self.root, settings)
                logger.info("Rendering template `%s`", module.name)
                try:
                    data = None
                    if True:#module.loader:
                        if files := self.files.by_name(f"{module.key}{module.extension}"):
                            data = module.ingest(files)
                            render = module.render(data)
                            generated.extend(module.write(self.output, render))
                        else:
                            logger.debug(
                                "No input for template `%s` found", module.key)
                except Exception as exception:
                    logger.exception(
                        "Generating failed: %s: %s", type(
                            exception).__name__, exception
                    )
                    raise SystemExit(0) from exception

        logger.info("Running against %d templates yielded %d files.",
                    len(templates_),
                    len(generated))

    # region boilerplate
#    def __getattr__(self, field: str):
#        return getattr(self.project, field)

    def __eq__(self, other: Path | str | Loader) -> bool:
        if isinstance(other, Path):
            return self.config_file == other.resolve()

        if isinstance(other, str):
            return str(self.config_file) == other

        if isinstance(other, Loader):
            return self.config_file == other.config_file

        return False

    def __str__(self) -> str:
        return str(self.project)
    # endregion
