import toml
import importlib
from pathlib import Path
from palgen.log import logger
from palgen.project import Project


class Generator:
    def __init__(self, config, out_path, modules):
        self.out_path = Path(out_path).resolve().absolute()
        self.modules = {}

        try:
            self.project = Project(config, out_path)
        except Exception as e:
            logger.error(
                f"Could not parse project config. {type(e).__name__}: {e}")
            raise SystemExit("Failed.")

        if len(modules) > 0:
            for module in modules:
                setting = {}
                if module in self.project.tables \
                        and isinstance(self.project.tables[module], dict):
                    setting = self.project.tables[module]

                if "enabled" in setting:
                    setting["enabled"] = True

                self._load(module, setting)
        else:
            for key, setting in self.project.tables.items():
                if not isinstance(setting, dict):
                    continue
                if "enabled" in setting and not setting["enabled"]:
                    continue

                self._load(key, setting)

        if "build" in self.modules:
            self.modules["build"].ingest(self.project, Path(config), self.project)

        logger.debug(f"Enabled modules: {list(self.modules.keys())}")
        logger.debug(f"Collecting from {self.project.folders}")
        logger.debug(f"Root folder: {self.project.root}")

    def _load(self, table, settings):
        module = importlib.import_module(
            f'palgen.tables.{table}.{table}')
        self.modules[table] = getattr(module,
                                      table.capitalize())(
            self.project.root,
            settings)

    def collect(self):
        for folder in self.project.folders:
            projects = {}

            for project in [*Path.glob(self.project.root, folder + '/**/project.toml')]:
                logger.debug(
                    f"Found another project at {project.relative_to(self.project.root)}")

                p = Project(project, self.out_path)
                projects[project] = p
                if 'build' in self.modules:
                    self.modules['build'].ingest(p, project, p)

            for config in [*Path.glob(self.project.root, folder + '/**/config.toml')]:
                logger.debug(f"Found config at {config.relative_to(self.project.root)}")

                project = self.project
                for path, value in projects.items():
                    if config.is_relative_to(path):
                        project = value

                for module, attributes in toml.load(config).items():
                    if module not in self.modules:
                        continue

                    if not self.modules[module].ingestable:
                        logger.warning(f"Found data to ingest at {config} but "
                                    f"module {type(self).__name__} does not expect input.")
                        continue

                    self.modules[module].ingest(attributes, config, project)

    def parse(self):
        for name, module in self.modules.items():
            logger.info(f"Preparing {name}")
            try:
                module.prepare()
            except Exception as e:
                logger.error(f"Preparation failed: {type(e).__name__}: {e}")
                raise SystemExit("Failed.")

            logger.info(f"Rendering {name}")
            try:
                module.render()
                module.write()
            except Exception as e:
                logger.error(f"Error occured: {type(e).__name__}: {e}")
                raise SystemExit("Failed.")
