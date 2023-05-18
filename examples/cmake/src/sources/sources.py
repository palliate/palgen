import logging

from palgen.ingest.filter import Extension
from palgen.ingest.file import Raw


from palgen.module import Module, Pipeline, Model
from typing import Annotated


class Sources(Module):
    """ Sources module help text. Spliced after the dot """

    ingest = {
        'headers': Pipeline >> Extension(".h") >> Raw,
        'sources': Pipeline >> Extension(".cpp") >> Raw
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
