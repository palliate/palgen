from abc import ABC
from typing import Annotated, get_args, get_origin, get_type_hints

import click

from palgen.util import strip_quotes


class ListParam(ABC, click.ParamType):
    name = "list"
    inner_t: type

    def convert(self, value, *_):
        if isinstance(value, list):
            return value

        separator = ';'
        if value.startswith('[') and value.endswith(']'):
            value = value[1:-1]
            separator = ','

        return [strip_quotes(val.strip())
                if issubclass(self.inner_t, str)
                else self.inner_t(val.strip())
                for val in value.split(separator)]

    def __class_getitem__(cls, inner_t):
        assert isinstance(inner_t, type)

        name = f"{getattr(cls, 'name')}[{inner_t.__name__}]"
        return type(name, (ListParam,), {'name': name, 'inner_t': inner_t})()


class DictParam(ABC, click.ParamType):
    name = "dict"
    key_t: type
    value_t: type

    def convert(self, value, param, ctx):
        if isinstance(value, dict):
            return value

        if not (value.startswith('{') and value.endswith('}')):
            self.fail("Dictionary is not wrapped in { }", param, ctx)
        value = value[1:-1]

        ret = {}
        for item in value.split(','):
            inner = [val.strip() for val in item.split(':')]
            if len(inner) != 2:
                self.fail(
                    "Dictionary item does not contain key:value mapping", param, ctx)

            for idx, field in enumerate([self.key_t, self.value_t]):
                if issubclass(field, str):
                    inner[idx] = strip_quotes(inner[idx])

            ret[self.key_t(inner[0])] = self.value_t(inner[1])

        return ret

    def __class_getitem__(cls, args):
        assert isinstance(args, tuple)
        assert len(args) == 2, "Dictionary needs key and value types"

        key_t, value_t = args
        assert isinstance(key_t, type)
        assert isinstance(value_t, type)

        name = f"{getattr(cls, 'name')}[{key_t.__name__}, {value_t.__name__}]"
        return type(name, (DictParam,), {'name': name, 'key_t': key_t, 'value_t': value_t})()


def extract_help(hint) -> str:
    assert get_origin(hint) is Annotated

    _, *args = get_args(hint)
    return "" if len(args) > 1 or not isinstance(args[0], str) else args[0]

def pydantic_to_click(cls: type):
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

            elif origin is dict:
                key_t, val_t, *rest = get_args(hint)
                assert len(rest) == 0
                options['type'] = DictParam[key_t, val_t]

        if not field.required:
            options['default'] = field.default

        if options['type'] is bool:
            options['is_flag'] = True
        yield key, options
