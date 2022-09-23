import toml
import importlib
from pathlib import Path
from palgen.log import logger
from palgen.project import Project

from typing import Optional

import importlib.util


class Generator:
    def __init__(self, config, out_path: str | Path = None, modules: Optional[list] = None):
        try:
            self.project = Project(config)
        except Exception as e:
            logger.error(
                f"Could not parse project config. {type(e).__name__}: {e}")
            raise SystemExit(1)

        if not out_path:
            self.out_path = self.project.root
        else:
            self.out_path = Path(out_path).resolve().absolute()

        # TODO handle enable module overrides

        logger.info(f"Loaded templates: {list(self.project.loaded())}")
        logger.debug(f"Collecting from {self.project.folders}")
        logger.debug(f"Root folder: {self.project.root}")

    def collect(self):
        for folder in self.project.folders:
            projects = {}

            for project in [*Path.glob(self.project.root, folder + '/**/palgen.toml')]:
                logger.debug(
                    f"Found another project at {project.relative_to(self.project.root)}")

                p = Project(project, self.out_path)
                projects[project] = p
                # TODO

            for config in [*Path.glob(self.project.root, folder + '/**/config.toml')]:
                logger.debug(
                    f"Found config at {config.relative_to(self.project.root)}")

                project = self.project
                for path, value in projects.items():
                    if config.is_relative_to(path):
                        project = value

                for module, attributes in toml.load(config).items():
                    if module not in self.project:
                        continue

                    if not self.project[module].ingestable:
                        logger.warning(f"Found data to ingest at {config} but "
                                       f"module {type(self).__name__} does not expect input.")
                        continue

                    self.project[module].ingest(attributes, config, project)

    def parse(self):
        generated = 0
        return
        for name, module in self.project.tables.items():
            logger.info(f"Preparing {name}")

            try:
                print(module.__dict__)
                module.prepare()
            except Exception as e:
                logger.error(f"Preparation failed: {type(e).__name__}: {e}")
                raise SystemExit(1)

            logger.info(f"Rendering {name}")

            try:
                module.render()
                generated += module.write()
            except Exception as e:
                logger.error(f"Error occured: {type(e).__name__}: {e}")
                raise SystemExit(1)

        logger.info(f"Generated {generated} files.")
