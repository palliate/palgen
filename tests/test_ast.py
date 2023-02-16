# pylint: disable=import-outside-toplevel

from unittest.mock import mock_open, patch

import pytest

from palgen.util.ast_helper import AST, get_import_name

MOCK_PATH = '/tmp/path.py'


def mock_file(content=""):
    return patch("builtins.open", mock_open(read_data=content))

def test_resolve_module():
    import palgen
    module, name = get_import_name(palgen)
    assert module == ['palgen']
    assert name is None

    import palgen.module
    module, name = get_import_name(palgen.module)
    assert module == ['palgen', 'module']
    assert name is None

def test_resolve_builtin():
    module, name = get_import_name(str)
    assert module == []
    assert name == 'str'


def test_resolve_bare():
    import palgen.module
    module, name = get_import_name(palgen.module.Module)
    assert module == ['palgen', 'module']
    assert name == 'Module'


def test_resolve_from():
    from palgen.module import Module
    module, name = get_import_name(Module)
    assert module == ['palgen', 'module']
    assert name == 'Module'

    from palgen import module
    module, name = get_import_name(module.Module)
    assert module == ['palgen', 'module']
    assert name == 'Module'


def test_resolve_alias():
    from palgen.module import Module as templ
    module, name = get_import_name(templ)
    assert module == ['palgen', 'module']
    assert name == 'Module'

    from palgen import module as module
    module, name = get_import_name(module.Module)
    assert module == ['palgen', 'module']
    assert name == 'Module'


def test_import_builtins():
    # builtins do not need to be imported
    # this must succeed even for empty files
    with mock_file(""):
        ast = AST(MOCK_PATH)
        #ast.has_import(str)
        #TODO
        assert True


@pytest.mark.parametrize('content', [
    'from palgen.module import Module',
    'from palgen import Module',
    'import palgen',
    'from palgen.module import Module as templ',
])
def test_import(content):
    from palgen.module import Module
    with mock_file(content):
        ast = AST(MOCK_PATH)
        #TODO
        for possible in ast.possible_names(Module):
            print(f"{possible=}")
        assert True


if __name__ == '__main__':
    for c in ['from palgen.module import Module',
    'from palgen import Module',
    'from palgen import *',
    'from palgen.module import Module as templ',
    'import palgen.module',
    'import palgen.module as t',
    'import palgen as p'
    ]:
        print()
        print(c)
        test_import(c)