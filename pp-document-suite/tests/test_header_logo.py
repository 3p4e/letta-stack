"""The running header's logo is one picture (Head of QC, 19.10.2026).

The base template floats two crops of the brand image; the wordmark's position depended on the header
table's height, and LibreOffice with the real Calibri laid the row out shorter than Word, so the leaf's
white box covered the middle of PURELYPLANT on every engine document. Every built document now carries
the one uncropped image on the leaf's own anchor, and no second anchor after the table."""
import os
import sys
import zipfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
pytest.importorskip("docx", reason="python-docx is the engine's own dependency")
import build_from_md  # noqa: E402

MD = """<!--HEADERDATA
mk_title: Барање за мострирање
en_title: Sampling request
code: QCSOP001A01
version: 1.0
doctype: FORM
orient: portrait
-->
# 1.0 СОДРЖИНА|CONTENT
[[FORM]]
Датум ||| Date |||
[[/FORM]]
"""


def test_built_header_carries_one_uncropped_logo(tmp_path):
    src = tmp_path / "a.md"; src.write_text(MD, encoding="utf-8")
    out = tmp_path / "a.docx"
    build_from_md.main(str(src), str(out))
    hdr = zipfile.ZipFile(out).read("word/header1.xml").decode("utf-8")
    assert hdr.count("<wp:anchor") == 1, "one logo picture, anchored in the first header cell"
    assert "srcRect" not in hdr, "the whole brand image, not a crop"
    assert "<wp:inline" not in hdr


def test_annex_body_has_no_title_block(tmp_path):
    """Head of QC, 19.10.2026: the running header carries the title, code and status; the body does not repeat them."""
    import zipfile as zf
    import re
    src = tmp_path / "b.md"; src.write_text(MD, encoding="utf-8")
    out = tmp_path / "b.docx"
    build_from_md.main(str(src), str(out))
    body = re.sub(r"<[^>]+>", "", zf.ZipFile(out).read("word/document.xml").decode("utf-8"))
    assert "NOT FOR USE" not in body and "(QCSOP001A01)" not in body
    assert "СОДРЖИНА" in body
