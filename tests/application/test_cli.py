import abc
from enum import Enum
from typing import Annotated, MutableSequence
import pytest
from pydantic import BaseModel

from palgen.application.util import pydantic_to_click, ListParam, DictParam
from palgen.machinery.types import issubtype


class BuildTypes(Enum):
    RELEASE = 'Release'
    DEBUG = 'Debug'


class DummyModel(BaseModel):
    model_config = {'arbitrary_types_allowed': True}

    bar: int = 3
    foo: Annotated[int, 5] = 6

    all: Annotated[list[str], "Build all targets"]
    lib: Annotated[bool, "Build lib target"] = False

    editable: Annotated[bool, "Install lib as editable package"] = False
    build_type: Annotated[BuildTypes, "Target build type"] = BuildTypes.RELEASE
    oof: int = 3


def test_pydantic_to_click():
    expected = {
        'bar': {
            'required': False,
            'type': int,
            'default': 3,
            'help': ''
        },
        'foo': {
            'required': False,
            'type': int,
            'default': 6,
            'help': ''
        },
        'all': {
            'required': True,
            'type': list[str],
            'help': "Build all targets"
        },
        'lib': {
            'required': False,
            'type': bool,
            'is_flag': True,
            'default': False,
            'help': "Build lib target"
        },
        'editable': {
            'required': False,
            'type': bool,
            'is_flag': True,
            'default': False,
            'help': "Install lib as editable package"
        },
        'build_type': {
            'required': False,
            'type': BuildTypes,
            'default': BuildTypes.RELEASE,
            'help': "Target build type"
        },
        'oof': {
            'required': False,
            'type': int,
            'default': 3,
            'help': ''
        }
    }

    for key, options in pydantic_to_click(DummyModel):
        assert key in expected

        for option, value in options.items():
            assert option in expected[key]

            if isinstance(value, type) and issubclass(value, MutableSequence):
                #TODO check subtype
                assert issubtype(expected[key][option], list)
            else:
                assert value == expected[key][option], value


def test_list_param_convert():
    assert ListParam[int]().convert("1;2;3;4") == [1, 2, 3, 4]
    assert ListParam[int]().convert("[1, 2, 3, 4]") == [1, 2, 3, 4]
    assert ListParam[str]().convert("1;2;3;4") == ["1", "2", "3", "4"]
    assert ListParam[str]().convert("['1', '2', '3', '4']") == ["1", "2", "3", "4"]


def test_list_param_convert_raises():
    with pytest.raises(ValueError):
        ListParam[int]().convert("1;2;3;4.5")

    with pytest.raises(ValueError):
        ListParam[int]().convert("[1,2,3,4.5]")


def test_dict_param_type():
    assert DictParam[int, str]().convert('{1: "one", 2: "two"}',
                                       None,
                                       None) == {1: "one", 2: "two"}


def test_dict_param_type_failure():
    with pytest.raises(ValueError):
        DictParam[int, int]().convert('{1: "one", 2: "two"}', None, None)
