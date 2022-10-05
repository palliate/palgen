''' Conan integration. To automatically enable palgen for a conan projects
 derive the conan schema from the Conan class defined in this module'''

from pathlib import Path
from conans import ConanFile

from palgen.project import Project
from palgen.generator import Generator
from palgen.log import set_min_level


class Conan(ConanFile):
    """Wrapper around conan recipes to automatically execute palgen.

    Base:
        ConanFile: Conan recipe base class
    """

    def init(self):
        """Derives name, version and optionally description from palgen project definition.
        Also adds the palgen project configuration and all sources to export_sources.

        Remember to call this method when overriding init() or alternatively
        override _init() instead.
        """
        self.exports = "palgen.toml"
        set_min_level(2)

        folder = Path(self.recipe_folder) # pylint: disable=no-member
        project = Project(folder / "palgen.toml", only_builtin=True)
        print(project)

        self.name = project.name
        self.version = project.version
        if project.description is not None:
            self.description = project.description

        if not self.exports_sources:
            self.exports_sources = []

        self.exports_sources.extend(
            [f"{folder}/*" for folder in project.folders])
        self.exports_sources.append("palgen.toml")

        if hasattr(self, "_init"):
            self._init()

    def generate(self):
        """Runs palgen during generate step.
        Derives palgen templates from python_requires.

        Remember to call this method when overriding generate() or alternatively
        override _generate() instead.
        """

        set_min_level(0)

        if hasattr(self, "python_requires"):
            #print(self.python_requires)
            for name, item in self.python_requires.items():
                print(item.path)
                print(name)
                #pprint(item.module.__dict__)

        # in non-package builds this will refer to the git repo
        folder = Path(self.recipe_folder) # pylint: disable=no-member

        if self.source_folder:
            # this is only set in package builds
            folder = Path(self.source_folder)

        generator = Generator(folder / "palgen.toml", folder, [])
        generator.collect()
        generator.parse()

        if hasattr(self, "_generate"):
            self._generate()
