import logging
from typing import Annotated, Optional

from palgen.ext import Extension, Model

# extension class must inherit from palgen.ext.Extension
class HelloWorld(Extension):
    ''' Prints hello world '''
    # a docstring can be used to provide a help text

    # we don't need to ingest anything for now
    ingest = None

    # settings and command line options for this extension.
    # note that the `Settings` subclass must inherit from `Model`
    class Settings(Model):
        # This is sufficient to require `name` to exist and be of type `str`
        name: str

        # Settings can also be annotated with a help text
        greeting: Annotated[str, "The greeting to display"] = "Hello"

        repeat: int = 1         # Optional int, defaults to 1
        uppercase: bool = False # Optional flag, defaults to False


    # since we do not use data pipelines in this simple command line tool
    # we instead override `Extension.run(...)` directly
    def run(self, files: list, jobs: Optional[int] = None) -> list:

        # this extension's settings can be accessed using self.settings
        greeting = self.settings.greeting

        if self.settings.uppercase:
            greeting = greeting.upper()

        for _ in range(self.settings.repeat):
            # `logging` should be prefered over `print` for output consistency
            logging.info("%s, %s", greeting, self.settings.name)


        # we didn't produce any files, so return an empty list or `None`

        # note that `return None`, `return` and no return statements whatsoever
        # are equivalent in Python. Any empty iterable would be fine too.
        return []
