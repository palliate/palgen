import logging
from collections import UserDict
from functools import cached_property
from pathlib import Path
from typing import Any, Iterable, Mapping, MutableMapping, Optional

import click
import toml
from pydantic import BaseModel, RootModel, ValidationError
from .application.util import pydantic_to_click
from .loaders import Builtin, ExtensionInfo, Kind, Loader, Manifest, Python
from .machinery.filesystem import discover, gitignore
from .schemas import PalgenSettings, ProjectSettings, RootSettings

_logger = logging.getLogger(__name__)


class Extensions(UserDict[str, ExtensionInfo]):

    def extend(self, loader: Loader, paths: Iterable[Path | str], inherited: bool = False):
        for extension in loader.ingest(paths):
            if extension.name in self.data:
                _logger.warning("Extension name collision: %s defined in files %s and %s. "
                                "Ignoring the latter.", extension.name, self.data[extension.name].path, extension.path)
                return

            if inherited:
                extension.inherited = True

            self.data[extension.name] = extension

    @property
    def runnable(self) -> dict[str, ExtensionInfo]:
        """Get all runnable extensions.
        Runnable extensions are all private and public extensions, including inherited ones.

        Returns:
            dict[str, Type[Extension]]: A dictionary of runnable extensions
        """
        return self.data

    @property
    def exportable(self) -> dict[str, ExtensionInfo]:
        """Get all exportable extensions.
        Exportable extensions are public extensions. Private and inherited ones are not exportable.

        Returns:
            dict[str, Type[Extension]]: A dictionary of exportable extensions
        """
        return {k: v for k, v in self.items() if v.kind == Kind.PUBLIC and not v.inherited}

    @property
    def builtin(self) -> dict[str, ExtensionInfo]:
        """Get all built-in extensions.

        Returns:
            dict[str, ExtensionInfo]: A dictionary of built-in extensions.
        """
        return {k: v for k, v in self.items() if v.kind == Kind.BUILTIN}

    @property
    def private(self) -> dict[str, ExtensionInfo]:
        """Get all private extensions.

        Private extensions are not accessible externally and are not inherited.

        Returns:
            dict[str, ExtensionInfo]: A dictionary of private extensions.
        """
        return {k: v for k, v in self.items() if v.kind == Kind.PRIVATE}

    @property
    def inherited(self) -> dict[str, ExtensionInfo]:
        """Get all inherited extensions.

        Inherited extensions are those inherited from parent classes.

        Returns:
            dict[str, ExtensionInfo]: A dictionary of inherited extensions.
        """
        return {k: v for k, v in self.items() if v.inherited}

    @property
    def local(self) -> dict[str, ExtensionInfo]:
        """Get all local extensions.

        Local extensions are those defined in the current project, excluding inherited and built-in ones.

        Returns:
            dict[str, ExtensionInfo]: A dictionary of local extensions.
        """
        return {k: v for k, v in self.items() if not v.inherited and v.kind != Kind.BUILTIN}

    def manifest(self, relative_to: Optional[Path] = None) -> str:
        """Returns exportable extensions and their file paths as TOML-formatted string.

        Returns:
            str: TOML representation of exportable extensions.
        """
        output = {}
        for extension in self.exportable.values():
            path = extension.path

            if relative_to and path.is_relative_to(relative_to):
                path = path.relative_to(relative_to)

            output[extension.module] = str(path)

        return toml.dumps(output)


