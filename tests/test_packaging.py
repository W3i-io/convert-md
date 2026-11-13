"""Checks that the project files agree with each other."""

import re
import subprocess
import sys
import tomllib
from importlib import resources
from pathlib import Path

import convert_md
from convert_md.windows import HOTKEY_SCRIPT

ROOT = Path(__file__).resolve().parent.parent
# A real user folder such as C:\Users\someone\ (placeholders like <you> are fine)
PERSONAL_PATH = re.compile(r"[a-z]:\\users\\[a-z0-9]", re.I)


def _req_lines(lines):
    return sorted(re.sub(r"\s+", "", l.replace('"', "'")) for l in lines
                  if l.strip() and not l.strip().startswith("#"))


def test_requirements_match_pyproject():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    reqs = (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
    assert _req_lines(project["dependencies"]) == _req_lines(reqs)


def test_changelog_has_current_version():
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"## [{convert_md.__version__}]" in changelog


def test_hotkey_script_is_packaged():
    script = resources.files("convert_md").joinpath(HOTKEY_SCRIPT)
    text = script.read_text(encoding="utf-8")
    assert "#Requires AutoHotkey v2.0" in text
    assert "-P -m convert_md" in text
    assert not PERSONAL_PATH.search(text)


def test_no_personal_paths_in_repo():
    skip = {".git", ".venv", "build", "dist", ".pytest_cache", "__pycache__", "tests"}
    for path in ROOT.rglob("*"):
        if path.is_file() and not skip.intersection(path.relative_to(ROOT).parts) \
                and path.suffix in {".py", ".md", ".ahk", ".ps1", ".toml", ".txt", ".yml", ".cfg"}:
            text = path.read_text(encoding="utf-8", errors="ignore")
            assert not PERSONAL_PATH.search(text), path


def test_module_runs_with_safe_path(sample, tmp_path):
    """The menus run `python -P -m convert_md` from the document's folder.
    A planted convert_md.py there must not be imported."""
    marker = tmp_path / "hijacked"
    (sample.parent / "convert_md.py").write_text(
        f"open(r'{marker}', 'w').write('x')\n", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-P", "-m", "convert_md", "--to", "html", sample.name],
        cwd=sample.parent, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert not marker.exists()
    assert (sample.parent / "Example.html").exists()
