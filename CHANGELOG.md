# Changelog

All notable changes to convert-md are listed here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

## [1.0.0] - 2026-11-13

First public release.

### Added
- Right-click **Convert to** submenu on `.md` and `.markdown` files: Word, PDF, Excel (tables only),
  PowerPoint, Web page, All formats, and "As set in the file".
- Right-click **Convert to Markdown** on `.docx .pdf .xlsx .xls .pptx .html .htm .csv .epub .msg`.
- **Ctrl+Alt+M** hotkey in File Explorer (needs AutoHotkey v2). It reads only the active Explorer tab
  and splits mixed selections: Markdown files go out, other files come in.
- "As set in the file": formats from `outputs:` front-matter or the filename (`Report.docx.pdf.md`).
- PDF output through Microsoft Word when installed, otherwise a Pandoc PDF engine.
- Excel output with one sheet per table, named after the heading above it; numbers, currency,
  percentages and bracketed negatives become real numbers; header row frozen and filtered.
- House styling with `reference.docx`, `reference.pptx` and `style.css` in the templates folder;
  `convert-md templates` creates starter copies.
- `convert-md setup`, `remove` and `doctor` commands; `install.ps1` and `uninstall.ps1`.
- Existing files are never overwritten; repeat runs write `Report (1).docx`.
- Success/problem popup, and a log at `%LOCALAPPDATA%\ConvertMd\convert-md.log`.

### Security
- Menus and hotkey run Python with `-P`, so a file named `convert_md.py` in the document's folder
  can't be run in place of convert-md.
- Per-user install only: registry changes are under `HKEY_CURRENT_USER`; no administrator rights.

### Upgrading from a pre-release copy
Earlier private copies were called md-convert. They ran `md_convert.py` from the project folder and
used `install.reg`, `make_reg.py` and a hand-edited `md-convert-hotkey.ahk`. Run `install.ps1`: it
removes the old md-convert menus, Startup shortcut and running hotkey and installs convert-md in their
place. The old files are no longer used and can be deleted, as can `%LOCALAPPDATA%\MdConvert`
(it only holds the old log).

[Unreleased]: https://github.com/W3i-io/convert-md/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/W3i-io/convert-md/releases/tag/v1.0.0
