import fnmatch
import logging
import re
from collections import defaultdict
from pathlib import Path
from typing import Optional, Pattern

logger = logging.getLogger(__name__)


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

    if (probe := path).exists():
        with open(probe, mode='r', encoding='utf-8') as file:
            return {re.compile(fnmatch.translate(line))
                    for line in file.read().splitlines()
                    if line}
    return set()


def walk(path: Path | str, ignores: PathFilter | set[Pattern]):
    if isinstance(ignores, set):
        ignores = PathFilter(ignores)

    path = Path(path).resolve()
    if not path.is_dir():
        raise NotADirectoryError

    if ignores.check(path):
        logger.debug("Skipped %s", path)
        return

    ignores = ignores.copy_extend(gitignore(path))

    if (probe := path / 'palgen.toml').exists():
        # skip subtrees of other projects but yield the project file
        logger.debug("Found another palgen project in `%s`. Skipping.")
        yield probe
        return

    for entry in path.iterdir():
        if ignores.check(entry):
            # honor .gitignore, skip this entry
            logger.debug("Skipped `%s`", entry)
            continue

        if entry.is_file():
            yield entry

        elif entry.is_dir():
            yield from walk(entry, ignores)


class SuffixDict(defaultdict[str, defaultdict[str, list[Path]]]):
    def __init__(self):
        super().__init__(lambda: defaultdict(list[Path]))

    def walk(self, path: Path, ignores: PathFilter | set[Pattern]):
        for entry in walk(path, ignores):
            self[entry.suffix][entry.stem].append(entry)

    def by_extension(self, extension) -> dict[str, list[Path]]:
        return self.get(extension, {})

    def by_name(self, name: str | Path) -> list[Path]:
        name = Path(name)
        if files := self.by_extension(name.suffix):
            return files.get(name.stem, [])
        return []
