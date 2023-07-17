import logging

from palgen.ext import Extension, Sources
from palgen.ingest import Name, Empty, Relative
from palgen.schemas import ProjectSettings
from palgen.integrations.jinja2 import Template

class Project(Extension):
    ingest = Sources >> Name("info.target") >> Relative >> Empty
    Settings = ProjectSettings

    def validate(self, data):
        yield from data

    def render(self, data):
        assert isinstance(self.settings, Project.Settings)

        for meta, _ in data:
            outpath = self.out_path / meta.parent
            logging.debug("Outpath: %s", outpath)

            yield outpath / "info.h", Template("info.h.in")(
                project=self.settings.name,
                version=self.settings.version,
                description=self.settings.description
            )
