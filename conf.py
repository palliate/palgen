# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import sys
from pathlib import Path
from typing import Any
sys.path.append(str(Path(__file__).parent.parent / "src"))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'palgen'
copyright = '2023, Tsche'
author = 'Tsche'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [

    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx.ext.autodoc.typehints',
    'sphinx.ext.autosectionlabel',

    'autoapi.extension',

    'sphinxcontrib.jquery',
    'sphinx_git',
    'sphinx_needs',

    'sphinxcontrib.test_reports',
    'sphinxcontrib.plantuml',
    'sphinx_immaterial.graphviz',

    'sphinx_mdinclude',
    'sphinx_click'
]

templates_path = ['docs/_templates']
autoapi_template_dir = 'docs/_templates'
root_doc = "index"
exclude_patterns = ['build/*', 'venv/*', 'dist/*', '.tox/*', '*/.pytest_cache/*', '.pytest_cache/*']


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_title = "palgen"

html_sidebars = {
    '**': [
        'sidebar/brand.html',
        'sidebar/search.html',
        'sidebar/scroll-start.html',
        'sidebar/navigation.html',
        'sidebar/scroll-end.html',
        'sidebar/variant-selector.html']
}
html_static_path = ['docs/_static']
html_theme_options: dict[str, Any] = {
    "font": False,
    "footer_icons": [
        {
            "name": "GitHub",
            "url": "https://github.com/palliate/palgen",
            "html": """
                <svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 16 16">
                    <path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"></path>
                </svg>
            """,
            "class": "",
        },
    ],
    "source_repository": "https://github.com/palliate/palgen",
    "source_branch": "master",
    "source_directory": "docs/",
}

html_css_files = [
    'responsive_graphviz.css',
]

# -- Extension configuration -------------------------------------------------

napoleon_numpy_docstring = False
napoleon_include_private_with_doc = True
napoleon_include_special_with_doc = True
napoleon_use_ivar = True
napoleon_preprocess_types = True

always_document_param_types = True
typehints_use_signature = True
typehints_use_signature_return = True

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None)
}

autoapi_root = 'reference/'
autoapi_dirs = ['src/palgen']
autoapi_file_patterns = ['*.py']
autoapi_options = ['members', 'inherited-members', 'undoc-members',
                   'show-inheritance', 'show-inheritance-diagram', 'special-members']

autoapi_python_class_content = 'both'
autodoc_typehints = 'description'


tr_report_template = "docs/_templates/testreport.rst"
