import logging
import os
import sys
from pathlib import Path
from typing import Optional

import click

from palgen.cli.loader import CommandLoader, init_context
from palgen.cli.util import ListParam
from palgen.loaders.python import Python
from palgen.palgen import Palgen
from palgen.util.filesystem import find_backwards
from palgen.util.log import set_min_level

_logger = logging.getLogger(__name__)


@click.command(cls=CommandLoader, chain=True,
               invoke_without_command=True, context_settings={'show_default': True})
@click.option('-v', "--version", help="Show palgen version", is_flag=True)
@click.option('--debug/--no-debug', default=False)
@click.option('-j', '--jobs',
              help=f"Amount of parallel tasks to use. Defaults to {os.cpu_count()}",
              default=None, type=int)
@click.option("-c", "--config",
              help="Path to project configuration.",
              default=Path.cwd() / "palgen.toml")
@click.option("--extra-folders", default=[], type=ListParam[Path])
@click.option("--dependencies", default=None, type=Path)
@click.pass_context
def main(ctx, debug: bool, version: bool, config: Path, extra_folders: ListParam[Path], dependencies: Optional[Path], jobs: int):
    if version:
        from palgen import __version__
        print(f"palgen {__version__}")
        return
    if debug:
        # logging.getLogger(__package__).setLevel(logging.DEBUG)
        set_min_level(0)

    init_context(ctx, config)

    assert isinstance(ctx.obj, Palgen)

    # override options
    if jobs is not None:
        ctx.obj.options.jobs = jobs

    if extra_folders:
        ctx.obj.options.modules.folders.extend(extra_folders)

    if dependencies:
        ctx.obj.options.modules.dependencies = dependencies

    if ctx.invoked_subcommand is None:
        assert isinstance(ctx.obj, Palgen)

        # no subcommand - run all enabled templates
        ctx.obj.run_all()

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
    module = dict(Python(obj.project).load(module_path))
    if len(module) > 1:
        _logger.warning("Found multiple modules: %s", list(module.keys()))
        _logger.warning("Cannot run directly, aborting.")
        sys.exit(0)

    for key, value in module.items():
        generated = obj.run(value.name, obj.settings[key] if key in obj.settings else {})
        _logger.info("Generated %d files.", len(generated))


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
