import toml
from dataclasses import dataclass
from pathlib import Path

from palgen.log import logger
from palgen.templates import Template, Templates
from palgen.validation import Dict

from pprint import pprint
class Project:
    schema = Dict({
        'project'  :Dict,
        'template' :Dict
    })

    def __init__(self, config_file, templates = [], only_builtin=False):
        settings = toml.load(config_file)
        self.root = Path(config_file).parent

        if not self.schema.check(settings):
            logger.error("Could not validate project config.")
            raise RuntimeError("Could not validate project config.")

        self.templates = Templates()
        self.tables = {}

        missing = self.load(settings)

        # lazy load templates from filesystem
        if not only_builtin:
            if 'folders' not in settings['template']:
                settings['template']['folders'] = []
            settings['template']['folders'].extend(templates)

            self.tables['template'].load_templates(self.templates)
            self.load(missing)

    def load(self, settings):
        missing = {}
        for template, setting in settings.items():
            logger.warning(f"template `{template}` in templates? {template in self.templates}")
            if template in self.templates:
                try:
                    self.tables[template] = self.templates[template](
                        self.root,
                        setting)
                except:
                    logger.error(f"Failed to configure template `{template}`")
                    raise SystemExit(1)

                logger.debug(f"Loaded template `{template}`")
            else:
                missing[template] = setting

        return missing

    def loaded(self):
        return self.tables.keys()

    def __contains__(self, table):
        return table in self.tables

    def __getitem__(self, field):
        return self.tables[field]

    def __getattr__(self, field):
        try:
            return self.tables["project"].settings[field]
        except KeyError:
            return None


@dataclass
class Project_old:
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
