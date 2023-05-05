import traceback
from pathlib import Path

class Template:
    def __init__(self):
        frame = traceback.extract_stack(limit=2)[-2]
        self.path = Path(frame.filename).parent
        print(self.path)


Template()
class Foo:
    def bar(self):
        Template()

Foo().bar()
