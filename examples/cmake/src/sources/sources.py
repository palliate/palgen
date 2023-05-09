import logging

from pydantic import BaseModel
from palgen.ingest import Filter
from palgen.ingest.file import Raw


from palgen.module import Module, Pipeline, Model
from typing import Annotated


class Sources(Module):
    """ Sources module help text. Spliced after the dot """

    class Settings(Model):
        foo: Annotated[str, "help text for foo"]
        bar: int = 3
        foobar: bool

    ingest = {
        'headers': Pipeline >> Filter(extension=".h") >> Raw,
        'sources': Pipeline >> Filter(extension=".cpp") >> Raw
    }

    def transform_headers(self, data):
        yield from data

    def validate(self, data):
        yield from data

    def render(self, data):
        logging.warning("render")
        return
        yield

    def render_headers(self, data):
        logging.warning("render_headers")
        return
        yield

    def render_sources(self, data):
        logging.warning("render_sources")
        return
        yield
