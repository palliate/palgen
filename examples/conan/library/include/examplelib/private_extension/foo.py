from palgen.ext import Extension

class Foo(Extension):
    def run(self, *_):
        print("this is only runnable in examplelib")
