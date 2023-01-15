import inspect
import logging
from functools import reduce
from pathlib import Path
from typing import Any, Iterator, Optional

import click
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel, ValidationError

from palgen.ingest import Ingest, Meta
from palgen.ingest.toml import Toml
from palgen.util.filesystem import SuffixDict

logger = logging.getLogger(__name__)


class Template:
    Config = BaseModel
    Schema = BaseModel

    environment: Environment
    key: str
    extension: str
    loader: Ingest

    @classmethod
    def _check_schema(cls, name):
        if hasattr(cls, name) and (schema := getattr(cls, name)):
            if schema is BaseModel:
                return

            if not isinstance(schema, type):
                raise SyntaxError(
                    f"{name} of template `{cls.key}` is not a type.")

            if BaseModel not in schema.__bases__:
                raise SyntaxError(
                    f"{name} of template `{cls.key}` isn't a pydantic model.")
    @staticmethod
    def _print_validationerror(exception: ValidationError):
        for error in exception.errors():
            for loc in error["loc"]:
                logger.warning("  %s", loc)
            logger.warning("    %s (type=%s)", error["msg"], error["type"])

    @classmethod
    def __init_subclass__(cls, *,
                          ingestable: bool = True,
                          key: Optional[str] = None,
                          extension: str = '.toml') -> None:
        setattr(cls, "key", key or cls.__name__.lower())
        setattr(cls, "extension", extension)
        Template._check_schema("Config")
        Template._check_schema("Schema")

        path = Path(inspect.stack()[1].filename).parent
        setattr(cls, "environment", Environment(
            loader=FileSystemLoader(path),
            block_start_string="@{",
            block_end_string="}",
            variable_start_string="@",
            variable_end_string="@",
            comment_start_string="@/*",
            comment_end_string="*/",
            keep_trailing_newline=True,
        ))

        if not hasattr(cls, "loader"):
            setattr(cls, "loader", Toml())

        if not hasattr(cls, "cli"):
            @click.command(name=cls.key)
            @click.pass_context
            def cli(ctx, **kwargs):
                settings = ctx.obj.settings.get(cls.key, {})
                settings |= {k:v for k, v in kwargs.items() if v}
                print(settings)
                parser = cls(ctx.obj.root, ctx.obj.root, settings)
                files = list(parser.run(ctx.obj.files))

                logger.info(f"{parser=} yielded {files=}")
            for field, attribute in cls.Config.__fields__.items():
                # TODO handle required
                cli = click.option(f'--{field}', type=attribute.type_)(cli)
            setattr(cls, "cli", cli)

    def __init__(self, root_path: Path, out_path: Path, settings: Optional[dict] = None):
        self.root_path = root_path
        self.out_path = out_path
        try:
            self.settings = self.Config.parse_obj(settings)
            logger.debug("Validated settings for %s", self.key)
        except ValidationError as ex:
            logger.warning("Failed verifying config for `%s`", self.key)
            self._print_validationerror(ex)
            raise SystemExit(1) from ex

    def ingest(self, source_tree: SuffixDict) -> Iterator[tuple[Meta, Any | BaseModel]]:
        if not self.loader:
            print("nothing to do")
            return

        for source in source_tree.by_name(f"{self.key}{self.extension}"):
            logger.debug("Ingesting %s.", source)

            for meta, data in self.loader.data(source):
                try:
                    yield meta, self.Schema.parse_obj(data)
                except ValidationError as ex:
                    logger.warning("%s failed verification.", meta.qualname)
                    self._print_validationerror(ex)

    def render(self, data: Iterator[tuple[str, Meta, BaseModel]]) -> Iterator[tuple[Path, str]]:
        """Render the prepared data.

        Args:
            data (Iterator[tuple[str, Meta, BaseModel]]): Generator producing
                full name, meta information and verifies data against our schema

        Raises:
            NotImplementedError: If not overridden

        Yields:
            Iterator[tuple[Path, str]]: Yields relative output path and content for generated files
        """

        raise NotImplementedError("Not implemented")
        # trunk-ignore(pylint/W0101)
        yield Path(), ""

    def write(self, output: Iterator[tuple[Path, str]]) -> Iterator[Path]:
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

    def run(self, source_tree: SuffixDict) -> Iterator[Path]:
        yield from reduce(lambda x, step: step(x), [
            source_tree,
            self.ingest,
            self.render,
            self.write
        ])

    def get_template(self, name: str, **kwargs):
        return self.environment.get_template(name, **kwargs)
