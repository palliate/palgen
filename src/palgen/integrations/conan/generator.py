import logging
from pathlib import Path

import toml
from conan import ConanFile
from conan.tools.files import save
from palgen.loaders import ManifestSchema
from palgen import Palgen
from palgen.schemas.palgen import PalgenSettings

def generate_manifest(conan_file: ConanFile):
    amalgamated: dict[str, str] = {}
    for dependency in conan_file.dependencies.host.values():
        package_folder = Path(dependency.package_folder).resolve()
        if (probe := package_folder / 'palgen.manifest').exists():
            logging.debug("Found manifest at %s", probe)
            file = toml.load(probe)
            manifest = ManifestSchema.model_validate(file)

            for name, path_str in manifest.items():
                if name in amalgamated:
                    logging.warning("Duplicate extension `%s`. Skipping.", name)
                    continue

                path = Path(path_str)
                if not path.is_absolute():
                    path = package_folder / path

                amalgamated[name] = str(path)

    assert conan_file.build_folder is not None

    cache_path = Path(conan_file.build_folder) / "palgen.cache"
    cache_path.write_text(toml.dumps(amalgamated))

    if not (config_file := conan_file.source_path / 'palgen.toml').exists():
        logging.warning('No palgen config found. Did you forget to add "palgen.toml" to exports_sources?')

    settings = PalgenSettings()
    settings.extensions.dependencies = [cache_path]
    palgen = Palgen(config_file, settings)

    manifest_path = Path(conan_file.build_folder) / "palgen.manifest"
    manifest_path.write_text(palgen.extensions.manifest())
    logging.info("Written build manifest.")
