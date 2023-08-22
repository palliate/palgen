from palgen import Extension

class Bar(Extension):
    def run(self, *_):
        print("this is only runnable in examplelib")
