from palgen import Extension

class NotExported(Extension):
    private = True

    def run(self, *_):
        print("this is only runnable in examplelib")
