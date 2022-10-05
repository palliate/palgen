import importlib.util
import logging
from dataclasses import dataclass
from pathlib import Path

from palgen import templates as builtin_templates
from palgen.parser import Parser

logger = logging.getLogger(__name__)


@dataclass
class Module:
    name: str
    parser: type
    path: Path

    def __call__(self, root, settings=None):
        return self.parser(root, self.path, settings or {})


class Modules:
    def __init__(self):
        self._templates = {}

        # load builtin templates
        for path in builtin_templates.__path__:
            self.load(path)

    def load(self, path: Path | str):
        """Loads templates from the given path.

        Args:
            path (Path | str): Path to template directory
        """

        if not isinstance(path, Path):
            path = Path(path)

        if not path.is_dir():
            return

        for folder in path.iterdir():
            if not folder.is_dir():
                continue
            if folder.name in self._templates:
                logger.warning(
                    "Template %s defined more than once.", folder.name)
                continue

            temp = []
            for file in folder.glob('*.py'):
                # TODO use unique id to avoid name conflicts?
                spec = importlib.util.spec_from_file_location(
                    folder.name, file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                attrs = [getattr(module, name)
                         for name in dir(module)
                         if not name.startswith('_')]

                temp.extend([attr
                             for attr in attrs
                             if isinstance(attr, type)
                             and issubclass(attr, Parser)
                             and attr is not Parser])

            if len(temp) == 1:
                logger.debug("Found template `%s`", folder.name)
                self._templates[folder.name] = Module(folder.name,
                                                      temp[0],
                                                      folder.resolve())
            elif len(temp) > 1:
                logger.warning("More than one template defined within subdirectory: %s",
                               folder.name)

    def __getitem__(self, key):
        return self._templates[key]

    def __contains__(self, item):
        return item in self._templates

    def __iter__(self):
        return iter(self._templates.items())

    def __str__(self) -> str:
        return str(self._templates)
