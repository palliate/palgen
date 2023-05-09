import logging
from typing import Annotated, get_args, get_origin, get_type_hints

from pydantic import BaseModel, ValidationError

from palgen.util.cli import DictParam, ListParam

logger = logging.getLogger(__name__)


def check_schema_attribute(cls: type, name: str):
    if hasattr(cls, name) and (schema := getattr(cls, name)):
        assert isinstance(schema, type), \
            f"Schema {name} of class `{cls.__name__}` is not a type."
        assert issubclass(schema, BaseModel), \
            f"Schema {name} of class `{cls.__name__}` isn't a pydantic model."


def print_validationerror(exception: ValidationError):
    for error in exception.errors():
        for loc in error["loc"]:
            logger.warning("  %s", loc)
        logger.warning("    %s (type=%s)", error["msg"], error["type"])


def extract_help(hint) -> str:
    assert get_origin(hint) is Annotated

    _, *args = get_args(hint)
    return "" if len(args) > 1 or not isinstance(args[0], str) else args[0]


def pydantic_to_click(cls):
    hints = get_type_hints(cls, include_extras=True)

    for key, field in getattr(cls, "__fields__").items():
        options = {
            'type': field.type_,
            'required': field.required,
            'help': ""
        }

        if hint := hints.get(key):
            if (origin := get_origin(hint)) is Annotated:
                type_, *_ = get_args(hint)
                options['help'] = extract_help(hint)
                options['type'] = type_

            elif origin is list:
                inner_type, *rest = get_args(hint)
                assert len(rest) == 0
                options['type'] = ListParam[inner_type]
                print(options)

            elif origin is dict:
                key_t, val_t, *rest = get_args(hint)
                assert len(rest) == 0
                options['type'] = DictParam[key_t, val_t]

        if not field.required:
            options['default'] = field.default

        if field.type_ is bool:
            options['is_flag'] = True
        yield key, options


class Scshema(BaseModel):
    def __set_name__(self, owner, name):
        print("called")
        print(self)
        print(owner)
        print(name)

        # return super().__set_name__(owner, name)
Model = BaseModel
