"""Conversion engine.

Markdown -> Word, PDF, Excel, PowerPoint, HTML   (Pandoc; Excel is built from the tables)
Anything -> Markdown                             (Microsoft MarkItDown)
"""

from __future__ import annotations

import datetime as _dt
import re
import shutil
import sys
import tempfile
import traceback
from pathlib import Path

from convert_md.paths import log_path, template_dir

OUT_FORMATS = ["docx", "pdf", "xlsx", "pptx", "html"]
FORMAT_ALIASES = {"word": "docx", "doc": "docx", "excel": "xlsx", "xls": "xlsx",
                  "powerpoint": "pptx", "ppt": "pptx", "htm": "html"}
MD_SUFFIXES = {".md", ".markdown", ".mdown", ".mkd"}
PDF_ENGINES = ["typst", "xelatex", "lualatex", "pdflatex", "weasyprint", "wkhtmltopdf"]


class ConversionError(Exception):
    """A conversion failed for a reason worth showing the user."""


# --------------------------------------------------------------------------- logging

def log(message: str) -> None:
    try:
        path = log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        stamp = _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(f"{stamp}  {message}\n")
    except OSError:
        pass


# --------------------------------------------------------------------------- helpers

def unique_path(path: Path) -> Path:
    """Return path, or 'name (1).ext', 'name (2).ext'... if it already exists."""
    if not path.exists():
        return path
    n = 1
    while True:
        candidate = path.with_name(f"{path.stem} ({n}){path.suffix}")
        if not candidate.exists():
            return candidate
        n += 1


def normalise_formats(raw: list[str]) -> list[str]:
    out: list[str] = []
    for item in raw:
        fmt = item.strip().lower().lstrip(".")
        fmt = FORMAT_ALIASES.get(fmt, fmt)
        if fmt == "all":
            for f in OUT_FORMATS:
                if f not in out:
                    out.append(f)
        elif fmt in OUT_FORMATS and fmt not in out:
            out.append(fmt)
        elif fmt and fmt not in OUT_FORMATS:
            raise ConversionError(f"Unknown format '{item}'. Use: {', '.join(OUT_FORMATS)}, all.")
    return out


def auto_formats(md_path: Path, text: str) -> tuple[list[str], str]:
    """Work out formats from front-matter ('outputs: [docx, pdf]') or the filename
    ('Report.docx.pdf.md'). Returns (formats, output stem). Defaults to Word."""
    parts = md_path.stem.split(".")
    from_name: list[str] = []
    while len(parts) > 1:
        candidate = FORMAT_ALIASES.get(parts[-1].lower(), parts[-1].lower())
        if candidate in OUT_FORMATS or candidate == "all":
            from_name.insert(0, candidate)
            parts.pop()
        else:
            break
    clean_stem = ".".join(parts)

    fm = re.match(r"\A---\s*\n(.*?)\n(?:---|\.\.\.)\s*\n", text, re.S)
    if fm:
        m = re.search(r"^outputs\s*:\s*(.+)$", fm.group(1), re.M)
        if m:
            items = re.split(r"[\s,\[\]]+", m.group(1))
            formats = normalise_formats([i for i in items if i])
            if formats:
                return formats, clean_stem
    if from_name:
        return normalise_formats(from_name), clean_stem
    return ["docx"], clean_stem


# --------------------------------------------------------------------------- pandoc

def _pandoc():
    try:
        import pypandoc
    except ImportError as exc:
        raise ConversionError("pypandoc is not installed. Reinstall convert-md.") from exc
    return pypandoc


def _common_args(src: Path) -> list[str]:
    return ["--standalone", f"--resource-path={src.parent}"]


def to_docx(src: Path, dest: Path) -> Path:
    args = _common_args(src)
    ref = template_dir() / "reference.docx"
    if ref.exists():
        args.append(f"--reference-doc={ref}")
    _pandoc().convert_file(str(src), "docx", format="markdown", outputfile=str(dest), extra_args=args)
    return dest


def to_pptx(src: Path, dest: Path) -> Path:
    args = _common_args(src)
    ref = template_dir() / "reference.pptx"
    if ref.exists():
        args.append(f"--reference-doc={ref}")
    _pandoc().convert_file(str(src), "pptx", format="markdown", outputfile=str(dest), extra_args=args)
    return dest


