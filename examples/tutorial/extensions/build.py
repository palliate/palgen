import logging
from pathlib import Path
from subprocess import check_call
from typing import Iterable

from palgen.ext import Extension, Sources, Model
from palgen.ingest import Suffixes, Relative

class Build(Extension):
    """ Very simple build system. Compiles with as many jobs as possible, links with one. """

    class Settings(Model):
        standard: int = 20

    def build(self, paths: Iterable[Path]):
        for path in paths:
            if ".in" in path.suffixes or ".tpl" in path.suffixes:
                continue

            output = self.out_path / path.with_suffix('.o')
            command = ["g++", str(path), "-c",
                       f"-I{self.out_path!s}",
                       f"-I{path.parent}",
                       "-o", str(output),
                       f"-std=c++{self.settings.standard}"]

            self._exec(command, "Compiled %s", output)
            yield str(output)

    #@max_jobs(1) # note that this is not needed, since `paths` is annotated with `list[...]`
    def link(self, paths: list[str]):
        output = self.out_path / self.project.name
        command = ["g++", *paths, "-o", str(output)]

        self._exec(command, "Linked %s", output)
        yield output

    def _exec(self, command, arg1, output):
        #logging.debug("Running: %s", ' '.join(command))
        check_call(command)
        logging.debug(arg1, output)

    ingest = Sources >> Suffixes('.cpp', '.c') >> Relative
    pipeline = Sources >> ingest >> build >> link
