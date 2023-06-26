import logging

from pydantic import BaseModel, ValidationError


_logger = logging.getLogger(__name__)


def check_schema_attribute(cls: type, name: str):
    if hasattr(cls, name) and (schema := getattr(cls, name)):
        assert isinstance(schema, type), \
            f"Schema {name} of class `{cls.__name__}` is not a type."
        assert issubclass(schema, BaseModel), \
            f"Schema {name} of class `{cls.__name__}` isn't a pydantic model."


def print_validationerror(exception: ValidationError):
    for error in exception.errors():
        for loc in error["loc"]:
            _logger.warning("  %s", loc)
        _logger.warning("    %s (type=%s)", error["msg"], error["type"])


Model = BaseModel
