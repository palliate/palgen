Quickstart
==================================

.. role:: bash(code)
   :language: bash

Minimum required project settings
##################################

To be able to run palgen the project's root directory must include a file called `palgen.toml`. This file can be used to configure both palgen and provide settings for extensions used in this project.

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
   output = "build" # Default output path
   jobs   = 4       # Maximum amount of parallel jobs to use. Defaults to number of virtual CPU cores.
   
   # Optional. All fields of the palgen.extensions table have defaults.
   [palgen.extensions]
   inline       = true           # Search for extensions in the project's source folders
   inherit      = true           # Whether to inherit extensions from dependencies
   folders      = ["templates"]  # Extra paths to check for extensions
   dependencies = ["dependency"] # List of Paths to dependencies
   
   python   = true # Load extensions from Python modules
   manifest = true # Load extensions from `palgen.manifest` files   


Schemas for these default settings can be found in the `palgen/schemas <https://github.com/palliate/palgen/tree/master/src/palgen/schemas>`_ subdirectory.


CLI
########

Palgen extensions can either be run from the project's root folder or directly:


Using the palgen command
-------------------------

The :bash:`palgen` command without any arguments is used to run all enabled extensions configured in the palgen.toml file.

To run a specific extension (ie. named :code:`foobar`), you can use the command :bash:`palgen foobar`. This extension should be defined somewhere within the project's source or extension folders. To run multiple extensions at once (ie :code:`foo` and :code:`bar`), you can use the compound command :bash:`palgen foo bar`.

You can also provide additional options for both the extension and palgen itself. These options will override configured settings from `palgen.toml` and can be required (if a field of the Setting schema has no default and no value is given to it in the settings file). For example:

.. code-block:: bash
   
   palgen --debug foo --zoinks=4 bar --baz "oh no"
   
This command executes palgen with debug printing enabled, runs the :code:`foo` extension with the :code:`zoinks` setting set to :code:`4`, and runs the :code:`bar` extension with the :code:`baz` setting set to :code:`"oh no"`.

To learn more about the available extensions and their settings, you can try running :bash:`palgen --help`. If you need help specifically for an extension (ie the :bash:`foo` extension), you can use the command :bash:`palgen foo --help`.


Executing the module directly
-------------------------------

It is also possible to execute palgen extensions directly. To do so just execute them with a Python interpreter. For example :bash:`python foobar.py` if foobar.py contains exactly one palgen extension.

.. warning::
   For this to work you may only define one palgen extension per Python module (that is, file).


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
