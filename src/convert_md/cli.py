"""Command line for convert-md.

    convert-md --to docx Report.md            convert (also: pdf, xlsx, pptx, html, all, auto)
    convert-md --to docx,pdf Report.md        several formats
    convert-md --to md Contract.pdf Deck.pptx anything to Markdown
    convert-md setup                          add the right-click menus and Ctrl+Alt+M hotkey
    convert-md remove                         take them away again
    convert-md doctor                         check the installation
    convert-md templates                      create starter Word/PowerPoint style templates

`python -m convert_md ...` works the same way.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from convert_md import __version__
from convert_md.converter import OUT_FORMATS, ConversionError, available_pdf_engines, run
from convert_md.paths import data_dir, log_path, template_dir

APP_NAME = "convert-md"
COMMANDS = ("setup", "remove", "doctor", "templates")


# --------------------------------------------------------------------------- popup

def show_popup(done: list[Path], errors: list[str]) -> None:
    lines: list[str] = []
    if done:
        lines.append("Created:")
        lines += [f"   {p.name}" for p in done]
    if errors:
        if lines:
            lines.append("")
        lines.append("Problems:")
        lines += [f"   {e}" for e in errors]
        lines += ["", f"Details in {log_path()}"]
    message = "\n".join(lines) or "Nothing to do."
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
    except Exception:  # no Tk, or no display
        print(message)
        return
    root.withdraw()
    root.attributes("-topmost", True)
    if errors:
        messagebox.showwarning(APP_NAME, message, parent=root)
        root.destroy()
        return
    # Success: small window in the corner that closes itself after a few seconds.
    win = tk.Toplevel(root)
    win.title(APP_NAME)
    win.attributes("-topmost", True)
    win.resizable(False, False)
    tk.Label(win, text=message, justify="left", padx=18, pady=14, font=("Segoe UI", 10)).pack()
    tk.Button(win, text="OK", width=10, command=root.destroy).pack(pady=(0, 12))
    win.protocol("WM_DELETE_WINDOW", root.destroy)
    win.update_idletasks()
    x = win.winfo_screenwidth() - win.winfo_width() - 40
    y = win.winfo_screenheight() - win.winfo_height() - 90
    win.geometry(f"+{max(x, 0)}+{max(y, 0)}")
    root.after(4000, root.destroy)
    root.mainloop()


# --------------------------------------------------------------------------- convert

def convert_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="convert-md", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--version", action="version", version=f"convert-md {__version__}")
    parser.add_argument("--to", required=True,
                        help="md, auto, all, or a comma list of: " + ", ".join(OUT_FORMATS))
    parser.add_argument("--gui", action="store_true", help="show a popup with the result")
    parser.add_argument("files", nargs="+")
    args = parser.parse_args(argv)

    try:
        done, errors = run(args.files, args.to)
    except ConversionError as exc:
        done, errors = [], [str(exc)]

    if args.gui:
        show_popup(done, errors)
    else:
        for p in done:
            print(f"created  {p}")
        for e in errors:
            print(f"error    {e}", file=sys.stderr)
    return 1 if errors else 0


# --------------------------------------------------------------------------- commands

def _require_windows(what: str) -> bool:
    if sys.platform != "win32":
        print(f"{what} is only available on Windows. Conversions work everywhere: convert-md --to ...")
        return False
    return True


def cmd_setup(args: argparse.Namespace) -> int:
    if not _require_windows("setup"):
        return 1
    from convert_md import windows
    pythonw = windows.pythonw_path()
    print(f"convert-md {__version__}  (Python: {pythonw})")
    status = 0
    if not args.no_menus:
        windows.install_menus(pythonw)
        print("  right-click menus   installed (under 'Show more options' on Windows 11)")
    if not args.no_hotkey:
        if windows.autohotkey_available():
            script = windows.install_hotkey(pythonw, args.hotkey)
            print(f"  hotkey              installed and started ({script})")
        else:
            print("  hotkey              skipped: AutoHotkey v2 is not installed")
            print("                      install it with: winget install AutoHotkey.AutoHotkey -e")
            print("                      then run: convert-md setup")
            status = 2
    return status


def cmd_remove(args: argparse.Namespace) -> int:
    if not _require_windows("remove"):
        return 1
    from convert_md import windows
    windows.remove_menus()
    windows.remove_hotkey()
    print("convert-md menus and hotkey removed.")
    print(f"Templates and the log are kept in {data_dir()} (delete the folder if you don't need them).")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    rows: list[tuple[str, str, bool]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        rows.append((name, detail, ok))

    check("convert-md", True, __version__)
    check("Python", sys.version_info >= (3, 11), f"{sys.version.split()[0]}  {sys.executable}")
    try:
        import pypandoc
        check("Pandoc", True, pypandoc.get_pandoc_version())
    except Exception as exc:
        check("Pandoc", False, f"not working: {exc}")
    try:
        from importlib.metadata import version
        check("MarkItDown", True, version("markitdown"))
    except Exception as exc:
        check("MarkItDown", False, f"not installed: {exc}")

    engines = available_pdf_engines()
    if sys.platform == "win32":
        from convert_md import windows
        word = windows.word_available()
        check("PDF", word or bool(engines),
              "Microsoft Word" if word else (f"Pandoc engine: {engines[0]}" if engines
                                             else "no Word and no PDF engine (winget install Typst.Typst)"))
        cmd = windows.menu_command()
        expected = windows.pythonw_path()
        if cmd is None:
            check("Right-click menus", False, "not installed (run: convert-md setup)")
        elif expected.lower() not in cmd.lower():
            check("Right-click menus", False, f"point at a different Python: {cmd}  (run: convert-md setup)")
        else:
            check("Right-click menus", True, "installed")
        if windows.hotkey_installed():
            check("Hotkey", True, "installed")
        elif windows.autohotkey_available():
            check("Hotkey", False, "not installed (run: convert-md setup)")
        else:
            check("Hotkey", False, "AutoHotkey v2 not installed (optional)")
    else:
        check("PDF", bool(engines), f"Pandoc engine: {engines[0]}" if engines else "no PDF engine found")

    tdir = template_dir()
    found = [p.name for p in (tdir / "reference.docx", tdir / "reference.pptx", tdir / "style.css") if p.exists()]
    check("Templates", True, ", ".join(found) if found else "none (optional; convert-md templates)")
    check("Log", True, str(log_path()))

    width = max(len(r[0]) for r in rows)
    for name, detail, ok in rows:
        print(f"  {'OK ' if ok else '-- '} {name.ljust(width)}  {detail}")
    essential = {"Python", "Pandoc", "MarkItDown"}
    return 0 if all(ok for name, _, ok in rows if name in essential) else 1


def cmd_templates(args: argparse.Namespace) -> int:
    import subprocess
    import pypandoc
    tdir = template_dir()
    tdir.mkdir(parents=True, exist_ok=True)
    for name in ("reference.docx", "reference.pptx"):
        dest = tdir / name
        if dest.exists():
            print(f"  kept      {dest}")
            continue
        with open(dest, "wb") as fh:
            subprocess.run([pypandoc.get_pandoc_path(), "--print-default-data-file", name],
                           stdout=fh, check=True)
        print(f"  created   {dest}")
    print("Open these in Word / PowerPoint and change the styles (not the text).")
    print("Add style.css in the same folder to style HTML output.")
    if sys.platform == "win32":
        import os
        os.startfile(str(tdir))  # type: ignore[attr-defined]
    return 0


def command_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="convert-md")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("setup", help="add the right-click menus and the hotkey")
    p.add_argument("--no-menus", action="store_true", help="skip the right-click menus")
    p.add_argument("--no-hotkey", action="store_true", help="skip the AutoHotkey hotkey")
    p.add_argument("--hotkey", default="^!m",
                   help="AutoHotkey key combination, default ^!m (Ctrl+Alt+M)")
    p.set_defaults(func=cmd_setup)
    sub.add_parser("remove", help="remove the menus and hotkey").set_defaults(func=cmd_remove)
    sub.add_parser("doctor", help="check the installation").set_defaults(func=cmd_doctor)
    sub.add_parser("templates", help="create starter style templates").set_defaults(func=cmd_templates)
    args = parser.parse_args(argv)
    return args.func(args)


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] in COMMANDS:
        return command_main(argv)
    return convert_main(argv)


if __name__ == "__main__":
    sys.exit(main())
