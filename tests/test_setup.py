"""convert-md setup: the hotkey is installed by default, installing AutoHotkey first if needed.
The Windows calls are replaced with fakes, so these tests run anywhere and change nothing."""

import pytest

from convert_md import cli, windows


@pytest.fixture
def fake_windows(monkeypatch):
    calls = []
    state = {"ahk": False, "winget_ok": True}

    monkeypatch.setattr(cli, "_is_windows", lambda: True)
    monkeypatch.setattr(windows, "pythonw_path", lambda: r"C:\py\pythonw.exe")
    monkeypatch.setattr(windows, "install_menus", lambda pythonw=None: calls.append("menus"))
    monkeypatch.setattr(windows, "autohotkey_available", lambda: state["ahk"])

    def install_autohotkey():
        calls.append("install-autohotkey")
        if state["winget_ok"]:
            state["ahk"] = True
            return True, ""
        return False, "winget is not available"

    monkeypatch.setattr(windows, "install_autohotkey", install_autohotkey)
    monkeypatch.setattr(windows, "install_hotkey",
                        lambda pythonw=None, hotkey="^!m": calls.append(f"hotkey {hotkey}") or "script.ahk")
    return calls, state


def test_setup_installs_autohotkey_then_hotkey_by_default(fake_windows, capsys):
    calls, _ = fake_windows
    assert cli.main(["setup"]) == 0
    assert calls == ["menus", "install-autohotkey", "hotkey ^!m"]
    assert "AutoHotkey v2       installed" in capsys.readouterr().out


def test_setup_uses_existing_autohotkey(fake_windows):
    calls, state = fake_windows
    state["ahk"] = True
    assert cli.main(["setup", "--hotkey", "^!k"]) == 0
    assert calls == ["menus", "hotkey ^!k"]


def test_setup_keeps_menus_when_autohotkey_cannot_be_installed(fake_windows, capsys):
    calls, state = fake_windows
    state["winget_ok"] = False
    assert cli.main(["setup"]) == 2
    assert calls == ["menus", "install-autohotkey"]
    assert "could not be installed (winget is not available)" in capsys.readouterr().out


def test_setup_no_hotkey_skips_autohotkey(fake_windows):
    calls, _ = fake_windows
    assert cli.main(["setup", "--no-hotkey"]) == 0
    assert calls == ["menus"]


def test_conversion_reminds_to_run_setup(sample, monkeypatch, capsys):
    monkeypatch.setattr(cli, "_is_windows", lambda: True)
    monkeypatch.setattr(windows, "menu_command", lambda: None)
    assert cli.main(["--to", "html", str(sample)]) == 0
    assert "convert-md setup" in capsys.readouterr().err


def test_no_reminder_once_set_up(sample, monkeypatch, capsys):
    monkeypatch.setattr(cli, "_is_windows", lambda: True)
    monkeypatch.setattr(windows, "menu_command", lambda: "pythonw -P -m convert_md ...")
    assert cli.main(["--to", "html", str(sample)]) == 0
    assert "setup" not in capsys.readouterr().err
