import importlib.util
from pathlib import Path
from dataclasses import dataclass

from palgen.log import logger
from palgen.parser import Parser

@dataclass
class Template:
    name    :str
    parser  :type
    path    :Path

    def __call__(self, root, settings = {}):
        return self.parser(root, self.path, settings)

class Templates:
    def __init__(self):
        self._templates = {}

        # load builtin templates
        from palgen import tables
        for path in tables.__path__:
            self.load(path)

    def load(self, path):
        if not isinstance(path, Path):
            path = Path(path)

        if not path.is_dir():
            return

        for folder in path.iterdir():
            if not folder.is_dir():
                continue
            if folder.name in self._templates:
                logger.warning(
                    f"Template {folder.name} defined more than once.")
                continue

            temp = []
            for file in folder.glob('*.py'):
                #TODO use unique id to avoid name conflicts?
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
                logger.debug(f"Found template {folder.name}")
                self._templates[folder.name] = Template(folder.name, temp[0], folder.resolve())
            elif len(temp) > 1:
                logger.warning(f"More than one template defined"
                               " within subdirectory: {folder.name}")

    def __getitem__(self, key):
        return self._templates[key]

    def __contains__(self, item):
        return item in self._templates

    def __iter__(self):
        return iter(self._templates.items())
