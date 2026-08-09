# Offline proof of the formatting core: the canonical merged engine builds
# real bilingual documents and the PASS gate actually gates.
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import builder  # noqa: E402

SOP_MD = """<!--HEADERDATA
mk_title: Тест СОП за примерок
en_title: Test Sampling SOP
code: QCSOP-999
version: 1.0
doctype: SOP
orient: portrait
-->
# 1.0 ЦЕЛ|PURPOSE
Оваа процедура ја опишува постапката за земање мостри.|This procedure describes sampling.

# 3.0 ОДГОВОРНОСТИ|RESPONSIBILITIES
[[TABLE]]
Улога~~Role|||Одговорност~~Responsibility
Аналитичар~~Analyst|||Земање мостра~~Sampling
[[/TABLE]]

# 6.0 ПОСТАПКА|PROCEDURE
Чекор еден: подготовка.|Step one: preparation.
"""

FORM_MD = """<!--HEADERDATA
mk_title: Образец за земање мостра
en_title: Sampling Form
code: FM-QC-999
version: 1.0
doctype: FORM
orient: portrait
-->
# 1.0 ИНФОРМАЦИИ|INFORMATION
[[FORM:grid]]
Датум~~Date|||
Серија~~Batch|||
Материјал~~Material|||
Аналитичар~~Analyst|||
[[/FORM]]
"""


def test_sop_builds_and_passes(tmp_path):
    r = builder.build(SOP_MD, tmp_path, "sop_test")
    assert r.path.exists() and r.bytes > 10_000
    assert "RESULT: PASS" in r.verify_report
    assert r.doctype == "SOP"


def test_form_grid_builds_and_passes(tmp_path):
    r = builder.build(FORM_MD, tmp_path, "form_test")
    assert r.path.exists() and r.bytes > 10_000
    assert "RESULT: PASS" in r.verify_report
    assert r.doctype == "FORM"


def test_verify_gate_blocks_and_deletes(tmp_path, monkeypatch):
    # Force the verifier to fail: the artifact must NOT survive on disk.
    monkeypatch.setattr(builder, "run_verify",
                         lambda p, min_pt=6.0, require_bilingual=True: (False, "RESULT: FAIL"))
    with pytest.raises(builder.VerifyFailed) as e:
        builder.build(SOP_MD, tmp_path, "gated")
    assert "FAIL" in e.value.report
    assert not (tmp_path / "gated.docx").exists()


def _fake_engine_build(text, min_pt=10):
    """Bypass the real house-style engine and write a minimal, controllable
    .docx directly — isolates exactly one verify dimension per test instead
    of depending on the real template's own boilerplate content."""
    import docx as docxlib

    def _write(src, out):
        d = docxlib.Document()
        p = d.add_paragraph(text)
        p.runs[0].font.size = docxlib.shared.Pt(min_pt)
        d.save(out)
    return _write


def test_bilingual_missing_now_fails_the_gate(tmp_path, monkeypatch):
    # B1: the bilingual check used to only print a WARN and never gate the
    # build. An English-only document must now be refused.
    monkeypatch.setattr(builder.build_from_md, "main",
                         _fake_engine_build("Only English content appears anywhere in this "
                                            "document body, repeated for length. " * 20))
    with pytest.raises(builder.VerifyFailed) as e:
        builder.build(SOP_MD, tmp_path, "bilingual_fail")
    assert "FAIL (missing a language)" in e.value.report


def test_bilingual_optout_allows_monolingual_document(tmp_path, monkeypatch):
    # The forward-compatible `bilingual: no` HEADERDATA escape hatch.
    monkeypatch.setattr(builder.build_from_md, "main",
                         _fake_engine_build("Only English content appears anywhere in this "
                                            "document body, repeated for length. " * 20))
    md = SOP_MD.replace("orient: portrait\n-->", "orient: portrait\nbilingual: no\n-->")
    r = builder.build(md, tmp_path, "bilingual_optout")
    assert "RESULT: PASS" in r.verify_report


