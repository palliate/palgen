Quickstart
==================================

.. role:: bash(code)
   :language: bash

Minimum required project settings
##################################

To be able to run palgen the project's root directory must include a file called `palgen.toml`. This file can be used to configure both palgen and provide settings for modules used in this project.

Builtin settings:

.. code-block:: toml
   :linenos:
   
   # Required
   [project]
   name        = "Foobar"       # Project name
   version     = "v0.1"         # Project version string
   description = "Bars the foo" # Project description. Optional.
   sources     = ["src"]        # List of source folders. Optional, defaults to none.
   
   # Optional. All fields of the palgen table have defaults.
   [palgen]
   output = "build" # Default output path used for modules
   jobs   = 4       # Maximum amount of parallel jobs to use. Defaults to number of virtual CPU cores.
   
   # Optional. All fields of the palgen.modules table have defaults.
   [palgen.modules]
   inline       = true           # Search for modules in the project's source folders
   inherit      = true           # Whether to inherit modules from dependencies
   folders      = ["templates"]  # Extra paths to check for modules
   dependencies = ["dependency"] # List of Paths to dependencies
   
   python   = true # Load Python modules
   manifest = true # Load modules from `palgen.manifest` files   


Schemas for these default settings can be found in the `palgen/schemas <https://github.com/palliate/palgen/tree/master/src/palgen/schemas>`_ subdirectory.


CLI
########

Palgen modules can either be run from the project's root folder or directly:


Using the palgen command
-------------------------

The :bash:`palgen` command without any arguments is used to run all enabled modules configured in the palgen.toml file.

To run a specific module (ie. named :code:`foobar`), you can use the command :bash:`palgen foobar`. This module should be defined somewhere within the project's source or module folders. To run multiple modules at once (ie :code:`foo` and :code:`bar`), you can use the compound command :bash:`palgen foo bar`.

You can also provide additional options for both the modules and palgen itself. These options will override configured settings from `palgen.toml` and can be required (if a field of the Setting schema has no default and no value is given to it in the settings file). For example:

.. code-block:: bash
   
   palgen --debug foo --zoinks=4 bar --baz "oh no"
   
This command executes palgen with debug printing enabled, runs the :code:`foo` module with the :code:`zoinks` setting set to :code:`4`, and runs the :code:`bar` module with the :code:`baz` setting set to :code:`"oh no"`.

To learn more about the available modules and their settings, you can try running :bash:`palgen --help`. If you need help specifically for a module (ie the :bash:`foo` module), you can use the command :bash:`palgen foo --help`.


Executing the module directly
-------------------------------

It is also possible to execute palgen modules directly. To do so just execute them with a Python interpreter. For example :bash:`python foobar.py` if foobar.py contains exactly one palgen module.

.. warning::
   For this to work you may only define one palgen module per Python module (that is, file).


Command line options and builtin commands
############################################

.. click:: palgen:main
   :prog: palgen
   :nested: none

.. click:: palgen.cli.commands.info:info
   :prog: palgen info
   :nested: full

.. click:: palgen.cli.commands.manifest:manifest
   :prog: palgen manifest
   :nested: full

.. click:: palgen.integrations.cmake.cli:cmake
   :prog: palgen cmake
   :nested: full
