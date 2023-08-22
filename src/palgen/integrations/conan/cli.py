import inspect
import logging
from pathlib import Path
import click
from conans.paths import get_conan_user_home
import shutil

@click.group()
def conan():
    ...

@conan.command()
def install_generator():
    import palgen.integrations.conan.palgen as PalgenGenerator
    generator_path = inspect.getfile(PalgenGenerator)

    conan_home = get_conan_user_home()
    output_path = Path(conan_home) / 'extensions' / 'generators' / 'palgen.py'
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logging.info("Copying generator to %s", output_path)
    shutil.copy(generator_path, output_path)
