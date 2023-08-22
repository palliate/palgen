# pylint: disable=import-outside-toplevel

from unittest.mock import mock_open, patch

import pytest

from palgen.loaders.ast_helper import AST, get_import_name

MOCK_PATH = '/tmp/path.py'


def mock_file(content=""):
    return patch("builtins.open", mock_open(read_data=content))


def test_resolve_module():
    import palgen
    module, name = get_import_name(palgen)
    assert module == ['palgen']
    assert name is None

    import palgen.interface
    module, name = get_import_name(palgen.interface)
    assert module == ['palgen', 'interface']
    assert name is None


def test_resolve_builtin():
    module, name = get_import_name(str)
    assert module == []
    assert name == 'str'


def test_resolve_bare():
    import palgen.interface
    module, name = get_import_name(palgen.interface.Extension)
    assert module == ['palgen', 'interface']
    assert name == 'Extension'


def test_resolve_from():
    from palgen.interface import Extension
    module_name, name = get_import_name(Extension)
    assert module_name == ['palgen', 'interface']
    assert name == 'Extension'

    from palgen import interface
    module_name, name = get_import_name(interface.Extension)
    assert module_name == ['palgen', 'interface']
    assert name == 'Extension'


def test_resolve_alias():
    from palgen.interface import Extension as templ
    module_name, name = get_import_name(templ)
    assert module_name == ['palgen', 'interface']
    assert name == 'Extension'

    from palgen import interface as mod
    module_name, name = get_import_name(mod.Extension)
    assert module_name == ['palgen', 'interface']
    assert name == 'Extension'


def test_import_builtins():
    # builtins do not need to be imported
    # this must succeed even for empty files
    with mock_file(""):
        ast = AST.load(MOCK_PATH)
        possible = list(ast.possible_names(str))
        assert len(possible) == 1
        assert possible[0] == "str"

def test_import_relative():
    with mock_file("from . import foo"):
        ast = AST.load(MOCK_PATH)


@pytest.mark.parametrize('import_,symbols', [
    ('from palgen import interface',                 ['interface.Extension']),
    ('from palgen import interface as alias',        ['alias.Extension']),
    ('from palgen.interface import Extension',          ['Extension']),
    ('from palgen.interface import Extension as alias', ['alias']),
    ('import palgen',                          ['palgen.interface.Extension', 'palgen.Extension']),
    ('import palgen as alias',                 ['alias.interface.Extension', 'alias.Extension']),
    ('import palgen.interface',                      ['palgen.interface.Extension']),
    ('import palgen.interface as alias',             ['alias.Extension'])

])
class TestParametrized:

    def test_import(self, import_, symbols):
        from palgen.interface import Extension
        ast = AST.parse(import_)

        assert len(ast.imports) == 1
        assert str(ast.imports[0]) == import_

        possible = list(ast.possible_names(Extension))
        assert len(possible) == len(symbols)
        for symbol in symbols:
            assert symbol in possible

    def test_class(self, import_, symbols):
        from palgen.interface import Extension
        code = f"{import_}\n"
        for symbol in symbols:
            code += f"class Foo({symbol}):\n  ...\n"

        ast = AST.parse(code)

        subclasses = list(ast.get_subclasses(Extension))

        assert len(subclasses) == len(symbols)
        for subclass in subclasses:
            assert any(symbol in subclass.bases for symbol in symbols)