class Palgen:
    __slots__ = '__dict__', 'config_path', 'root', 'settings', 'project', 'options', 'output_path'

    def __init__(self, config_file: str | Path, settings: Optional[PalgenSettings] = None):
        """Palgen application. Loads and verifies config_file

        Args:
            config_file (str | Path): Project configuration file

        Raises:
            ValidationError:   Incorrect or missing project configuration
            FileNotFoundError: Config file does not exist
        """

        def merge(source: Mapping, target: MutableMapping) -> MutableMapping:
            for key, value in source.items():
                if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                    target[key] = merge(target[key], value)
                elif key in target and isinstance(target[key], list) and isinstance(value, list):
                    target[key].extend(value)
                elif key in target and isinstance(target[key], set) and isinstance(value, set):
                    assert isinstance(target[key], set)
                    target[key].update(value)
                else:
                    target[key] = value
            return target

        # default to `palgen.toml` if no file name is given
        self.config_path = Path(config_file).resolve()
        if self.config_path.is_dir():
            self.config_path /= "palgen.toml"

        if not self.config_path.exists():
            raise FileNotFoundError("Config file does not exist")

        self.root = self.config_path.parent
        config = toml.load(self.config_path)
        self.settings = RootSettings.model_validate(config)

        self.project = ProjectSettings.model_validate(self.settings['project'])

        if settings:
            merge(settings.model_dump(), self.settings['palgen'])
        self.options = PalgenSettings.model_validate(self.settings['palgen'])

        self.project.sources = self._expand_paths(self.project.sources)
        self.options.extensions.folders = self._expand_paths(self.options.extensions.folders)
        self.output_path = self._path_for(self.options.output) if self.options.output else self.root

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
        extension_settings = self.options.extensions

        extension_paths = discover(extension_settings.folders, gitignore(self.root), jobs=1)

        loaders: list[Loader] = []
        if extension_settings.manifest:
            loaders.append(Manifest())

        if extension_settings.python:
            loaders.append(Python(project_name=self.project.name))

        for loader in loaders:
            _extensions.extend(loader, extension_paths)

            if extension_settings.inline:
                _extensions.extend(loader, self.files)

            if extension_settings.inherit:
                _extensions.extend(loader, extension_settings.dependencies, inherited=True)

        _extensions.extend(Builtin(), ["palgen.application.commands", "palgen.integrations"])

        # WORKAROUND flatten nested settings for dependencies
        settings: dict[Any, Any] = self.settings.root

        for extension in _extensions.inherited:
            package, command = extension.split('.', 1)
            if package not in settings:
                continue

            assert isinstance(settings[package], dict)

            if (setting := settings[package].pop(command, None)) is not None:
                settings[extension] = setting

            if not settings[package]:
                del settings[package]

        return _extensions

    def get_command(self, command: str | ExtensionInfo) -> Optional[click.Group | click.Command]:
        if not isinstance(command, ExtensionInfo):
            if command not in self.extensions:
                return None

            command = self.extensions[command]

        if isinstance(command.extension, (click.Group, click.Command)):
            return command.extension

        return getattr(command.extension, "cli", self._generate_cli(command))

    def _generate_cli(self, extension_info: ExtensionInfo) -> click.Command:
        key = extension_info.name
        extension = extension_info.extension

        @click.command(name=key,
                       help=extension.__doc__,
                       context_settings={'show_default': True})
        @click.pass_obj
        def wrapper(obj, **kwargs):
            nonlocal key
            obj.run(key, kwargs)

        if key in self.settings and extension.Settings is not None:
            assert issubclass(extension.Settings, (BaseModel, RootModel))

            try:
                extension.Settings.model_validate(self.settings[key])
            except ValidationError as exc:
                filtered = [error for error in exc.errors()
                            if error.get('type', None) != 'missing']

                if filtered:
                    raise

        for field, options in pydantic_to_click(extension.Settings):
            if key in self.settings and field in self.settings[key]:
                options["required"] = False
                options["default"] = self.settings[key][field]
            wrapper = click.option(f'--{field}', **options)(wrapper)

        return wrapper

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
        if name not in self.extensions.runnable:
            _logger.warning("Extension `%s` not found.", name)
            return []
        info = self.extensions.runnable[name]
        assert info.kind != Kind.BUILTIN, "Running builtins is currently only supported via command line"

        extension = info.extension(self.project, self.root, self.output_path, settings)
        _logger.info("Running extension `%s` with %d jobs", extension.name, self.options.jobs or 1)

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
            if name not in self.extensions.runnable:
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
            return self.config_path == other.resolve()

        if isinstance(other, str):
            return str(self.config_path) == other

        if isinstance(other, Palgen):
            return self.config_path == other.config_path

        return False
