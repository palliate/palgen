import logging

from palgen.parser import Parser
from palgen.validation import Dict, List, Maybe, String

logger = logging.getLogger("palgen")


class Template(Parser):
    settings_schema = Dict(
        {
            "folders": Maybe(List(String)),
        }
    )

    config_schema = List(Dict)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print(f"{self.settings=}")

    def prepare(self):
        # TODO collect export headers
        # glob for .h, .cpp and CMakeLists.txt?
        # TODO decide on folder structure
        pass

    def render(self):
        for input in self.input:
            # TODO copy export headers
            pass
