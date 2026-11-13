from pathlib import Path

import pytest

from convert_md.converter import (ConversionError, auto_formats, cell_value, normalise_formats,
                                  unique_path)


@pytest.mark.parametrize("raw, expected", [
    (["docx"], ["docx"]),
    (["Word", ".PDF"], ["docx", "pdf"]),
    (["excel", "ppt", "htm"], ["xlsx", "pptx", "html"]),
    (["all"], ["docx", "pdf", "xlsx", "pptx", "html"]),
    (["docx", "docx", "word"], ["docx"]),
])
def test_normalise_formats(raw, expected):
    assert normalise_formats(raw) == expected


def test_normalise_formats_rejects_unknown():
    with pytest.raises(ConversionError, match="Unknown format"):
        normalise_formats(["odt"])


def test_auto_formats_front_matter_wins():
    text = "---\ntitle: x\noutputs: [pdf, xlsx]\n---\n# Hi\n"
    assert auto_formats(Path("Report.docx.md"), text) == (["pdf", "xlsx"], "Report")


def test_auto_formats_from_filename():
    assert auto_formats(Path("Proposal.docx.pdf.md"), "# Hi\n") == (["docx", "pdf"], "Proposal")


def test_auto_formats_keeps_dotted_names():
    assert auto_formats(Path("v1.2 notes.md"), "# Hi\n") == (["docx"], "v1.2 notes")


def test_auto_formats_default_is_word():
    assert auto_formats(Path("Plain.md"), "# Hi\n") == (["docx"], "Plain")


@pytest.mark.parametrize("text, value, fmt", [
    ("1,200", 1200, "#,##0"),
    ("980", 980, None),
    ("$1,450.50", 1450.5, "#,##0.00"),
    ("(300)", -300, None),
    ("12%", 0.12, "0%"),
    ("3.1%", 0.031, "0.0%"),
    ("-5%", -0.05, "0%"),
    ("NSW", "NSW", None),
    ("", "", None),
    ("2026-11-13", "2026-11-13", None),
])
def test_cell_value(text, value, fmt):
    got_value, got_fmt = cell_value(text)
    assert got_fmt == fmt
    if isinstance(value, float):
        assert got_value == pytest.approx(value)
    else:
        assert got_value == value


def test_unique_path(tmp_path):
    first = tmp_path / "Report.docx"
    assert unique_path(first) == first
    first.write_text("x")
    second = unique_path(first)
    assert second.name == "Report (1).docx"
    second.write_text("x")
    assert unique_path(first).name == "Report (2).docx"