def to_html(src: Path, dest: Path) -> Path:
    args = _common_args(src) + ["--embed-resources", f"--metadata=pagetitle:{dest.stem}"]
    css = template_dir() / "style.css"
    if css.exists():
        args.append(f"--css={css}")
    _pandoc().convert_file(str(src), "html5", format="markdown", outputfile=str(dest), extra_args=args)
    return dest


# --------------------------------------------------------------------------- pdf

def _word_docx_to_pdf(docx: Path, pdf: Path) -> bool:
    """Use installed Microsoft Word to save a .docx as PDF. False if Word isn't usable."""
    if sys.platform != "win32":
        return False
    try:
        import pythoncom
        import win32com.client
    except ImportError:
        return False
    word = None
    pythoncom.CoInitialize()
    try:
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0
        doc = word.Documents.Open(str(docx.resolve()), ReadOnly=True, AddToRecentFiles=False)
        try:
            doc.SaveAs2(str(pdf.resolve()), FileFormat=17)  # 17 = wdFormatPDF
        finally:
            doc.Close(SaveChanges=0)
        return pdf.exists()
    except Exception as exc:  # Word missing, licence prompt, COM error...
        log(f"Word PDF export failed, falling back to a Pandoc PDF engine: {exc}")
        return False
    finally:
        if word is not None:
            try:
                word.Quit()
            except Exception:
                pass
        pythoncom.CoUninitialize()


def available_pdf_engines() -> list[str]:
    return [e for e in PDF_ENGINES if shutil.which(e)]


def to_pdf(src: Path, dest: Path, docx_hint: Path | None = None) -> Path:
    # 1. Microsoft Word: matches the Word output and needs no extra installs.
    if sys.platform == "win32":
        with tempfile.TemporaryDirectory() as tmp:
            docx = docx_hint if docx_hint and docx_hint.exists() else to_docx(src, Path(tmp) / "temp.docx")
            if _word_docx_to_pdf(docx, dest):
                return dest
    # 2. Pandoc with whichever PDF engine is installed.
    for engine in available_pdf_engines():
        args = _common_args(src) + [f"--pdf-engine={engine}"]
        if engine.endswith("latex"):
            args += ["-V", "geometry:margin=2cm"]
        _pandoc().convert_file(str(src), "pdf", format="markdown", outputfile=str(dest), extra_args=args)
        return dest
    raise ConversionError(
        "No way to make a PDF was found. Install Microsoft Word, "
        "or a PDF engine such as Typst: winget install Typst.Typst")


# --------------------------------------------------------------------------- excel

_NUM = re.compile(r"^\(?-?[$€£¥]?\s?-?[\d,]*\.?\d+\)?%?$")


def cell_value(text: str):
    """Turn '1,234', '$12.50', '(300)', '45%' into numbers; leave other text alone.
    Returns (value, number_format or None)."""
    t = text.strip()
    if not t or not _NUM.match(t) or not re.search(r"\d", t):
        return t, None
    negative = t.startswith("(") and t.endswith(")")
    pct = t.endswith("%")
    core = re.sub(r"[()$€£¥%,\s]", "", t)
    try:
        num = float(core)
    except ValueError:
        return t, None
    if negative:
        num = -abs(num)
    if pct:
        return num / 100, "0.0%" if "." in core else "0%"
    if num.is_integer() and "." not in core:
        return int(num), "#,##0" if "," in t else None
    return num, "#,##0.00" if "," in t else None


def _sheet_title(raw: str, used: set[str]) -> str:
    title = re.sub(r"[\[\]:*?/\\]", "", raw).strip()[:31] or "Table"
    base, n = title, 2
    while title.lower() in used:
        suffix = f" ({n})"
        title = base[: 31 - len(suffix)] + suffix
        n += 1
    used.add(title.lower())
    return title


