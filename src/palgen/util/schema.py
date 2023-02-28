import logging
from typing import Annotated, get_args, get_origin, get_type_hints

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)


def check_schema_attribute(cls: type, name: str):
    if hasattr(cls, name) and (schema := getattr(cls, name)):
        if schema is BaseModel:
            return
        if not isinstance(schema, type):
            raise SyntaxError(
                f"{name} of class `{cls.__name__}` is not a type.")
        if BaseModel not in schema.__bases__:
            raise SyntaxError(
                f"{name} of class `{cls.__name__}` isn't a pydantic model.")


def print_validationerror(exception: ValidationError):
    for error in exception.errors():
        for loc in error["loc"]:
            logger.warning("  %s", loc)
        logger.warning("    %s (type=%s)", error["msg"], error["type"])


def extract_help(hint) -> str:
    if get_origin(hint) is not Annotated:
        return ""

    _, *args = get_args(hint)

    return "" if len(args) > 1 or not isinstance(args[0], str) else args[0]


def pydantic_to_click(cls):
    hints = get_type_hints(cls, include_extras=True)

    for key, field in getattr(cls, "__fields__").items():
        options = {
            'type': field.type_,  # TODO possible bug, check list[str]
            'required': field.required,
            'help': ""
        }

        if hint := hints.get(key):
            options['help'] = extract_help(hint)

        if not field.required:
            options['default'] = field.default

        if field.type_ is bool:
            options['is_flag'] = True

        yield key, options