def test_fidelity_shortfall_fails_the_gate(tmp_path, monkeypatch):
    # B1: a produced document that is a content SHORTFALL vs. its own source
    # markdown must be refused — the impoverishment/fabrication-by-omission
    # class of failure.
    monkeypatch.setattr(builder.build_from_md, "main", _fake_engine_build("Кратко. Short."))
    with pytest.raises(builder.VerifyFailed) as e:
        builder.build(SOP_MD, tmp_path, "fidelity_fail")
    assert "FIDELITY" in e.value.report and "FAIL" in e.value.report


def test_parse_survives_embedded_comment_terminator_in_value():
    # B2: a HEADERDATA field value containing a literal '-->' must not be
    # mistaken for the block's own terminator.
    import build_from_md
    md = (
        "<!--HEADERDATA\n"
        "mk_title: Опис --> на нешто\n"
        "en_title: Description\n"
        "code: C-1\n"
        "version: 1.0\n"
        "doctype: SOP\n"
        "orient: portrait\n"
        "-->\n"
        "# 1.0 ЦЕЛ|PURPOSE\n"
        "Текст.|Text.\n"
    )
    hd, blocks = build_from_md.parse(md)
    assert hd["mk_title"] == "Опис --> на нешто"
    assert hd["en_title"] == "Description"
    assert hd["code"] == "C-1"
    assert hd["doctype"] == "SOP"
    body_text = " ".join(str(b) for b in blocks)
    assert "en_title" not in body_text and "doctype" not in body_text and "version" not in body_text


def test_house_style_in_output(tmp_path):
    # The produced docx carries the house navy #2B547E and Calibri.
    import zipfile
    r = builder.build(FORM_MD, tmp_path, "style_test")
    xml = zipfile.ZipFile(r.path).read("word/document.xml").decode("utf-8")
    assert "2B547E" in xml
    assert "Calibri" in xml


def test_safe_name():
    assert builder.safe_name("../../etc/passwd") == ".._.._etc_passwd"
    assert builder.safe_name("") == "document"
    assert "/" not in builder.safe_name("a/b\\c d")


def test_concurrent_builds_of_same_code_produce_two_intact_documents(tmp_path):
    """H13 — the output path used to be derived from the document CODE alone,
    so two concurrent builds of the same code wrote the same file: they
    interleaved, and the FAIL cleanup could delete the OTHER build's passing
    document. The in-process lock cannot help, because the service runs
    multiple uvicorn worker PROCESSES.

    Each build now owns a unique path, so both artifacts survive intact."""
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        results = [f.result() for f in
                   [ex.submit(builder.build, SOP_MD, tmp_path, "same_code") for _ in range(4)]]

    paths = [r.path for r in results]
    assert len({str(p) for p in paths}) == 4, "builds collided on one path"
    for r in results:
        assert r.path.exists() and r.path.stat().st_size == r.bytes > 0
        assert r.path.name.startswith("same_code-") and r.path.suffix == ".docx"
    # nothing half-written is left behind under the dot-prefixed staging name
    assert not list(tmp_path.glob(".*partial*"))


def test_failed_build_cannot_delete_another_builds_document(tmp_path, monkeypatch):
    """H13 — the FAIL path unlinks its own staging file, which is uniquely
    named, so it can no longer take out a sibling build's passing artifact."""
    good = builder.build(SOP_MD, tmp_path, "shared_code")
    assert good.path.exists()
    monkeypatch.setattr(builder, "run_verify", lambda *a, **k: (False, "RESULT: FAIL"))
    with pytest.raises(builder.VerifyFailed):
        builder.build(SOP_MD, tmp_path, "shared_code")     # same code, must FAIL
    assert good.path.exists(), "a failed build deleted a different build's document"
    assert good.path.stat().st_size == good.bytes
