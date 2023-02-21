import sys
import logging
import uuid
from importlib.util import spec_from_file_location, module_from_spec

from pathlib import Path
from palgen.loaders import Loader
from palgen.module import Module
from palgen.schemas.project import ProjectSettings

from palgen.util.filesystem import SuffixDict
from palgen.ingest import Filter

logger = logging.getLogger(__name__)

class Python(Loader):

    @staticmethod
    def ingest(project: ProjectSettings, source_tree: SuffixDict):
        files = Filter(extension='.py')(source_tree)

        for file in files:
            yield from Python.load(project, file)

    @staticmethod
    def load(project: ProjectSettings, path: Path):
        module_name = ["palgen", "ext", project.name, path.parent.stem] #str(uuid.uuid4().hex)
        if path.name == '__init__.py':
            ...
            # TODO check for private/public constant
        else:
            module_name.append(path.stem)

            # TODO precheck by inspecting AST before loading, see ast_helper.py

        name = '.'.join(module_name)
        spec = spec_from_file_location(name, path)

        # file is pre-checked, these assertions should never fail
        assert spec, "Spec could not be loaded"
        assert spec.loader, "Spec has no loader"

        module = module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)

        attrs = [getattr(module, name)
                 for name in dir(module)
                 if not name.startswith('_')]

        for attr in attrs:
            if not isinstance(attr, type):
                continue
            if not issubclass(attr, Module) or attr is Module:
                continue

            attr_name = attr.__name__.lower()
            logger.debug("Found module `%s` (importable from `%s`)", attr_name, name)
            yield attr_name, attr
