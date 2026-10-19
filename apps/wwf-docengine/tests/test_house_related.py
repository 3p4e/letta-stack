"""The documents an SOP works with (Head of QC, 19.10.2026): QCSOP001 names QCT002 (Request for analysis) and five
more in its text, the engine held all six, and drafted a request form beside QCT002 without a word."""
import pytest

from app import house, library


SOP_TEXT = ("... согласно QCT 002 Барање за анализа, QCT 003 и QCT 004; извештај QCT 010; QCCoA 001; "
            "види QCSOP 001 (самиот документ) и QCSOP001A01. Број 15.0 не е код, ниту AB 123.")


def test_listed_codes_are_normalised_known_and_in_order_of_mention():
    known = {"QCT002", "QCT003", "QCT004", "QCT010", "QCCoA001", "QCSOP001", "QCSOP001A01"}
    assert house.listed_codes(SOP_TEXT, known) == ["QCT002", "QCT003", "QCT004", "QCT010", "QCCoA001", "QCSOP001",
                                                   "QCSOP001A01"]
    assert house.listed_codes("nothing here", known) == []


def test_relations_by_code_parent_and_text_first_match_wins():
    codes = ["QCSOP001", "QCSOP001A01", "QCSOP001A02", "QCT002", "QCT003", "QCLB005", "QCSOP002"]
    parents = {"QCLB005": "QCSOP001", "QCT003": "QCSOP001"}
    rel = house.relations("QCSOP001", codes, parents, ["QCT002", "QCT003", "QCSOP001", "QCSOP001A01"])
    assert rel == [("QCLB005", "child"), ("QCSOP001A01", "annex"), ("QCSOP001A02", "annex"), ("QCT002", "listed"),
                   ("QCT003", "child")]
    assert house.relations("QCSOP002", codes, parents, []) == []


@pytest.mark.asyncio
async def test_related_reports_the_approved_sop_and_its_documents(monkeypatch):
    docs = [{"id": "r1", "code": "QCSOP001", "version": "01", "title_en": "QC activities", "title_mk": "", "chars": 10,
             "parent": ""},
            {"id": "r2", "code": "QCT002", "version": "02", "title_en": "Request for analysis", "title_mk": "", "chars": 5,
             "parent": ""}]

    async def in_use_list():
        return docs

    async def reference_get(rid):
        return {"markdown": SOP_TEXT if rid == "r1" else "form text"}
    monkeypatch.setattr(house, "in_use_list", in_use_list)
    monkeypatch.setattr(house.db, "reference_get", reference_get)
    r = await house.related("qcsop 001")
    assert r["found"] and r["version"] == "01" and [x["code"] for x in r["related"]] == ["QCT002"]
    assert r["related"][0]["relation"] == "listed" and r["related"][0]["version"] == "02"
    assert (await house.related("QCSOP099"))["found"] is False
    block, codes = await house.related_block("QCSOP001")
    assert codes == ["QCT002"] and "QCT002 v02 — Request for analysis" in block and "form text" in block
    assert block.startswith(house.RELATED_NOTE)


def test_library_packages_group_sops_with_their_documents_in_two_groups():
    register = [{"code": "QCSOP001", "title_en": "QC activities", "status": "effective"},
                {"code": "QCT002", "title_en": "Request for analysis", "status": "effective"},
                {"code": "QCLB005", "title_en": "Sampling logbook", "status": "effective", "parent": "QCSOP001"},
                {"code": "QCSOP026", "title_en": "New SOP", "status": "draft"},
                {"code": "QCSOP026A01", "title_en": "Its annex", "status": "draft", "parent": "QCSOP026"},
                {"code": "QCT099", "title_en": "A loose form", "status": "draft"}]
    lib = library.shelve(register, [], [], {}, listed={"QCSOP001": ["QCT002"]})
    in_use, drafts = lib["packages"]["in_use"], lib["packages"]["drafts"]
    assert [p["sop"]["code"] for p in in_use] == ["QCSOP001"]
    assert [(m["code"], m["relation"]) for m in in_use[0]["members"]] == [("QCLB005", "child"), ("QCT002", "listed")]
    assert [p["sop"]["code"] for p in drafts] == ["QCSOP026"]
    assert [(m["code"], m["relation"]) for m in drafts[0]["members"]] == [("QCSOP026A01", "annex")]
    assert [e["code"] for e in lib["loose"]["drafts"]] == ["QCT099"] and lib["loose"]["in_use"] == []
