"""Windows integration: right-click menus, Ctrl+Alt+M hotkey, status checks.

Everything is per-user (HKEY_CURRENT_USER and the user's Startup folder), so no
administrator rights are needed. The menus and hotkey call
    pythonw.exe -P -m convert_md --gui --to <format> "<file>"
-P stops Python adding the current folder to the import path, so a file named
convert_md.py sitting next to the document can't be run in place of convert-md.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from importlib import resources
from pathlib import Path

from convert_md.paths import data_dir

ROOT = r"HKEY_CURRENT_USER\Software\Classes\SystemFileAssociations"
MARKDOWN_EXTS = [".md", ".markdown"]
TO_MD_EXTS = [".docx", ".pdf", ".xlsx", ".xls", ".pptx", ".html", ".htm", ".csv", ".epub", ".msg"]
MD_MENU_KEY = "ConvertMd"
TO_MD_KEY = "ConvertMdToMarkdown"

# (key, label, --to value, separator_before)
MD_MENU = [
    ("1_docx", "Word (.docx)", "docx", False),
    ("2_pdf", "PDF (.pdf)", "pdf", False),
    ("3_xlsx", "Excel (.xlsx) - tables only", "xlsx", False),
    ("4_pptx", "PowerPoint (.pptx)", "pptx", False),
    ("5_html", "Web page (.html)", "html", False),
    ("6_all", "All formats", "all", True),
    ("7_auto", "As set in the file", "auto", False),
]

HOTKEY_SCRIPT = "convert-md-hotkey.ahk"
HOTKEY_CONFIG = "convert-md.ini"
SHORTCUT_NAME = "convert-md-hotkey.lnk"

# Names used by pre-1.0 private builds (then called md-convert); setup and remove clean them up.
LEGACY_MENU_KEYS = ["MdConvert", "MdConvertToMarkdown"]
LEGACY_SCRIPT = "md-convert-hotkey.ahk"
LEGACY_SHORTCUT = "md-convert-hotkey.lnk"
DEFAULT_HOTKEY = "^!m"   # Ctrl+Alt+M in AutoHotkey notation


# --------------------------------------------------------------------------- paths

def pythonw_path() -> str:
    """pythonw.exe next to the running Python (runs without a console window)."""
    exe = Path(sys.executable)
    candidate = exe.with_name("pythonw.exe")
    return str(candidate) if candidate.exists() else str(exe)


def startup_dir() -> Path:
    appdata = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
    return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def command_line(pythonw: str, target: str, file_arg: str = "%1") -> str:
    return f'"{pythonw}" -P -m convert_md --gui --to {target} "{file_arg}"'


# --------------------------------------------------------------------------- registry

def _esc(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def registry_files(pythonw: str) -> tuple[str, str]:
    """Return (install, uninstall) .reg file text for the right-click menus."""
    lines = ["Windows Registry Editor Version 5.00", "",
             "; convert-md right-click menus (current user only)", ""]
    remove = ["Windows Registry Editor Version 5.00", "", "; Removes the convert-md right-click menus", ""]

    legacy = []
    for ext in MARKDOWN_EXTS + TO_MD_EXTS:
        legacy += [f"[-{ROOT}\\{ext}\\shell\\{key}]" for key in LEGACY_MENU_KEYS]
    lines += ["; remove menus left by pre-1.0 builds"] + legacy + [""]
    remove += legacy + [""]

    for ext in MARKDOWN_EXTS:
        base = f"{ROOT}\\{ext}\\shell\\{MD_MENU_KEY}"
        lines += [f"[{base}]", '"MUIVerb"="Convert to"', '"SubCommands"=""', ""]
        for key, label, target, sep in MD_MENU:
            lines += [f"[{base}\\shell\\{key}]", f'"MUIVerb"="{_esc(label)}"']
            if sep:
                lines.append('"CommandFlags"=dword:00000020')
            lines += ["", f"[{base}\\shell\\{key}\\command]", f'@="{_esc(command_line(pythonw, target))}"', ""]
        remove += [f"[-{base}]", ""]

    for ext in TO_MD_EXTS:
        base = f"{ROOT}\\{ext}\\shell\\{TO_MD_KEY}"
        lines += [f"[{base}]", '"MUIVerb"="Convert to Markdown"', "",
                  f"[{base}\\command]", f'@="{_esc(command_line(pythonw, "md"))}"', ""]
        remove += [f"[-{base}]", ""]

    return "\r\n".join(lines), "\r\n".join(remove)


def _reg_import(text: str) -> None:
    fd, name = tempfile.mkstemp(suffix=".reg")
    os.close(fd)
    try:
        Path(name).write_text(text, encoding="utf-16")  # regedit expects UTF-16 with BOM
        subprocess.run(["reg", "import", name], check=True, capture_output=True)
    finally:
        os.unlink(name)


def install_menus(pythonw: str | None = None) -> None:
    _reg_import(registry_files(pythonw or pythonw_path())[0])


def remove_menus() -> None:
    _reg_import(registry_files(pythonw_path())[1])


def menu_command() -> str | None:
    """The command the 'Convert to → Word' entry currently runs, or None if not installed."""
    import winreg
    key = rf"Software\Classes\SystemFileAssociations\.md\shell\{MD_MENU_KEY}\shell\1_docx\command"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key) as k:
            return winreg.QueryValueEx(k, "")[0]
    except OSError:
        return None


# --------------------------------------------------------------------------- hotkey

def autohotkey_available() -> bool:
    """True if .ahk files are associated with a program (AutoHotkey is installed)."""
    import winreg
    for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        try:
            with winreg.OpenKey(root, r"Software\Classes\.ahk"):
                return True
        except OSError:
            continue
    return False


def hotkey_config(pythonw: str, hotkey: str) -> str:
    return f"[convert-md]\r\npythonw={pythonw}\r\nhotkey={hotkey}\r\n"


def stop_hotkey() -> None:
    """End any running copy of the hotkey script (current or pre-1.0), wherever it was started from."""
    ps = ("Get-CimInstance Win32_Process -Filter \"Name LIKE 'AutoHotkey%'\" | "
          f"Where-Object {{ $_.CommandLine -like '*{HOTKEY_SCRIPT}*' -or $_.CommandLine -like '*{LEGACY_SCRIPT}*' }} | "
          "Invoke-CimMethod -MethodName Terminate | Out-Null")
    subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
                   capture_output=True, check=False)


def _create_shortcut(link: Path, target: Path) -> None:
    import win32com.client
    shell = win32com.client.Dispatch("WScript.Shell")
    sc = shell.CreateShortcut(str(link))
    sc.TargetPath = str(target)
    sc.WorkingDirectory = str(target.parent)
    sc.Description = "convert-md hotkey"
    sc.Save()


def install_hotkey(pythonw: str | None = None, hotkey: str = DEFAULT_HOTKEY) -> Path:
    """Copy the hotkey script to the data folder, write its settings, add it to Startup and start it."""
    folder = data_dir()
    folder.mkdir(parents=True, exist_ok=True)
    script = folder / HOTKEY_SCRIPT
    script.write_bytes(resources.files("convert_md").joinpath(HOTKEY_SCRIPT).read_bytes())
    (folder / HOTKEY_CONFIG).write_text(hotkey_config(pythonw or pythonw_path(), hotkey), encoding="utf-16")
    stop_hotkey()
    startup = startup_dir()
    startup.mkdir(parents=True, exist_ok=True)
    _unlink(startup / LEGACY_SHORTCUT)
    _create_shortcut(startup / SHORTCUT_NAME, script)
    os.startfile(str(script))  # type: ignore[attr-defined]
    return script


def _unlink(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def remove_hotkey() -> None:
    stop_hotkey()
    for path in (startup_dir() / SHORTCUT_NAME, startup_dir() / LEGACY_SHORTCUT,
                 data_dir() / HOTKEY_SCRIPT, data_dir() / HOTKEY_CONFIG):
        _unlink(path)


def hotkey_installed() -> bool:
    return (startup_dir() / SHORTCUT_NAME).exists() and (data_dir() / HOTKEY_SCRIPT).exists()


# --------------------------------------------------------------------------- word

def word_available() -> bool:
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"Word.Application\CLSID"):
            return True
    except OSError:
        return False
