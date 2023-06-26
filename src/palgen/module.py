import logging
import traceback
from pathlib import Path
from typing import Any, Iterable, Optional

from pydantic import BaseModel, ValidationError

from palgen.ingest.filter import Extension, Name
from palgen.ingest.loader import Nothing, Toml
from palgen.util import Pipeline, setattr_default
from palgen.util.filesystem import Sources
from palgen.util.schema import Model, check_schema_attribute, print_validationerror

logger = logging.getLogger(__name__)


def jobs(max_jobs: int):
    def wrapper(fnc):
        fnc.max_jobs = max_jobs
        return fnc
    return wrapper


class Module:
    Settings = Model
    Schema = Model

    name: str  # defaults to lowercase class name
    private: bool

    # pipelines
    ingest: Pipeline | dict[str, Pipeline]
    pipeline: Pipeline | dict[str, Pipeline]

    # set by the loader
    module: str
    path: Path

    def transform(self, data: Iterable[tuple[Path, Any]]) -> Iterable[tuple[Path, Any]]:
        """This step is intended to transform input data to something
        pydantic can validate in the `validate` step.

        Args:
            data (Iterable[tuple[Path, Any]]): Iterable of inputs from the `ingest` pipeline

        Yields:
            tuple[Path, Any]: Transformed output
        """
        yield from data

    def validate(self, data: Iterable[tuple[Path, Any]]) -> Iterable[tuple[Path, BaseModel | Any]]:
        """Validates elements in the `data` Iterable against the pydantic schema `Schema` of this module.

        Args:
            data (Iterable[tuple[Path, Any]]): Iterable of inputs from the `transform` step

        Yields:
            tuple[Path, BaseModel | Any]: Input file path and validated `Schema` object

        Warning:
            By default inputs failing verification do not cause the module run to fail,
            they simply get skipped.
        """
        for path, value in data:
            try:
                yield path, self.Schema.parse_obj(value)
            except ValidationError as ex:
                logger.warning("%s failed verification.", path)
                print_validationerror(ex)

    def render(self, data: Iterable[tuple[Path, BaseModel | Any]]) -> Iterable[tuple[Path, str]]:
        """Renders the output content.

        Args:
            data (Iterable[tuple[str, Meta, BaseModel]]): Iterable of inputs from the `validate` step.

        Yields:
            tuple[Path, str]: Output path and content for generated files
        """
        # Yes yes, this is intended.
        # despite yield being unreachable its existence will set the CO_GENERATOR flag
        # hence making this a generator

        # it's ugly but it stops some linters from crying

        return
        # sourcery skip: remove-unreachable-code; pylint: disable=unreachable
        yield Path(), ""  # type: ignore [unreachable]

    def write(self, output: Iterable[tuple[Path, str]]) -> Iterable[Path]:
        """Write the rendered files back to disk.

        Args:
            output (Iterable[tuple[Path, str]]): Iterable of inputs from the `render` step

        Yields:
            Path: Path to every generated file
        """
        for filename, generated in output:
            filename = self.out_path / filename
            filename.parent.mkdir(parents=True, exist_ok=True)
            with open(filename, "w+", encoding="utf8") as file:
                file.write(generated)

            logger.debug("Generated `%s`", filename)
            yield filename

    def run(self, files: list[Path], jobs: Optional[int] = None) -> list[Path]:
        """Runs the module's pipeline.
        If the pipeline is a dictionary, it will loop through each item and run
        the associated pipeline. Otherwise, it will run the single pipeline.

        This method may be overridden for modules that do not wish to use the
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
                logger.debug("Running pipeline `%s`", key)
                output.extend(pipeline(files, obj=self, max_jobs=jobs))
        else:
            output = self.pipeline(files, obj=self, max_jobs=jobs)

        logger.info("Module `%s` yielded %s file%s",
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
Schema:      {cls.Schema}

Pipeline(s): {cls.pipeline}"""

    def __str__(self) -> str:
        return self.to_string()

    def __init__(self, root_path: Path, out_path: Path, settings: Optional[dict[str, Any]] = None):
        """Module constructor. If settings are provided they are checked against the `Settings` schema.

        Args:
            root_path (Path): Path to the project's root folder
            out_path (Path): Output path
            settings (Optional[dict[str, Any]], optional): Module settings. Defaults to None.

        Raises:
            SystemExit: If settings are provided but fail to validate
        """
        self.root = root_path
        self.out_path = out_path

        if settings is None:
            return

        try:
            self.settings = self.Settings(**settings)
            logger.debug("Validated settings for %s", self.name)

        except ValidationError as ex:
            logger.warning("Failed verifying config for `%s`", self.name)
            print_validationerror(ex)
            # TODO rethrow ValidationError instead, make sure we terminate with retcode 1 somewhere else
            raise SystemExit(1) from ex

    @classmethod
    def __init_subclass__(cls, *,
                          name: Optional[str] = None,
                          private: bool = False) -> None:
        """This class method is used to preprocess subclasses of the `Module` interface.


        It sets the following attributes on the subclass:

        Attributes:
            path (Path):       Path object containing the filename of the subclass.
            name (str):        Name of the subclass. If no name is provided,
                               the name of the class converted to lowercase is used.
            private (bool):    Indicates whether the subclass should be private or not.
            ingest (Pipeline): Defaults `ingest` to ingest toml files matching the module name.
                               Use `ingest = None` if you want to disable ingest.

        Args:
            name (Optional[str], optional): Overrides the module name. Defaults to None.
            private (bool, optional):       Sets this module as private. Defaults to False.

        Raises:
            RuntimeError: Throws RuntimeError if an invalid ingest pipeline has been given.
        """
        frame = traceback.extract_stack(limit=2)[0]
        setattr(cls, "path", Path(frame.filename))

        setattr_default(cls, "name", name or cls.__name__.lower())
        setattr_default(cls, "private", private)

        setattr_default(cls, "ingest", Pipeline >> Extension('toml')
                                                >> Name(getattr(cls, "name"))
                                                >> Toml)
        assert hasattr(cls, "ingest")
        ingest = getattr(cls, "ingest")

        if not hasattr(cls, "pipeline"):
            match ingest:
                case Pipeline():
                    setattr(cls, "pipeline", Pipeline() >> ingest
                                                        >> cls.transform
                                                        >> cls.validate
                                                        >> cls.render
                                                        >> cls.write)
                    logging.debug("Pipeline: \n%s", str(getattr(cls, "pipeline")))
                case None:
                    setattr(cls, "pipeline", Pipeline() >> Nothing)
                    logging.debug("Pipeline: \n%s", str(getattr(cls, "pipeline")))
                case dict():
                    pipelines = {}
                    for key, value in ingest.items():
                        pipeline = Pipeline >> value
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

        check_schema_attribute(cls, "Settings")
        check_schema_attribute(cls, "Schema")

__all__ = ['Module', 'Sources']
