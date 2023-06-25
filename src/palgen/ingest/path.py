from pathlib import Path
from typing import Iterable


def Relative(self, files: Iterable[Path]) -> Iterable[Path]:
    for file in files:
        yield file.relative_to(self.root)

def Absolute(self, files: Iterable[Path]) -> Iterable[Path]:
    for file in files:
        yield self.root / file
