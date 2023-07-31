import logging
from pathlib import Path

import click

from ...palgen import Palgen

_logger = logging.getLogger(__name__)


@click.command()
@click.option("-o", "--output", help="Output path", type=Path, required=True)
@click.option("-r", "--relative", help="Output relative paths instead of absolute ones.", is_flag=True)
@click.pass_context
def manifest(ctx, output: Path, relative: bool):
    """Generate palgen.manifest for the current project. This is a builtin command.
    """

    assert isinstance(ctx.obj, Palgen)

    if output.is_dir():
        output /= 'palgen.manifest'
    output.parent.mkdir(exist_ok=True)

    generated = ctx.obj.extensions.manifest(output.parent.absolute()
                                            if relative else None)

    with open(output, 'w', encoding="utf-8") as file:
        file.write(generated)
    _logger.info("Written manifest file %s", output)
