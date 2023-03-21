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
from palgen.util.ast_helper import AST

logger = logging.getLogger(__name__)


class Python(Loader):

    @staticmethod
    def ingest(project: ProjectSettings, source_tree: SuffixDict):
        files = Filter(extension='.py')(source_tree)

        for file in files:
            yield from Python.load(project, file)

    @staticmethod
    def load(project: ProjectSettings, path: Path):
        ast = AST.load(path)
        module_name = ["palgen", "ext", project.name]

        # TODO
        if path.name == '__init__.py':
            module_name.append(ast.constants.get('_NAME', path.parent.name))
            if not ast.constants.get('_PUBLIC', False):
                module_name.append(str(uuid.uuid4()))
        else:
            if path.name.startswith('_'):
                return

            if (probe := path.parent / '__init__.py').exists():
                # TODO cache this
                init_ast = AST.load(probe)
                if not init_ast.constants.get('_PUBLIC', False):
                    module_name.append(str(uuid.uuid4()))
                module_name.append(init_ast.constants.get(
                    '_NAME', path.parent.name))

            module_name.append(path.stem)

        if not any(ast.get_subclasses(Module)):
            logger.debug("%s does not contain Module subclasses", path)

        name = '.'.join(module_name)
        logging.info("Adding to sys.modules: %s", name)
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
            logger.debug(
                "Found module `%s` (importable from `%s`)", attr_name, name)
            yield attr_name, attr
