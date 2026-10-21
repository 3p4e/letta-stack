"""build_from_md parse/build contract — content the engine used to drop or crash on (review 14.10.2026).

Each case was reproduced against the delivered transport annexes or a minimal input before the fix. They
build in memory with python-docx and read the text back off the XML; no LibreOffice needed."""
import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
pytest.importorskip("docx", reason="python-docx is the engine's own dependency")
import build_from_md as B  # noqa: E402

HD = "<!--HEADERDATA\nmk_title: Тест\nen_title: Test\ncode: T_01\ndoctype: {dt}\n-->\n"


def build(tmp_path, body, dt="FORM"):
    src, out = tmp_path / "in.md", tmp_path / "out.docx"
    src.write_text(HD.format(dt=dt) + body, encoding="utf-8")
    B.main(str(src), str(out))
    xml = zipfile.ZipFile(out).read("word/document.xml").decode("utf-8")
    import re
    return re.sub(r"<[^>]+>", " ", xml), xml.count('w:type="page"')


def test_a_labelled_option_field_keeps_its_label(tmp_path):
    """WHSOP_003_A05 printed the receipt options with no 'Receipt status' in front of them."""
    txt, _ = build(tmp_path, "[[FORM]]\nСтатус на приемот ||| Receipt status ||| ☐ Прифатено | Accepted   ☐ Одбиено | Rejected\n[[/FORM]]\n")
    assert "Статус на приемот" in txt and "Receipt status" in txt and "Одбиено" in txt


def test_a_sibling_field_beside_an_option_row_is_kept(tmp_path):
    txt, _ = build(tmp_path, "[[FORM]]\nДатум на пратка ||| Shipment date ||| _\nТовар ||| Load ||| ☐ A ☐ B\n[[/FORM]]\n")
    assert "Shipment date" in txt and "Load" in txt


def test_a_pure_option_block_is_still_a_status_grid(tmp_path):
    assert B.as_options([["☐ Да | Yes   ☐ Не | No"]]) == ["Да | Yes", "Не | No"]
    assert B.as_options([["Статус ||| Status", "☐ A ☐ B"]]) is None


def test_a_fourth_form_cell_is_part_of_the_value(tmp_path):
    txt, _ = build(tmp_path, "[[FORM]]\nЦел ||| Purpose ||| Испорака до купувач ||| Delivery to customer\n[[/FORM]]\n")
    assert "Delivery to customer" in txt


def test_an_unterminated_table_stops_at_the_next_block_marker(tmp_path):
    txt, breaks = build(tmp_path, "[[TABLE]]\nКод~~Code ||| Назив~~Title\nA01 ||| Листа\n[[PAGEBREAK]]\n[[BOX:3]]\nПример ||| Specimen\n[[/BOX]]\n")
    assert "[[PAGEBREAK]]" not in txt and "[[BOX" not in txt and "Specimen" in txt and breaks == 1


def test_sop_keeps_boxes_page_breaks_and_long_rows(tmp_path):
    body = ("# 1.0 ЦЕЛ | PURPOSE\nЦел ||| Purpose\n[[TABLE]]\nКод~~Code ||| Наслов~~Title ||| Кој~~Who\n"
            "A01 ||| Листа ||| Форма ||| 5 години\n[[/TABLE]]\n[[PAGEBREAK]]\n[[BOX:3]]\nПример етикета ||| Specimen label\n[[/BOX]]\n")
    txt, _ = build(tmp_path, body, dt="SOP")          # an IndexError before: no document at all
    assert "5 години" in txt and "Specimen label" in txt
    no_break, _ = build(tmp_path, body.replace("[[PAGEBREAK]]\n", ""), dt="SOP")
    assert txt.count("Specimen label") == no_break.count("Specimen label")


def test_a_heading_written_with_the_prose_separator(tmp_path):
    _, blocks = B.parse(HD.format(dt="FORM") + "## 6.1 Подготовка ||| Preparation\n")
    assert blocks[0][2:] == ("6.1", "Подготовка", "Preparation")


def test_an_unclosed_headerdata_block_fails_loud():
    with pytest.raises(ValueError, match="not closed"):
        B.parse("<!--HEADERDATA\nmk_title: X\ndoctype: FORM\n# 1 A | B\n")


# ---------------------------------------------------------------- review 19.10.2026
def _tables(tmp_path, body, dt="FORM"):
    import docx
    src, out = tmp_path / "in.md", tmp_path / "out.docx"
    src.write_text(HD.format(dt=dt) + body, encoding="utf-8")
    B.main(str(src), str(out))
    return [[[c.text for c in r.cells] for r in t.rows] for t in docx.Document(str(out)).tables]


