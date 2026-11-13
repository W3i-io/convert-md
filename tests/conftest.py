import shutil
from pathlib import Path

import pytest

SAMPLE = Path(__file__).resolve().parent.parent / "samples" / "Example.md"


@pytest.fixture(autouse=True)
def isolated_home(tmp_path, monkeypatch):
    """Keep logs and templates out of the real user folder."""
    monkeypatch.setenv("CONVERT_MD_HOME", str(tmp_path / "home"))


@pytest.fixture
def sample(tmp_path) -> Path:
    work = tmp_path / "work"
    work.mkdir()
    dest = work / "Example.md"
    shutil.copy(SAMPLE, dest)
    return dest
