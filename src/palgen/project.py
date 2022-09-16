import toml
from dataclasses import dataclass, asdict
from pathlib import Path
from palgen.log import logger


@dataclass
class Project:
    name: str
    version: str
    description: str
    type: str
    folders: list
    tables: dict
    output: Path

    def __init__(self, config_file, out_path):
        self.root = Path(config_file).parent
        self.folders = []
        self.tables = {}

        config = toml.load(config_file)

        if "output" in config:
            if Path(config["output"]).is_absolute():
                self.output = Path(config["output"])
            else:
                self.output = self.root / config["output"]
        else:
            self.output = Path(out_path)

        # project info
        self.name = config["name"]
        self.version = config["version"]
        self.description = config["description"] if "description" in config else ""
        self.type = config["type"]

        # input folders
        if "folders" not in config:
            raise RuntimeError("Configuration invalid: Missing folders list")

        if not isinstance(config["folders"], list):
            raise RuntimeError("Configuration invalid: folders isn't a list")

        self.folders = config["folders"]

        # root path

        if "root" in config and isinstance(config["root"], str):
            self.root = self.root / config["root"]
        self.root = self.root.resolve().absolute()

        if not self.root.exists():
            raise RuntimeError(
                "Configuration invalid: root folder does not exist.")

        # tables
        for key, setting in config.items():
            if not isinstance(setting, dict):
                continue
            if "enabled" not in setting:
                setting["enabled"] = True

            self._sanitize_outpath(setting)
            self.tables[key] = setting

    def _sanitize_outpath(self, setting):
        # set default if output hasn't been overriden
        if "output" not in setting:
            setting["output"] = self.output
        else:
            if not Path(setting["output"]).is_absolute():
                setting["output"] = self.output / setting["output"]
