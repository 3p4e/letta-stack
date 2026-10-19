# API surface: auth gate, questionnaires, direct build (PASS + FAIL), and
# graceful degradation with no DB/Letta configured. Fully offline.
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import builder, db  # noqa: E402
from app.config import settings  # noqa: E402
from app.main import app  # noqa: E402

KEY = "test-key-123"


@pytest.fixture(autouse=True)
def _configure(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "api_key", KEY)
    monkeypatch.setattr(settings, "out_dir", tmp_path)
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def h(key=KEY):
    return {"X-API-Key": key}


def test_health_open(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["ok"] is True


def test_auth_required(client):
    assert client.get("/questionnaires").status_code == 401
    assert client.get("/questionnaires", headers=h("wrong")).status_code == 401


def test_unconfigured_key_is_503(client, monkeypatch):
    monkeypatch.setattr(settings, "api_key", "")
    assert client.get("/questionnaires", headers=h("")).status_code == 503


def test_questionnaires(client):
    r = client.get("/questionnaires", headers=h())
    assert r.status_code == 200
    keys = [q["key"] for q in r.json()["questionnaires"]]
    assert "sop_qc" in keys and "annex_form" in keys
    r = client.get("/questionnaires/sop_qc", headers=h())
    assert r.status_code == 200 and r.json()["doctype"] == "SOP"
    assert client.get("/questionnaires/nope", headers=h()).status_code == 404


def test_transport_questionnaire_answers_itself_from_defaults(client):
    """sop_transport mirrors the approved WHSOP_003: every question has a default, so an
    untouched questionnaire still yields a complete brief."""
    from app.questionnaires import QUESTIONNAIRES, apply_defaults
    r = client.get("/questionnaires/sop_transport", headers=h())
    assert r.status_code == 200 and r.json()["doctype"] == "SOP"
    filled = apply_defaults("sop_transport", {})
    asked = [q["key"] for rnd in QUESTIONNAIRES["sop_transport"]["rounds"] for q in rnd["questions"]]
    assert asked and all(filled.get(k) for k in asked)
    assert "Written MoIA confirmation mandatory before dispatch" in filled["authorities"]


def test_brief_carries_requester_instructions_and_sources():
    from app.pipeline import _brief
    b = _brief("sop_transport", {"lane": "QUALIFIED"}, "  Write for road transport only.  ",
               ["EU GDP 2013/C 343/01", " ", "WHO TRS 961 Annex 9"])
    assert "Requester's instructions:\nWrite for road transport only." in b
    assert "- EU GDP 2013/C 343/01\n- WHO TRS 961 Annex 9" in b
    assert "Sources named" not in _brief("sop_qc", {}, "", [])


def test_form_row_written_mk_tilde_en_renders_as_two_labels(tmp_path):
    """'Label MK~~Label EN ||| value' (the grammar DocEngine taught until 11.10.2026) must not print '~~'."""
    import docx
    from app import builder
    md = ("<!--HEADERDATA\nmk_title: Тест\nen_title: Test\ncode: T-FORM\n"
          "version: 1.0\ndoctype: FORM\norient: portrait\n-->\n"
          "# 1.0 СОДРЖИНА|CONTENT\n[[FORM]]\nДатум~~Date ||| \nВерзија ||| Version ||| \n[[/FORM]]\n")
    r = builder.build(md, tmp_path, "t-form")
    text = "\n".join(c.text for t in docx.Document(str(r.path)).tables for row in t.rows for c in row.cells)
    assert "~~" not in text and "Датум" in text and "Date" in text and "Version" in text


def test_direct_build_pass(client):
    md = (
        "<!--HEADERDATA\nmk_title: Тест\nen_title: Test\ncode: QCT901\n"
        "version: 1.0\ndoctype: FORM\norient: portrait\n-->\n"
        "# 1.0 ИНФОРМАЦИИ|INFORMATION\n[[FORM:grid]]\nДатум~~Date|||\n[[/FORM]]\n"
    )
    r = client.post("/build", json={"markdown": md, "out_name": "t1", "meta": {"code": "QCT901"}}, headers=h())
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True and "RESULT: PASS" in body["verify"]


def test_direct_build_fail_gated(client, monkeypatch):
    monkeypatch.setattr(builder, "run_verify",
                         lambda p, min_pt=6.0, require_bilingual=True: (False, "RESULT: FAIL"))
    md = (
        "<!--HEADERDATA\nmk_title: Тест\nen_title: Test\ncode: QCT902\n"
        "version: 1.0\ndoctype: FORM\norient: portrait\n-->\n"
        "# 1.0 ИНФОРМАЦИИ|INFORMATION\nТекст.|Text.\n"
    )
    r = client.post("/build", json={"markdown": md, "out_name": "t2", "meta": {"code": "QCT902"}}, headers=h())
    assert r.status_code == 422
    assert "FAIL" in r.json()["detail"]["verify"]


def test_workflow_degrades_without_db(client, monkeypatch):
    """Degraded mode is FORCED here, not inherited from the environment.

    This used to rely on no DOCENGINE_DATABASE_URL being set, which was true
    only because the suite had no database at all. Now that CI gives docengine
    a real Postgres (so app/db.py is actually exercised) an ambient-absence
    assertion would just flip to 200 and the degradation path would go
    untested — the opposite of what adding a database was for. Patching
    db.ready() pins the behaviour itself: whatever the environment, an
    unavailable database must 503 rather than 500."""
    monkeypatch.setattr(db, "ready", lambda: False)
    r = client.post(
        "/workflows", headers=h(),
        json={"questionnaire": "sop_qc", "answers": {},
              "meta": {"title_mk": "а", "title_en": "a", "code": "QCT903"}},
    )
    assert r.status_code == 503
    assert client.get("/documents", headers=h()).status_code == 503


def test_workflow_validates_meta(client):
    r = client.post(
        "/workflows", headers=h(),
        json={"questionnaire": "sop_qc", "answers": {}, "meta": {"title_mk": "x"}},
    )
    assert r.status_code == 400
    r = client.post(
        "/workflows", headers=h(),
        json={"questionnaire": "nope", "answers": {}, "meta": {}},
    )
    assert r.status_code == 400


# ---- POST /workflows/{id}/review ----
JID = "11111111-2222-4333-8444-555555555555"


def _review_db(monkeypatch, tmp_path, status="awaiting_review", with_file=True):
    art = tmp_path / "TEST-1.docx"
    if with_file:
        art.write_bytes(b"docx")
    row = {"id": JID, "status": status, "stage": "format", "created_by": "ppdocwiz-session",
           "payload": {"questionnaire": "sop_qc", "meta": {"title_mk": "а", "title_en": "a", "code": "TEST-1", "doctype": "SOP"}},
           "result": {"qa_verdict": "FIX", "verify": "RESULT: PASS", "artifact": {"path": str(art), "bytes": 4}}}
    calls = {"docs": [], "updates": []}

    async def job_get(jid):
        return dict(row)

    async def job_claim(jid, frm, to):
        if row["status"] != frm:
            return False
        row["status"] = to
        return True

    async def job_update(jid, **f):
        calls["updates"].append(f)
        row.update({k: v for k, v in f.items() if k in ("status", "stage", "error", "result")})

    async def document_create(jid, meta):
        calls["docs"].append(meta)
        return "doc-1"

    async def job_merge_result(jid, extra):
        row["result"] = {**row["result"], **extra}
        calls["updates"].append({"result": dict(row["result"])})

    monkeypatch.setattr(db, "ready", lambda: True)
    for n, f in (("job_get", job_get), ("job_claim", job_claim), ("job_update", job_update), ("document_create", document_create),
                 ("job_merge_result", job_merge_result)):
        monkeypatch.setattr(db, n, f)
    return row, calls


def test_review_approve_registers_once(client, monkeypatch, tmp_path):
    row, calls = _review_db(monkeypatch, tmp_path)
    r = client.post(f"/workflows/{JID}/review", headers=h(), json={"decision": "approve", "note": "ok", "reviewer": "QC Manager"})
    assert r.status_code == 200 and row["status"] == "done"
    assert len(calls["docs"]) == 1 and calls["docs"][0]["code"] == "TEST-1"
    review = row["result"]["review"]
    assert row["result"]["document_id"] == "doc-1" and row["result"]["qa_verdict"] == "FIX"   # merged, nothing lost
    assert review["decision"] == "approve" and review["by"] == "QC Manager" and review["qa_verdict"] == "FIX"
    # a second approval finds the job no longer awaiting review
    assert client.post(f"/workflows/{JID}/review", headers=h(), json={"decision": "approve"}).status_code == 409
    assert len(calls["docs"]) == 1


def test_review_return_requires_a_note_and_fails_the_job(client, monkeypatch, tmp_path):
    row, calls = _review_db(monkeypatch, tmp_path)
    assert client.post(f"/workflows/{JID}/review", headers=h(), json={"decision": "return", "note": "  "}).status_code == 422
    r = client.post(f"/workflows/{JID}/review", headers=h(), json={"decision": "return", "note": "§3.2 RACI legend missing"})
    assert r.status_code == 200 and row["status"] == "failed" and not calls["docs"]
    assert row["error"] == "returned for revision: §3.2 RACI legend missing" and row["result"]["review"]["decision"] == "return"


def test_review_rejects_bad_input_and_wrong_state(client, monkeypatch, tmp_path):
    _review_db(monkeypatch, tmp_path, status="running")
    assert client.post(f"/workflows/{JID}/review", headers=h(), json={"decision": "maybe"}).status_code == 422
    assert client.post("/workflows/not-a-uuid/review", headers=h(), json={"decision": "approve"}).status_code == 404
    assert client.post(f"/workflows/{JID}/review", headers=h(), json={"decision": "approve"}).status_code == 409
    assert client.post(f"/workflows/{JID}/review", json={"decision": "approve"}).status_code == 401


def test_review_approve_without_the_built_file_is_410(client, monkeypatch, tmp_path):
    row, calls = _review_db(monkeypatch, tmp_path, with_file=False)
    assert client.post(f"/workflows/{JID}/review", headers=h(), json={"decision": "approve"}).status_code == 410
    assert row["status"] == "awaiting_review" and not calls["docs"]


def test_review_approve_that_cannot_register_goes_back_to_awaiting_review(client, monkeypatch, tmp_path):
    """The claim moves the job to 'running'; a failed registration used to leave it there (review 14.10.2026)."""
    row, calls = _review_db(monkeypatch, tmp_path)

    async def boom(jid, meta):
        raise RuntimeError("db down")

    monkeypatch.setattr(db, "document_create", boom)
    with pytest.raises(RuntimeError):
        client.post(f"/workflows/{JID}/review", headers=h(), json={"decision": "approve"})
    assert row["status"] == "awaiting_review"


def test_running_service_reaps_stale_jobs_on_an_interval():
    import inspect
    from app import main
    assert main.REAP_INTERVAL_S <= 15 * 60
    assert "_reap_forever()" in inspect.getsource(main.lifespan)


def test_non_ascii_key_is_401_not_500(client):
    r = client.get("/questionnaires", headers={"X-API-Key": "ключ".encode()})
    assert r.status_code == 401


@pytest.mark.parametrize("meta", [
    {"title_mk": "а", "title_en": "a", "code": 123},
    {"title_mk": "а\nbilingual: no", "title_en": "a", "code": "X"},
    {"title_mk": "а", "title_en": "a", "code": "X", "version": "01 -->"},
])
def test_workflow_meta_is_checked_before_any_generation(client, monkeypatch, meta):
    """These used to fail only at assembly or build, after every section had been generated."""
    started = []
    monkeypatch.setattr(db, "ready", lambda: True)
    monkeypatch.setattr("app.main.run_workflow", lambda jid: started.append(jid))
    r = client.post("/workflows", headers=h(), json={"questionnaire": "sop_qc", "meta": meta})
    assert r.status_code == 400 and not started


@pytest.mark.parametrize("meta,out_name", [({}, "labels_raw (final) v3"), ({"code": "QASOP_0YY"}, "x"), ({"code": "pasted"}, "x")])
def test_a_file_name_is_never_registered_as_a_document_code(client, meta, out_name):
    md = "<!--HEADERDATA\nmk_title: Т\nen_title: T\ncode: X\ndoctype: FORM\n-->\n# 1 А | A\nтекст ||| text\n"
    r = client.post("/build", json={"markdown": md, "out_name": out_name, "meta": meta}, headers=h())
    assert r.status_code == 400 and "document code" in r.json()["detail"]


def test_register_routes(client, monkeypatch):
    assert client.get("/register").status_code == 401
    rows = client.get("/register", headers=h(), params={"family": "QCSOP", "status": "effective"}).json()["documents"]
    assert rows and all(r["code"].startswith("QCSOP") and r["status"] == "effective" for r in rows)
    monkeypatch.setattr(db, "ready", lambda: False)
    assert client.get("/register/next", headers=h(), params={"family": "QCSOP"}).json()["code"] == "QCSOP026"
    assert client.get("/register/next", headers=h(), params={"parent": "QCSOP 011"}).json()["code"] == "QCSOP011A10"
    assert client.get("/register/next", headers=h()).status_code == 400


def test_codes_are_stored_in_house_form(client, monkeypatch):
    seen = {}

    async def fake_create(kind, payload, by=""):
        seen.update(payload)
        return "00000000-0000-0000-0000-000000000001"
    monkeypatch.setattr(db, "ready", lambda: True)
    monkeypatch.setattr(db, "job_create", fake_create)
    monkeypatch.setattr("app.main.LettaClient", lambda: type("L", (), {"configured": True})())
    async def no_run(jid):
        return None
    monkeypatch.setattr("app.main.run_workflow", no_run)
    r = client.post("/workflows", headers=h(), json={"questionnaire": "annex_form", "parent_sop": "WHSOP_003",
                                                     "meta": {"title_mk": "а", "title_en": "a", "code": "WHSOP_003_A08"}})
    assert r.status_code == 200
    assert seen["meta"]["code"] == "WHSOP003A08" and seen["parent_sop"] == "WHSOP003"


@pytest.mark.parametrize("extra", [{"meta": {"title_mk": "б", "title_en": "Request for Sampling", "code": "QCSOP001A01"}},
                                   {"meta": {"title_mk": "б", "title_en": "Request", "code": "QCSOP026"},
                                    "parent_sop": "QCSOP001"}])
def test_workflow_refuses_an_annex_with_the_sop_question_set(client, monkeypatch, extra):
    """19.10.2026: Jobs → Re-run of a job carrying sop_qc built QCSOP001A01 as an SOP four times. The engine refuses
    it before any job exists, whichever screen sends it."""
    created = []

    async def fake_create(kind, payload, by=""):
        created.append(payload)
        return "00000000-0000-0000-0000-000000000002"
    monkeypatch.setattr(db, "ready", lambda: True)
    monkeypatch.setattr(db, "job_create", fake_create)
    monkeypatch.setattr("app.main.LettaClient", lambda: type("L", (), {"configured": True})())
    r = client.post("/workflows", headers=h(), json={"questionnaire": "sop_qc", **extra})
    assert r.status_code == 422 and "annex_form" in r.json()["detail"]
    assert created == []


def test_rerun_copies_the_stored_payload_and_records_it_on_the_brief(client, monkeypatch):
    """Review 19.10.2026: Jobs > Re-run rebuilt the payload client-side from six fields, dropping the sources' text,
    the package annexes and the brief link. The engine now re-runs from the stored payload."""
    stored = {"questionnaire": "annex_form", "parent_sop": "QCSOP001", "source_texts": [{"name": "s.docx", "text": "t"}],
              "package_annexes": [], "brief_id": "11111111-1111-1111-1111-111111111111", "requested_by": "c.cekic",
              "meta": {"title_mk": "б", "title_en": "Form", "code": "QCSOP001A01"}}
    jobs = {"00000000-0000-0000-0000-00000000000a": {"id": "00000000-0000-0000-0000-00000000000a", "kind": "workflow",
                                                      "status": "failed", "payload": stored, "created_by": "c.cekic"}}
    brief = {"id": stored["brief_id"], "rev": 3, "job_ids": ["00000000-0000-0000-0000-00000000000a"], "status": "open"}
    created, saved = [], []

    async def job_get(jid):
        return jobs.get(jid)

    async def job_create(kind, payload, by=""):
        created.append((kind, payload, by))
        return "00000000-0000-0000-0000-00000000000b"

    async def brief_get(bid):
        return brief

    async def brief_save(b, old_rev, events):
        saved.append((b, old_rev, events))
        return True
    monkeypatch.setattr(db, "ready", lambda: True)
    monkeypatch.setattr(db, "job_get", job_get)
    monkeypatch.setattr(db, "job_create", job_create)
    monkeypatch.setattr(db, "brief_get", brief_get)
    monkeypatch.setattr(db, "brief_save", brief_save)
    monkeypatch.setattr("app.main.LettaClient", lambda: type("L", (), {"configured": True})())

    async def no_run(jid):
        return None
    monkeypatch.setattr("app.main.run_workflow", no_run)
    r = client.post("/workflows/00000000-0000-0000-0000-00000000000a/rerun", headers=h())
    assert r.status_code == 200 and r.json()["job_id"].endswith("b")
    kind, payload, by = created[0]
    assert payload["source_texts"] == stored["source_texts"] and payload["brief_id"] == stored["brief_id"]
    assert payload["rerun_of"].endswith("a") and by == "c.cekic"
    assert saved[0][0]["job_ids"][-1].endswith("b") and saved[0][1] == 3 and saved[0][2][0]["op"] == "build"
    # not failed → 409; an annex job that carried the SOP question set is refused like a new one
    jobs["00000000-0000-0000-0000-00000000000a"]["status"] = "done"
    assert client.post("/workflows/00000000-0000-0000-0000-00000000000a/rerun", headers=h()).status_code == 409
    jobs["00000000-0000-0000-0000-00000000000a"]["status"] = "failed"
    stored["questionnaire"] = "sop_qc"
    assert client.post("/workflows/00000000-0000-0000-0000-00000000000a/rerun", headers=h()).status_code == 422


def test_approving_an_sop_starts_its_package_annexes(client, monkeypatch, tmp_path):
    """Review 19.10.2026: the annexes of a package used to start when the SOP was parked for review; now the approved
    SOP is what they read."""
    from app import pipeline
    row, calls = _review_db(monkeypatch, tmp_path)
    row["payload"]["meta"]["code"] = "QCSOP026"
    row["payload"]["package_annexes"] = [{"title_en": "Log"}, {"title_mk": "Листа", "kind": "checklist"}]
    created = []

    async def job_create(kind, payload, by=""):
        created.append(payload)
        return f"annex-{len(created)}"

    async def taken(*a):
        return set()

    async def no_run(jid):
        return None
    monkeypatch.setattr(db, "job_create", job_create)
    monkeypatch.setattr(db, "codes_in_use", taken)
    monkeypatch.setattr(db, "codes_of_brief", taken)
    monkeypatch.setattr(pipeline, "run_workflow", no_run)
    r = client.post(f"/workflows/{JID}/review", headers=h(), json={"decision": "approve", "note": "ok"})
    assert r.status_code == 200 and row["status"] == "done"
    assert [c["meta"]["code"] for c in created] == ["QCSOP026A01", "QCSOP026A02"]
    assert all(c["package_of"] == JID and c["parent_sop"] == "QCSOP026" for c in created)
    assert [j["job_id"] for j in row["result"]["package_jobs"]] == ["annex-1", "annex-2"]
    assert row["result"]["document_id"] == "doc-1"                      # merged beside the registration, nothing lost


def test_house_related_route_and_source_roles(client, monkeypatch):
    """Head of QC, 19.10.2026: the Parent SOP page shows the SOP's own documents; a source says what it is for."""
    async def related(code):
        return {"code": code, "found": True, "version": "01", "title_en": "x", "title_mk": "", "related": []}
    monkeypatch.setattr(db, "ready", lambda: True)
    monkeypatch.setattr("app.main.house.related", related)
    r = client.get("/house/related/qcsop_001", headers=h())
    assert r.status_code == 200 and r.json()["code"] == "QCSOP001"
    assert client.get("/house/related/not-a-code", headers=h()).status_code == 400
    brief = {"id": "11111111-1111-1111-1111-111111111111", "rev": 1, "status": "open", "package": "annex",
             "questionnaire": "annex_form", "meta": {}, "fields": {}, "annexes": [], "job_ids": [], "proposals": {},
             "parent_sop": ""}
    seen = {}

    async def brief_get(bid):
        return brief

    async def brief_sources(bid, with_text=True):
        return []

    async def brief_source_role(bid, sid, role, actor):
        seen.update(sid=sid, role=role, actor=actor)
        return True
    monkeypatch.setattr(db, "brief_get", brief_get)
    monkeypatch.setattr(db, "brief_sources", brief_sources)
    monkeypatch.setattr(db, "brief_source_role", brief_source_role)
    sid = "22222222-2222-2222-2222-222222222222"
    assert client.patch(f"/briefs/{brief['id']}/sources/{sid}", headers=h(), json={"role": "poem"}).status_code == 422
    r = client.patch(f"/briefs/{brief['id']}/sources/{sid}", headers=h(), json={"role": "format", "actor": "c.cekic"})
    assert r.status_code == 200 and seen == {"sid": sid, "role": "format", "actor": "c.cekic"}
    r = client.post(f"/briefs/{brief['id']}/sources", headers=h(), json={"name": "a.md", "content_b64": "YQ==", "role": "poem"})
    assert r.status_code == 422


def test_a_form_under_an_sop_passes_the_workflow_guard(client, monkeypatch):
    """Head of QC, 19.10.2026: QCT002 is written to QCSOP001 under its own number; QCSOP026 under QCSOP001 is not."""
    async def fake_create(kind, payload, by=""):
        return "00000000-0000-0000-0000-000000000003"
    monkeypatch.setattr(db, "ready", lambda: True)
    monkeypatch.setattr(db, "job_create", fake_create)
    monkeypatch.setattr("app.main.LettaClient", lambda: type("L", (), {"configured": True})())

    async def no_run(jid):
        return None
    monkeypatch.setattr("app.main.run_workflow", no_run)
    ok = client.post("/workflows", headers=h(), json={"questionnaire": "annex_form", "parent_sop": "QCSOP001",
                                                      "meta": {"title_mk": "б", "title_en": "Request", "code": "QCT002"}})
    assert ok.status_code == 200
    bad = client.post("/workflows", headers=h(), json={"questionnaire": "annex_form", "parent_sop": "QCSOP001",
                                                       "meta": {"title_mk": "б", "title_en": "Request", "code": "QCSOP026"}})
    assert bad.status_code == 422 and "no annex number" in bad.json()["detail"]


def test_a_house_conflict_is_registered_only_with_a_reason(client, monkeypatch, tmp_path):
    """Head of QC, 19.10.2026: a draft that conflicts with an approved document is never registered silently."""
    art = tmp_path / "d.docx"; art.write_bytes(b"x")
    job = {"id": "00000000-0000-0000-0000-0000000000c1", "kind": "workflow", "status": "awaiting_review", "created_by": "x",
           "payload": {"questionnaire": "annex_form", "meta": {"code": "QCT002", "title_mk": "б", "title_en": "R", "version": "03"}},
           "result": {"artifact": {"path": str(art), "bytes": 1}, "verify": "PASS",
                      "house_check": {"verdicts": {"QCSOP001": {"verdict": "CONFLICT", "detail": "x"},
                                                   "QCT002": {"verdict": "CHANGES", "detail": "v03"}}}}}
    merged = {}

    async def job_get(jid):
        return job

    async def job_claim(jid, a, b):
        return True

    async def document_create(jid, d):
        return "doc-9"

    async def job_merge_result(jid, extra):
        merged.update(extra)

    async def job_update(jid, **f):
        return None

    async def start_package(*a, **k):
        return None
    monkeypatch.setattr(db, "ready", lambda: True)
    for name, fn in (("job_get", job_get), ("job_claim", job_claim), ("document_create", document_create),
                     ("job_merge_result", job_merge_result), ("job_update", job_update)):
        monkeypatch.setattr(db, name, fn)
    monkeypatch.setattr("app.main.start_package", start_package, raising=False)
    url = f"/workflows/{job['id']}/review"
    r = client.post(url, headers=h(), json={"decision": "approve"})
    assert r.status_code == 422 and "QCSOP001" in r.json()["detail"] and "QCT002" not in r.json()["detail"]
    r = client.post(url, headers=h(), json={"decision": "approve", "note": "QCSOP001 §6 is revised with this form"})
    assert r.status_code == 200 and merged["review"]["house_conflicts"] == ["QCSOP001"]
