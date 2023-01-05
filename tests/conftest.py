import sys

import pytest


@pytest.fixture(scope="session")
def mock_fixture():
    yield None


@pytest.fixture
def capture_stdout(monkeypatch):
    ret = {"buffer": "", "calls": 0}
    def fake_write(s):
        ret["buffer"] += s
        ret["calls"] += 1

    monkeypatch.setattr(sys.stdout, 'write', fake_write)
    return ret
