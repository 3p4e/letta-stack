"""The house consistency check (Head of QC, 19.10.2026): a finished draft against the full text of a named set of
approved, in-use documents; a conflict waits for a person, who registers it only with a reason."""
import pytest

from app import house, library
from app.pipeline import _house_check

DOCS = [
    {"id": "1", "code": "QCSOP001", "version": "01", "title_en": "Activities in the Quality Control Department", "title_mk": "", "parent": ""},
    {"id": "2", "code": "QCT002", "version": "02", "title_en": "Request for analysis", "title_mk": "Барање за анализа", "parent": ""},
    {"id": "3", "code": "QCT003", "version": "01", "title_en": "Report from microbiological analysis", "title_mk": "", "parent": ""},
    {"id": "4", "code": "QCLB005", "version": "01", "title_en": "Sampling logbook", "title_mk": "", "parent": ""},
    {"id": "5", "code": "QCSOP014", "version": "01", "title_en": "Water sampling and analysis request handling", "title_mk": "", "parent": ""},
    {"id": "6", "code": "WHSOP003", "version": "01", "title_en": "Inland transport", "title_mk": "", "parent": ""},
]


def test_the_set_is_named_in_priority_order_with_why():
    s = house.check_set("QCT002", "QCSOP001", "… see QCLB005 …", "Request for sampling and/or analysis",
                        "Барање за мострирање и/или анализа", DOCS, {}, {"QCSOP001": ["QCT002", "QCT003"]})
    assert [(d["code"], d["why"]) for d in s][:5] == [
        ("QCT002", "the approved version this draft revises"), ("QCSOP001", "the parent SOP"),
        ("QCT003", "listed of the parent SOP QCSOP001"), ("QCLB005", "named in the draft"),
        ("QCSOP014", "a title like this draft's")]
    assert "WHSOP003" not in [d["code"] for d in s]


def test_verdicts_are_parsed_and_a_silent_document_is_unchecked():
    reply = ("HOUSE QCT002: CHANGES — adds sampling requests\n- HOUSE QCSOP 001: CONFLICT — draft: «QA signs» | "
             "approved: «Head of department signs»\nHOUSE QCT003: NOT RELEVANT\nHOUSE WHSOP003: CONSISTENT")
    v = house.parse_verdicts(reply, ["QCT002", "QCSOP001", "QCT003", "QCLB005"])
    assert v["QCT002"]["verdict"] == "CHANGES" and v["QCSOP001"]["verdict"] == "CONFLICT"
    assert "Head of department signs" in v["QCSOP001"]["detail"] and v["QCT003"]["verdict"] == "NOT RELEVANT"
    assert v["QCLB005"]["verdict"] == "UNCHECKED" and "WHSOP003" not in v


def test_batches_keep_each_exchange_within_the_budget():
    docs = [{"code": f"QCT{i:03d}", "text": "x" * 20_000} for i in range(1, 6)]
    assert [len(b) for b in house.batches(docs)] == [2, 2, 1]


@pytest.mark.asyncio
async def test_the_pipeline_step_checks_the_named_documents(monkeypatch):
    async def checking_docs(*a):
        return [{"code": "QCT002", "version": "02", "title": "Request for analysis", "why": "revises", "text": "approved"},
                {"code": "QCSOP001", "version": "01", "title": "QC", "why": "parent", "text": "sop"}]
    monkeypatch.setattr(house, "checking_docs", checking_docs)
    seen = []

    async def ask(agent, tag, prompt):
        seen.append((agent, tag, prompt))
        return "HOUSE QCT002: CHANGES — v03\nHOUSE QCSOP001: CONFLICT — draft: «a» | approved: «b»"
    out = await _house_check(ask, {"code": "QCT002", "title_en": "R", "title_mk": "Р"}, "DRAFT TEXT", "QCSOP001", "brief")
    assert [a for a, *_ in seen] == ["gf_house_checker"] and "DRAFT TEXT" in seen[0][2] and "QCT002, QCSOP001" in seen[0][2]
    assert out["verdicts"]["QCSOP001"]["verdict"] == "CONFLICT" and [c["code"] for c in out["checked"]] == ["QCT002", "QCSOP001"]

    async def none(*a):
        return []
    monkeypatch.setattr(house, "checking_docs", none)
    out = await _house_check(ask, {"code": "QCT099"}, "x", "", "b")
    assert out["verdicts"] == {} and "no approved" in out["note"] and len(seen) == 1


def test_reconcile_names_the_missing_and_the_unlisted():
    register = [{"code": "QCSOP011", "title_en": "Sampling", "status": "effective"},
                {"code": "QCSOP001", "title_en": "QC", "status": "effective"}]
    refs = [{"kind": "approved", "code": "QCSOP001", "version": "01", "title_en": "QC"},
            {"kind": "approved", "code": "QAT010", "version": "01", "title_en": "Risk analysis"}]
    rec = library.reconcile(library.shelve(register, refs, [], {}))
    assert [e["code"] for e in rec["missing"]] == ["QCSOP011"]
    assert [(e["code"], e["status"]) for e in rec["unlisted"]] == [("QAT010", "not in the register")]


def test_verdicts_on_one_line_are_all_read():
    """The live checker of 19.10.2026 answered on one line; every verdict must still be read, with its own detail."""
    reply = ("HOUSE QCSOP001: CONSISTENT | HOUSE QCCoA001: NOT RELEVANT | HOUSE QCT002: CONFLICT — draft: «QA signs» | "
             "approved: «the requester signs» | HOUSE QCT003: CHANGES — adds sampling | HOUSE QCT010: CONSISTENT")
    v = house.parse_verdicts(reply, ["QCSOP001", "QCCoA001", "QCT002", "QCT003", "QCT010"])
    assert [v[c]["verdict"] for c in ["QCSOP001", "QCCoA001", "QCT002", "QCT003", "QCT010"]] == \
        ["CONSISTENT", "NOT RELEVANT", "CONFLICT", "CHANGES", "CONSISTENT"]
    assert v["QCT002"]["detail"] == "draft: «QA signs» | approved: «the requester signs»"
    assert v["QCT003"]["detail"] == "adds sampling" and v["QCSOP001"]["detail"] == ""
