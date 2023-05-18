import fnmatch
import logging
import re
from collections import defaultdict
from pathlib import Path
from typing import Optional, Pattern, Iterable
from palgen.util import Pipeline

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

    if path.exists():
        logger.debug("Parsing `%s`", path)
        with open(path, mode='r', encoding='utf-8') as file:
            return {re.compile(fnmatch.translate(line))
                    for line in file.read().splitlines()
                    if line}
    return set()


def walk(path: Path | str, ignores: PathFilter | set[Pattern]) -> Iterable[Path]:
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

        yield entry

        if entry.is_dir():
            yield from walk(entry, ignores)


class SuffixDict(defaultdict[str, defaultdict[str, list[Path]]]):
    def __init__(self):
        super().__init__(lambda: defaultdict(list[Path]))
        self.directories: list[Path] = []

    def walk(self, path: Path, ignores: PathFilter | set[Pattern]):
        for entry in walk(path, ignores):
            if entry.is_file():
                self[entry.suffix][entry.stem].append(entry)
            elif entry.is_dir():
                self.directories.append(entry)

    def by_extension(self, extension: str | Pattern) -> Iterable[Path]:
        if not isinstance(extension, Pattern):
            if not extension.startswith('.'):
                extension = f'.{extension}'

            if extension.count('.') > 1:
                extensions = extension.split('.')
                for stem, paths in self.get(extensions[-1], {}).items():
                    if stem.endswith('.'.join(extensions[:-1])):
                        yield from paths
            else:
                for _, paths in self.get(extension, {}).items():
                    return paths

        for suffix, entry in self.items():
            if not re.match(extension, suffix):
                continue
            yield from entry.values()

    def by_name(self, name: str | Pattern) -> Iterable[Path]:
        if not isinstance(name, Pattern):
            path = Path(name)
            assert path.is_file(), f"Name {name} cannot refer to a valid file"

            if files := self.get(path.suffix):
                yield from files.get(path.stem, [])

        for path in self:
            if not re.match(name, path.name):
                continue
            yield path

    def by_stem(self, stem: str | Pattern) -> Iterable[Path]:
        for path in self:
            if isinstance(stem, Pattern):
                if not re.match(stem, path.stem):
                    continue
            elif stem != path.stem:
                continue

            yield path

    def by_pattern(self, pattern: Pattern) -> Iterable[Path]:
        for path in self:
            if not re.match(pattern, str(path)):
                continue
            yield path

    def __iter__(self) -> Iterable[Path]:
        for _, entry in self.items():
            for _, paths in entry.items():
                yield from paths


class Sources(Pipeline):
    def __call__(self, state: SuffixDict):
        assert isinstance(state, SuffixDict)
        yield from super().__call__(state)
