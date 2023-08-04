Extensions
==================================

When palgen starts up it traverses the source and extension directories (both or either one based on configuration) and looks for extensions. By default palgen will inspect all discovered Python source files and attempt to load them if they contain palgen extensions. If the setting :code:`palgen.extensions.manifest` is enabled palgen will also look for :code:`palgen.manifest` files and load all extensions listed in those files.

.. note::
   To prevent executing Python modules (that is, .py files) that cannot possibly contain a palgen extension, Python files are first statically analyzed. 

   This means palgen first looks at imports and module-level classes within that Python module's AST. If the Python module cannot be parsed as a valid Python AST, does not import :code:`palgen.ext.Extension` in any valid way or does not contain any module-level classes that inherit from :code:`palgen.ext.Extension` the Python module is skipped and not executed.

   Otherwise the Python module will be executed and all palgen extensions extracted by iterating over the Python module's attributes.

   This additional check is done to reduce the possibility of screwing up everything due to side effects of executing arbitrary Python modules. To further reduce this possibility you should disable :code:`palgen.extensions.inline` and load extensions from :code:`palgen.extensions.folders` only if your project's sources contain other Python files.


Make sure your extension class inherits from :code:`palgen.ext.Extension`. This is required for palgen to automatically detect extensions.
