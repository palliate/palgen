import logging
from pathlib import Path
from typing import Any, Iterable

from pydantic import BaseModel as Model, ValidationError

from .module import Module, _print_validationerror

_logger = logging.getLogger(__name__)

class Codegen(Module):
    template = "codegen"

    def validate(self, data: Iterable[tuple[Path, Any]]) -> Iterable[tuple[Path, Model | Any]]:
        """Validates elements in the `data` Iterable against the pydantic schema `Schema` of this module.

        Args:
            data (Iterable[tuple[Path, Any]]): Iterable of inputs from the `transform` step

        Yields:
            tuple[Path, BaseModel | Any]: Input file path and validated `Schema` object

        Warning:
            By default inputs failing verification do not cause the module run to fail,
            they simply get skipped.
        """
        for path, value in data:
            try:
                yield path, self.Schema.parse_obj(value)
            except ValidationError as ex:
                _logger.warning("%s failed verification.", path)
                _print_validationerror(ex) # TODO
