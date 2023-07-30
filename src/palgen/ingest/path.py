#pylint: disable=invalid-name

from pathlib import Path
from typing import Iterable


def Relative(self, files: Iterable[Path]) -> Iterable[Path]:
    """Turns absolute file paths into relative (to the project root) file paths.

    Args:
        files (Iterable[Path]): Iterable of file paths.

    Yields:
        Path: Resulting relative paths.
    """
    for file in files:
        yield file.relative_to(self.root_path)

def Absolute(self, files: Iterable[Path]) -> Iterable[Path]:
    """Turns relative (to the project root) file paths into absolute file paths.

    Args:
        files (Iterable[Path]): Iterable of file paths.

    Yields:
        Path: Resulting absolute paths.
    """
    for file in files:
        yield self.root_path / file
