import logging
from functools import cached_property
from pathlib import Path
from typing import Iterable, Optional, Type

import toml

from ..ext import Extension
from ..loaders.manifest import Manifest, Python
from ..schemas import PalgenSettings, ProjectSettings, RootSettings

from ..machinery.filesystem import discover, gitignore

_logger = logging.getLogger(__name__)


class Extensions:
    __slots__ = ['private', 'public', 'inherited']

    def __init__(self) -> None:
        self.private: dict[str, Type[Extension]] = {}
        self.public: dict[str, Type[Extension]] = {}
        self.inherited: dict[str, Type[Extension]] = {}

    def extend(self, extensions: Iterable[tuple[str, Type[Extension]]]):
        for name, extension in extensions:
            target = self.private if extension.private else self.public
            self.append_checked(target, name, extension)

    def append_checked(self, target: dict[str, Type[Extension]], name: str, extension: Type[Extension]):
        if name in target:
            other = target[name]
            _logger.warning("Extension name collision: %s defined in files %s and %s. "
                            "Ignoring the latter.", name, other.path, extension.path)
            return

        target[name] = extension

    @property
    def runnables(self) -> dict[str, Type[Extension]]:
        """Returns all runnable extensions.
        Runnable extensions are all private and public extensions, including inherited ones.

        Returns:
            dict[str, Type[Extension]]: Runnable extensions
        """
        return self.public | self.private | self.inherited

    @property
    def exportables(self) -> dict[str, Type[Extension]]:
        """Returns all exportable extensions.
        Exportable extensions are all public extensions. Private and inherited ones are not exportable.

        Returns:
            dict[str, Type[Extension]]: Exportable extensions
        """
        return self.public

    def manifest(self, relative_to: Optional[Path] = None) -> str:
        """Returns exportable extensions and their file paths as TOML-formatted string.

        Returns:
            str: TOML representation of exportable extensions.
        """
        output = {}
        for extension in self.exportables.values():
            path = extension.path

            if relative_to and path.is_relative_to(relative_to):
                path = path.relative_to(relative_to)

            output[extension.module] = str(path)

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

        if self.options.extensions.folders:
            self.options.extensions.folders = self._expand_paths(self.options.extensions.folders)

        self.output = self._path_for(self.options.output) if self.options.output else self.root

    @cached_property
    def files(self) -> list[Path]:
        """ List of all input files. This is pre-filtered to exclude everything
        ignored through .gitignore files.

        First access to this can be slow, since it has to walk the entire
        source tree once. After that it'll be in cache.

        Returns:
            list[Path]: input files
        """
        files: list[Path] = discover(self.project.sources, gitignore(self.root), jobs=self.options.jobs)
        if not files:
            _logger.warning("No source files detected.")
        return files

    @cached_property
    def extensions(self) -> Extensions:
        """ Discovered extensions.

        First access to this can be slow, since it has to actually load the extensions.
        """
        _extensions = Extensions()
        extension_paths = discover(
            self.options.extensions.folders, gitignore(self.root), jobs=1)

        extension_settings = self.options.extensions

        if extension_settings.inherit:
            manifest_loader = Manifest()
            _logger.debug("Loading from manifests")
            for name, extension in manifest_loader.ingest(extension_paths):
                _extensions.append_checked(_extensions.inherited, name, extension)

            for name, extension in manifest_loader.ingest(extension_settings.dependencies):
                _extensions.append_checked(_extensions.inherited, name, extension)

        if extension_settings.python:
            python_loader = Python(project=self.project)
            _logger.debug("Loading from Python modules")
            _extensions.extend(python_loader.ingest(extension_paths))

            if extension_settings.inline:
                _extensions.extend(python_loader.ingest(self.files))

        return _extensions

    def run(self, name: str, settings: dict) -> list[Path]:
        """Runs the specified extension with the given settings.

        Args:
            name (str): The name of the extension to run.
            settings (dict): A dictionary of settings to use when running the extension.

        Raises:
            SystemExit: Terminates if running the extension threw any uncaught exceptions.

        Returns:
            list[Path]: Files generated by the extension.
        """
        if name not in self.extensions.runnables:
            _logger.warning("Extension `%s` not found.", name)
            return []

        extension = self.extensions.runnables[name](self.project, self.root, self.output, settings)

        _logger.info("Running extension `%s` with %d jobs",
                     extension.name, self.options.jobs or 1)

        try:
            return extension.run(self.files, self.options.jobs or 1)
        except Exception as exception:
            _logger.exception("Running failed: %s: %s", type(exception).__name__, exception)

            raise

    def run_all(self) -> None:
        """Runs all extensions enabled in the settings.

        This method will try running all extensions enabled in the `palgen.toml` settings file.
        If a extension is not found or isn't runnable it will be skipped.
        """
        generated: list[Path] = []
        for name, settings in self.settings.items():
            if name not in self.extensions.runnables:
                if name not in ('palgen', 'project'):
                    _logger.warning("Extension `%s` not found.", name)
                continue

            generated.extend(self.run(name, settings) or [])

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
