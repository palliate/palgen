import logging
from pathlib import Path

import click

from palgen.palgen import Palgen

logger = logging.getLogger(__name__)


@click.command()
@click.option("-o", "--output", help="Output path", type=Path, required=True)
@click.option("-r", "--relative", help="Output relative paths instead of absolute ones.", is_flag=True)
@click.pass_context
def cli(ctx, output: Path, relative: bool):
    assert isinstance(ctx.obj, Palgen)

    if output.is_dir():
        output /= 'palgen.manifest'
    output.parent.mkdir(exist_ok=True)

    # TODO generate sane relative paths. I don't like the current way but it's fine for now
    manifest = ctx.obj.generate_manifest(
        output.parent.absolute() if relative else None)

    with open(output, 'w', encoding="utf-8") as file:
        file.write(manifest)
    logger.info("Written manifest file %s", output)
