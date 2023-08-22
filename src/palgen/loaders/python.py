import functools
import logging
import sys
import uuid
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Iterable, Optional

from ..interface import Extension
from ..ingest import Suffix
from .ast_helper import AST
from .loader import Loader, ExtensionInfo, Kind

_logger = logging.getLogger(__name__)


class Python(Loader):
    __slots__ = ('project_name',)

    def __init__(self, project_name: Optional[str] = None):
        """Loads palgen extensions from Python modules (that is, files).

        Args:
            project_name (Optional[str], optional): Project name used to give extensions
                a proper import name. Defaults to None.
        """
        self.project_name = project_name

    def ingest(self, sources: Iterable[Path]) -> Iterable[ExtensionInfo]:
        """Ingests extensions from the given sources. This skips all files not ending in '.py'.

        Args:
            sources (Iterable[Path]): An iterable of paths to input files

        Yields:
            tuple[str, Type[Extension]]: name and class of all discovered palgen extensions
        """
        files = Suffix('.py')(sources)
        for file in files:
            yield from self.load(file)

    def load(self, source: Path, import_name: Optional[str] = None) -> Iterable[ExtensionInfo]:
        """Attempt loading palgen extensions from Python module at the given path.

        Args:
            path (Path): Path to the Python module
            import_name (Optional[str], optional): Qualified name to use for the Python module. Defaults to None.

        Yields:
            tuple[str, Type[Extension]]: name and class of all discovered palgen extensions
        """
        if not Python.check_candidate(source):
            return
        module_name = import_name

        private = False
        if not module_name:
            private, module_name = self.get_module(source)

        import_name = '.'.join(["palgen.ext", module_name])
        spec = spec_from_file_location(import_name, source)

        # file is pre-checked, this assertion should never fail
        assert spec and spec.loader, "Spec could not be loaded"

        try:
            _logger.debug("Adding to sys.modules: %s", import_name)
            # TODO set parents as well

            module = module_from_spec(spec)
            sys.modules[import_name] = module
            spec.loader.exec_module(module)

        except ImportError as exc:
            import traceback
            _logger.warning("Failed loading %s. Error: %s", source, exc)

            if _logger.isEnabledFor(logging.DEBUG):
                traceback.print_exception(exc)

        else:
            for attr_name in dir(module):
                if attr_name.startswith('_'):
                    continue

                attr = getattr(module, attr_name)
                if not isinstance(attr, type) or not issubclass(attr, Extension) or attr is Extension:
                    continue

                _logger.debug("Found extension `%s` (importable from `%s`). Key `%s`",
                            attr.__name__, import_name, attr.name)

                #TODO check other ways extension could be set to private
                yield ExtensionInfo(attr, module_name, source, Kind.PRIVATE if attr.private or private else Kind.PUBLIC)

    @staticmethod
    def check_candidate(path: Path) -> bool:
        """Analyzes the AST of the Python extension at the given path without executing it.
        If the AST does not contain any valid subclasses of palgen.Extension the
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
            if not any(ast.get_subclasses(Extension)):
                return False

        except UnicodeDecodeError:
            _logger.warning("Could not decode file %s", path)
            return False

        return True

    @staticmethod
    @functools.lru_cache(maxsize=64)
    def get_parent(path: Path) -> tuple[bool, str]:
        """Gets the name of the parent package (in terms of Python's import machinery).
        The __init__.py will be analyzed without executing the Python module. If it includes
        a constant named :code:`_PRIVATE` and :code:`_PRIVATE = True` it will randomize the parent module name.
        Otherwise it will use the content of the string constant :code:`_NAME` or fall back to the
        folder's name.

        Warning:

        Args:
            path (Path): Path to the __init__.py

        Returns:
            tuple[bool, str]: Whether the package is to be considered private and its name
        """
        ast = AST.load(path)
        if ast.constants.get('_PRIVATE', False):
            return True, str(uuid.uuid4())

        return False, ast.constants.get('_NAME', path.parent.name)

    def get_module(self, path: Path) -> tuple[bool, str]:
        """Gets the qualified name for the Python module found at path.
        Falls back to a random project name (and therefore a private extension)
        if this loader hasn't been assigned a project yet.

        Args:
            path (Path): Path to a Python file.

        Returns:
            tuple[bool, str]: Whether the module is to be considered private and the qualified name of the module
        """
        module_name: list[str] = []
        private = False

        if self.project_name is not None:
            module_name.append(self.project_name)

            if (probe := path.parent / '__init__.py').exists():
                private, parent_name = Python.get_parent(probe)
                module_name.append(parent_name)

            module_name.append(path.stem)
        else:
            # no way to avoid conflicts, make this private
            module_name.append(str(uuid.uuid4()))

        return private, '.'.join(module_name)
