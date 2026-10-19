# The Document Brief (Head of QC, 18.10.2026): one workflow, every answer chosen / suggested / locked, a scope change
# marks decided answers stale instead of rewriting them, every change is an event, build from any page.
import asyncio
import base64
import io
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import brief as B  # noqa: E402
from app import db, main, pipeline, sources  # noqa: E402
from app.config import settings  # noqa: E402
from app.main import app  # noqa: E402

KEY = "k"


def fresh(**kw):
    return B.new_brief("sop", {"title_en": "Sampling", "code": "QCSOP011"}, **kw)


def test_a_change_needs_the_current_rev_and_counts_one_rev():
    b = fresh()
    b1, ev = B.apply_patch(b, {"rev": 0, "set": {"doc.purpose": "Sample finished product"}}, "bn")
    assert b1["rev"] == 1 and b1["fields"]["doc.purpose"]["state"] == "chosen" and ev[0]["op"] == "set"
    with pytest.raises(B.BriefConflict):
        B.apply_patch(b1, {"rev": 0, "set": {"purpose": "x"}})            # an old tab cannot overwrite
    same, ev = B.apply_patch(b1, {"rev": 1, "set": {"doc.purpose": "Sample finished product"}})
    assert same["rev"] == 1 and ev == []                                     # nothing changed, no new rev


def test_a_locked_answer_is_never_overwritten_until_unlocked():
    b, _ = B.apply_patch(fresh(), {"rev": 0, "set": {"process_type": "Finished product"}, "lock": ["process_type"]})
    with pytest.raises(B.BriefConflict):
        B.apply_patch(b, {"rev": 1, "set": {"process_type": "Incoming"}})
    b2, ev = B.apply_patch(b, {"rev": 1, "suggest": {"process_type": "Incoming"}})
    assert b2["fields"]["process_type"]["value"] == "Finished product" and ev == []   # a suggestion never wins
    b3, ev = B.apply_patch(b, {"rev": 1, "unlock": ["process_type"], "set": {"process_type": "Incoming"}})
    assert [e["op"] for e in ev] == ["unlock", "set"] and b3["fields"]["process_type"]["state"] == "chosen"


def test_a_scope_change_marks_decided_answers_stale_but_not_locked_ones():
    b, _ = B.apply_patch(fresh(), {"rev": 0, "set": {"doc.scope_in": "FP", "a": 1, "c": 3}, "lock": ["c"]})
    b2, ev = B.apply_patch(b, {"rev": 1, "set": {"doc.scope_in": "FP and intermediates"}})
    assert b2["fields"]["a"]["stale"] and not b2["fields"]["c"]["stale"] and not b2["fields"]["doc.scope_in"]["stale"]
    assert {e["key"] for e in ev if e["op"] == "stale"} == {"a"}
    b3, _ = B.apply_patch(b2, {"rev": 2, "set": {"a": 1}})                   # re-confirming clears it
    assert not b3["fields"]["a"]["stale"]


def test_a_build_from_an_early_page_lists_what_was_not_decided():
    b, _ = B.apply_patch(B.new_brief("sop_annexes", {"title_en": "Sampling"}),
                         {"rev": 0, "set": {"doc.purpose": "Sample FP"}, "suggest": {"doc.scope_in": "FP"},
                          "annexes": [{"title_en": "Sampling plan"}]})
    p = B.to_workflow(b, [{"name": "old.docx", "text": "x" * 20_000}, {"name": "scan.pdf", "text": ""}])
    assert p["questionnaire"] == "sop_qc" and p["meta"]["title_mk"] == "Sampling"
    assert "title_mk (copied from title_en)" in p["assumed"] and "doc.scope_in (suggested, not confirmed)" in p["assumed"]
    assert "focus" in p["assumed"] and "Purpose: Sample FP" in p["instructions"]
    assert p["package_annexes"] == [{"title_en": "Sampling plan", "title_mk": "", "kind": "form"}]
    assert [t["name"] for t in p["source_texts"]] == ["old.docx"] and len(p["source_texts"][0]["text"]) == 12_000
    with pytest.raises(B.BriefError):
        B.to_workflow(B.new_brief("sop"), [])                                 # a title is the one thing required


