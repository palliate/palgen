import ast
from pathlib import Path
from types import ModuleType
from typing import Optional

# TODO


class Import:
    def __init__(self, name: Optional[str] = None,
                 module: Optional[list[str]] = None,
                 alias: Optional[str] = None):
        self._name = name
        self.module = module or []
        self.alias = alias

    @property
    def name(self):
        if self.alias is not None:
            return self.alias
        return self._name

    @property
    def real_name(self):
        return self._name

    def full_name(self):
        return '.'.join([*self.module, self._name])

    def __str__(self) -> str:
        ret = ""
        if self._name:
            ret += f"from {'.'.join(self.module)} import {self._name}"
        else:
            ret += f"import {'.'.join(self.module)}"

        if self.alias:
            return ret + f" as {self.alias}"
        return ret


class Class:
    def __init__(self, name, bases) -> None:
        pass


class AST:
    def __init__(self, path: Path | str, encoding='utf-8'):
        self.path = Path(path)
        self.classes: list[Class] = []
        self.imports: list[Import] = []

        with open(self.path, 'r', encoding=encoding) as file:
            self.tree = ast.parse(file.read())
        self.parse()

    def parse(self):
        for node in self.tree.body:
            match node:
                case ast.ClassDef():
                    """ClassDef(identifier name,
             expr* bases,
             keyword* keywords,
             stmt* body,
             expr* decorator_list)"""
                    pass
                    #self.classes.append(Class(name, bases))
                case ast.Import():
                    # Import(alias* names)
                    self.imports += [Import(module=name.name.split('.'),
                                            alias=name.asname)
                                     for name in node.names]

                case ast.ImportFrom():
                    # ImportFrom(identifier? module, alias* names, int? level)
                    if node.level > 0 or not node.module:
                        # skip relative imports
                        continue

                    # TODO handle wildcard imports properly

                    self.imports += [Import(name=name.name,
                                            module=node.module.split('.'),
                                            alias=name.asname)
                                     for name in node.names]

    def possible_names(self, base: type):
        module, name = get_import_name(base)
        print(f"{module=}")
        print(f"{name=}")

        if not module:
            # builtins do not need to be imported
            yield name
            return

        for import_ in self.imports:
            print(f"{import_.module=}")
            print(f"{import_.real_name=}")

            if import_.module and import_.module[0] != module[0]:
                continue

            if import_.module == module:
                print(f"{name} -- {import_.real_name}")

                if import_.real_name == name:
                    yield import_.name


    def contains_subclass(self, base: type, count: int | None = None):
        module = base.__module__ if base.__module__ != 'builtin' else None
        name = base.__qualname__

        # skip import checking for builtins
        has_import: bool = not module

        for node in self.tree.body:
            match node:
                case ast.Import() if has_import:
                    ...
                case ast.ImportFrom() if has_import:
                    ...


def get_import_name(import_: type | ModuleType) -> tuple[list[str], Optional[str]]:
    #TODO use __qualname__ (dotted full name)
    if isinstance(import_, type):
        if import_.__module__ == 'builtins':
            return [], import_.__name__

        return import_.__module__.split('.'), import_.__name__

    if isinstance(import_, ModuleType):
        return import_.__name__.split('.'), None

    raise TypeError("Only module and class imports are supported")
