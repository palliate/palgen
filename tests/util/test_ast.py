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

    import palgen.interfaces.module
    module, name = get_import_name(palgen.interfaces.module)
    assert module == ['palgen', 'module']
    assert name is None


def test_resolve_builtin():
    module, name = get_import_name(str)
    assert module == []
    assert name == 'str'


def test_resolve_bare():
    import palgen.interfaces.module
    module, name = get_import_name(palgen.interfaces.module.Module)
    assert module == ['palgen', 'module']
    assert name == 'Module'


def test_resolve_from():
    from palgen.interfaces.module import Module
    module_name, name = get_import_name(Module)
    assert module_name == ['palgen', 'module']
    assert name == 'Module'

    from palgen.interfaces import module
    module_name, name = get_import_name(module.Module)
    assert module_name == ['palgen', 'module']
    assert name == 'Module'


def test_resolve_alias():
    from palgen.interfaces.module import Module as templ
    module_name, name = get_import_name(templ)
    assert module_name == ['palgen', 'module']
    assert name == 'Module'

    from palgen.interfaces import module as mod
    module_name, name = get_import_name(mod.Module)
    assert module_name == ['palgen', 'module']
    assert name == 'Module'


def test_import_builtins():
    # builtins do not need to be imported
    # this must succeed even for empty files
    with mock_file(""):
        ast = AST.load(MOCK_PATH)
        #TODO

def test_import_relative():
    with mock_file("from . import foo"):
        ast = AST.load(MOCK_PATH)


@pytest.mark.parametrize('import_,symbol', [
    ('from palgen import module',             'module.Module'),
    ('from palgen.module import Module',      'Module'),
    ('from palgen import module as t',        't.Module'),
    ('from palgen.module import Module as t', 't'),
    ('import palgen',                         'palgen.module.Module'),
    ('import palgen.module',                  'palgen.module.Module'),
    ('import palgen.module as t',             't.Module'),
    ('import palgen as p',                    'p.module.Module')
])
class TestParametrized:

    def test_import(self, import_, symbol):
        from palgen.interfaces.module import Module
        ast = AST.parse(import_)

        assert len(ast.imports) == 1
        assert str(ast.imports[0]) == import_

        possible = list(ast.possible_names(Module))
        assert len(possible) == 1
        assert possible[0] == symbol

    def test_class(self, import_, symbol):
        from palgen.interfaces.module import Module
        ast = AST.parse(f"{import_}\nclass Foo({symbol}):\n  ...")
        subclasses = list(ast.get_subclasses(Module))

        assert len(subclasses) == 1
        assert symbol in subclasses[0].bases
