import logging

from palgen.ingest.filter import Name
from palgen.ingest.file import Empty

from palgen.schemas.project import ProjectSettings
from palgen.module import Module, Sources


class Project(Module):
    ingest = Sources >> Name("info.target") >> Empty
    Settings = ProjectSettings

    def validate(self, data):
        yield from data

    def render(self, data):
        print(self.settings)
        for meta, _ in data:
            outpath = meta.parent
            logging.debug("Outpath: %s", outpath)

            yield outpath / "info.h", self.get_template("info.h.in").render(
                project=self.settings.name,
                version=self.settings.version,
                description=self.settings.description
            )
