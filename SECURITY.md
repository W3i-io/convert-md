# Security policy

## Supported versions

Security fixes are made in the latest release. Please update before reporting.

| Version | Supported |
|---|---|
| 1.x (latest) | Yes |
| Earlier | No |

## Reporting a vulnerability

Please report security problems privately, not in a public issue:
on GitHub, open the repository's **Security** tab and choose **Report a vulnerability**.

Include the convert-md version (`convert-md --version`), your Windows and Python versions, and the steps
or a sample file that shows the problem. We aim to acknowledge reports within a week and will keep you
informed while a fix is prepared. Please give us a reasonable chance to release a fix before disclosing
the issue publicly.

## How convert-md behaves

| Area | Behaviour |
|---|---|
| Network | convert-md makes no network requests of its own and sends nothing anywhere. Pandoc downloads images that a Markdown file links to by URL when it embeds them in the output. |
| Permissions | Installs and runs as the current user. No administrator rights; registry changes are limited to `HKEY_CURRENT_USER\Software\Classes\SystemFileAssociations`. |
| Startup | The optional hotkey adds one shortcut to the user's Startup folder, which runs an AutoHotkey script in `%LOCALAPPDATA%\ConvertMd`. |
| Files | Reads only the files you choose. Writes new files next to them and never overwrites existing files. Writes a log of file paths and errors to `%LOCALAPPDATA%\ConvertMd`. |
| Code loading | The menus and hotkey run Python with `-P`, so a file named `convert_md.py` placed in a document's folder can't be run in place of convert-md. MarkItDown plugins are disabled. |
| PDF through Word | Word opens only the `.docx` that convert-md has just generated, read-only. Macros in your source documents are never run. |

## Converting untrusted documents

convert-md passes documents to Pandoc, MarkItDown and the libraries they use (for example PDF and Office
parsers). A deliberately malformed document could exploit a bug in one of those libraries. Keep convert-md
and its dependencies up to date (run the installer again, or `py -m pip install --upgrade convert-md`),
and take the same care with unknown files as you would when opening them in any other program.
