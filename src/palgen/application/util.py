from abc import ABC
from types import UnionType
from typing import Annotated, Any, Iterable, Union, get_args, get_origin, get_type_hints

import click


def strip_quotes(string):
    if string[0] == string[-1] and string[0] in ('\'', '\"'):
        return string[1:-1]
    return string

class ListParam(ABC, click.ParamType):
    """Click friendly list proxy. Can be used like a parameterized generic,
    ie ListParam[int] will check if all elements of the list are actually of type int.
    """
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

    def __class_getitem__(cls, inner_t) -> 'ListParam':
        assert isinstance(inner_t, type)

        name = f"{getattr(cls, 'name')}[{inner_t.__name__}]"
        return type(name, (ListParam,), {'name': name, 'inner_t': inner_t})()


class DictParam(ABC, click.ParamType):
    """Click friendly dict proxy. Can be used like a parameterized generic.
    ie: :code:`DictParam[str, int] will check all keys for type :code:`str`
    and all values for type :code:`int`
    """
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
                self.fail("Dictionary item does not contain key:value mapping", param, ctx)

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
    """Extracts help text from a variable annotated with an :code:`Annotated[...]`
    with at least one string among the parameters.

    ie. :code:`Annotated[int, "This takes a whole number"]`
    also supports unions and parameterized generics as parameters, ie
    :code:`Annotated[int | str, "Takes a number or a string"]`
    :code:`Annotated[ListParam[int], "Takes a list of ints"]`

    Args:
        hint (_type_): _description_

    Returns:
        str: _description_
    """
    assert get_origin(hint) is Annotated

    args = get_args(hint)
    return next((hint for hint in args if isinstance(hint, str)), "")

def pydantic_to_click(cls: type) -> Iterable[tuple[str, dict[str, Any]]]:
    """Converts a extension's Settings schema to click arguments.

    To make an argument optional annotated with a union of the desired type and :code:`None`
    or utilize :code:`typing.Optional`.

    Attributes annotated with :code:`bool` will have :code:`is_flag` set, meaning they will be treated as flags.

    Help text is automatically extracted from attributes annotated with :code:`Annotated[..., "help text"]`

    Args:
        cls (type): Setting schema

    Raises:
        TypeError: Invalid annotation found.

    Yields:
        tuple[str, dict[str, Any]]: Tuple consisting of attribute key and converted options.
    """

    #TODO consider moving this into `palgen.machinery`
    hints = get_type_hints(cls, include_extras=True)

    for key, field in getattr(cls, "__fields__").items():
        assert isinstance(key, str)

        options = {
            'type': field.type_,
            'required': field.required,
            'help': ""
        }

        if hint := hints.get(key):
            if get_origin(hint) is Annotated:
                type_, *_ = get_args(hint)
                options['help'] = extract_help(hint)
                options['type'] = type_

            origin = get_origin(options['type'])

            if origin in (Union, UnionType):
                args = get_args(options['type'])
                if len(args) != 2 or type(None) not in args:
                    raise TypeError("Unions other than Optional are not supported at the moment.")

                options['required'] = False
                options['type'] = args[isinstance(args[0], type(None))]

            elif origin is list:
                inner_type, *rest = get_args(options['type'])
                assert len(rest) == 0
                options['type'] = ListParam[inner_type]

            elif origin is dict:
                key_t, val_t, *rest = get_args(options['type'])
                assert len(rest) == 0
                options['type'] = DictParam[key_t, val_t]

        if not field.required:
            options['default'] = field.default

        if options['type'] is bool:
            options['is_flag'] = True

        yield key, options