def _docx(text: str) -> bytes:
    from docx import Document
    d, buf = Document(), io.BytesIO()
    d.add_paragraph(text)
    t = d.add_table(rows=1, cols=2)
    t.rows[0].cells[0].text, t.rows[0].cells[1].text = "ЦЕЛ", "PURPOSE"
    d.save(buf)
    return buf.getvalue()


def test_uploaded_sources_keep_their_text():
    assert "Мострирање" in sources.extract("a.docx", _docx("Мострирање на примероци")) and "ЦЕЛ | PURPOSE" in sources.extract("a.docx", _docx("x"))
    assert sources.extract("a.md", "# Title\nbody".encode()) == "# Title\nbody"
    assert '"a": 1' in sources.extract("a.json", b'{"a":1}')
    for name, blob in (("a.exe", b"x"), ("a.json", b"{not json"), ("a.pdf", b"not a pdf")):
        with pytest.raises(sources.SourceError):
            sources.extract(name, blob)


def test_the_brief_reaches_the_authors_with_its_source_files():
    text = pipeline._brief("sop_qc", {"x": "y"}, "DOCUMENT BRIEF", ["old.docx"], [{"name": "old.docx", "text": "Old SOP"}])
    assert "SOURCE FILE «old.docx»" in text and "Old SOP" in text


@pytest.fixture
def api(monkeypatch):
    """The brief routes over an in-memory store (the SQL itself is covered by test_db.py against Postgres)."""
    monkeypatch.setattr(settings, "api_key", KEY)
    store, srcs, started = {}, {}, []

    async def create(b, by=""):
        bid = "11111111-1111-1111-1111-11111111111" + str(len(store))
        store[bid] = {**b, "id": bid}
        srcs[bid] = []
        return bid

    async def get(bid):
        return {**store[bid], "sources": [{k: v for k, v in s.items() if k != "text"} for s in srcs[bid]]} if bid in store else None

    async def save(b, old, events):
        if store[b["id"]]["rev"] != old:
            return False
        store[b["id"]] = {k: v for k, v in b.items() if k != "sources"}
        return True

    async def add(bid, rev, actor, s):
        srcs[bid].append({**s, "id": "22222222-2222-2222-2222-22222222222" + str(len(srcs[bid])), "chars": len(s["text"])})
        store[bid]["rev"] += 1
        return srcs[bid][-1]["id"]

    async def lst(bid, with_text=True):
        return srcs[bid]

    async def jcreate(kind, payload, by=""):
        started.append(payload)
        return "33333333-3333-3333-3333-333333333333"

    async def nothing(*a):
        return None

    async def taken():
        return {"QCSOP026"}

    for name, fn in (("brief_create", create), ("brief_get", get), ("brief_save", save), ("brief_source_add", add),
                     ("brief_sources", lst), ("job_create", jcreate), ("codes_in_use", taken)):
        monkeypatch.setattr(db, name, fn)
    monkeypatch.setattr(db, "ready", lambda: True)
    monkeypatch.setattr(main, "run_workflow", nothing)
    monkeypatch.setattr(main.LettaClient, "configured", property(lambda self: True))
    with TestClient(app) as c:
        yield c, store, started


def h():
    return {"X-API-Key": KEY}


