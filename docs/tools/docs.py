import logging
from pathlib import Path
from sphinx.cmd.build import build_main

from palgen import Extension


class Docs(Extension):
    """ Build documentation using sphinx.
    This is internal to palgen, you can find its implementation in docs/modules
    """
    ingest = None

    def run(self, _: list, jobs: int=1):
        out_path = Path(self.out_path / 'html')
        args: list[str] = ['-b', 'html', '.', str(out_path)]
        logging.info("Sphinx build returned %d", build_main(args))

        output = list(out_path.rglob('*'))

        logging.info("Sphinx yielded %d files", len(output))
        return output
