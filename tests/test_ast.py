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
    assert module == 'palgen'
    assert name is None

    import palgen.template
    module, name = get_import_name(palgen.template)
    assert module == 'palgen.template'
    assert name is None

def test_resolve_builtin():
    module, name = get_import_name(str)
    assert module is None
    assert name == 'str'


def test_resolve_bare():
    import palgen.template
    module, name = get_import_name(palgen.template.Template)
    assert module == 'palgen.template'
    assert name == 'Template'


def test_resolve_from():
    from palgen.template import Template
    module, name = get_import_name(Template)
    assert module == 'palgen.template'
    assert name == 'Template'

    from palgen import template
    module, name = get_import_name(template.Template)
    assert module == 'palgen.template'
    assert name == 'Template'


def test_resolve_alias():
    from palgen.template import Template as templ
    module, name = get_import_name(templ)
    assert module == 'palgen.template'
    assert name == 'Template'

    from palgen import template as module
    module, name = get_import_name(module.Template)
    assert module == 'palgen.template'
    assert name == 'Template'


def test_import_builtins():
    # builtins do not need to be imported
    # this must succeed even for empty files
    with mock_file(""):
        ast = AST(MOCK_PATH)
        #ast.has_import(str)
        #TODO
        assert True


@pytest.mark.parametrize('content', [
    'from palgen.template import Template',
    'from palgen import template',
    'import palgen',
    'from palgen.template import Template as templ',
])
def test_import(content):
    from palgen.template import Template
    with mock_file(content):
        ast = AST(MOCK_PATH)
        #TODO
        for possible in ast.possible_names(Template):
            print(f"{possible=}")
        assert True


if __name__ == '__main__':
    for c in ['from palgen.template import Template',
    'from palgen import template',
    'from palgen import *',
    'from palgen.template import Template as templ',
    'import palgen.template',
    'import palgen.template as t',
    'import palgen as p'
    ]:
        print()
        print(c)
        test_import(c)
