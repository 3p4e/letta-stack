# The house document code form (Head of QC, 18.10.2026): the form of QALI 001 — QCSOP011, QCT017, QCSOP011A01.
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import house_codes as hc  # noqa: E402


@pytest.mark.parametrize("raw,house", [
    ("QCSOP011", "QCSOP011"), ("QCSOP 011", "QCSOP011"), ("QCSOP_011", "QCSOP011"), ("qcsop-11", "QCSOP011"),
    ("QCSOP011А01", "QCSOP011A01"),          # Cyrillic А, as QALI 001 writes it
    ("QCSOP_025_A01", "QCSOP025A01"), ("WHSOP_003_A04", "WHSOP003A04"), ("WHSOP 003", "WHSOP003"),
    ("QCT 017", "QCT017"), ("QCLB 21", "QCLB021"), ("QCSPW 005", "QCSPW005"),
    ("QCCoA 001", "QCCoA001"), ("QCCOA001", "QCCoA001"), ("SSP-001", "SSP001"),
])
def test_forms_in_circulation_become_the_house_form(raw, house):
    assert hc.normalize(raw) == house


@pytest.mark.parametrize("raw", ["labels_raw (final) v3", "pasted", "QASOP_0XX", "T-1", "", "123", "QCSOP"])
def test_what_is_not_a_document_code_is_refused(raw):
    assert hc.normalize(raw) is None


def test_the_register_loads_in_house_form_with_review_dates():
    rows = {r["code"]: r for r in hc.load_register()}
    assert rows["QCSOP011A01"]["parent"] == "QCSOP011"
    assert rows["QCSOP022"]["review_date"] == "2028-01-31"          # three years after 31.01.2025
    assert rows["QCSOP020"]["status"] == "withdrawn"
    assert all(hc.normalize(c) == c for c in rows)


def test_next_free_code_never_reuses_or_fills_gaps():
    assert hc.next_code(family="QCSOP") == "QCSOP026"                # QCSOP020 withdrawn, not freed; 025 reserved
    assert hc.next_code(family="QCT") == "QCT025"                    # QCT007/014/015/021 gaps stay empty
    assert hc.next_code(family="QCLB") == "QCLB022"
    assert hc.next_code(family="qcwi") == "QCWI023"
    assert hc.next_code(family="QCCoA") == "QCCoA002"


def test_codes_held_by_open_drafts_are_taken():
    assert hc.next_code(family="QCSOP", taken={"QCSOP_026", "QCSOP 027"}) == "QCSOP028"


def test_codes_the_acme_drafts_carry_are_reserved():
    # QALI 001 alone gave QCSOP025, QCT017 and QCLB021 — numbers drafts in ACME_SOP already carry.
    rows = {r["code"]: r for r in hc.load_register()}
    for code in ("QCSOP025", "QCT017", "QCT018", "QCT024", "QCLB021", "QCSOP011A09", "QCSOP018A10"):
        assert rows[code]["status"] == "reserved", code
    assert rows["QCSOP011"]["status"] == "effective_revising"         # a reservation never shadows a QALI row


def test_next_annex_of_a_parent():
    assert hc.next_code(parent="QCSOP011") == "QCSOP011A10"
    assert hc.next_code(parent="QCSOP018") == "QCSOP018A11"
    assert hc.next_code(parent="WHSOP 003", taken={"WHSOP_003_A07"}) == "WHSOP003A08"
    with pytest.raises(ValueError):
        hc.next_code(parent="QCSOP011A01")
