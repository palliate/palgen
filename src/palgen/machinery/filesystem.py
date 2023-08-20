import logging
from multiprocessing.pool import Pool
from pathlib import Path
from typing import Optional

from pathspec import PathSpec
from pathspec.patterns.gitwildmatch import GitWildMatchPattern

_logger = logging.getLogger(__name__)


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
        _logger.exception("Error occurred while opening gitignore")
        return PathSpec([])


def walk(path: Path, ignores: PathSpec = PathSpec([]), jobs: Optional[int] = None) -> list[Path]:
    """Traverse a directory tree and return a list of Path objects
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
    with Pool(processes=jobs) as pool:
        while tasks:
            ret = pool.imap_unordered(_walk_worker, tasks.copy())
            tasks = []
            for new_tasks, new_output in ret:
                tasks.extend(new_tasks)
                output.extend(new_output)

        return output


def discover(paths: list[Path], ignores: Optional[PathSpec] = None, jobs: Optional[int] = None) -> list[Path]:
    """Walks through every folder in :code:`paths`, returns list of all non-ignored files and folders.

    Args:
        paths (list[Path]): List of paths to walk through
        ignores (Optional[PathSpec], optional): Patterns to match files and folders which ought to be ignored.
            You probably want to use :code:`gitignore(...)` to get a :code:`PathSpec` object for this parameter.
        jobs (Optional[int], optional): Amount of jobs to run this at.
            Defaults to None, meaning however many cpu cores the system has.

    Returns:
        list[Path]: _description_
    """
    if ignores is None:
        ignores = PathSpec([])

    return [element
            for path in paths
            for element in walk(path, ignores, jobs)]


def find_backwards(filename: str, source_dir: Optional[Path] = None) -> Path:
    """Traverse up the folder hierarchy until any of the parent folders contain the file we're looking for.

    Args:
        filename (str): Name of the file to be found
        source_dir (Optional[Path], optional): What folder to start searching in.
            Defaults to the current working directory.

    Raises:
        FileNotFoundError: File wasn't found

    Returns:
        Path: Path to the file if it was found
    """
    current_dir: Path = source_dir or Path.cwd()
    while current_dir:
        if (file_path := current_dir / filename).exists():
            return file_path
        current_dir = current_dir.parent

    raise FileNotFoundError(f"{filename} not found in parent directories.")


def _walk_worker(args: tuple[Path, PathSpec]) -> tuple[list[tuple[Path, PathSpec]], list[Path]]:
    path, ignores = args
    if not path.is_dir():
        _logger.warning("%s is not a directory.", path)

    if ignores.match_file(path):
        return [], []

    if (probe := path / '.gitignore').exists():
        ignores = PathSpec(ignores.patterns)
        ignores += gitignore(probe)

    folders: list[tuple[Path, PathSpec]] = []
    entries: list[Path] = []
    for entry in path.iterdir():
        if ignores.match_file(entry):
            # honor .gitignore, skip this entry
            continue

        entries.append(entry)

        if entry.is_dir():
            folders.append((entry, ignores))
    return folders, entries
