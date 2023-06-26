import logging
from pathlib import Path

import toml
from conans.model.dependencies import ConanFileDependencies

from palgen.loaders import ManifestSchema


def dependency_manifest(dependencies: ConanFileDependencies, output: Path | str):
    amalgamated: dict[str, str] = {}
    for flags, dependency in dependencies.host.items():
        # print(flags.visible) TODO only pass dependencies with visible set to True downstream

        package_folder = Path(dependency.package_folder).resolve()
        if (probe := package_folder / 'palgen.manifest').exists():
            logging.debug("Found manifest at %s", probe)
            file = toml.load(probe)
            manifest = ManifestSchema.parse_obj(file)

            for name, path_str in manifest.items():
                if name in amalgamated:
                    logging.warning("Duplicate module `%s`. Skipping.", name)
                    continue

                path = Path(path_str)
                if not path.is_absolute():
                    path = package_folder / path

                amalgamated[name] = str(path)

    if isinstance(output, str):
        output = Path(output)

    if output.is_dir():
        output /= 'palgen.cache'

    with open(output, 'w', encoding='UTF-8') as out_file:
        out_file.write(toml.dumps(amalgamated))

    logging.info("Written build manifest to %s", output)
