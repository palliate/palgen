import logging
import textwrap
import traceback
from pathlib import Path
from typing import Any, Iterable, Optional

from pydantic import BaseModel as Model
from pydantic import RootModel, ValidationError
from pydantic_core import PydanticUndefined

from .ingest import Name, Nothing, Suffix, Toml
from .machinery import Pipeline as Sources
from .machinery import setattr_default
from .schemas import ProjectSettings

_logger = logging.getLogger(__name__)


def max_jobs(amount: int):
    def wrapper(fnc):
        fnc.max_jobs = amount
        return fnc
    return wrapper


class Extension:
    Settings: Optional[type[Model]] = None  # Schema for extension configuration
    Schema: Optional[type[Model]] = None   # Optional schema to be used to validate each ingested item.

    name: str               # Extension name. Defaults to lowercase class name
    description: str        # Description of this extension. Automatically dedented,
    # can be the docstring of this class.
    private: bool           # Whether this extension is local to this project.
    # Setting this to true mangles the import name

    # pipelines
    ingest: Sources | dict[str, Sources] | None    # Pipeline used to select and read input files
    pipeline: Sources | dict[str, Sources] | None  # Overall extension pipeline.
    # Override this if you want to disable all default steps

    __slots__ = ('root_path', 'out_path', 'project', 'settings')

    def transform(self, data: Iterable[tuple[Path, Any]]) -> Iterable[tuple[Path, Any]]:
        """This step is intended to transform input data to something
        pydantic can validate in the :code:`validate` step.

        By default passes through whatever it received.

        Args:
            data (Iterable[tuple[Path, Any]]): Iterable of inputs from the :code:`ingest` pipeline

        Yields:
            tuple[Path, Any]: Transformed output
        """
        yield from data

    def validate(self, data: Iterable[tuple[Path, Any]]) -> Iterable[tuple[Path, Any]]:
        """Intended to validate elements in the :code:`data` Iterable against
        the pydantic schema :code:`Schema` of this extension.

        By default passes through whatever it received.

        Args:
            data (Iterable[tuple[Path, Any]]): Iterable of inputs from the :code:`transform` step

        Yields:
            tuple[Path, BaseModel | Any]: Input file path and validated :code:`Schema` object
        """
        if self.Schema is not None:
            for path, value in data:
                try:
                    yield path, self.Schema.parse_obj(value)
                except ValidationError as ex:
                    _logger.warning("%s failed validation.", path)
                    _print_validationerror(ex)
        else:
            yield from data

    def render(self, data: Iterable[tuple[Path, Model | Any]]) -> Iterable[tuple[Path, str | bytes]]:
        """Intended to render the output content.

        By default yields nothing.

        Args:
            data (Iterable[tuple[str, Meta, BaseModel]]): Iterable of inputs from the :code:`validate` step.

        Yields:
            tuple[Path, str]: Output path and content for generated files
        """
        # Yes yes, this is intended.
        # despite yield being unreachable its existence will set the CO_GENERATOR flag
        # hence making this a generator

        # it's ugly but it stops some linters from crying

        return
        # sourcery skip: remove-unreachable-code; pylint: disable=unreachable
        yield from data  # type: ignore [unreachable]

    def write(self, output: Iterable[tuple[Path, str | bytes]]) -> Iterable[Path]:
        """Write the rendered files back to disk.

        Args:
            output (Iterable[tuple[Path, str]]): Iterable of inputs from the :code:`render` step

        Yields:
            Path: Path to every generated file
        """
        for filename, generated in output:
            filename = self.out_path / filename
            filename.parent.mkdir(parents=True, exist_ok=True)
            with open(filename, "wb+" if isinstance(generated, bytes) else "w+",
                                encoding=None if isinstance(generated, bytes) else "utf8") as file:
                file.write(generated)

            _logger.debug("Generated `%s`", filename)
            yield filename

    def run(self, files: list[Path], jobs: Optional[int] = None) -> list[Path]:
        """Runs the extension's pipeline.
        If the pipeline is a dictionary, it will loop through each item and run
        the associated pipeline. Otherwise, it will run the single pipeline.

        This method may be overridden for extensions that do not wish to use the
        default pipelines at all or need to do custom pipeline preprocessing.

        Args:
            files (list[Path]): possibly pre-filtered list of paths to consider for ingest.
            jobs (Optional[int]): Maximum number of jobs to spawn. Defaults to None.

        Returns:
            list[Path]: Aggregated list of paths to generated files
        """
        assert self.pipeline is not None, "No pipeline defined"
        output: list[Path] = []

        if isinstance(self.pipeline, dict):
            for key, pipeline in self.pipeline.items():
                _logger.debug("Running pipeline `%s`", key)
                output.extend(pipeline(files, obj=self, max_jobs=jobs))
        else:
            output = self.pipeline(files, obj=self, max_jobs=jobs)

        _logger.info("Extension `%s` yielded %s file%s",
                     self.name,
                     len(output),
                     's' if len(output) > 1 else '')

        return output

    @classmethod
    def to_string(cls) -> str:
        # TODO stringify Settings and Schema properly
        indentation = ' '*13

        description = cls.description.replace('\n', f'\n{indentation}')

        pipeline: str = str(cls.pipeline)
        if isinstance(cls.pipeline, dict):
            pipeline = f'\n{indentation}'.join(f"{key}: {value}" for key, value in cls.pipeline.items())

        return f"""\
Name:        {cls.name}
Description: {description}

Options:     {_stringify_pydantic(cls.Settings, 13) or "No options"}
Schema:      {_stringify_pydantic(cls.Schema, 13)   or "No schema"}

Pipeline(s): {pipeline}"""

    def __str__(self) -> str:
        return self.to_string()

    def __init__(self, project: ProjectSettings,
                 root_path: Path, out_path: Path,
                 settings: Optional[dict[str, Any]] = None):
        """Extension constructor. If settings are provided they are checked against the :code:`Settings` schema.

        It's not recommended to override this unless you want to disable settings validation.

        Args:
            root_path (Path):                              Path to the project's root folder
            out_path (Path):                               Output path
            settings (Optional[dict[str, Any]], optional): Extension settings. Defaults to None.

        Raises:
            SystemExit: If settings are provided but fail to validate
        """

        self.project = project
        self.root_path = root_path
        self.out_path = out_path
        self.settings: Model | None = None

        if self.Settings is None:
            return

        if settings is None:
            raise RuntimeError(f"No settings found for extension {self.name}")

        try:
            assert issubclass(self.Settings, (Model, RootModel)), "Invalid settings"
            self.settings = self.Settings.model_validate(settings)
            _logger.debug("Validated settings for %s", self.name)

        except ValidationError as ex:
            _logger.warning("Failed verifying config for `%s`", self.name)
            _print_validationerror(ex)
            raise

    @classmethod
    def __init_subclass__(cls, *,
                          name: Optional[str] = None,
                          private: bool = False) -> None:
        """This class method is used to preprocess subclasses of the :code:`Extension` interface.


        It sets the following attributes on the subclass:

        Attributes:
            path (Path):       Path object containing the filename of the subclass.
            name (str):        Name of the subclass. If no name is provided,
                               the name of the class converted to lowercase is used.
            private (bool):    Indicates whether the subclass should be private or not.
            ingest (Pipeline): Defaults :code:`ingest` to ingest toml files matching the extension name.
                               Use :code:`ingest = None` if you want to disable ingest.

        Args:
            name (Optional[str], optional): Overrides the extension name. Defaults to None.
            private (bool, optional):       Sets this extension as private. Defaults to False.

        Raises:
            RuntimeError: Throws RuntimeError if an invalid ingest pipeline has been given.
        """
        frame = traceback.extract_stack(limit=2)[0]
        setattr(cls, "module_path", Path(frame.filename))

        setattr_default(cls, "name", name or cls.__name__.lower())
        setattr_default(cls, "private", private)

        setattr_default(cls, "ingest", Sources() >> Suffix('toml')
                                                 >> Name(getattr(cls, "name"))
                                                 >> Toml)
        _process_pipelines(cls)

        if isinstance(cls.pipeline, dict):
            _logger.debug("Pipelines: \n%s", '\n'.join(f'    {k}: {str(v)}' for k, v in cls.pipeline.items()))
        else:
            _logger.debug("Pipeline: \n%s", str(cls.pipeline))

        _check_schema_attribute(cls, "Settings")
        _check_schema_attribute(cls, "Schema")

        # dedent the Extension's docstring
        _dedent_description(cls)


