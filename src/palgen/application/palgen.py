import logging
from functools import cached_property
from pathlib import Path
from typing import Iterable, Optional, Type

import toml

from ..interfaces import Module
from ..loaders.manifest import Manifest, Python
from ..schemas import PalgenSettings, ProjectSettings, RootSettings

from ..machinery.filesystem import discover, gitignore

_logger = logging.getLogger(__name__)

class Modules:
    __slots__ = ['private', 'public', 'inherited']

    def __init__(self) -> None:
        self.private: dict[str, Type[Module]] = {}
        self.public: dict[str, Type[Module]] = {}
        self.inherited: dict[str, Type[Module]] = {}


    def extend(self, modules: Iterable[tuple[str, Type[Module]]]):
        for name, module in modules:
            target = self.private if module.private else self.public
            self.append_checked(target, name, module)

    def append_checked(self, target: dict[str, Type[Module]], name: str, module: Type[Module]):
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


class Palgen:
    def __init__(self, config_file: str | Path):
        """Palgen application. Loads and verifies config_file

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
            self.options.modules.folders = self._expand_paths(
                self.options.modules.folders)

        self.output = self._path_for(self.options.output) \
            if self.options.output else self.root

    @cached_property
    def files(self) -> list[Path]:
        """ List of all input files. This is pre-filtered to exclude everything
        ignored through .gitignore files.

        First access to this can be slow, since it has to walk the entire
        source tree once. After that it'll be in cache.

        Returns:
            list[Path]: input files
        """
        files: list[Path] = discover(
            self.project.sources, gitignore(self.root), jobs=self.options.jobs)
        if not files:
            _logger.warning("No source files detected.")
        return files

    @cached_property
    def modules(self) -> Modules:
        """ Discovered modules.

        First access to this can be slow, since it has to actually load the modules.
        """
        modules = Modules()
        module_paths = discover(
            self.options.modules.folders, gitignore(self.root), jobs=1)

        module_settings = self.options.modules

        if module_settings.inherit:
            manifest_loader = Manifest()
            _logger.debug("Loading manifests")
            for name, module in manifest_loader.ingest(module_paths):
                modules.append_checked(modules.inherited, name, module)

            for name, module in manifest_loader.ingest(module_settings.dependencies):
                modules.append_checked(modules.inherited, name, module)

        if module_settings.python:
            python_loader = Python(project=self.project)
            _logger.debug("Loading Python modules")
            modules.extend(python_loader.ingest(module_paths))

            if module_settings.inline:
                modules.extend(python_loader.ingest(self.files))

        return modules

    def run(self, name: str, settings: dict) -> list[Path]:
        """Runs the specified module with the given settings.

        Args:
            name (str): The name of the module to run.
            settings (dict): A dictionary of settings to use when running the module.

        Raises:
            SystemExit: Terminates if running the module threw any uncaught exceptions.

        Returns:
            list[Path]: Files generated by the module.
        """
        if name not in self.modules.runnables:
            _logger.warning("Module `%s` not found.", name)
            return []

        module = self.modules.runnables[name](self.root, self.output, settings)
        _logger.info("Running module `%s` with %d jobs",
                     module.name, self.options.jobs or 1)

        try:
            return module.run(self.files, self.options.jobs or 1)
        except Exception as exception:
            _logger.exception("Running failed: %s: %s",
                              type(exception).__name__, exception)

            # TODO do not terminate using SystemExit here
            raise SystemExit(1) from exception

    def run_all(self) -> None:
        """Runs all modules enabled in the settings.

        This method will try running all modules enabled in the `palgen.toml` settings file.
        If a module is not found or isn't runnable it will be skipped.
        """
        generated: list[Path] = []
        for name, settings in self.settings.items():

            if name not in self.modules.runnables:
                if name not in ('palgen', 'project'):
                    _logger.warning("Module `%s` not found.", name)
                continue

            generated.extend(self.run(name, settings))

        _logger.info("Generated %d files.", len(generated))

    def _path_for(self, folder: str | Path) -> Path:
        path = Path(folder)
        return path if path.is_absolute() else self.root / path

    def _expand_paths(self, folders: list[Path]) -> list[Path]:
        return [self._path_for(folder) for folder in folders]

    def __eq__(self, other) -> bool:
        if isinstance(other, Path):
            return self.config_file == other.resolve()

        if isinstance(other, str):
            return str(self.config_file) == other

        if isinstance(other, Palgen):
            return self.config_file == other.config_file

        return False
