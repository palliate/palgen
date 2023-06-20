import sys
import logging
import uuid
from importlib.util import spec_from_file_location, module_from_spec
from typing import Iterable, Optional

from pathlib import Path
from palgen.loaders import Loader
from palgen.module import Module
from palgen.schemas.project import ProjectSettings

from palgen.ingest.filter import Extension
from palgen.util.ast_helper import AST

logger = logging.getLogger(__name__)


class Python(Loader):

    @staticmethod
    def ingest(sources: Iterable[Path], project: Optional[ProjectSettings] = None):
        files = Extension('.py')(sources)
        for file in files:
            yield from Python.load(file, project=project)

    @staticmethod
    def parse_init(path: Path, module_name: list[str]):
        #TODO cache this
        ast = AST.load(path)
        module_name.append(ast.constants.get('_NAME', path.parent.name))
        if not ast.constants.get('_PUBLIC', False):
            module_name.append(str(uuid.uuid4()))
        return module_name

    @staticmethod
    def load(path: Path, project: Optional[ProjectSettings] = None, import_name: Optional[str] = None):
        if project is not None and import_name is not None:
            raise RuntimeError("expected project or import_name, not both.")

        if path.name.startswith('_'):
            # TODO figure out if we need to load __init__.py
            return

        try:
            ast = AST.load(path)
            if not any(ast.get_subclasses(Module)):
                return
        except UnicodeDecodeError:
            return

        module_name: list[str] = ["palgen", "ext"]
        if project is not None:
            module_name.append(project.name)

            if (probe := path.parent / '__init__.py').exists():
                module_name = Python.parse_init(probe, module_name)

            module_name.append(path.stem)

        elif import_name is not None:
            module_name.extend(import_name.split('.'))

        else:
            # no way to avoid conflicts, make this private
            module_name.append(str(uuid.uuid4()))


        name = '.'.join(module_name)
        logger.debug("Adding to sys.modules: %s", name)
        spec = spec_from_file_location(name, path)

        # file is pre-checked, these assertions should never fail
        assert spec, "Spec could not be loaded"
        assert spec.loader, "Spec has no loader"
        try:
            module = module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
        except ImportError as exc:
            import traceback
            logging.warning("Failed loading %s. Error: %s", path, exc)

            if logger.isEnabledFor(logging.DEBUG):
                traceback.print_exception(exc)

        else:
            attrs = [getattr(module, attr_name)
                    for attr_name in dir(module)
                    if not attr_name.startswith('_')]

            for attr in attrs:
                if not isinstance(attr, type):
                    continue
                if not issubclass(attr, Module) or attr is Module:
                    continue

                attr.module = '.'.join(module_name[2:])
                logger.info("Found module `%s` (importable from `%s`). Key `%s`",
                            attr.__name__, name, attr.name)

                yield attr.name, attr
