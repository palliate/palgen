import logging
from pathlib import Path
from typing import Optional

import toml

from palgen.module import Modules
from palgen.validation import Dict, Maybe

logger = logging.getLogger(__name__)


class Project:
    """Project class. Holds basic information (such as name and version)
    of a project."""

    schema = Dict({"project": Dict, "template": Maybe(Dict)})

    def __init__(self,
                 config_file: str | Path,
                 templates: Optional[list] = None,
                 only_builtin: Optional[bool] = False):
        """Project constructor. Loads from config_file, verifies the schema
        and loads all necessary templates.

        Args:
            config_file (str | Path): Project configuration file
            templates (Optional[list], optional): Additional template folders.
                                                  Defaults to None.
            only_builtin (Optional[bool], optional): Only load builtin templates.
                                                     Defaults to False.

        Raises:
            RuntimeError: _description_
        """
        config_file = Path(config_file).resolve()

        settings = toml.load(config_file)
        self.root = config_file.parent

        if not self.schema.check(settings):
            raise RuntimeError("Could not validate project config.")

        self.templates = Modules()
        self.tables = {}

        missing = self.load(settings)

        # lazy load templates from filesystem
        if not only_builtin:
            if "folders" not in settings["template"]:
                settings["template"]["folders"] = []
            settings["template"]["folders"].extend(templates or [])

            for folder in self.tables["template"].settings["folders"]:
                folder = Path(folder)
                if not folder.is_absolute():
                    folder = self.root / folder

                logger.debug("Loading templates from %s", folder)
                self.templates.load(folder)

                missing = self.load(missing)

            if len(missing) != 0:
                logger.warning(
                    "Found settings for templates %s "
                    "but those templates have not been loaded.",
                    missing.keys(),
                )
        logger.info("Finished loading project %s.", self.name)

    def load(self, settings: dict) -> dict:
        """Instantiate all required templates (activate them).

        Args:
            settings (dict): Settings for the templates.

        Raises:
            SystemExit: Failure

        Returns:
            dict: Settings for not (yet) loaded templates.
        """

        missing = {}
        for template, setting in settings.items():
            if template in self.templates:
                try:
                    # default enable
                    if "enabled" not in setting:
                        setting["enabled"] = True

                    self.tables[template] = self.templates[template](self.root,
                                                                     setting)
                except Exception as exception:
                    logger.error("Failed to configure template `%s`", template)
                    raise SystemExit(1) from exception

                logger.debug("Finished loading template `%s`", template)
            else:
                missing[template] = setting

        return missing

    def loaded(self) -> list:
        """List all activated templates.

        Returns:
            list: active templates
        """
        return list(self.tables.keys())

    def __contains__(self, table):
        return table in self.tables

    def __getitem__(self, field):
        return self.tables[field]

    def __iter__(self):
        return iter(self.tables.items())

    def __getattr__(self, field):
        try:
            return self.tables["project"].settings[field]
        except KeyError:
            return None

    def __str__(self) -> str:
        return str(self.tables["project"])