def to_xlsx(src: Path, dest: Path) -> Path:
    from bs4 import BeautifulSoup
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    html = _pandoc().convert_file(str(src), "html5", format="markdown")
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")
    if not tables:
        raise ConversionError("No tables found in this Markdown file, so there is nothing to put in Excel.")

    wb = Workbook()
    wb.remove(wb.active)
    used: set[str] = set()
    header_fill = PatternFill("solid", fgColor="DDEBF7")

    for i, table in enumerate(tables, start=1):
        caption = table.find("caption")
        heading = table.find_previous(re.compile(r"^h[1-6]$"))
        name = (caption.get_text(" ", strip=True) if caption else
                heading.get_text(" ", strip=True) if heading else f"Table {i}")
        ws = wb.create_sheet(_sheet_title(name, used))

        rows = table.find_all("tr")
        widths: dict[int, int] = {}
        first_is_header = False
        for r, tr in enumerate(rows, start=1):
            cells = tr.find_all(["th", "td"])
            is_header = tr.find_parent("thead") is not None or all(c.name == "th" for c in cells)
            if r == 1:
                first_is_header = is_header
            for c, cell in enumerate(cells, start=1):
                text = cell.get_text(" ", strip=True)
                value, fmt = (text, None) if is_header else cell_value(text)
                target = ws.cell(row=r, column=c, value=value)
                if fmt:
                    target.number_format = fmt
                if is_header:
                    target.font = Font(bold=True)
                    target.fill = header_fill
                    target.alignment = Alignment(vertical="center", wrap_text=True)
                widths[c] = max(widths.get(c, 0), min(len(text), 60))
        for c, w in widths.items():
            ws.column_dimensions[get_column_letter(c)].width = max(10, w + 2)
        if first_is_header:
            ws.freeze_panes = "A2"
            ws.auto_filter.ref = ws.dimensions

    wb.save(dest)
    return dest


# --------------------------------------------------------------------------- to markdown

def to_markdown(src: Path) -> Path:
    from markitdown import MarkItDown

    result = MarkItDown(enable_plugins=False).convert(str(src))
    text = (result.text_content or "").strip()
    if not text:
        raise ConversionError("No text was found. If this is a scanned PDF it needs OCR first.")
    dest = unique_path(src.with_suffix(".md"))
    dest.write_text(text + "\n", encoding="utf-8")
    return dest


# --------------------------------------------------------------------------- driver

CONVERTERS = {"docx": to_docx, "pptx": to_pptx, "html": to_html, "xlsx": to_xlsx}


def _first_line(exc: Exception) -> str:
    text = str(exc).strip()
    return text.splitlines()[0] if text else exc.__class__.__name__


def convert_markdown(src: Path, formats: list[str]) -> tuple[list[Path], list[str]]:
    text = src.read_text(encoding="utf-8", errors="replace")
    stem = src.stem
    if formats == ["auto"]:
        formats, stem = auto_formats(src, text)
    done: list[Path] = []
    errors: list[str] = []
    docx_out: Path | None = None
    for fmt in sorted(formats, key=OUT_FORMATS.index):  # Word first so PDF can reuse it
        dest = unique_path(src.with_name(f"{stem}.{fmt}"))
        try:
            out = to_pdf(src, dest, docx_hint=docx_out) if fmt == "pdf" else CONVERTERS[fmt](src, dest)
            if fmt == "docx":
                docx_out = out
            done.append(out)
            log(f"OK   {src} -> {out}")
        except Exception as exc:
            errors.append(f"{src.name} → {fmt}: {_first_line(exc)}")
            log(f"FAIL {src} -> {fmt}: {exc}\n{traceback.format_exc()}")
    return done, errors


def run(paths: list[str], target: str) -> tuple[list[Path], list[str]]:
    """Convert each path. target is 'md', 'auto', 'all' or a comma list of formats."""
    done: list[Path] = []
    errors: list[str] = []
    target = target.strip().lower()
    to_md = target in {"md", "markdown"}
    formats = ["auto"] if target == "auto" else ([] if to_md else normalise_formats(target.split(",")))

    for raw in paths:
        src = Path(raw)
        if not src.is_file():
            errors.append(f"{raw}: file not found")
            continue
        try:
            if to_md:
                if src.suffix.lower() in MD_SUFFIXES:
                    errors.append(f"{src.name}: already Markdown")
                    continue
                out = to_markdown(src)
                done.append(out)
                log(f"OK   {src} -> {out}")
            else:
                if src.suffix.lower() not in MD_SUFFIXES:
                    errors.append(f"{src.name}: not a Markdown file")
                    continue
                d, e = convert_markdown(src, formats)
                done += d
                errors += e
        except Exception as exc:
            errors.append(f"{src.name}: {_first_line(exc)}")
            log(f"FAIL {src}: {exc}\n{traceback.format_exc()}")
    return done, errors
