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

Palgen modules can either be run from the project's root folder:

:bash:`palgen` runs all enabled modules configured in `palgen.toml`.

:bash:`palgen foobar` runs the `foobar` module defined somewhere within the project's source or module folders.

:bash:`palgen foo bar` runs the modules `foo` and `bar`

Additional options can be supplied for all modules and palgen itself:

:bash:`palgen --debug foo --zoinks=4 bar --baz "oh no"` executes palgen with debug printing enabled, module `foo` with setting `zoinks = 4` and module `bar` with setting `baz = "oh no"`.

Try :bash:`palgen --help` to learn more about available modules and settings.

:bash:`palgen foo --help` can be used to print help text for module `foo`