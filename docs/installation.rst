Installation
==================================

.. warning::
    Palgen is not yet ready for its first proper release. You can clone the repository and install it directly to evaluate it, but please keep in mind things might change a lot until the first proper release.

Manual installation
###########################

If you do not plan on editing palgen itself you can use pip to install the current development version from git.

.. code-block:: bash

    pip install git+https://github.com/palliate/palgen.git@master

You can replace :code:`master` with any branch name, including but not limited to release branches.


Otherwise clone the repository at an appropriate location and install palgen in editable mode. This is perfect for development since changes to palgen will manifest immediately without having to reinstall the package.

.. code-block:: bash

    git clone https://github.com/palliate/palgen palgen
    pip install -e palgen

.. note::
    This is still work-in-progress. Expect more ways to install palgen soon.