from palgen.log import logger
from palgen.parser import Parser
from palgen.templates import Templates
from palgen.validation import *

from pathlib import Path

class Template(Parser):
    settings_schema = Dict({
        'folders': Maybe(List(String)),
    })

    config_schema = Dict

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print(f"{self.settings=}")
        print(f"{self.settings_schema.check(self.settings)=}")

    def load_templates(self, target :Templates):
        if 'folders' not in self.settings:
            return

        for folder in self.settings['folders']:
            path = Path(folder)
            if not path.is_absolute():
                path = self.root_path / path

            target.load(path)
