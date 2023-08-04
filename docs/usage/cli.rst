Command Line Interface
==================================

Palgen extensions can either be run from the project's root folder or directly:


Using the palgen command
############################################

By default, running the :code:`palgen` command without any arguments executes all enabled extensions configured in the :code:`palgen.toml` file.

Running a specific extension
-----------------------------

To run a specific extension, for instance, one named :code:`foobar`, you can use the command :bash:`palgen foobar`. The extension should be defined somewhere within the project's source or extension folders. To run multiple extensions at once, for example, :code:`foo` and :code:`bar`, you can use the compound command :bash:`palgen foo bar`.

Providing additional options
-----------------------------

You can also provide additional options for both the extension and palgen itself. These options will override configured settings from `palgen.toml` and can be required if a field of the Setting schema has no default and no value is given to it in the settings file. For example:

.. code-block:: bash
   
   palgen --debug foo --zoinks=4 bar --baz "oh no"
   
This command executes palgen with debug printing enabled, runs the :code:`foo` extension with the :code:`zoinks` setting set to :code:`4`, and runs the :code:`bar` extension with the :code:`baz` setting set to :code:`"oh no"`.

Getting help
------------------

To learn more about the available extensions and their settings, you can try running :bash:`palgen --help`. If you need help specifically for an extension (ie the :bash:`foo` extension), you can use the command :bash:`palgen foo --help`.


Executing the module directly
############################################

It is also possible to execute palgen extensions directly using a Python interpreter. For example, you can execute :bash:`python foobar.py` if :code:`foobar.py` contains exactly one palgen extension.

.. warning::
   For this to work, ensure that you define only one palgen extension per Python module (that is, file).


Command line options and builtin commands
############################################

.. click:: palgen:main
   :prog: palgen
   :nested: none

.. click:: palgen.application.commands.info:info
   :prog: palgen info
   :nested: full

.. click:: palgen.application.commands.manifest:manifest
   :prog: palgen manifest
   :nested: full

.. click:: palgen.integrations.cmake.cli:cmake
   :prog: palgen cmake
   :nested: full
