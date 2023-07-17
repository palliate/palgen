import logging
import traceback
from pathlib import Path
from typing import Any, Iterable, Optional, Type

from pydantic import BaseModel as Model
from pydantic import ValidationError

from .ingest import Suffix, Name, Nothing, Toml
from .machinery import setattr_default
from .machinery import Pipeline as Sources

_logger = logging.getLogger(__name__)


def max_jobs(amount: int):
    def wrapper(fnc):
        fnc.max_jobs = amount
        return fnc
    return wrapper


class Extension:
    Settings: Type[Model] = Model        # Schema for extension configuration
    Schema: Optional[Type[Model]] = None # Optional schema to be used to validate each ingested item.

    name: str               # Extension name. Defaults to lowercase class name
    private: bool           # Whether this extension is local to this project.
                            # Setting this to true mangles the import name
    template: Optional[str] # Optional extension template name to fetch defaults from

    # pipelines
    ingest: Sources | dict[str, Sources]   # Pipeline used to select and read input files
    pipeline: Sources | dict[str, Sources] # Overall extension pipeline.
                                           # Override this if you want to disable all default steps

    # set by the loader
    module: str # full module name
    path: Path  # path to this module

    def transform(self, data: Iterable[tuple[Path, Any]]) -> Iterable[tuple[Path, Any]]:
        """This step is intended to transform input data to something
        pydantic can validate in the :code:`validate` step.

        By default does nothing.

        Args:
            data (Iterable[tuple[Path, Any]]): Iterable of inputs from the :code:`ingest` pipeline

        Yields:
            tuple[Path, Any]: Transformed output
        """
        yield from data

    def validate(self, data: Iterable[tuple[Path, Any]]) -> Iterable[tuple[Path, Any]]:
        """Intended to validate elements in the :code:`data` Iterable against the pydantic schema :code:`Schema` of this extension.

        By default does nothing.

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
                    _logger.warning("%s failed verification.", path)
                    _print_validationerror(ex)
        else:
            yield from data

    def render(self, data: Iterable[tuple[Path, Model | Any]]) -> Iterable[tuple[Path, str | bytes]]:
        """Intended to render the output content.
        By default cancels the pipeline at this point.

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
                      encoding="utf8") as file:
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
        return f"""\
Name:        {cls.name}
Module:      palgen.ext.{cls.module}
Private:     {cls.private}
Description: {cls.__doc__ or ""}

Options:     {cls.Settings}
Schema:      {cls.Schema or ""}

Pipeline(s): {cls.pipeline}"""

    def __str__(self) -> str:
        return self.to_string()

    def __init__(self, root_path: Path, out_path: Path, settings: Optional[dict[str, Any]] = None):
        """Extension constructor. If settings are provided they are checked against the :code:`Settings` schema.

        It's not recommended to override this unless you want to disable settings validation.

        Args:
            root_path (Path):                              Path to the project's root folder
            out_path (Path):                               Output path
            settings (Optional[dict[str, Any]], optional): Extension settings. Defaults to None.

        Raises:
            SystemExit: If settings are provided but fail to validate
        """
        self.root = root_path
        self.out_path = out_path
        self.settings: Optional[Any]
        if settings is None:
            raise RuntimeError(f"No settings found for extension {self.name}")

        try:
            self.settings = self.Settings(**settings)
            _logger.debug("Validated settings for %s", self.name)

        except ValidationError as ex:
            _logger.warning("Failed verifying config for `%s`", self.name)
            _print_validationerror(ex)
            # TODO rethrow ValidationError instead, make sure we terminate with retcode 1 somewhere else
            raise SystemExit(1) from ex

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
        setattr(cls, "path", Path(frame.filename))

        setattr_default(cls, "name", name or cls.__name__.lower())
        setattr_default(cls, "private", private)

        setattr_default(cls, "ingest", Sources() >> Suffix('toml')
                                                 >> Name(getattr(cls, "name"))
                                                 >> Toml)
        assert hasattr(cls, "ingest")
        ingest = getattr(cls, "ingest")

        if not hasattr(cls, "pipeline"):
            match ingest:
                case Sources():
                    setattr(cls, "pipeline", Sources() >> ingest
                                                       >> cls.transform
                                                       >> cls.validate
                                                       >> cls.render
                                                       >> cls.write)
                    logging.debug("Pipeline: \n%s", str(getattr(cls, "pipeline")))
                case None:
                    setattr(cls, "pipeline", Sources() >> Nothing)
                    logging.debug("Pipeline: \n%s", str(getattr(cls, "pipeline")))
                case dict():
                    pipelines = {}
                    for key, value in ingest.items():
                        pipeline = Sources() >> value
                        for fnc in 'transform', 'validate', 'render':
                            name = f"{fnc}_{key}"
                            pipeline >>= getattr(cls, name, getattr(cls, fnc))
                        pipeline >>= cls.write
                        pipelines[key] = pipeline
                    logging.debug("Pipelines: \n%s",
                                  '\n'.join(f'    {k}: {str(v)}' for k, v in pipelines.items()))

                    setattr(cls, "pipeline", pipelines)
                case _:
                    raise RuntimeError("Invalid ingest")

        _check_schema_attribute(cls, "Settings")
        _check_schema_attribute(cls, "Schema")

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


__all__ = ['Model', 'Extension', 'Sources']
