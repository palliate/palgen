import logging
from multiprocessing.pool import Pool
from pathlib import Path
from typing import Iterable, Optional

from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern

from palgen.util import Pipeline

logger = logging.getLogger(__name__)


def gitignore(path: Path):
    if path.is_dir():
        path = path / '.gitignore'
        if not path.exists():
            return PathSpec([])

    with open(path, 'r', encoding='utf-8') as file:
        return PathSpec.from_lines(GitWildMatchPattern,
                                   file.read().splitlines())


def _walk_worker(args: tuple[Path, PathSpec]):
    path, ignores = args
    if not path.is_dir():
        raise NotADirectoryError

    if ignores.match_file(path):
        logger.debug("Skipped %s", path)
        return [], []

    if (probe := path / '.gitignore').exists():
        ignores = PathSpec(ignores.patterns)
        ignores += gitignore(probe)

    '''if (probe := path / 'palgen.toml').exists():
            # skip subtrees of other projects but yield the project file
            logger.debug("Found another palgen project in `%s`. Skipping.")
            return [], [probe]'''

    folders = []
    entries = []
    for entry in path.iterdir():
        if ignores.match_file(entry):
            # honor .gitignore, skip this entry
            logger.debug("Skipped `%s`", entry)
            continue

        entries.append(entry)

        if entry.is_dir():
            folders.append((entry, ignores))
    return folders, entries


def walk(path: Path, ignores: PathSpec, jobs: Optional[int] = None) -> Iterable[Path]:
    tasks, output = _walk_worker((path, ignores))
    with Pool(jobs) as pool:
        while tasks:
            ret = pool.map(_walk_worker, tasks)
            tasks = []
            for new_tasks, new_output in ret:
                tasks.extend(new_tasks)
                output.extend(new_output)
        return output


class Sources(Pipeline):
    def __call__(self, state: list[Path]):
        assert isinstance(state, list[Path])
        yield from super().__call__(state)
