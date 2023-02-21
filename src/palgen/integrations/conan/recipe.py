""" Conan integration. To automatically enable palgen for a conan projects
 derive the conan schema from the Conan class defined in this module"""

#! TODO experimental

from pathlib import Path

from conan import ConanFile

from palgen.util.log import set_min_level
from palgen.palgen import Palgen

# Some of the instance vars used are automagically coming from Conan
# ignore the relevant linting rules.
# trunk-ignore-all(pylint/E0203)
# trunk-ignore-all(pylint/W0201)


class Conan(ConanFile):
    """Wrapper around conan recipes to automatically execute palgen.

    Base:
        ConanFile: Conan recipe base class
    """

    @classmethod
    def __init_subclass__(cls, **kwargs):
        cls._wrap("init")
        cls._wrap("generate")

    @classmethod
    def _wrap(cls, name):
        if hasattr(cls, name):
            setattr(cls, f'_{name}', getattr(cls, name))

        def replacement(self):
            nonlocal name
            for fnc in [f'_palgen_{name}', f'_{name}']:
                if hasattr(self, fnc):
                    getattr(self, fnc)()

        setattr(cls, name, replacement)

    def _palgen_init(self):
        """Derives name, version and optionally description from palgen project definition.
        Also adds the palgen project configuration and all sources to export_sources.
        """
        self.exports = "palgen.toml"
        set_min_level(2)

        folder = Path(self.recipe_folder)
        loader = Palgen(folder / "palgen.toml")
        print(loader)

        self.name = loader.project.name
        self.version = loader.project.version
        if loader.project.description is not None:
            self.description = loader.project.description

        if not self.exports_sources:
            self.exports_sources = []

        self.exports_sources.extend([f"{folder}/*"
                                     for folder in loader.project.folders])
        self.exports_sources.append("palgen.toml")

    def _palgen_generate(self):
        """Runs palgen during generate step.
        Derives palgen templates from python_requires.
        """

        set_min_level(0)
        folder = Path(self.source_folder or self.recipe_folder)

        loader = Palgen(folder / "palgen.toml")

        if hasattr(self, "python_requires"):
            for name, dependency in self.python_requires.items():
                if name in loader.subprojects:
                    continue

                path = Path(dependency.path).parent / "export_source" / "palgen.toml"
                loader.subprojects[name] = Palgen(path)

        loader.run()
