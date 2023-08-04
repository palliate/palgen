Multiple pipelines
==================================

As mentioned before, extensions may define more than one :code:`ingest` and :code:`pipeline` pipeline. For this to work :code:`ingest` or respectively :code:`pipeline` must be a dictionary of string keys and :code:`Pipeline` (or :code:`Sources`, since that's just an alias) objects. 

Dictionaries in Python keep insertion order, hence individual pipelines will be ran sequentially in order.

To disambiguate steps between pipelines you can append an underscore and the pipeline's key to the step name. If no pipeline-specific step could be found the generic one will be used instead.

.. code-block:: python
  
  from palgen.ext import Extension, Sources
  from palgen.ingest import Suffix
  
  class MultiPipeline(Extension):
      """ Description for the MultiPipeline extension """

      ingest = {
        'foo': Sources() >> Suffix('.c'),
        'bar': Sources() >> Suffix('.h')
      }

      def transform(self, data):
          # fallback, will be used for bar
          yield from data
    
      def transform_foo(self, data):
          # will only be used for foo
          yield from data

      def validate(self, data):
          # will be used for both foo and bar
          yield from data
      
      def render_foo(self, data):
          # will be used for foo
          return []
      
      def render_bar(self, data):
          # will be used for bar
          return []
      
      def render(self, data):
          # fallback, will not be used
          return []


Full example
----------------

TODO