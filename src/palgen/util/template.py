import traceback
from pathlib import Path
from typing import Any

import jinja2

class Template:
    def __init__(self, filename: Path | str, **kwargs) -> Any:
        frame = traceback.extract_stack(limit=2)[-2]
        print(frame.locals)
        path = Path(frame.filename).parent
        print(path)


    __call__ = jinja2.Template.render


Template("")
class Foo:
    environment = "FOo"
    def bar(self):
        zoinks = "bar"
        self.boinks = "foo"
        Template("")

Foo().bar()
