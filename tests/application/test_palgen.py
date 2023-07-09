from pathlib import Path

from palgen import Palgen


def test_load():
    root = Path(__file__).parent.parent / "mock"

    project = Palgen(root / "palgen.toml")
    assert project.root == root
    assert project == root / "palgen.toml"
    assert project == str(root / "palgen.toml")

    project_folder = Palgen(root)
    assert project_folder.root == root
    assert project_folder == root / "palgen.toml"
    assert project_folder == str(root / "palgen.toml")

    assert project == project_folder
