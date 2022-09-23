from pathlib import Path
from conans import ConanFile

from palgen.project import Project
from palgen.generator import Generator
from palgen.log import set_min_level
set_min_level(0)

class Conan(ConanFile):
    def init(self):
        self.exports = "palgen.toml"

        folder = Path(self.recipe_folder)
        project = Project(folder / "palgen.toml", only_builtin=True)
        self.name = project.name
        self.version = project.version
        if project.description is not None:
            self.description = project.description

        if not self.exports_sources:
            self.exports_sources = []

        self.exports_sources.extend([f"{folder}/*" for folder in project.folders])
        self.exports_sources.append("palgen.toml")

    def generate(self):
        from pprint import pprint
        if hasattr(self, "python_requires"):
            print(self.python_requires)
            for name, item in self.python_requires.items():
                print(item.path)
                pprint(item.module.__dict__)

        # in non-package builds this will refer to the git repo
        folder = Path(self.recipe_folder)
        if self.source_folder:
            # this is only set in package builds
            folder = Path(self.source_folder)

        generator = Generator(folder / "palgen.toml", folder, [])
        generator.collect()
        generator.parse()