def test_a_hash_ordinal_header_is_a_row_not_a_heading(tmp_path):
    """'# ||| Параметар~~Parameter' ended the table and printed as a heading; the rows became prose."""
    _, blocks = B.parse(HD.format(dt="FORM") + "[[TABLE]]\n# ||| Параметар~~Parameter\n1 ||| pH\n[[/TABLE]]\nТекст ||| Text\n")
    assert [x[0] for x in blocks] == ["table", "p"] and blocks[0][1] == [["#", "Параметар~~Parameter"], ["1", "pH"]]
    assert B.HEADING.match("# 1 Опфат | Scope") and not B.HEADING.match("# ||| x") and not B.HEADING.match("#")
    txt, _ = build(tmp_path, "[[TABLE]]\n# ||| Параметар~~Parameter\n1 ||| pH\n[[/TABLE]]\n")
    assert "Parameter" in txt and "[[/TABLE]]" not in txt


def test_a_literal_line_is_never_a_heading_bullet_or_marker(tmp_path):
    _, blocks = B.parse(HD.format(dt="FORM") + "\\# 3 Напомена ||| Note\n\\- 20 °C\n[[TABLE]]\n\\[[x]] ||| y\n[[/TABLE]]\n")
    assert blocks == [("p", "# 3 Напомена", "Note"), ("p", "- 20 °C", ""), ("table", [["[[x]]", "y"]], None)]


def test_an_sop_form_is_a_label_value_form(tmp_path):
    """In an SOP the first field became the navy header row and the '_' write-ins printed literally."""
    tables = _tables(tmp_path, "# 7 Записи | Records\n[[FORM]]\nИме ||| Name ||| _\nДатум ||| Date ||| _\n[[/FORM]]\n", dt="SOP")
    assert [["Име | Name", ""], ["Датум | Date", ""]] in tables
    assert not any("_" in c for t in tables for r in t for c in r)


def test_a_two_cell_row_with_a_cyrillic_value(tmp_path):
    tables = _tables(tmp_path, "[[FORM]]\nИме ||| Петар\nДатум ||| 12.10.2026\nМесто ||| Place\n[[/FORM]]\n")
    assert [["Име", "Петар"], ["Датум", "12.10.2026"], ["Место | Place", ""]] in tables


def _wide(n):
    return "[[TABLE]]\n" + " ||| ".join(f"Колона {i}~~Column {i}" for i in range(n)) + "\n" + "|" * 17 + "\n[[/TABLE]]\n"


def test_a_pipe_only_row_is_an_empty_entry_row(tmp_path):
    """QCT026 (20.10.2026): an entry row of 17 pipes printed a stray '||' in one cell."""
    txt, _ = build(tmp_path, _wide(5))
    assert "||" not in txt and "Column 4" in txt


@pytest.mark.parametrize("n,land", [(10, False), (11, True)])
def test_a_form_wider_than_ten_columns_is_landscape(tmp_path, n, land):
    """15 columns on portrait A4 broke every header word mid-syllable (QCT026, 20.10.2026)."""
    out = tmp_path / "out.docx"
    build(tmp_path, _wide(n))
    xml = zipfile.ZipFile(out).read("word/document.xml").decode("utf-8")
    assert ('w:orient="landscape"' in xml) is land


def test_sop_cover_takes_signatories_from_the_header(tmp_path):
    """A QA SOP printed the QC chain as its signatories (21.10.2026); '—' leaves the line blank."""
    body = "# 1.0 ЦЕЛ|PURPOSE\nЦел на постапката за тест. ||| Purpose of the test procedure.\n"
    txt, _ = build(tmp_path, body, dt="SOP")
    assert "Romevska" in txt                      # default kept for SOPs that name nobody
    src, out = tmp_path / "q.md", tmp_path / "q.docx"
    src.write_text("<!--HEADERDATA\nmk_title: Тест\nen_title: Test\ncode: QASOPXXX\ndoctype: SOP\nprepared_by: —\n"
                   "reviewed_by: —\napproved_by: —\n-->\n" + body, encoding="utf-8")
    B.main(str(src), str(out))
    xml = zipfile.ZipFile(out).read("word/document.xml").decode("utf-8")
    assert "Romevska" not in xml and "Petrova" not in xml and "Nikolov" not in xml
