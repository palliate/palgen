GitHub Action
==================================

Palgen provides a GitHub Action that allows you to easily install and run palgen. The action provides options to customize the installation and execution process based on your requirements.

Usage
############################################

To use the palgen GitHub Action in your workflow, you need to create a YAML file in your repository under the :code:`.github/workflows/` directory (e.g., ci.yml). Add the following content to the YAML file:

.. code-block:: yaml

    name: Your Workflow Name

    on:
      push:
        branches: [master]
      pull_request:
        branches: [master]

    jobs:
      palgen_job:
        name: palgen Action Job
        runs-on: ubuntu-latest

        steps:
          - name: Checkout Repository
            uses: actions/checkout@v2

          - name: Run palgen Action
            uses: palliate/palgen@master
            with:
              # Set to 'false' if you don't want to install the optional conan dependency. Defaults to false.
              conan: true

              # Set to 'false' if you only want to install but not run palgen. Defaults to true.
              run: true    
              
              # Set the path to extension requirements.txt if needed
              requirements: 'path/to/requirements.txt'

Replace :code:`Your Workflow Name` with the desired name for your GitHub Actions workflow. Modify the :code:`on` section according to your desired trigger events (e.g. :code:`push`, :code:`pull_request` etc.).

Inputs
-----------------------------

The following inputs are available for the palgen GitHub Action:

conan *(optional)*
**********************

.. table:: 
  :align: left

  =============== ===============
  Description:    Set this input to install the optional conan dependency along with palgen.
  Required:       No (default is :code:`false`)
  Allowed values: :code:`true`, :code:`false`
  =============== ===============


run *(optional)*
**********************

.. table:: 
  :align: left

  =============== ===============
  Description:    Set this input to control whether to run palgen after installation or not.
  Required:       No (default is :code:`true`)
  Allowed values: :code:`true`, :code:`false`
  =============== ===============

requirements *(optional)*
**************************

.. table:: 
  :align: left

  =============== ===============
  Description:    Set the path to the requirements.txt file for any additional extension dependencies.
  Required:       No (default is an empty string)
  Example value:  :code:`path/to/requirements.txt`
  =============== ===============


Workflow steps
-----------------------------

The palgen GitHub Action consists of the following steps:

1. **Setup Python:** Sets up the required Python version. The action currently uses Python version 3.11.

2. **Install palgen:** Installs the palgen Python package.

3. **Install Conan *(optional)*:** Installs the optional conan dependency if conan input is set to true.

4. **Install extension dependencies *(optional)*:** If the requirements input is provided with a valid path to a requirements.txt file, this step will install additional dependencies specified in the file.

5. **Run palgen *(optional)*:** If the run input is set to true, this step will execute the palgen tool.

