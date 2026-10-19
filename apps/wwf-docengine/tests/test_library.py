# The Library's shelves (Head of QC, 18.10.2026): approved and in use, under revision, drafts, numbers, retired.
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import db, library  # noqa: E402
from app.config import settings  # noqa: E402
from app.main import app  # noqa: E402

REG = [
    {"code": "QCSOP022", "status": "effective", "version": "01", "title_en": "Chemicals"},
    {"code": "QCSOP011", "status": "effective_revising", "version": "01"},
    {"code": "QCSOP023", "status": "effective", "version": "01"},
    {"code": "QCSOP019", "status": "awaiting_signature"},
    {"code": "QCSOP020", "status": "withdrawn"},
    {"code": "QCT024", "status": "reserved"},
    {"code": "QCSOP013", "status": "draft"},
]


def test_every_code_lands_on_one_shelf():
    refs = [{"kind": "approved", "code": "QCSOP022", "version": "01", "id": "a"},
            {"kind": "wip", "code": "QCSOP011", "version": "03", "id": "w"},
            {"kind": "approved", "code": "QCSOP019", "version": "01", "id": "b"}]
    out = library.shelve(REG, refs, [{"code": "WHSOP003", "id": "d", "version": "01"}],
                         {"QCSOP023": [{"id": "j", "status": "awaiting_review"}]})
    where = {e["code"]: s for s, es in out["shelves"].items() for e in es}
    assert where == {"QCSOP022": "approved", "QCSOP011": "revision", "QCSOP023": "revision", "QCSOP019": "approved",
                     "QCSOP020": "retired", "QCT024": "numbers", "QCSOP013": "drafts", "WHSOP003": "drafts"}
    e19 = next(e for e in out["shelves"]["approved"] if e["code"] == "QCSOP019")
    assert "register says awaiting_signature" in e19["notes"][0]          # in use per DB3; the register lag is shown
    assert sum(out["counts"].values()) == 8


def test_the_library_route_needs_the_key_and_storage(monkeypatch):
    monkeypatch.setattr(settings, "api_key", "k")
    with TestClient(app) as c:
        assert c.get("/library").status_code == 401
        monkeypatch.setattr(db, "ready", lambda: False)
        assert c.get("/library", headers={"X-API-Key": "k"}).status_code == 503


def test_an_approved_document_is_indexed_once_in_db3(monkeypatch):
    monkeypatch.setattr(settings, "api_key", "k")
    store, indexed = {}, []

    async def upsert(doc, sha):
        changed = store.get("sha") != sha
        store.update(sha=sha, doc=doc)
        return "11111111-1111-1111-1111-111111111111", changed

    async def get(rid):
        return {"ragflow_doc_id": store.get("rf", "")}

    async def set_rf(rid, rf):
        store["rf"] = rf

    async def index_text(self, ds, name, text, replace_id=""):
        indexed.append((ds, name, replace_id, text[:40]))
        return f"rf-{len(indexed)}"

    monkeypatch.setattr(db, "ready", lambda: True)
    monkeypatch.setattr(db, "reference_upsert", upsert)
    monkeypatch.setattr(db, "reference_get", get)
    monkeypatch.setattr(db, "reference_set_ragflow", set_rf)
    monkeypatch.setattr("app.ragflow.RagflowClient.index_text", index_text)
    body = {"kind": "approved", "code": "QCSOP 022", "version": "01", "title_en": "Chemicals", "markdown": "x" * 50}
    with TestClient(app) as c:
        r = c.put("/reference", json=body, headers={"X-API-Key": "k"}).json()
        assert r["code"] == "QCSOP022" and r["changed"] and r["ragflow_doc_id"] == "rf-1"
        assert indexed[0][:3] == (settings.ragflow_example_datasets[0], "QCSOP022_v01.md", "")
        assert c.put("/reference", json=body, headers={"X-API-Key": "k"}).json()["ragflow_doc_id"] == "rf-1"
        assert len(indexed) == 1                                           # unchanged text: not uploaded again
        r = c.put("/reference", json={**body, "markdown": "y" * 50}, headers={"X-API-Key": "k"}).json()
        assert indexed[1][2] == "rf-1" and r["ragflow_doc_id"] == "rf-2"   # a new text replaces the old entry
        wip = c.put("/reference", json={**body, "kind": "wip", "markdown": "z" * 50}, headers={"X-API-Key": "k"}).json()
        assert len(indexed) == 2 and wip["changed"]                         # work in progress is never indexed


# ---- review 19.10.2026 ----

def test_the_library_keeps_the_newest_approved_version_by_number_not_text():
    refs = [{"kind": "approved", "code": "QCSOP022", "version": "1.9", "id": "old"},
            {"kind": "approved", "code": "QCSOP022", "version": "1.10", "id": "new"}]
    out = library.shelve([], refs, [], {})
    assert out["shelves"]["approved"][0]["approved"]["id"] == "new"


def test_a_failed_index_clears_the_stale_id_so_the_next_put_retries(monkeypatch):
    """A RAGFlow failure left the old ragflow_doc_id on the row, so the next PUT of the same text saw "unchanged and
    indexed" and the new text was never indexed."""
    from app.ragflow import RagflowError
    monkeypatch.setattr(settings, "api_key", "k")
    store, calls = {"rf": "rf-old", "sha": "x"}, {"index": 0, "set": []}

    async def upsert(doc, sha):
        changed = store.get("sha") != sha
        store.update(sha=sha)
        return "11111111-1111-1111-1111-111111111111", changed

    async def get(rid):
        return {"ragflow_doc_id": store.get("rf", "")}

    async def set_rf(rid, rf):
        store["rf"] = rf
        calls["set"].append(rf)

    async def index_text(self, ds, name, text, replace_id=""):
        calls["index"] += 1
        if calls["index"] == 1:
            raise RagflowError("RAGFlow unreachable: timeout")
        return "rf-new"
    monkeypatch.setattr(db, "ready", lambda: True)
    monkeypatch.setattr(db, "reference_upsert", upsert)
    monkeypatch.setattr(db, "reference_get", get)
    monkeypatch.setattr(db, "reference_set_ragflow", set_rf)
    monkeypatch.setattr("app.ragflow.RagflowClient.index_text", index_text)
    body = {"kind": "approved", "code": "QCSOP 022", "version": "01", "markdown": "y" * 50}
    with TestClient(app) as c:
        r = c.put("/reference", json=body, headers={"X-API-Key": "k"}).json()
        assert r["index_error"].startswith("RAGFlow unreachable") and r["ragflow_doc_id"] == "" and calls["set"] == [""]
        r = c.put("/reference", json=body, headers={"X-API-Key": "k"}).json()         # same text: retried, not skipped
        assert not r["changed"] and r["ragflow_doc_id"] == "rf-new" and calls["index"] == 2
