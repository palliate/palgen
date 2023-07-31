import pytest
from pathlib import Path

from palgen import Palgen

root = Path(__file__).parent.parent / "examples" / "tutorial"


@pytest.mark.parametrize('path', [root / "palgen.toml", root])
def test_load(path: Path):
    project = Palgen(path)
    assert project.root == root
    assert project == root / "palgen.toml"
    assert project == str(root / "palgen.toml")
