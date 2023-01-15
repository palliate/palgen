from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Iterator, Any

@dataclass
class Meta:
    qualname: list[str]
    source: Path

    @cached_property
    def name(self):
        assert self.qualname
        return self.qualname[0]

    @cached_property
    def namespace(self):
        assert self.qualname
        return self.qualname[:-1]

class Ingest:

    @classmethod
    def data(cls, path: Path) -> Iterator[tuple[Meta, Any]]:
        pass

    @classmethod
    def template(cls, path: Path):
        pass
