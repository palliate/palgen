from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from palgen.log import logger
from palgen.project import Project


class Parser:
    root = Path(__file__).parent.absolute()
    env = Environment(loader=FileSystemLoader(root / "tables"),
                      block_start_string="$%",
                      block_end_string="%$",
                      variable_start_string="${",
                      variable_end_string="}$",
                      comment_start_string="$#",
                      comment_end_string="#$",
                      keep_trailing_newline=True
                      )

    def __init__(self, root_path, settings):
        self.settings = settings
        self.root_path = Path(root_path)
        self.out_path = Path(settings["output"])
        self.input = None
        self.output = {}
        self.ingestable = True


    def prepare(self):
        raise NotImplementedError("Not implemented")

    def render(self):
        raise NotImplementedError("Not implemented")

    def write(self):
        for file, data in self.output.items():
            logger.debug(f"Generated {file.relative_to(self.root_path)}")
            file.parent.mkdir(parents=True, exist_ok=True)
            with open(file, 'w+') as f:
                f.write(data)

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

        elif type(data) is Project:
            if not self.input:
                self.input = []

            data.source = source.parent
            self.input.append(data)


