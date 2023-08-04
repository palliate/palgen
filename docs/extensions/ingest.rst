Ingesting files
==================================

To make common operations such as ingesting files from your project's source directory a little easier, palgen comes with a "magic" :code:`Pipeline` helper. This helper allows palgen to automatically parallelize tasks if possible.

Essentially a Pipeline such as

.. code-block:: python

    pipeline = Sources() >> foo >> bar >> baz

when invoked with :code:`pipeline(iterable)` would essentially expand to

.. code-block:: python
    baz(bar(foo(iterable)))


You can use the :code:`@max_jobs(...)` decorator from :code:`palgen.ext` to control the amount of jobs a step can be run at. Additionally annotating the :code:`data` parameter with :code:`list` is equivalent to decorating the step with :code:`@max_jobs(1)`.

All steps must be functions or function objects returning an iterable, generators, a class implementing the iterator protocol or an instance of such a class. The :code:`palgen.machinery.pipelines.Pipeline` class is aliased as :code:`palgen.ext.Sources` for convenience. The default :code:`run(...)` method will call the :code:`pipeline` class attribute of your extension with a pre-filtered list of source files.

Filters and loaders
--------------------

For convenience some commonly used path filters and file loaders are implemented in :code:`palgen.ingest`. All of the built-in filter and file loader steps expect an iterable of :code:`Path`s, so make sure to use only one loader as last step as it yields a tuple of the :code:`Path` to the file and the file's loaded content.


Default pipelines
-------------------

By default palgen searches for `TOML <https://toml.io/en/>`_ files named after the extension's name. For example an extension called :code:`error` would by default ingest all files called :code:`error.toml` from the source directories.

.. code-block:: python

    ingest = Sources() >> Suffix('toml')
                       >> Name(<extension name>)
                       >> Toml

This behavior can be overridden by defining the :code:`ingest` class variable of your extension. Possible values are :code:`None` to disable ingest entirely, a pipeline or a dictionary of pipelines with string keys.


The overall pipeline of an extension can be overridden by setting the :code:`pipeline` class variable of your extension. By default palgen will execute the :code:`ingest` pipeline and the :code:`transform`, :code:`validate`, :code:`render` and :code:`write` methods of your extension in order. This is equivalent to setting something like

.. code-block:: python

    pipeline = Sources() >> <extension>.ingest
                         >> <extension>.transform
                         >> <extension>.validate
                         >> <extension>.render
                         >> <extension>.write

Full example
-------------

.. literalinclude:: /examples/tutorial/src/embed/embed.py
   :language: Python
   :linenos:
