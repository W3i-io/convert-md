# Installing, updating and removing convert-md

For what convert-md does and how to use it, see [README.md](README.md).

## What gets installed where

Everything is for the current Windows account only; no administrator rights are needed.

| Item | Location |
|---|---|
| convert-md code and libraries | Your Python's site-packages (installed by pip) |
| Right-click menus | `HKEY_CURRENT_USER\Software\Classes\SystemFileAssociations\<ext>\shell\ConvertMd` and `...\ConvertMdToMarkdown` |
| Hotkey script and its settings | `%LOCALAPPDATA%\ConvertMd\convert-md-hotkey.ahk` and `convert-md.ini` |
| Hotkey start at login | `convert-md-hotkey.lnk` in your Startup folder (`shell:startup`) |
| Style templates | `%LOCALAPPDATA%\ConvertMd\templates\` |
| Log | `%LOCALAPPDATA%\ConvertMd\convert-md.log` |

The menus and hotkey run `pythonw.exe -P -m convert_md ...` using the Python that ran setup.
The download folder isn't used after installation, so you can move or delete it.

---

## 1. Install

### Option A: installer script (recommended)

1. **Python 3.11 or newer**, the python.org build:

   ```powershell
   winget install --id Python.Python.3.12 -e --scope user
   ```

   Open a new PowerShell window and check `py --version` works. If typing `python` opens the
   Microsoft Store, turn that off in **Settings → Apps → Advanced app settings → App execution aliases**.

2. **Get convert-md**: download **Source code (zip)** from the
   [latest release](https://github.com/W3i-io/convert-md/releases/latest) and extract it, or

   ```powershell
   git clone https://github.com/W3i-io/convert-md
   ```

3. **Run the installer** from that folder:

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\install.ps1
   ```

   | Option | Effect |
   |---|---|
   | `-NoHotkey` | Right-click menus only; no AutoHotkey |
   | `-Yes` | Install AutoHotkey without asking if it's missing |
   | `-Hotkey '^!k'` | Use a different key (AutoHotkey notation: `^` Ctrl, `!` Alt, `+` Shift, `#` Win) |
   | `-SkipTest` | Skip the test conversions |

### Option B: pip

```powershell
py -m pip install convert-md
py -m convert_md setup
```

For the hotkey, install AutoHotkey first (`winget install AutoHotkey.AutoHotkey -e`), then run setup.
`pipx install convert-md` followed by `convert-md setup` also works.

### PDF output

PDFs are made through Microsoft Word when it's installed. Without Word, install a PDF engine:

```powershell
winget install Typst.Typst
```

### Check it works

```powershell
py -m convert_md doctor
```

| Check | Expected |
|---|---|
| `doctor` | `OK` for Python, Pandoc, MarkItDown, PDF and Right-click menus (and Hotkey if installed) |
| Right-click a `.md` file → **Show more options** | **Convert to** submenu |
| Right-click a `.docx` → **Show more options** | **Convert to Markdown** |
| Select a file in File Explorer, press **Ctrl+Alt+M** | Convert menu at the mouse pointer |

---

## 2. Update

From a new download or `git pull` in your clone, run the installer again:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

With pip:

```powershell
py -m pip install --upgrade convert-md
py -m convert_md setup
```

Setup replaces the menus, hotkey script and Startup shortcut, and restarts the hotkey.

## 3. Moving to a new Python version

The menus point at a specific Python. After installing a new Python version (for example 3.12 to 3.13),
run the installer again, or `py -m pip install convert-md` followed by `py -m convert_md setup`.
`doctor` reports **Right-click menus: point at a different Python** when this is needed.

## 4. Uninstall

```powershell
powershell -ExecutionPolicy Bypass -File .\uninstall.ps1
```

This removes the right-click menus, stops the hotkey and removes it from Startup.

| Option | Also removes |
|---|---|
| `-RemovePackage` | The convert-md Python package |
| `-RemoveData` | `%LOCALAPPDATA%\ConvertMd`: your templates and the log |

Without the script: `py -m convert_md remove`, then `py -m pip uninstall convert-md`.
Python and AutoHotkey are left installed; remove them in **Settings → Apps** if nothing else uses them.

---

## Troubleshooting

Start with `py -m convert_md doctor`; it names most problems.

| Symptom | Likely cause | Fix |
|---|---|---|
| Menu item does nothing | Menus point at a Python that has moved or been removed | Run the installer again |
| Popup says something failed | See the message, then the log | `%LOCALAPPDATA%\ConvertMd\convert-md.log` |
| Ctrl+Alt+M does nothing | Hotkey not running | Double-click `%LOCALAPPDATA%\ConvertMd\convert-md-hotkey.ahk`, or run setup again |
| "convert-md can't find Python" message at login | Python was upgraded or removed | Run the installer again |
| Ctrl+Alt+M on the desktop shows a tip instead of a menu | The hotkey works in File Explorer windows only | Right-click the file instead |
| PDF option fails | No Word and no PDF engine | `winget install Typst.Typst` |
| `convert-md` is not recognised | pip's Scripts folder isn't on PATH | Use `py -m convert_md` instead |
| Script blocked: "running scripts is disabled" | PowerShell execution policy | Use `powershell -ExecutionPolicy Bypass -File .\install.ps1` |
| `python` opens the Microsoft Store | Windows app execution alias | Turn it off (step 1) and use `py` |
| Menus missing on Windows 11 | They're in the classic menu | **Show more options**, Shift + right-click, or Shift + F10 |
