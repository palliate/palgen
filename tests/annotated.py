from pydantic import BaseModel
from typing import Annotated
from typing import get_type_hints, get_origin, get_args
from enum import Enum
from pprint import pprint


class BuildTypes(Enum):
    RELEASE = 'Release'
    DEBUG = 'Debug'


class Test(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    bar: int = 3
    foo: Annotated[int, 5] = 6

    all: Annotated[list[str], "Build all targets"]
    lib: Annotated[bool, "Build lib target"] = False

    editable: Annotated[bool, "Install lib as editable package"] = False
    build_type: Annotated[BuildTypes, "Target build type"] = BuildTypes.RELEASE
    oof = 3

# print(Test.__annotations__['foo'])


def extract_help(hint) -> str:
    if get_origin(hint) is not Annotated:
        return ""

    _, *args = get_args(hint)

    if len(args) > 1 or not isinstance(args[0], str):
        return ""

    return args[0]


def pydantic_to_click(cls):
    hints = get_type_hints(cls, include_extras=True)

    for key, field in getattr(cls, "__fields__").items():
        options = {
            'type': field.type_, #TODO possible bug, check list[str]
            'required': field.required,
        }

        if not field.required:
            options['default'] = field.default

        if hint := hints.get(key):
            options['help'] = extract_help(hint)

        if field.type_ is bool:
            options['is_flag'] = True

        yield key, options


pprint(dict(pydantic_to_click(Test)))
