import functools
import logging
import sys
import uuid
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Iterable, Optional

from ..ingest import Extension
from ..schemas import ProjectSettings
from ..interfaces import Module

from .ast_helper import AST
from .loader import Loader, LoaderGenerator

_logger = logging.getLogger(__name__)


class Python(Loader):
    def __init__(self, project: Optional[ProjectSettings] = None):
        """Loads palgen modules from Python modules (that is, files).

        Args:
            project (Optional[ProjectSettings], optional): Project settings used to give modules a proper import name. Defaults to None.
        """
        self.project = project

    def ingest(self, sources: Iterable[Path]) -> LoaderGenerator:
        """Ingests modules from the given sources. This skips all files not ending in '.py'.

        Args:
            sources (Iterable[Path]): An iterable of paths to input files

        Yields:
            tuple[str, Type[Module]]: name and class of all discovered palgen modules
        """
        files = Extension('.py')(sources)
        for file in files:
            yield from self.load(file)

    def load(self, path: Path, import_name: Optional[str] = None) -> LoaderGenerator:
        """Attempt loading palgen modules from Python module at the given path.

        Args:
            path (Path): Path to the Python module
            import_name (Optional[str], optional): Qualified name to use for the Python module. Defaults to None.

        Yields:
            tuple[str, Type[Module]]: name and class of all discovered palgen modules
        """
        if not Python.check_candidate(path):
            return

        name = import_name or self.get_module_name(path)
        _logger.debug("Adding to sys.modules: %s", name)

        spec = spec_from_file_location(name, path)

        # file is pre-checked, this assertion should never fail
        assert spec and spec.loader, "Spec could not be loaded"

        try:
            module = module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)

        except ImportError as exc:
            import traceback
            _logger.warning("Failed loading %s. Error: %s", path, exc)

            if _logger.isEnabledFor(logging.DEBUG):
                traceback.print_exception(exc)

        else:
            for attr_name in dir(module):
                if attr_name.startswith('_'):
                    # ignore "private" modules
                    continue

                attr = getattr(module, attr_name)
                if not isinstance(attr, type) or not issubclass(attr, Module) or attr is Module:
                    continue

                attr.module = name
                _logger.debug("Found module `%s` (importable from `%s`). Key `%s`",
                            attr.__name__, name, attr.name)

                yield attr.name, attr

    @staticmethod
    def check_candidate(path: Path) -> bool:
        """Analyzes the AST of the Python module at the given path without executing it.
        If the AST does not contain any valid subclasses of palgen.module.Module the
        Python module will not be deemed a valid candidate for further processing.

        Args:
            path (Path): Path to the file to check

        Returns:
            bool: True if the path points to a valid candidate, False otherwise.
        """
        if path.name.startswith('_') or path.suffix != '.py':
            return False

        try:
            ast = AST.load(path)
            if not any(ast.get_subclasses(Module)):
                return False

        except UnicodeDecodeError:
            _logger.warning("Could not decode file %s", path)
            return False

        return True

    @staticmethod
    @functools.lru_cache(maxsize=64)
    def get_parent_name(path: Path) -> str:
        """Gets the name of the parent module (in terms of Python's import machinery).
        The __init__.py will be analyzed without executing the Python module. If it includes
        a constant named :code:`_PUBLIC` and :code:`_PUBLIC = True` it will randomize the parent module name.
        Otherwise it will use the content of the string constant :code:`_NAME` or fall back to the
        folder's name.

        Warning:

        Args:
            path (Path): Path to the __init__.py

        Returns:
            str: Parent module name
        """
        ast = AST.load(path)
        if not ast.constants.get('_PUBLIC', False):
            return str(uuid.uuid4())

        return ast.constants.get('_NAME', path.parent.name)

    def get_module_name(self, path: Path) -> str:
        """Gets the qualified name for the Python module found at path.
        Falls back to a random project name (and therefore a private module)
        if this loader hasn't been assigned a project yet.

        Args:
            path (Path): Path to a Python file.

        Returns:
            str: qualified name of the module
        """
        module_name: list[str] = ["palgen", "ext"]

        if self.project is not None:
            module_name.append(self.project.name)

            if (probe := path.parent / '__init__.py').exists():
                module_name.append(Python.get_parent_name(probe))

            module_name.append(path.stem)
        else:
            # no way to avoid conflicts, make this private
            module_name.append(str(uuid.uuid4()))

        return '.'.join(module_name)
