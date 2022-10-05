import logging
import re
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass(frozen=True, repr=True)
class Value:
    def silence(self, enable: bool):
        if enable:
            object.__setattr__(self, "print", lambda *args: None)
        else:
            object.__setattr__(self, "print", logger.warning)

    def check(self, data, silent=False):
        self.silence(silent)
        return data is not None


@dataclass(frozen=True, repr=True)
class Maybe:
    field: Value

    def check(self, data, silent=False):
        if data is None:
            return True

        if isinstance(self.field, type):
            return self.field().check(data)

        return self.field.check(data)


@dataclass(frozen=True, repr=True)
class String(Value):
    min_length: int = 1
    max_length: Optional[int] = None
    pattern: Optional[re.Pattern] = None
    either: Optional[list] = None

    def check(self, data, silent=False):
        super().check(data, silent)

        if not isinstance(data, str):
            self.print(f"Wrong type. Expected str got {type(data)}")
            return False

        if len(data) < self.min_length:
            self.print(
                "String too short. " f"Required: {self.min_length} Got: {len(data)}"
            )
            return False

        if self.max_length is not None and len(data) > self.max_length:
            self.print(
                "String too long. " "Required: {self.max_length} Got: {len(data)}"
            )
            return False

        if self.pattern is not None and not re.match(self.pattern, data):
            self.print(f"String {data} does not match pattern {self.pattern}")
            return False

        if self.either is not None:
            if not isinstance(self.either, list):
                raise ValueError(
                    "Schema invalid. String.either must be a list")

            if data not in self.either:
                self.print(f"String `{data}` not in {self.either}.")
                return False

        return True


@dataclass(frozen=True, repr=True)
class Int(Value):
    min: Optional[int] = None
    max: Optional[int] = None

    def check(self, data: int, silent=False):
        if not super().check(data, silent):
            return False

        if not isinstance(data, int):
            self.print(f"Wrong type. Expected int got {type(data)}")
            return False

        if self.min is None and self.max is None:
            return True

        if self.min is None:
            return data <= self.max
        if self.max is None:
            return self.min <= data

        return self.min <= data <= self.max


@dataclass(frozen=True, repr=True)
class Bool(Value):
    def check(self, data: bool, silent=False):
        super().check(data, silent)

        if not isinstance(data, bool):
            return False
        return True


@dataclass(frozen=True, repr=True)
class List(Value):
    item: Value
    min_length: int = 0
    max_length: Optional[int] = None

    def check(self, data: list, silent=False):
        if not super().check(data, silent):
            return False

        if not isinstance(data, list):
            self.print(f"Wrong type. Expected list got {type(data)}")
            return False

        if len(data) < self.min_length:
            self.print(
                "List too short. " f"Required: {self.min_length} Got: {len(data)}"
            )
            return False

        if self.max_length is not None and len(data) > self.max_length:
            self.print(
                "List too long. " f"Required: {self.max_length} Got: {len(data)}"
            )
            return False

        ret = True
        validator = self.item() if isinstance(self.item, type) else self.item

        for item in data:
            if not validator.check(item):
                self.print(f"Item {item} failed check against {self.item}")
                ret = False

        return ret


@dataclass(frozen=True, repr=True)
class Dict(Value):
    schema: dict = field(default_factory=dict)

    def check(self, data: dict, silent=False):
        if not super().check(data, silent):
            return False

        if not isinstance(data, dict):
            self.print(f"Wrong type. Expected dict got {type(data)}")
            return False

        ret = True
        for key, validator in self.schema.items():
            if isinstance(key, tuple):
                temp = False
                for idx, k in enumerate(key):
                    if temp and k in data.keys():
                        self.print(
                            f"More than one key defined for optional {key}")
                        ret = False
                        break

                    validate = (
                        validator[idx] if isinstance(
                            validator, tuple) else validator
                    )

                    if self._check(data, k, validate, True):
                        temp = True
                    self.silence(silent)

                if not temp:
                    self.print(f"None of the variant keys {key} found")
                    ret = False

            elif isinstance(key, str):
                if not self._check(data, key, validator):
                    ret = False

        return ret

    def _check(self, data, key, validator, silent=False):
        self.silence(silent)
        if key not in data.keys():
            if isinstance(validator, Maybe):
                return True

            self.print(f"Missing key: {key}")
            return False

        if isinstance(validator, type):
            validator = validator()
        if not validator.check(data[key]):
            self.print(f"Validation of key {key} failed.")
            return False

        return True


@dataclass(frozen=True, init=False, repr=True)
class Variant(Value):
    variants: list

    def __init__(self, *args):
        super().__init__()
        variants = [arg() if isinstance(arg, type) else arg for arg in args]
        object.__setattr__(self, "variants", variants)

    def check(self, data, silent=False):
        if not super().check(data, silent):
            return False

        for variant in self.variants:
            if variant.check(data, True):
                return True
        self.print(
            f"Allowed types for variant {self.variants}, got {type(data)}")
        return False


"""
schema = Dict(schema={
  'name': String(),
  'folders': List(item=String(True)),
  'version': String(pattern="v[0-9.]+$"),
  'type': String(pattern="(application|library|plugin)$"),
  'test': Maybe(Dict()),
  'ambi': Variant(String(max_length=2), Int()),
  #('multi', 'foo'): (Int(), String())
})

schema = {
  'name': str,
  'folders': [str],
  'version': String(pattern="v[0-9.]+$"),
  'type': String(either=["application", "library", "plugin"]),
  'test': Optional[{}],0
  'ambi': Any[String(max_length=2), int],
  ('multi', 'foo'): (int, str)
}

data = {
  'name': "3",
  'version': "v0.1",
  'type': "library",
  'folders': ["affa", "3", "b"],
  'test': {},
  'ambi': "33",
  #'test': 34
  #'multi': 3
}

check = schema.check(data)
print(f"{check=}")"""
