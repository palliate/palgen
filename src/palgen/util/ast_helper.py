import ast
import logging
from functools import singledispatchmethod
from pathlib import Path
from types import ModuleType
from typing import Any, Optional

logger = logging.getLogger(__name__)


class Import:
    def __init__(self, name: Optional[str] = None,
                 module: Optional[list[str]] = None,
                 alias: Optional[str] = None):
        self._name = name
        self.module = module or []
        self.alias = alias

    @property
    def name(self):
        return self.alias or self._name

    @property
    def real_name(self):
        return self._name

    def full_name(self):
        if self._name is None:
            return '.'.join(self.module)

        return '.'.join([*self.module, self._name])

    def __str__(self) -> str:
        ret = ""
        if self._name:
            ret += f"from {'.'.join(self.module)} import {self._name}"
        else:
            ret += f"import {'.'.join(self.module)}"

        return f"{ret} as {self.alias}" if self.alias else ret


class Class:
    def __init__(self):
        self.name: str = ""
        self.bases: list[str] = []

    @singledispatchmethod
    def visit(self, node: ast.AST):
        pass

    @visit.register
    def _(self, node: ast.ClassDef):
        '''
        ClassDef(identifier name,
             expr* bases,
             keyword* keywords,
             stmt* body,
             expr* decorator_list)
        '''
        self.name = node.name

        for base in node.bases:
            self.bases.append(self.visit(base))

        return self

    @visit.register
    def _(self, node: ast.Attribute):
        '''
            Attribute(expr value, identifier attr, expr_context ctx)
        '''
        return '.'.join([self.visit(node.value), node.attr])

    @visit.register
    def _(self, node: ast.Name):
        '''
            Name(identifier id, expr_context ctx)
        '''
        return node.id


def get_import_name(import_: type | ModuleType) -> tuple[list[str], Optional[str]]:
    # TODO use __qualname__ (dotted full name)
    if isinstance(import_, type):
        if import_.__module__ == 'builtins':
            return [], import_.__name__

        return import_.__module__.split('.'), import_.__name__

    if isinstance(import_, ModuleType):
        return import_.__name__.split('.'), None

    raise TypeError("Only module and class imports are supported")


class AST:
    """AST parsing utility
    Extracts:
        - constants
        - imports
        - import aliases
        - classes
    """

    def __init__(self, tree: ast.Module):
        """Module level AST parsing utility.
        Will visit the AST and extract information automatically.

        Unsupported but legal tree types:
            - ast.Interactive
            - ast.Expression
            - ast.FunctionType

        Args:
            tree (ast.Module): Module to inspect
        """
        assert isinstance(tree, ast.Module), "Tree is not of type ast.Module"

        self.tree = tree

        self.constants: dict[str, Any] = {}
        self.imports: list[Import] = []
        self.classes: list[Class] = []

        self.visit(self.tree)

    @classmethod
    def parse(cls, text: str) -> 'AST':
        """Parse AST from string

        Args:
            text (str): String containing valid Python code.

        Returns:
            AST: parsed AST
        """
        return cls(ast.parse(text))

    @classmethod
    def load(cls, path: Path | str, encoding='utf-8') -> 'AST':
        """Parse AST from file

        Args:
            path (Path | str): Path to file
            encoding (str, optional): Encoding to use. Defaults to 'utf-8'.

        Returns:
            AST: parsed AST
        """
        with open(path, 'r', encoding=encoding) as input_file:
            return cls.parse(input_file.read())

    @singledispatchmethod
    def visit(self, node: ast.AST) -> None:
        ''' Generic node visitor '''

        if not isinstance(node, ast.AST):
            raise NotImplementedError

        # do nothing with unrecognized nodes

    @visit.register
    def _(self, node: ast.Module):
        ''' Module(stmt* body, type_ignore* type_ignores) '''

        for child_node in node.body:
            self.visit(child_node)

    def try_constant(self, target: ast.expr, value: ast.expr):
        # `expr` can refer to a bunch of things that we cannot evaluate without executing
        # => filter aggressively

        if not isinstance(target, ast.Name):
            # Other common possible types include:
            #   - ast.Tuple:
            #       assignments of the form `a, b = False, 7`
            #       possible to implement by matching Tuple.elts to value Tuple.elts
            #   - ast.List:
            #       assignments of the form `[a, b] = 1, 2`
            #   - ast.Starred:
            #       assignments of the form `*a = foo`

            return  # ? implement

        if not isinstance(value, ast.Constant):
            # only care about constant rhs
            # refer to https://docs.python.org/3/library/ast.html#ast.Constant
            # > The values represented can be simple types such as a number, string or None,
            # > but also immutable container types (tuples and frozensets)
            # > if all of their elements are constant.

            # Note that number type as used here does include complex literals (ie `2j`)
            # but not expressions such as `4 + 2j`
            # `...` is included, however `Ellipsis` is not

            # ? constant arithmetic expressions could be computed without otherwise evaluating
            return

        self.constants[target.id] = value.value

    @visit.register
    def visit_assign(self, node: ast.Assign):
        ''' Assign(expr* targets, expr value, string? type_comment) '''
        # ignore type_comment, deduce type from value instead

        if len(node.targets) > 1:
            # assignments of the form `a = b = 42`

            # difficult to parse if at least one target is a tuple, ie
            # `foo, *bar = foobar = 1, 2, 3, 4`

            return  # ? implement

        self.try_constant(node.targets[0], node.value)

    @visit.register
    def visit_assign_annotated(self, node: ast.AnnAssign):
        ''' AnnAssign(expr target, expr annotation, expr? value, int simple) '''
        # ignore annotation, deduce type from value instead

        if node.value is None:
            # ignore statements such as `foo: bool`
            return

        self.try_constant(node.target, node.value)

    @visit.register
    def _(self, node: ast.Import):
        ''' Import(alias* names) '''
        for name in node.names:
            self.imports.append(Import(module=name.name.split('.'),
                                       alias=name.asname))

    @visit.register
    def _(self, node: ast.ImportFrom):
        ''' ImportFrom(identifier? module, alias* names, int? level) '''
        for name in node.names:
            self.imports.append(Import(name=name.name,
                                       module=node.module.split(
                                           '.') if node.module else None,
                                       alias=name.asname))

    @visit.register
    def _(self, node: ast.ClassDef):
        '''
        ClassDef(identifier name,
             expr* bases,
             keyword* keywords,
             stmt* body,
             expr* decorator_list)
        '''
        self.classes.append(Class().visit(node))

    def possible_names(self, base: type):
        ''' yields all possible symbols referring to the target type '''
        module, name = get_import_name(base)
        assert name, f"Target has no name {base}"

        if not module:
            # builtins do not need to be imported
            yield name
            return

        for import_ in self.imports:
            assert import_.module, f"Import has no module: {str(import_)}"
            for idx, (import_part, search_part) in enumerate(zip(import_.module, module)):
                if import_part != search_part:
                    break
            else:
                idx += 1
                if idx != len(import_.module):
                    continue

                remainder = module[idx:]

                if import_.real_name:
                    if remainder and remainder[0] == import_.real_name:
                        # from foo import module
                        del remainder[0]
                elif not import_.alias:
                    # no name means module import => prepend module if not aliased
                    remainder = import_.module + remainder

                if import_.real_name != name:
                    # from foo import class
                    remainder.append(name)

                if not import_.name:
                    yield '.'.join(remainder)
                else:
                    yield '.'.join([import_.name, *remainder])

    def get_subclasses(self, base: type):
        names = list(self.possible_names(base))

        for class_ in self.classes:
            for name in names:
                if name not in class_.bases:
                    continue

                yield class_
