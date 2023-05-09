from typing import Any

import click

from palgen.util import strip_quotes


class ListParam(click.ParamType):
    name = "list"
    inner_t = Any

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


class DictParam(click.ParamType):
    name = "dict"
    key_t = Any
    value_t = Any

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
