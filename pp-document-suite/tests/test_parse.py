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
