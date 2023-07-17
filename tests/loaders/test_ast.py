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

    import palgen.ext
    module, name = get_import_name(palgen.ext)
    assert module == ['palgen', 'ext']
    assert name is None


def test_resolve_builtin():
    module, name = get_import_name(str)
    assert module == []
    assert name == 'str'


def test_resolve_bare():
    import palgen.ext
    module, name = get_import_name(palgen.ext.Extension)
    assert module == ['palgen', 'ext']
    assert name == 'Extension'


def test_resolve_from():
    from palgen.ext import Extension
    module_name, name = get_import_name(Extension)
    assert module_name == ['palgen', 'ext']
    assert name == 'Extension'

    from palgen import ext
    module_name, name = get_import_name(ext.Extension)
    assert module_name == ['palgen', 'ext']
    assert name == 'Extension'


def test_resolve_alias():
    from palgen.ext import Extension as templ
    module_name, name = get_import_name(templ)
    assert module_name == ['palgen', 'ext']
    assert name == 'Extension'

    from palgen import ext as mod
    module_name, name = get_import_name(mod.Extension)
    assert module_name == ['palgen', 'ext']
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


@pytest.mark.parametrize('import_,symbol', [
    ('from palgen import ext',                 'ext.Extension'),
    ('from palgen import ext as alias',        'alias.Extension'),
    ('from palgen.ext import Extension',          'Extension'),
    ('from palgen.ext import Extension as alias', 'alias'),
    ('import palgen',                          'palgen.ext.Extension'),
    ('import palgen as alias',                 'alias.ext.Extension'),
    ('import palgen.ext',                      'palgen.ext.Extension'),
    ('import palgen.ext as alias',             'alias.Extension')

])
class TestParametrized:

    def test_import(self, import_, symbol):
        from palgen.ext import Extension
        ast = AST.parse(import_)

        assert len(ast.imports) == 1
        assert str(ast.imports[0]) == import_

        possible = list(ast.possible_names(Extension))
        assert len(possible) == 1
        assert possible[0] == symbol

    def test_class(self, import_, symbol):
        from palgen.ext import Extension
        ast = AST.parse(f"{import_}\nclass Foo({symbol}):\n  ...")
        subclasses = list(ast.get_subclasses(Extension))

        assert len(subclasses) == 1
        assert symbol in subclasses[0].bases
