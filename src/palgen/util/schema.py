import logging
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
