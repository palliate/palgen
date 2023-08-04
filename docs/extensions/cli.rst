Command Line Tool
==================================

To get started, create a new Python file for your extension. Let's name it :code:`hello_world.py`. In this file, we will define the :code:`HelloWorld` extension class.

Please ensure this file is within one of the configured source paths (:code:`project.source` key in :code:`palgen.toml`) or extension paths (:code:`palgen.extensions.folders` key in :code:`palgen.toml`), otherwise it will not be picked up. If you haven't yet created a `palgen.toml` file please do so now.

Minimal command line tool extension
------------------------------------

.. code-block:: python
  
  import logging
  from palgen.ext import Extension
  
  class HelloWorld(Extension):
      """ Description for this tool """

      # disable ingest
      ingest = None

      def run(self, files: list, jobs: Optional[int] = None) -> list:
          logging.info("hello world")

This does not use any of the pipelines.

Adding options
------------------------------------

Options for our extension can be set either in :code:`palgen.toml` or as command line options. So far our :code:`HelloWorld` module does not have any options aside from the built-in ones (such as :code:`--help`). To add some declare a subclass called :code:`Settings`.

.. code-block:: python
  
  import logging
  from typing import Annotated
  from palgen.ext import Extension, Model
  
  class HelloWorld(Extension):
      """ Description for this tool """

      # disable ingest
      ingest = None

      # options of this extension
      class Settings(Model):
        # This is sufficient to require `name` to exist and be of type `str`
        name: str

        # Settings can also be annotated with a help text
        greeting: Annotated[str, "The greeting to display"] = "Hello"

      def run(self, files: list, jobs: Optional[int] = None) -> list:
          logging.info("hello world")

Note that help texts can be added by using :code:`typing.Annotated` as shown in the example above.

Full example
--------------------

Here's a thoroughly commented full example for a command line tool. It can be found in `hello_world.py <https://github.com/palliate/palgen/blob/master/examples/tutorial/extensions/hello_world.py>`_.

You can run it by invoking :code:`palgen helloworld --name somename` within the :code:`examples/tutorial` directory of this repository.

.. literalinclude:: /examples/tutorial/extensions/hello_world.py
   :language: Python
   :linenos:
