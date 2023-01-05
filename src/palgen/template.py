import inspect
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Generator, Iterator, Optional

import toml
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel, ValidationError

from palgen.util.transformations import compress

logger = logging.getLogger(__name__)


@dataclass
class Meta:
    name: str
    namespace: str
    source: Path
    relative_path: Path


class Template:
    Schema = BaseModel
    environment: Environment
    ingestable: bool

    @classmethod
    def __init_subclass__(cls,
                          ingestable: bool = True,
                          key: Optional[str] = None,
                          extension: str = '.toml') -> None:

        if hasattr(cls, "Schema") and (schema := getattr(cls, "Schema")):
            if schema is not BaseModel:
                name = cls.__name__
                if not isinstance(schema, type):
                    raise SyntaxError(
                        f"Schema of template `{name}` is not a type.")

                if BaseModel not in schema.__bases__:
                    print(schema.__bases__)
                    raise SyntaxError(
                        f"Schema of template `{name}` isn't a pydantic model.")

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

        setattr(cls, "ingestable", ingestable)
        setattr(cls, "key", key or cls.__name__.lower())
        setattr(cls, "extension", extension)

    def __init__(self, root_path: Path, settings: dict):
        self.settings: Any = None
        self.name: str = type(self).__name__
        self.root_path = root_path
        self.keys: set[str] = set()
        self.output = {}

        if hasattr(self, "Settings"):
            validator = getattr(self, "Settings")
            if BaseModel not in validator.__bases__:
                raise TypeError(
                    "Settings subclass must be of type pydantic.BaseModel")

            self.settings = validator(**settings)
            logger.debug("Validated settings for %s", self.name)
        else:
            if settings:
                logger.warning(
                    "Got settings but %s accepts no settings.", self.name)

    def ingest(self, paths: list[Path]) -> Iterator[tuple[str, Meta, BaseModel]]:
        for source in paths:
            logger.debug("Ingesting %s.", source)

            yield from self.load_toml(source)

    def load_toml(self, path: Path):

        if (relative_path := path.parent).is_relative_to(self.root_path):
            relative_path = relative_path.relative_to(self.root_path)
        else:
            raise RuntimeError("Config file isn't within root directory.")

        data = toml.load(path)

        file_namespace = data.pop("namespace", None)
        if isinstance(file_namespace, str):
            file_namespace = file_namespace.split('.')

        for namespace, name, value in compress(data, file_namespace):
            full_name = f"{namespace}.{name}" if namespace else name
            if full_name in self.keys:
                logger.warning(
                    "Key collision: `%s` already contained", full_name)
                continue

            try:
                self.keys.add(full_name)
                yield (full_name,
                       Meta(name, namespace, path, relative_path),
                       self.Schema.parse_obj(value))

            except ValidationError as ex:
                logger.warning("%s failed verification.", full_name)
                for error in ex.errors():
                    for loc in error["loc"]:
                        logger.warning("  %s", loc)
                    logger.warning("    %s (type=%s)",
                                   error["msg"], error["type"])

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

    def write(self, out_path: Path, output: Iterator[tuple[Path, str]]) -> Iterator[Path]:
        """Write the rendered files back to disk.

        Args:
            out_path (Path): Root output path
            output (Iterator[tuple[Path, str]]): Generator producing file content

        Yields:
            Iterator[Path]: Paths of generated files
        """
        for filename, generated in output:
            filename = out_path / filename
            filename.parent.mkdir(parents=True, exist_ok=True)
            with open(filename, "w+", encoding="utf8") as file:
                file.write(generated)

            logger.debug("Generated %s", filename)
            yield filename

    def get_template(self, name: str, **kwargs):
        return self.environment.get_template(name, **kwargs)
