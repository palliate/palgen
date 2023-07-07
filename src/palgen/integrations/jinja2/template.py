import traceback
from functools import lru_cache
from pathlib import Path
from typing import Optional

import jinja2

from palgen.machinery import copy_attrs


class Template(jinja2.Template):
    def __new__(cls, filename: Path | str,
                environment: Optional[jinja2.Environment] = None,
                encoding: Optional[str] = 'utf-8') -> 'Template':
        frame = traceback.extract_stack(limit=2)[-2]
        path = Path(frame.filename).parent

        with open(path / filename, 'r', encoding=encoding) as file:
            if environment is None:
                environment = Template.default_environment()

            template = environment.from_string(file.read(), template_class=cls)
            instance = object.__new__(cls)

            copy_attrs(template, instance)
            return instance

    __call__ = jinja2.Template.render

    @staticmethod
    @lru_cache(maxsize=1)
    def default_environment() -> jinja2.Environment:
        return jinja2.Environment(
            block_start_string="@{",
            block_end_string="}",
            variable_start_string="@",
            variable_end_string="@",
            comment_start_string="@/*",
            comment_end_string="*/",
            keep_trailing_newline=True,
        )
