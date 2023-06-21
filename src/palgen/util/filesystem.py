import logging
from multiprocessing.pool import Pool
from pathlib import Path
from typing import Iterable, Optional

from pathspec import PathSpec
from pathspec.patterns.gitwildmatch import GitWildMatchPattern

from palgen.util import Pipeline

logger = logging.getLogger(__name__)


class Sources(Pipeline):
    def __call__(self, state: list[Path]):
        assert isinstance(state, list)
        yield from super().__call__(state)


def gitignore(path: Path):
    """This function creates a PathSpec object from a .gitignore file.

    Args:
        path (Path): The path to the .gitignore file.

    Returns:
        PathSpec: A PathSpec object
    """
    if path.is_dir():
        path = path / '.gitignore'
        if not path.exists():
            return PathSpec([])

    try:
        with open(path, 'r', encoding='utf-8') as file:
            return PathSpec.from_lines(GitWildMatchPattern,
                                       file.read().splitlines())
    except FileNotFoundError:
        logger.exception("Error occurred while opening gitignore")
        return PathSpec([])


def walk(path: Path, ignores: PathSpec, jobs: Optional[int] = None) -> Iterable[Path]:
    """traverse a directory tree and return a list of Path objects
    representing the files and folders found in the directory.

    Args:
        path (Path): Path to the directory to traverse
        ignores (PathSpec): A PathSpec object representing the patterns to ignore when traversing the directory.
        jobs (Optional[int], optional): An integer representing the number of concurrent jobs to use for traversal.
                                        Defaults to None, meaning however many CPU cores the system has.

    Returns:
        Iterable[Path]: An iterable object representing the files and folders found in the directory.
    """
    tasks, output = _walk_worker((path, ignores))
    if jobs == 1:
        while tasks:
            _tasks = []
            for task in tasks:
                new_tasks, new_output = _walk_worker(task)
                _tasks.extend(new_tasks)
                output.extend(new_output)
            tasks = _tasks
        return output

    with Pool(processes=jobs) as pool:
        while tasks:
            ret = pool.map(_walk_worker, tasks)
            tasks = []
            for new_tasks, new_output in ret:
                tasks.extend(new_tasks)
                output.extend(new_output)
        return output


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

def find_backwards(filename: str, source_dir: Optional[Path] = None) -> Path:
    current_dir: Path = source_dir or Path.cwd()
    while current_dir:
        if (file_path := current_dir / filename).exists():
            return file_path
        current_dir = current_dir.parent

    raise FileNotFoundError(f"{filename} not found in parent directories.")
