Modules
==================================

When palgen starts up it traverses the source and module directories (both or either one based on configuration) and looks for modules. By default palgen will inspect all discovered Python source files and attempt to load them if they contain palgen modules. If the setting :code:`palgen.modules.manifest` is enabled palgen will also look for :code:`palgen.manifest` files and load all modules listed in those files.

.. note::
   To prevent executing Python modules (that is, .py files) that cannot possibly contain a palgen module, Python files are first statically analyzed. 

   This means palgen first looks at imports and module-level classes within that Python module's AST. If the Python module cannot be parsed as a valid Python AST, does not import :code:`palgen.module.Module` in any valid way or does not contain any module-level classes that inherit from :code:`palgen.module.Module` the Python module is skipped and not executed.

   Otherwise the Python module will be executed and all palgen modules extracted by iterating over the Python module's attributes.

   This additional check is done to reduce the possibility of screwing up everything due to side effects of executing arbitrary Python modules. To further reduce this possibility you should disable :code:`palgen.modules.inline` and load modules from :code:`palgen.modules.folders` only if your project's sources contain other Python files.

Creating your first module
###########################

To start off create a :code:`palgen.toml` file in your project's root directory. Refer to :ref:`Quickstart` for default :code:`palgen.toml` options.

Create a Python module named :code:`hello_world.py` somewhere within the configured directories scanned for module lookup.

For now let's write a simple "hello world" command line tool. This does not use any of the pipelines.

.. literalinclude:: /examples/tutorial/modules/hello_world.py
   :language: Python
   :linenos:
       