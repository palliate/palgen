import toml
import importlib
from pathlib import Path
from palliate_codegen.log import logger


class generator:
    def __init__(self, config, out_path):
        self.whitelist = []
        self.no_cli = False
        self.out_path = Path(out_path).resolve().absolute() / "generated"
        self.modules = {}
        try:
            self._parse_config(config)
        except FileNotFoundError as e:
            logger.error(e)
            raise SystemExit(1)

    def _parse_config(self, config):
        conf = toml.load(config)
        if "folders" not in conf:
            raise RuntimeError("Configuration invalid: Missing folders list")
            return
        if not isinstance(conf["folders"], list):
            raise RuntimeError("Configuration invalid: folders isn't a list")

        self.root_path = Path(config).parent
        if "root" in conf and isinstance(conf["root"], str):
            self.root_path = self.root_path / conf["root"]
        self.root_path = self.root_path.resolve().absolute()
        self.folders = conf["folders"]

        logger.debug(f"Collecting from {self.folders}")
        logger.debug(f"Root folder: {self.root_path}")

        if "tables" in conf and isinstance(conf["tables"], list):
            self.whitelist = conf["tables"]

        # TODO figure out a better solution
        if "no_cli" in conf:
            self.no_cli = conf["no_cli"]

    def _load(self, module):
        module_m = importlib.import_module(f'palliate_codegen.tables.{module}')
        self.modules[module] = getattr(module_m, module)(
            self.root_path, self.out_path, self.no_cli)

    def collect(self):
        # accumulate paths to all config files
        configs = [Path.glob(self.root_path, folder + '/**/config.toml')
                   for folder in self.folders]
        # flatten
        configs = [item for sublist in configs for item in sublist]

        for config in configs:
            logger.debug("Found config at %s" %
                         config.relative_to(self.root_path))
            for module, attributes in toml.load(config).items():

                if self.whitelist and module not in self.whitelist:
                    logger.info(f"Skipping table {module}")
                    continue

                if module not in self.modules:
                    self._load(module)

                self.modules[module].ingest(attributes, config.parent)

        return len(configs)

    def parse(self):
        for name, module in self.modules.items():
            logger.info(f"Preparing {name}")
            try:
                module.prepare()
            except Exception as e:
                logger.error(f"Preparation failed: {e}")
                raise SystemExit("Failed.")

            logger.info(f"Rendering {name}")
            module.render()
            module.write()
