from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from palgen.log import logger
#from palgen.project import Project


class Parser:
    def __init__(self, root_path: Path, template_path: Path, settings: dict):
        self.settings = settings
        self.root_path = root_path
        self.template_path = template_path
        self.input = {}
        self.output = {}
        self.ingestable = True

        self.env = Environment(loader=FileSystemLoader(template_path),
                               block_start_string="$%",
                               block_end_string="%$",
                               variable_start_string="${",
                               variable_end_string="}$",
                               comment_start_string="$#",
                               comment_end_string="#$",
                               keep_trailing_newline=True
                               )

        if hasattr(self, "settings_schema"):
            if self.settings_schema.check(self.settings):
                logger.debug(f"Successfully validated settings for `{self.__module__}`")
            else:
                raise RuntimeError(f"Failed to verify schema")

    def prepare(self):
        pass

    def generate(self):
        pass

    def render(self):
        raise NotImplementedError("Not implemented")

    def write(self, out_path=None):
        # TODO refactor
        if not out_path:
            out_path = Path(self.settings["output"])

        for file, data in self.output.items():
            logger.debug(f"Generated {file.relative_to(self.out_path)}")
            file.parent.mkdir(parents=True, exist_ok=True)
            with open(file, 'w+') as f:
                f.write(data)

        return len(self.output)

    def ingest(self, data, source, project):
        if type(data) is dict:
            if not self.input:
                self.input = {}

            collisions = self.input.keys() & data.keys()
            if collisions:
                raise Exception(f"Key collision(s): {collisions}")

            for _, item in data.items():
                item["source"] = source.parent
                item["project"] = project

            self.input |= data

        elif type(data) is list:
            if not self.input:
                self.input = []

            for item in data:
                item["source"] = source.parent
                item["project"] = project

            self.input.extend(data)
