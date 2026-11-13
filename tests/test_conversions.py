import sys

import pytest
from openpyxl import load_workbook

from convert_md.cli import main
from convert_md.converter import available_pdf_engines, run


@pytest.mark.parametrize("fmt", ["docx", "pptx", "html", "xlsx"])
def test_markdown_to_format(sample, fmt):
    done, errors = run([str(sample)], fmt)
    assert errors == []
    assert [p.name for p in done] == [f"Example.{fmt}"]
    assert done[0].stat().st_size > 0


def test_excel_has_one_sheet_per_table_with_numbers(sample):
    (xlsx,), errors = run([str(sample)], "xlsx")
    assert errors == []
    wb = load_workbook(xlsx)
    assert wb.sheetnames == ["Revenue by region", "Headcount"]
    ws = wb["Revenue by region"]
    assert ws.freeze_panes == "A2"
    assert [c.value for c in ws[1]] == ["Region", "Q1", "Q2", "Growth"]
    assert ws["B2"].value == 1200
    assert ws["C2"].value == pytest.approx(1450.5)
    assert ws["B4"].value == -300
    assert ws["D2"].value == pytest.approx(0.12)


def test_excel_without_tables_is_an_error(tmp_path):
    md = tmp_path / "Plain.md"
    md.write_text("# Hello\n\nNo tables here.\n", encoding="utf-8")
    done, errors = run([str(md)], "xlsx")
    assert done == []
    assert "No tables found" in errors[0]


def test_auto_uses_front_matter(sample):
    done, errors = run([str(sample)], "auto")
    assert errors == []
    assert sorted(p.name for p in done) == ["Example.docx", "Example.xlsx"]


def test_never_overwrites(sample):
    run([str(sample)], "html")
    (second,), _ = run([str(sample)], "html")
    assert second.name == "Example (1).html"


@pytest.mark.parametrize("fmt", ["docx", "pptx", "xlsx", "html"])
def test_round_trip_to_markdown(sample, fmt):
    (out,), _ = run([str(sample)], fmt)
    (md,), errors = run([str(out)], "md")
    assert errors == []
    text = md.read_text(encoding="utf-8")
    assert "NSW" in text and "Sales" in text


def test_rejects_wrong_input_types(sample, tmp_path):
    _, errors = run([str(sample)], "md")
    assert "already Markdown" in errors[0]
    other = tmp_path / "notes.txt"
    other.write_text("hi")
    _, errors = run([str(other)], "docx")
    assert "not a Markdown file" in errors[0]
    _, errors = run([str(tmp_path / "missing.md")], "docx")
    assert "file not found" in errors[0]


@pytest.mark.skipif(sys.platform == "win32" or not available_pdf_engines(),
                    reason="needs a Pandoc PDF engine (Word is used on Windows instead)")
def test_pdf_with_pandoc_engine(sample):
    (pdf,), errors = run([str(sample)], "pdf")
    assert errors == []
    assert pdf.read_bytes()[:4] == b"%PDF"


def test_cli_exit_codes(sample, capsys):
    assert main(["--to", "docx", str(sample)]) == 0
    assert "created" in capsys.readouterr().out
    assert main(["--to", "bogus", str(sample)]) == 1
    assert "Unknown format" in capsys.readouterr().err
