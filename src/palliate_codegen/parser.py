from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from palliate_codegen.log import logger


class parser:
    root = Path(__file__).parent.absolute()
    env = Environment(loader=FileSystemLoader(root / "templates"),
                      block_start_string="$%",
                      block_end_string="%$",
                      variable_start_string="${",
                      variable_end_string="}$",
                      comment_start_string="$#",
                      comment_end_string="#$",
                      keep_trailing_newline=True
                      )

    def __init__(self, root_path, out_path, no_cli=False):
        self.no_cli = no_cli
        self.root_path = Path(root_path)
        self.out_path = Path(out_path)
        self.table = {}
        self.source_map = {}
        self.output = {}

    def validate(self):
        raise NotImplementedError

    def render(self):
        raise NotImplementedError

    def write(self):
        for file, data in self.output.items():
            logger.debug(f"Generated {file}")
            file.parent.mkdir(parents=True, exist_ok=True)
            with open(file, 'w+') as f:
                f.write(data)

    def ingest(self, data, source):
        if type(data) is dict:
            if not self.table:
                self.table = {}

            collisions = self.table.keys() & data.keys()
            if collisions:
                raise Exception(f"Key collision(s): {collisions}")

            self.source_map |= {key: source
                                for key in data.keys()}
            self.table |= data
        elif type(data) is list:
            if not self.table:
                self.table = []

            self.table.extend(data)
            self.source_map |= {v["name"]: source
                                for v in data
                                if "name" in v}

    def fix_value(self, value) -> str:
        if type(value) is str:
            return f'"{value}"'
        elif type(value) is bool:
            return str(value).lower()
        elif type(value) is list:
            if len(value) > 1:
                raise ValueError(
                    "Raw default list contained more than one item")
            return value[0]

        return str(value)
