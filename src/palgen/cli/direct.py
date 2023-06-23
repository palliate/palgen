from pathlib import Path
import sys
import logging

from palgen.palgen import Palgen
from palgen.loaders.python import Python
from palgen.util.filesystem import find_backwards
from palgen.util.log import set_min_level

logger = logging.getLogger(__name__)


def run_directly(module_path: Path):
    # TODO add proper command line interface
    # TODO add options
    set_min_level(0)

    # find palgen.toml
    config = find_backwards("palgen.toml", source_dir=module_path.parent)

    obj = Palgen(config)

    # TODO investigate why running with more than one job does not work in this mode
    obj.options.jobs = 1

    # load file to inspect modules
    module = dict(Python().load(module_path, project=obj.project))
    if len(module) > 1:
        logger.warning("Found multiple modules: %s", list(module.keys()))
        logger.warning("Cannot run directly, aborting.")
        sys.exit(0)

    for key, value in module.items():
        generated = obj.run(value.name, obj.settings[key])
        logger.info("Generated %d files.", len(generated))


# This hack allows running modules directly
def check_direct_run():
    import __main__
    if not (importer := getattr(__main__, '__file__', None)):
        return

    importer = Path(importer)
    if importer.suffix == '.py' and Python.check_candidate(importer):
        # when palgen is run directly the suffix will never be '.py'
        # however if you run a module directly it'll correspond to the module's file
        # ie `python test.py` => _module = 'test.py'

        run_directly(importer)
