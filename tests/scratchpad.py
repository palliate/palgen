import fnmatch
import logging
import re
from collections import defaultdict
from pathlib import Path
from typing import Optional, Pattern, Iterable
from palgen.util import Pipeline

_logger = logging.getLogger(__name__)


class PathFilter:
    def __init__(self, patterns: Optional[set[Pattern]] = None):
        self.blacklist: set[Pattern] = set(patterns) if patterns else set()

    def extend(self, patterns: set[Pattern]) -> None:
        self.blacklist.update(patterns)

    def copy_extend(self, patterns: set[Pattern]) -> 'PathFilter':
        if not patterns:
            return self

        ret = PathFilter(self.blacklist.copy())
        ret.extend(patterns)
        return ret

    def check(self, path: Path) -> bool:
        return any(i.match(str(path)) for i in self.blacklist)


def gitignore(path: Path) -> set[Pattern]:
    if path.is_dir():
        path = path / '.gitignore'

    if path.exists():
        _logger.debug("Parsing `%s`", path)
        with open(path, mode='r', encoding='utf-8') as file:
            return {re.compile(fnmatch.translate(line))
                    for line in file.read().splitlines()
                    if line}
    return set()


def walk(path: Path | str, ignores: PathFilter | set[Pattern]) -> Iterable[Path]:
    if isinstance(ignores, set):
        ignores = PathFilter(ignores)

    path = Path(path)
    if not path.is_dir():
        raise NotADirectoryError

    if ignores.check(path):
        _logger.debug("Skipped %s", path)
        return

    ignores = ignores.copy_extend(gitignore(path))

    if (probe := path / 'palgen.toml').exists():
        # skip subtrees of other projects but yield the project file
        _logger.debug("Found another palgen project in `%s`. Skipping.")
        yield probe
        return

    for entry in path.iterdir():
        if ignores.check(entry):
            # honor .gitignore, skip this entry
            _logger.debug("Skipped `%s`", entry)
            continue

        yield entry

        if entry.is_dir():
            yield from walk(entry, ignores)

root = Path("/home/che/src/llvm-project")
files = list(walk(root, gitignore(root)))
print(len(files))
