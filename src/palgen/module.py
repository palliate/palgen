import traceback
import logging
from pathlib import Path
from typing import Any, Optional, Iterable, Type

import click
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel, ValidationError

from palgen.ingest import Ingest, Nothing, Filter
from palgen.ingest.toml import Toml

from palgen.util import Pipeline, setattr_default
from palgen.util.filesystem import SuffixDict, Sources
from palgen.util.schema import check_schema_attribute, print_validationerror, pydantic_to_click

logger = logging.getLogger(__name__)


class Module:
    Settings = BaseModel
    Schema = BaseModel

    name: str  # defaults to lowercase class name
    private: bool

    # pipelines
    ingest: Pipeline
    pipeline: Pipeline

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

    def run(self, source_tree: SuffixDict) -> list[Path]:
        output: list[Path] = list(self.pipeline(source_tree, self))

        logger.info("Module `%s` yielded %s file%s",
                    self.name,
                    len(output),
                    's' if len(output) > 1 else '')
        return output

    def get_template(self, name: str, **kwargs):
        return self.environment.get_template(name, **kwargs)

    def __init__(self, root_path: Path, out_path: Path, settings: Optional[dict] = None):
        self.root_path = root_path
        self.out_path = out_path
        try:
            self.settings = self.Settings.parse_obj(settings)
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
        setattr_default(cls, "ingest", Pipeline >> Filter(getattr(cls, "name"))
                                                >> Toml)
        #if getattr(cls, "ingest") is None:
        #    # TODO
        #    # replace None with ingest that never yields
        #    setattr(cls, "ingest", Nothing)

        setattr_default(cls, "pipeline", Pipeline >> getattr(cls, "ingest")
                                                  >> cls.transform
                                                  >> cls.validate
                                                  >> cls.render
                                                  >> cls.write)
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

        if not hasattr(cls, "cli"):
            @click.command(name=cls.name,
                           help=cls.__doc__,
                           context_settings={'show_default': True})
            @click.pass_context
            def cli(ctx, **kwargs):
                settings = ctx.obj.settings.get(cls.name, {})
                settings |= {k: v for k, v in kwargs.items() if v}

                parser = cls(ctx.obj.root, ctx.obj.root, settings)
                parser.run(ctx.obj.files)

            for field, options in pydantic_to_click(cls.Settings):
                cli = click.option(f'--{field}', **options)(cli)

            setattr(cls, "cli", cli)


__all__ = ['Module', 'Sources']
