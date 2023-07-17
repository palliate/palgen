import re
from pathlib import Path
from typing import Iterable

from palgen.ingest import Suffix, Text, Relative
from palgen.ext import Extension, Sources


class FString(Extension):
    ingest = Sources >> Suffix(".cpp", ".c", ".hpp", ".h") >> Relative >> Text

    string_pattern = re.compile(r"(?P<prefix>(u|U|u8|L)?f?(u|U|u8|L)?)"
                                r"((R\"(?P<delimiter>.*)\((?P<raw>(\n|.)*?)\)\6\")|"
                                r"(\"(?P<literal>((\\[\"\n])|[^\"\n])*)\"))")

    replacement_pattern = re.compile(r"((?<!{)|{{){(?P<variable>(::|[\w_.()$])*)"
                                     r"(?P<format_spec>:[^}]*)?}")

    def render(self, data: Iterable[tuple[Path, str]]):
        def replace_literal(string: re.Match[str]):
            if 'f' not in string['prefix']:
                return string.group()

            if not string['raw'] and not string['literal']:
                return string.group()

            literal = string['raw'] or string['literal']
            variables = []

            def replace_variable(replacement: re.Match[str]):
                if not replacement['variable']:
                    return replacement.group()

                variables.append(replacement['variable'])
                return replacement.group().replace(replacement['variable'], '')

            literal = re.sub(FString.replacement_pattern, replace_variable, literal)
            prefix = string["prefix"].replace('f', '')

            if string['delimiter']:
                literal = f'{prefix}R"{string["delimiter"]}({literal}){string["delimiter"]}"'
            else:
                literal = f'{prefix}"{literal}"'

            return f'std::format({literal}, {",".join(variables)}).c_str()' if variables else literal

        for path, content in data:
            yield self.out_path / path, re.sub(FString.string_pattern, replace_literal, content)
