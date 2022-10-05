import toml
from dataclasses import dataclass
from pathlib import Path

from palgen.module import Modules
from palgen.validation import Maybe, Dict

import logging
logger = logging.getLogger(__name__)


class Project:
    schema = Dict({
        'project': Dict,
        'template': Maybe(Dict)
    })

    def __init__(self, config_file, templates=[], only_builtin=False):
        settings = toml.load(config_file)
        self.root = Path(config_file).parent

        if not self.schema.check(settings):
            raise RuntimeError("Could not validate project config.")

        self.templates = Modules()
        self.tables = {}

        missing = self.load(settings)

        # lazy load templates from filesystem
        if not only_builtin:
            if 'folders' not in settings['template']:
                settings['template']['folders'] = []
            settings['template']['folders'].extend(templates)

            self.tables['template'].load_templates(self.templates)
            missing = self.load(missing)

            if len(missing) != 0:
                logger.warning("Found settings for templates %s "
                            "but those templates have not been loaded.", missing.keys())
        logger.info("Finished loading project %s.", self.name)

    def load(self, settings):
        missing = {}
        for template, setting in settings.items():
            if template in self.templates:
                try:
                    self.tables[template] = self.templates[template](
                        self.root,
                        setting)
                except:
                    logger.error("Failed to configure template `%s`", template)
                    raise SystemExit(1)

                logger.debug("Finished loading template `%s`", template)
            else:
                missing[template] = setting

        return missing

    def loaded(self):
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
        return str(self.tables['project'])
