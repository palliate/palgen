import logging

from palgen.interfaces.module import Module, Model

# module class must inherit from palgen.module.Module
class HelloWorld(Module):
    ''' Prints hello world '''
    # a docstring can be used to provide a help text

    # we don't need to ingest anything for now
    ingest = None

    # settings and command line options for this module.
    # note that the `Settings` subclass must inherit from `Model`
    class Settings(Model):
        enabled: bool = True

    # since we do not use data pipelines in this simple command line tool
    # we instead override `Module.run(...)` directly
    def run(self, data: list) -> list:
        # this module's settings can be accessed using self.settings
        if self.settings.enabled:
            # `logging` should be prefered over `print` for consistency
            logging.info("Hello world")

        # we didn't produce any files, so return an empty list
        return []
