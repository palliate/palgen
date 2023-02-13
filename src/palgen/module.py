import traceback
import logging
from pathlib import Path
from typing import Any, Iterator, Optional, Iterable, Type

import click
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel, ValidationError

from palgen.ingest import Ingest, Nothing
from palgen.ingest.toml import Toml

from palgen.util import Pipeline, setattr_default
from palgen.util.filesystem import SuffixDict
from palgen.util.schema import check_schema_attribute, print_validationerror

logger = logging.getLogger(__name__)


class Module:
    Settings = BaseModel
    Schema = BaseModel

    environment: Environment
    path: Path
    name: str
    ingest: Type[Ingest]
    private: bool

    @classmethod
    def __init_subclass__(cls, *,
                          name: Optional[str] = None,
                          private: bool = False) -> None:

        frame = traceback.extract_stack(limit=2)[0]
        setattr(cls, "path", Path(frame.filename))

        setattr_default(cls, "name", name or cls.__name__.lower())
        setattr_default(cls, "private", private)
        setattr_default(cls, "ingest", Toml(getattr(cls, "name")))

        if getattr(cls, "ingest") is None:
            # replace None with ingest that never yields
            setattr(cls, "ingest", Nothing)

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
            @click.command(name=cls.name, help=cls.__doc__)
            @click.pass_context
            def cli(ctx, **kwargs):
                settings = ctx.obj.settings.get(cls.name, {})
                settings |= {k: v for k, v in kwargs.items() if v}

                parser = cls(ctx.obj.root, ctx.obj.root, settings)
                parser.run(ctx.obj.files)

            for field, attribute in cls.Settings.__fields__.items():
                options = {'type': attribute.type_,
                           'required': attribute.required,
                           'help' : ""} #TODO option help texts

                if attribute.type_ is bool:
                    options['help'] = f"[flag] {options['help']}"
                    options['is_flag'] = True

                cli = click.option(f'--{field}', **options)(cli)

            setattr(cls, "cli", cli)

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

    def validate(self, data: Iterable[tuple[Path, Any]]) -> Iterator[tuple[Path, BaseModel | Any]]:
        for meta, value in data:
            try:
                yield meta, self.Schema.parse_obj(value)
            except ValidationError as ex:
                logger.warning("%s failed verification.", meta)
                print_validationerror(ex)

    def render(self, data: Iterator[tuple[Path, BaseModel | Any]]) -> Iterable[tuple[Path, str]]:
        """Render the prepared data.

        Args:
            data (Iterator[tuple[str, Meta, BaseModel]]): Generator producing
                full name, meta information and verifies data against our schema

        Yields:
            Iterator[tuple[Path, str]]: Yields relative output path and content for generated files
        """

        return
        # pylint: disable=unreachable
        yield Path(), ""  # type: ignore [unreachable]

    def write(self, output: Iterator[tuple[Path, str]]) -> Iterable[Path]:
        """Write the rendered files back to disk.

        Args:
            out_path (Path): Root output path
            output (Iterator[tuple[Path, str]]): Generator producing file content

        Yields:
            Iterator[Path]: Paths of generated files
        """
        for filename, generated in output:
            filename = self.out_path / filename
            filename.parent.mkdir(parents=True, exist_ok=True)
            with open(filename, "w+", encoding="utf8") as file:
                file.write(generated)

            logger.debug("Generated %s", filename)
            yield filename

    def run(self, source_tree: SuffixDict) -> list[Path]:
        output: list[Path] = list(Pipeline(source_tree)
                                  >> self.ingest
                                  >> self.validate
                                  >> self.render
                                  >> self.write)

        logger.info("%s yielded %s", self.name, output)
        return output

    def get_template(self, name: str, **kwargs):
        return self.environment.get_template(name, **kwargs)