def test_one_workflow_from_first_page_to_build(api):
    c, store, started = api
    assert c.post("/briefs", json={"package": "sop"}).status_code == 401
    b = c.post("/briefs", json={"package": "sop_annexes", "meta": {"title_en": "Sampling", "code": "qcsop 11"}}, headers=h()).json()
    assert b["meta"]["code"] == "QCSOP011" and b["rev"] == 0
    b = c.patch(f"/briefs/{b['id']}", json={"rev": 0, "set": {"doc.purpose": "Sample FP"}, "lock": ["doc.purpose"],
                                            "annexes": [{"title_en": "Sampling plan"}]}, headers=h()).json()
    assert b["rev"] == 1 and b["fields"]["doc.purpose"]["state"] == "locked"
    assert c.patch(f"/briefs/{b['id']}", json={"rev": 0, "set": {"doc.use": "x"}}, headers=h()).status_code == 409
    assert c.patch(f"/briefs/{b['id']}", json={"rev": 1, "set": {"doc.purpose": "x"}}, headers=h()).status_code == 409
    up = c.post(f"/briefs/{b['id']}/sources", json={"name": "old.docx", "content_b64": base64.b64encode(_docx("Old SOP text")).decode()},
                headers=h()).json()
    assert up["chars"] > 0 and up["brief"]["rev"] == 2 and up["brief"]["sources"][0]["name"] == "old.docx"
    assert c.post(f"/briefs/{b['id']}/sources", json={"name": "x.exe", "content_b64": "eA=="}, headers=h()).status_code == 400
    r = c.post(f"/briefs/{b['id']}/build", json={"rev": 2}, headers=h()).json()
    assert r["code"] == "QCSOP011" and r["status"] == "queued" and "doc.scope_in" in r["assumed"]
    assert started[0]["package_annexes"][0]["title_en"] == "Sampling plan" and started[0]["source_texts"][0]["name"] == "old.docx"
    assert store[b["id"]]["job_ids"] == ["33333333-3333-3333-3333-333333333333"] and store[b["id"]]["rev"] == 3


def test_a_build_without_a_code_takes_the_next_free_one(api):
    c, store, started = api
    b = c.post("/briefs", json={"package": "sop", "meta": {"title_mk": "Мострирање"}}, headers=h()).json()
    r = c.post(f"/briefs/{b['id']}/build", json={}, headers=h()).json()
    assert r["code"] == "QCSOP027"                                           # QCSOP026 held by an open job


def test_package_annexes_start_after_the_sop_and_number_under_it(monkeypatch):
    made, started = [], []

    async def taken():
        return {"QCSOP011A01"}

    async def jcreate(kind, payload, by=""):
        made.append(payload)
        return f"job-{len(made)}"

    async def fake_run(jid):
        started.append(jid)

    monkeypatch.setattr(db, "codes_in_use", taken)
    monkeypatch.setattr(db, "job_create", jcreate)
    monkeypatch.setattr(pipeline, "run_workflow", fake_run)
    p = {"package_annexes": [{"title_en": "Plan"}, {"title_mk": "Дневник", "kind": "log"}], "instructions": "BRIEF"}

    async def go():
        out = await pipeline._start_package_annexes("sop-job", p, {"code": "QCSOP011", "version": "03"})
        await asyncio.sleep(0)
        return out
    out = asyncio.run(go())
    assert [o["code"] for o in out] == ["QCSOP011A10", "QCSOP011A11"]     # A01–A09 held by the register and jobs
    assert made[0]["parent_sop"] == "QCSOP011" and made[1]["meta"]["title_en"] == "Дневник" and started == ["job-1", "job-2"]


# ---------- phase 3: the questions react to the answers (question_rules) and the advisor proposes (advisor) ----------
from app import advisor, question_rules as QR  # noqa: E402


def test_an_answer_recommends_options_of_later_questions_and_says_why():
    b, _ = B.apply_patch(fresh(), {"rev": 0, "set": {"focus": "Potency"}})
    g = QR.guide(b, {"techniques": ["HPLC-DAD", "GC-MS"], "reference_standards": ["CRS", "SST", "Internal"]})
    assert g["questions"]["techniques"]["recommended"] == [{"value": "HPLC-DAD", "because": ["focus: Potency"]}]
    assert [r["value"] for r in g["questions"]["reference_standards"]["recommended"]] == ["CRS", "SST"]
    assert g["questions"]["techniques"]["depends_on"] == ["focus", "sample_types"]