def _process_pipelines(cls: type[Extension]):
    if hasattr(cls, "pipeline"):
        # pipeline has been manually overridden, do nothing
        return

    match ingest := getattr(cls, "ingest", None):
        case Sources():
            setattr(cls, "pipeline", Sources() >> ingest
                    >> cls.transform
                    >> cls.validate
                    >> cls.render
                    >> cls.write)
        case None:
            setattr(cls, "pipeline", Sources() >> Nothing)
        case dict():
            pipelines = {}
            for key, value in ingest.items():
                pipeline = Sources() >> value
                for fnc in 'transform', 'validate', 'render':
                    name = f"{fnc}_{key}"
                    pipeline >>= getattr(cls, name, getattr(cls, fnc))
                pipeline >>= cls.write
                pipelines[key] = pipeline
            setattr(cls, "pipeline", pipelines)
        case _:
            raise RuntimeError("Invalid ingest")


def _check_schema_attribute(cls: type, name: str):
    if hasattr(cls, name) and (schema := getattr(cls, name)) is not None:
        assert isinstance(schema, type), \
            f"Schema {name} of class `{cls.__name__}` is not a type."
        assert issubclass(schema, Model), \
            f"Schema {name} of class `{cls.__name__}` isn't a pydantic model."


def _print_validationerror(exception: ValidationError):
    for error in exception.errors():
        for loc in error["loc"]:
            _logger.warning("  %s", loc)
        _logger.warning("    %s (type=%s)", error["msg"], error["type"])


def _dedent_description(cls: type[Extension]):
    description = (getattr(cls, "description", cls.__doc__) or "").strip()
    starts_with_newline = description.startswith('\n')
    description = description.strip('\n')

    if starts_with_newline:
        description = textwrap.dedent(description)

    elif description.find('\n') != -1:
        first, rest = description.split('\n', 1)
        description = '\n'.join([first, textwrap.dedent(rest)])

    setattr(cls, "description", description)


def _stringify_pydantic(cls: Optional[type[Model]], indent=0) -> Optional[str]:
    if cls is None:
        return None

    assert issubclass(cls, Model), f"Expected pydantic model, got {cls}"
    fields = []
    for name, options in cls.model_fields.items():
        field = f"{name}"
        if options.annotation is not None:
            field += f": {options.annotation.__name__}"

            if args := getattr(options.annotation, "__args__", None):
                args = ', '.join([getattr(arg, '__name__', '')
                                  for arg in args])
                field += f"[{args}]"

        if options.default is not None and options.default is not PydanticUndefined:
            default = f'"{options.default}"' if isinstance(options.default, str) else options.default
            field += f" = {default}"
        fields.append(field)

    return ('\n' + ' ' * indent).join(fields)


__all__ = ['Extension', 'Model', 'Sources', 'max_jobs']
