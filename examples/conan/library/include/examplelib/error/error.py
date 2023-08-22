from pathlib import Path
from typing import Iterable
from pydantic import RootModel
from palgen.ext import Extension, Sources, Model
from palgen.ingest import Name, Toml
from palgen.template.jinja import Template


class Error(Extension):
    ingest = Sources >> Name("error.toml") >> Toml

    class Settings(Model):
        namespace: str = ""

    class Schema(RootModel):
        root: dict[str, dict[str, str]]

    def render(self, data: list):
        for file, content in data:
            categories: dict[str, dict[str, str]] = content.root
            out_path: Path = self.out_path / file.parent.relative_to(self.root_path) / 'error.hpp'

            rendered = [
                Template("error.hpp.in").render(
                    namespace=self.settings.namespace,
                    name=category,
                    error_codes=errors,
                )
                for category, errors in categories.items()
            ]

            yield out_path, '\n'.join(rendered)
