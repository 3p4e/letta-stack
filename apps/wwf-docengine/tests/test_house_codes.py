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


@pytest.mark.parametrize("raw", ["labels_raw (final) v3", "pasted", "QASOP_0YY", "T-1", "", "123", "QCSOP"])
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
    assert hc.next_code(family="QCT") == "QCT026"                    # QCT007/014/015/021 gaps stay empty; 025 a draft's
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


def test_other_departments_are_known_from_the_files_we_have():
    # Head of QC, 18.10.2026: add the other departments, only with the information we have so far.
    rows = {r["code"]: r for r in hc.load_register()}
    for code, dept in (("WHSOP002A09", "WH"), ("WHSOP003A07", "WH"), ("EQSOP013A08", "EQ"), ("QASOP031A10", "QA"),
                       ("QAT053", "QA"), ("SPT004", "SP"), ("CULI001", "CU")):
        assert rows[code]["department"] == dept and rows[code]["status"] in ("known", "unconfirmed"), code
    assert hc.next_code(family="WHSOP") == "WHSOP004"
    assert hc.next_code(parent="WHSOP003") == "WHSOP003A08"
    assert hc.next_code(family="EQSOP") == "EQSOPXXX"            # the EQSOP family is not yet approved


def test_qasop_99_is_a_placeholder_not_a_code():
    # Head of QC, 18.10.2026: "QASOP_99 is not true, i just named it 99 instead of xxx".
    assert "QASOP099" not in {r["code"] for r in hc.load_register()}
    assert hc.next_code(family="QASOP") == "QASOPXXX"


@pytest.mark.parametrize("raw,house", [("QASOP_0XX", "QASOPXXX"), ("qasop xxx", "QASOPXXX"), ("QASOP_0XX_A06", "QASOPXXXA06"),
                                       ("EQSOP XXX A01", "EQSOPXXXA01")])
def test_an_unconfirmed_number_is_written_xxx(raw, house):
    # Head of QC, 18.10.2026: "all QA SOP drafts should be xxx unknown numbers actualy until not confirmed".
    assert hc.normalize(raw) == house
    assert hc.parts(house)[1] is None


def test_unconfirmed_families_get_xxx_and_their_drafts_are_marked():
    # QA SOP numbers are not confirmed; the EQSOP family is not yet approved (Head of QC, 18.10.2026).
    assert {"QASOP", "EQSOP"} <= hc.unconfirmed_families()
    rows = {r["code"]: r for r in hc.load_register()}
    assert rows["QASOP031"]["status"] == rows["EQSOP013"]["status"] == "unconfirmed"
    assert rows["QAT053"]["status"] == "known"                        # forms keep their numbers
    assert hc.next_code(parent="QASOPXXX", taken={"QASOP_0XX_A06"}) == "QASOPXXXA07"
    assert hc.next_code(family="QAT") == "QAT054" and hc.next_code(family="QCSOP") == "QCSOP026"


# ---- review 19.10.2026 ----

@pytest.mark.parametrize("raw", ["QC01", "AB001", "ABC001", "WHSOP00", "QCT000", "QCSOP000A01", "QCSOP011A00"])
def test_a_short_unknown_family_or_a_zero_number_is_not_a_code(raw):
    """"QC01", "AB001" and "WHSOP00" passed as codes; a family is four letters or one the register knows, a number is
    1 or more (XXX allowed)."""
    assert hc.normalize(raw) is None


def test_three_letter_families_the_register_knows_still_pass():
    assert hc.normalize("QCT 017") == "QCT017" and hc.normalize("SSP-001") == "SSP001"
    assert hc.normalize("QAT053") == "QAT053" and hc.normalize("QCSOP011A01") == "QCSOP011A01"
    assert hc.normalize("WHSOP003") == "WHSOP003" and hc.normalize("QASOPXXX") == "QASOPXXX"
    assert hc.normalize("QCCoA001") == "QCCoA001" and hc.normalize("ABCD001") == "ABCD001"


def test_versions_order_as_numbers_per_dot():
    """house.py and library.py compared versions as text, so "1.9" beat "1.10"; one shared key now."""
    k = hc.version_key
    assert k("1.10") > k("1.9") > k("1.0") and k("01") == k("1") and k("2") > k("1.10")
    assert k("1.0a") > k("1.0") and k("") < k("01")                         # text parts last; an empty version first
    assert sorted(["1.10", "1.9", "2.0", "1.2"], key=k) == ["1.2", "1.9", "1.10", "2.0"]
