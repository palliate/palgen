palgen.toml
==================================

.. role:: bash(code)
   :language: bash

Minimum required project settings
##################################

To be able to run palgen the project's root directory must include a file called :code:`palgen.toml`. This file can be used to configure both palgen and provide settings for extensions used in this project.

Builtin settings:

.. code-block:: toml
   :linenos:
   
   # Required
   [project]
   name        = "Foobar"       # Project name
   version     = "v0.1"         # Project version string. Optional.
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
