import os
import sys

import pytest

from convert_md import windows


def test_registry_text_commands():
    pythonw = r"C:\Program Files\Python312\pythonw.exe"
    install, uninstall = windows.registry_files(pythonw)
    assert install.startswith("Windows Registry Editor Version 5.00")
    expected = ('@="\\"C:\\\\Program Files\\\\Python312\\\\pythonw.exe\\" -P -m convert_md '
                '--gui --to docx \\"%1\\""')
    assert expected in install
    for _, _, target, _ in windows.MD_MENU:
        assert f"--to {target} " in install
    for ext in windows.MARKDOWN_EXTS:
        assert f"[-{windows.ROOT}\\{ext}\\shell\\{windows.MD_MENU_KEY}]" in uninstall
    for ext in windows.TO_MD_EXTS:
        assert f"{ext}\\shell\\{windows.TO_MD_KEY}]" in install
        assert f"[-{windows.ROOT}\\{ext}\\shell\\{windows.TO_MD_KEY}]" in uninstall
    assert "\r\n" in install
    for key in windows.LEGACY_MENU_KEYS:   # pre-1.0 menus are removed on install and uninstall
        assert f"[-{windows.ROOT}\\.md\\shell\\{key}]" in install
        assert f"[-{windows.ROOT}\\.pdf\\shell\\{key}]" in uninstall


def test_command_line():
    assert windows.command_line("p.exe", "md", "C:\\a b\\c.pdf") == '"p.exe" -P -m convert_md --gui --to md "C:\\a b\\c.pdf"'


def test_hotkey_config():
    assert windows.hotkey_config("C:\\py\\pythonw.exe", "^!m") == \
        "[convert-md]\r\npythonw=C:\\py\\pythonw.exe\r\nhotkey=^!m\r\n"


@pytest.mark.skipif(sys.platform != "win32" or os.environ.get("CONVERT_MD_REGISTRY_TEST") != "1",
                    reason="changes the real registry; runs on CI with CONVERT_MD_REGISTRY_TEST=1")
def test_install_and_remove_menus():
    windows.install_menus()
    try:
        cmd = windows.menu_command()
        assert cmd is not None and "-P -m convert_md" in cmd
        assert windows.pythonw_path().lower() in cmd.lower()
    finally:
        windows.remove_menus()
    assert windows.menu_command() is None
