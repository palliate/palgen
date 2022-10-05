from pathlib import Path

from palgen.parser import Parser
from palgen.module import Modules
from palgen.validation import *

import logging
logger = logging.getLogger('palgen')

class Template(Parser):
    settings_schema = Dict({
        'folders': Maybe(List(String)),
    })

    config_schema = Dict({'output': Maybe(String)})

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print(f"{self.settings=}")

    def load_templates(self, target: Modules):
        if 'folders' not in self.settings:
            return

        for folder in self.settings['folders']:
            path = Path(folder)
            if not path.is_absolute():
                path = self.root_path / path
            logger.debug("Loading templates from %s", path)
            target.load(path)

    def render(self):
        pass
