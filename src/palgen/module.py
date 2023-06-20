import logging
import traceback
from pathlib import Path
from typing import Any, Iterable, Optional

from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel, ValidationError

from palgen.ingest.filter import Extension, Name
from palgen.ingest.loader import Nothing, Toml
from palgen.util import Pipeline, setattr_default
from palgen.util.filesystem import Sources
from palgen.util.schema import Model, check_schema_attribute, print_validationerror

logger = logging.getLogger(__name__)


class Module:
    Settings = Model
    Schema = Model

    name: str  # defaults to lowercase class name
    private: bool

    # pipelines
    ingest: Pipeline | dict[str, Pipeline]
    pipeline: Pipeline | dict[str, Pipeline]

    # set by the loader
    environment: Environment
    module: str
    path: Path

    def transform(self, data: Iterable[tuple[Path, Any]]) -> Iterable[tuple[Path, Any]]:
        yield from data

    def validate(self, data: Iterable[tuple[Path, Any]]) -> Iterable[tuple[Path, BaseModel | Any]]:
        for path, value in data:
            try:
                yield path, self.Schema.parse_obj(value)
            except ValidationError as ex:
                logger.warning("%s failed verification.", path)
                print_validationerror(ex)

    def render(self, data: Iterable[tuple[Path, BaseModel | Any]]) -> Iterable[tuple[Path, str]]:
        """Render the prepared data.

        Args:
            data (Iterable[tuple[str, Meta, BaseModel]]): Generator producing
                full name, meta information and verifies data against our schema

        Yields:
            Iterable[tuple[Path, str]]: Yields relative output path and content for generated files
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
            out_path (Path): Root output path
            output (Iterable[tuple[Path, str]]): Generator producing file content

        Yields:
            Iterable[Path]: Paths of generated files
        """
        for filename, generated in output:
            filename = self.out_path / filename
            filename.parent.mkdir(parents=True, exist_ok=True)
            with open(filename, "w+", encoding="utf8") as file:
                file.write(generated)

            logger.debug("Generated `%s`", filename)
            yield filename

    def run(self, files: list[Path], jobs: int) -> list[Path]:
        """Runs the module's pipeline

        Args:
            files (list[Path]): possibly pre-filtered list of paths to consider for ingest.

        Returns:
            list[Path]: List of paths to generated files
        """
        output: list[Path] = []

        if isinstance(self.pipeline, dict):
            for key, pipeline in self.pipeline.items():
                logger.debug("Running pipeline `%s`", key)
                output.extend(pipeline(files, obj=self, jobs=jobs))
        else:
            output = self.pipeline(files, obj=self, jobs=jobs)

        logger.info("Module `%s` yielded %s file%s",
                    self.name,
                    len(output),
                    's' if len(output) > 1 else '')
        return output

    def get_template(self, name: str, **kwargs):
        # TODO out of class definition might be better
        return self.environment.get_template(name, **kwargs)

    def __init__(self, root_path: Path, out_path: Path, settings: Optional[dict[str, Any]] = None):
        self.root_path = root_path
        self.out_path = out_path

        if settings is None:
            return

        try:
            self.settings = self.Settings(**settings)
            logger.debug("Validated settings for %s", self.name)

        except ValidationError as ex:
            logger.warning("Failed verifying config for `%s`", self.name)
            print_validationerror(ex)
            raise SystemExit(1) from ex

    @classmethod
    def __init_subclass__(cls, *,
                          name: Optional[str] = None,
                          private: bool = False) -> None:

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
                case None:
                    setattr(cls, "pipeline", Pipeline() >> Nothing)
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
                                  '\n'.join(f'    {k}: {str(v)}' for k,v in pipelines.items()))

                    setattr(cls, "pipeline", pipelines)
                case _:
                    raise RuntimeError("Invalid ingest")

        check_schema_attribute(cls, "Settings")
        check_schema_attribute(cls, "Schema")

        setattr(cls, "environment", Environment(
            loader=FileSystemLoader(cls.path.parent),
            block_start_string="@{",
            block_end_string="}",
            variable_start_string="@",
            variable_end_string="@",
            comment_start_string="@/*",
            comment_end_string="*/",
            keep_trailing_newline=True,
        ))


__all__ = ['Module', 'Sources']
