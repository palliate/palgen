import traceback
from functools import lru_cache
from pathlib import Path
from typing import Optional

import jinja2


class Template(jinja2.Template):
    def __new__(cls, filename: Path | str,
                environment: Optional[jinja2.Environment] = None,
                encoding: Optional[str] = 'utf-8') -> 'jinja2.Template':

        frame = traceback.extract_stack(limit=2)[-2]
        path = Path(frame.filename).parent

        with open(path / filename, 'r', encoding=encoding) as file:
            if environment is None:
                environment = Template.default_environment()
            template = environment.from_string(file.read(), template_class=cls)

            # patch in call operator
            setattr(template, '__call__', template.render)
            return template

    __call__ = jinja2.Template.render

    @staticmethod
    @lru_cache(maxsize=1)
    def default_environment():
        return jinja2.Environment(
            block_start_string="@{",
            block_end_string="}",
            variable_start_string="@",
            variable_end_string="@",
            comment_start_string="@/*",
            comment_end_string="*/",
            keep_trailing_newline=True,
        )