def test_a_changed_answer_makes_only_its_dependents_stale_and_never_a_locked_one():
    b, _ = B.apply_patch(fresh(), {"rev": 0, "set": {"focus": "Potency", "techniques": ["HPLC-DAD"],
                                                       "acceptance": ["LOD NMT 12 %"], "performer": "QC Analyst"}})
    b, _ = B.apply_patch(b, {"rev": 1, "lock": ["acceptance"]})
    b, ev = B.apply_patch(b, {"rev": 2, "set": {"focus": "Contaminants"}})
    assert b["fields"]["techniques"]["stale"] and not b["fields"]["performer"]["stale"]
    assert b["fields"]["acceptance"]["state"] == "locked" and not b["fields"]["acceptance"]["stale"]
    assert [e["key"] for e in ev if e["op"] == "stale"] == ["techniques"]


def test_a_transport_title_points_to_the_transport_question_bank():
    b = B.new_brief("sop", {"title_en": "Transport of bulk cannabis"})
    assert QR.guide(b, {})["questionnaire_hint"] == "sop_transport"
    assert QR.guide(B.new_brief("sop", {"title_en": "Sampling"}), {})["questionnaire_hint"] == ""


def test_the_advisor_answer_is_kept_to_the_questions_asked():
    asked = {"techniques": {"label": "Techniques", "multi": True, "options": ["HPLC-DAD"]},
             "doc.purpose": {"label": "Purpose", "multi": False, "options": []}}
    raw = {"proposals": [
        {"key": "techniques", "options": [{"value": "GC-MS", "why": "terpenes", "source": "E1"}, {"value": ""}],
         "pick": ["GC-MS", "invented"]},
        {"key": "doc.purpose", "options": [{"value": "To define sampling", "why": "x"}], "pick": "not offered"},
        {"key": "made_up", "options": [{"value": "x"}]}]}
    out = advisor.clean(raw, asked)
    assert set(out) == {"techniques", "doc.purpose"}
    assert out["techniques"] == {"options": [{"value": "GC-MS", "why": "terpenes", "source": "E1"}], "pick": ["GC-MS"]}
    assert out["doc.purpose"]["pick"] == "" and out["doc.purpose"]["options"][0]["source"] == "house practice"
    assert advisor._first_json('Here: ```json\n{"proposals": []}\n```') == {"proposals": []}
    text = advisor.prompt(fresh(), asked, "[E1] house", "[R1] reg", [{"name": "a.md", "text": "src"}])
    assert "techniques: Techniques (several may be chosen)" in text and "SOURCE FILE «a.md»" in text


def test_suggest_keeps_proposals_and_never_overwrites_a_decision(api, monkeypatch):
    c, store, _ = api
    seen = {}

    async def fake(brief, asked, sources, client=None, rag=None):
        seen["asked"] = set(asked)
        return {"proposals": {k: {"options": [{"value": "HPLC-DAD", "why": "potency", "source": "E1"}],
                                  "pick": ["HPLC-DAD"] if asked[k]["multi"] else "HPLC-DAD"} for k in asked},
                "notes": []}
    monkeypatch.setattr(advisor, "propose", fake)
    b = c.post("/briefs", json={"package": "sop", "meta": {"title_en": "Potency"}}, headers=h()).json()
    assert "guide" in b and b["proposals"] == {}
    b = c.patch(f"/briefs/{b['id']}", json={"rev": 0, "set": {"focus": "Potency"}}, headers=h()).json()
    assert b["guide"]["questions"]["techniques"]["recommended"][0]["value"] == "HPLC-DAD"
    assert c.post(f"/briefs/{b['id']}/suggest", json={"rev": 0}, headers=h()).status_code == 409
    assert c.post(f"/briefs/{b['id']}/suggest", json={"rev": 1, "keys": ["nope"]}, headers=h()).status_code == 400
    r = c.post(f"/briefs/{b['id']}/suggest", json={"rev": 1, "keys": ["focus", "techniques"]}, headers=h()).json()
    assert seen["asked"] == {"techniques"}                     # focus is decided: not asked about
    nb = r["brief"]
    assert nb["fields"]["focus"] == {**b["fields"]["focus"]}
    assert nb["fields"]["techniques"]["state"] == "suggested" and nb["fields"]["techniques"]["value"] == ["HPLC-DAD"]
    assert nb["proposals"]["techniques"]["options"][0]["source"] == "E1" and nb["rev"] == 2
