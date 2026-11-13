"""Where convert-md keeps its per-user files: log, templates, hotkey script and its settings."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def data_dir() -> Path:
    """Per-user data folder, e.g. %LOCALAPPDATA%\\ConvertMd on Windows.

    Set CONVERT_MD_HOME to use a different folder.
    """
    override = os.environ.get("CONVERT_MD_HOME")
    if override:
        return Path(override)
    if sys.platform == "win32" and os.environ.get("LOCALAPPDATA"):
        return Path(os.environ["LOCALAPPDATA"]) / "ConvertMd"
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(base) / "convert-md"


def log_path() -> Path:
    return data_dir() / "convert-md.log"


def template_dir() -> Path:
    return data_dir() / "templates"
