import logging
from typing import Any

from palgen.ingest.filter import Extension
from palgen.ingest.loader import Raw


from palgen.module import Module, Sources

class Preprocess(Module):
    """ Sources module help text. Spliced after the dot """

    ingest = {
        'headers': Sources >> Extension(".h") >> Raw,
        'sources': Sources >> Extension(".cpp") >> Raw
    }

    def transform_headers(self, data: list):
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
