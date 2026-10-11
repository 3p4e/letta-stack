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


def test_direct_build_pass(client):
    md = (
        "<!--HEADERDATA\nmk_title: Тест\nen_title: Test\ncode: T-1\n"
        "version: 1.0\ndoctype: FORM\norient: portrait\n-->\n"
        "# 1.0 ИНФОРМАЦИИ|INFORMATION\n[[FORM:grid]]\nДатум~~Date|||\n[[/FORM]]\n"
    )
    r = client.post("/build", json={"markdown": md, "out_name": "t1"}, headers=h())
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True and "RESULT: PASS" in body["verify"]


def test_direct_build_fail_gated(client, monkeypatch):
    monkeypatch.setattr(builder, "run_verify",
                         lambda p, min_pt=6.0, require_bilingual=True: (False, "RESULT: FAIL"))
    md = (
        "<!--HEADERDATA\nmk_title: Тест\nen_title: Test\ncode: T-2\n"
        "version: 1.0\ndoctype: FORM\norient: portrait\n-->\n"
        "# 1.0 ИНФОРМАЦИИ|INFORMATION\nТекст.|Text.\n"
    )
    r = client.post("/build", json={"markdown": md, "out_name": "t2"}, headers=h())
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
              "meta": {"title_mk": "а", "title_en": "a", "code": "X-1"}},
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

    monkeypatch.setattr(db, "ready", lambda: True)
    for n, f in (("job_get", job_get), ("job_claim", job_claim), ("job_update", job_update), ("document_create", document_create)):
        monkeypatch.setattr(db, n, f)
    return row, calls


def test_review_approve_registers_once(client, monkeypatch, tmp_path):
    row, calls = _review_db(monkeypatch, tmp_path)
    r = client.post(f"/workflows/{JID}/review", headers=h(), json={"decision": "approve", "note": "ok", "reviewer": "QC Manager"})
    assert r.status_code == 200 and row["status"] == "done"
    assert len(calls["docs"]) == 1 and calls["docs"][0]["code"] == "TEST-1"
    review = calls["updates"][-1]["result"]["review"]
    assert review["decision"] == "approve" and review["by"] == "QC Manager" and review["qa_verdict"] == "FIX"
    # a second approval finds the job no longer awaiting review
    assert client.post(f"/workflows/{JID}/review", headers=h(), json={"decision": "approve"}).status_code == 409
    assert len(calls["docs"]) == 1


def test_review_return_requires_a_note_and_fails_the_job(client, monkeypatch, tmp_path):
    row, calls = _review_db(monkeypatch, tmp_path)
    assert client.post(f"/workflows/{JID}/review", headers=h(), json={"decision": "return", "note": "  "}).status_code == 422
    r = client.post(f"/workflows/{JID}/review", headers=h(), json={"decision": "return", "note": "§3.2 RACI legend missing"})
    assert r.status_code == 200 and row["status"] == "failed" and not calls["docs"]
    assert calls["updates"][-1]["error"] == "returned for revision: §3.2 RACI legend missing"


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
