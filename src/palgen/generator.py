from pathlib import Path

import logging
import toml

from palgen.project import Project
logger = logging.getLogger(__name__)


class Generator:
    def __init__(self, config, out_path: str | Path = None, modules: list | None = None):
        try:
            self.project = Project(config)
        except Exception as exception:
            logger.exception("Could not parse project config. %s: %s.",
                             type(exception).__name__,
                             exception)
            raise SystemExit(1) from exception

        self.out_path = Path(out_path).resolve().absolute() \
            if out_path else self.project.root

        # TODO handle enable module overrides

        logger.info("Loaded templates: %s", self.project.loaded())
        logger.debug("Collecting from %s", self.project.folders)
        logger.debug("Root folder: %s", self.project.root)

    def collect(self):
        for folder in self.project.folders:
            projects = {}

            for project in [*Path.glob(self.project.root, folder + '/**/palgen.toml')]:
                logger.debug("Found another project at %s",
                             project.relative_to(self.project.root))

                projects[project] = Project(project, self.out_path)

            for config in [*Path.glob(self.project.root, folder + '/**/config.toml')]:
                logger.debug("Found config at %s",
                             config.relative_to(self.project.root))

                project = self.project
                for path, value in projects.items():
                    if config.is_relative_to(path):
                        project = value

                for module, attributes in toml.load(config).items():
                    if module not in self.project:
                        continue

                    if not self.project[module].ingestable:
                        logger.warning("Found data to ingest at %s but "
                                       "module %s does not expect input.",
                                       config,
                                       type(self).__name__)
                        continue

                    self.project[module].ingest(attributes, config, project)

    def parse(self):
        generated = 0
        for name, module in self.project:
            try:
                module.generate()
                logger.info("Rendering %s", name)
                module.render()
                generated += module.write(self.out_path)
            except Exception as exception:
                logger.exception("Generating failed: %s: %s",
                                 type(exception).__name__,
                                 exception)
                raise SystemExit(1) from exception

        logger.info("Generated %s files.", generated)
