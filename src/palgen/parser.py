import logging
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)


class Parser:
    def __init__(self, root_path: Path, template_path: Path, settings: dict):
        self.settings = settings
        self.root_path = root_path
        self.template_path = template_path
        self.input = {}
        self.output = {}
        self.ingestable = True

        self.env = Environment(
            loader=FileSystemLoader(template_path),
            block_start_string="$%",
            block_end_string="%$",
            variable_start_string="${",
            variable_end_string="}$",
            comment_start_string="$#",
            comment_end_string="#$",
            keep_trailing_newline=True,
        )

        if hasattr(self, "settings_schema"):
            if self.settings_schema.check(self.settings):
                logger.info("Successfully validated settings for `%s`",
                            self.__module__)
            else:
                raise ValueError("Failed to verify schema")

    def prepare(self):
        """Prepare the collected data for rendering.
        This step is optional and usually only required if the incoming
        data has to be further processed.
        """

    def render(self):
        """Render the prepared data.

        Raises:
            NotImplementedError: If not overridden
        """

        raise NotImplementedError("Not implemented")

    def write(self, out_path: Path) -> int:
        """Write the rendered files back to disk.

        Args:
            out_path (Path): Root output path

        Returns:
            int: Number of generated files
        """

        for file, data in self.output.items():
            file = out_path / file
            logger.debug("Generated %s", file)
            file.parent.mkdir(parents=True, exist_ok=True)
            with open(file, "w+", encoding="utf8") as file:
                file.write(data)

        return len(self.output)

    def ingest(self, data: dict | list, source: Path, project: Any):
        """Ingests data. This step also verifies the incoming data if a schema is given.

        Args:
            data (dict | list): data to ingest
            source (Path): path to the config the data originated from
            project (Project): project to which the config belongs

        Raises:
            RuntimeError: Ingest failed
            KeyError: Key defined more than once
            ValueError: Validation against config schema failed
        """

        source = source.parent.resolve()
        if source.is_relative_to(self.root_path):
            source = source.relative_to(self.root_path)
        else:
            raise RuntimeError(
                "Error during ingest. Config file isn't within root directory."
            )

        if hasattr(self, "config_schema"):
            if not self.config_schema.check(data):
                raise ValueError("Failed to verify schema")

        if isinstance(data, dict):
            if not self.input:
                self.input = {}

            collisions = self.input.keys() & data.keys()
            if collisions:
                raise KeyError(f"Key collision(s): {collisions}")

            for _, item in data.items():
                item["source"] = source
                item["project"] = project

            self.input |= data

        if isinstance(data, list):
            if not self.input:
                self.input = []

            for item in data:
                item["source"] = source
                item["project"] = project

            self.input.extend(data)
