import logging
import os
from pathlib import Path
from typing import Optional

import click

from palgen.palgen import Palgen
from palgen.loaders.command import CommandLoader, init_context
from palgen.util.cli import ListParam
from palgen.util.log import set_min_level

logger = logging.getLogger(__name__)


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
def cli(ctx, debug: bool, version: bool, config: Path, extra_folders: str, dependencies: Optional[Path], jobs: int):
    if version:
        from palgen import __version__
        print(f"palgen {__version__}")
        return
    if debug:
        # logging.getLogger(__package__).setLevel(logging.DEBUG)
        set_min_level(0)

    init_context(ctx, config)

    # override options
    if jobs is not None:
        ctx.obj.options.jobs = jobs

    if extra_folders:
        ctx.obj.options.modules.extra_folders = extra_folders

    if dependencies:
        ctx.obj.options.modules.dependencies = dependencies

    if ctx.invoked_subcommand is None:
        assert isinstance(ctx.obj, Palgen)

        # no subcommand - run all enabled templates
        ctx.obj.run_all()
