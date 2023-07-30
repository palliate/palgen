import string
import traceback
from pathlib import Path
from typing import Optional


class Template(string.Template):
    def __init__(self, filename: Path | str, encoding: Optional[str] = 'utf-8'):
        frame = traceback.extract_stack(limit=2)[-2]
        path = Path(frame.filename).parent

        super().__init__((path / filename).read_text(encoding = encoding))

    render = string.Template.substitute
    __call__ = render
