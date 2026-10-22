"""The glyph guard flags text a declared face cannot render, but lets symbols fall back.

House rule (CLAUDE.md): a letter, digit or "№" in a fallback face is a defect; symbols the house
faces lack (☐ ☒ ✎ ≤ ∑ Δ) may fall back. Before 09.10.2026 the guard failed every form for its
☐ checkboxes wherever fontTools was installed, and skipped silently wherever it was not.
"""
import os
import sys

import pytest
from docx import Document

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import pp_assets  # noqa: E402

LATIN_ONLY = {ord(c) for c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,|"}


@pytest.fixture
def latin_only_face(monkeypatch, tmp_path):
    monkeypatch.setattr(pp_assets, "_resolve", lambda face: "/fake/face.ttf")
    monkeypatch.setattr(pp_assets, "_cmap", lambda path: LATIN_ONLY)


def _doc(tmp_path, text):
    d = Document(); r = d.add_paragraph().add_run(text); r.font.name = "Calibri"
    p = tmp_path / "t.docx"; d.save(p); return str(p)


@pytest.mark.parametrize("ch", ["☐", "☒", "✎", "≤", "∑"])
def test_symbols_may_fall_back(latin_only_face, tmp_path, ch):
    assert pp_assets.audit_docx(_doc(tmp_path, f"{ch} Yes")) == []


@pytest.mark.parametrize("text", ["Да | Yes", "№ 5"])
def test_letters_and_numero_must_be_covered(latin_only_face, tmp_path, text):
    bad = pp_assets.audit_docx(_doc(tmp_path, text))
    assert bad and bad[0][0] == "Calibri"


def test_must_cover():
    assert pp_assets.must_cover("Ж") and pp_assets.must_cover("7") and pp_assets.must_cover("№")
    assert not pp_assets.must_cover("☐") and not pp_assets.must_cover("✎")
