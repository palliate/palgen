import logging
import shutil
from pathlib import Path

import click

from palgen.schemas import ProjectSettings

_logger = logging.getLogger(__name__)


@click.command()
@click.option("-o", "--outpath",
              help="Relative path to output folder",
              default=Path.cwd() / "build")
@click.option("--toolchain", help="Generate toolchain script", is_flag=True)
@click.option("--project", help="Generate project info script", is_flag=True)
@click.pass_context
def cmake(ctx, outpath, toolchain, project):
    """Generates CMake helper scripts. This is a builtin command of the CMake integration."""
    if toolchain:
        path = Path(__file__).parent / "palgen.cmake"
        out = Path(outpath) / "palgen.cmake"

        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(path, out)

        logging.info("Generated toolchain file %s", out)

    if project:
        settings: ProjectSettings = ctx.obj.project

        out = Path(outpath) / "palgen_info.cmake"
        out.parent.mkdir(parents=True, exist_ok=True)

        text = f"""
SET(TARGET "{settings.name}")
SET(TARGET_VERSION "{settings.version}")"""

        with open(out, "w", encoding="utf-8") as file:
            file.write(text)
        _logger.info("Generated project helper script %s", out)
