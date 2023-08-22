import logging
from pathlib import Path
from subprocess import check_call
from typing import Iterable

from palgen import Extension, Sources, Model
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

            check_call(["g++", str(path), "-c",
                       f"-I{self.out_path!s}",
                       f"-I{path.parent}",
                       "-o", str(output),
                       f"-std=c++{self.settings.standard}"])
            logging.info("Compiled %s", output)

            yield str(output)

    #@max_jobs(1) # note that this is not needed, since `paths` is annotated with `list[...]`
    def link(self, paths: list[str]):
        output = self.out_path / self.project.name

        check_call(["g++", *paths, "-o", str(output)])
        logging.info("Linking %s", output)

        yield output

    ingest = Sources >> Suffixes('.cpp', '.c') >> Relative
    pipeline = Sources >> ingest >> build >> link
