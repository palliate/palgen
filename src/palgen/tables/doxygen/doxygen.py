from palgen.parser import Parser
from palgen.log import logger

class Doxygen(Parser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ingestable = False

    def prepare(self):
        # write doxyfile
        # write
        print(self.settings)
        print("done")

    def render(self):
        print("done")
