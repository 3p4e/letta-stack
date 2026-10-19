# GET /engine/environment: the Fleet & health page's engine panel, measured rather than sampled.
# The page showed a 501 ("no engine-environment endpoint yet") until 18.10.2026. Fully offline:
# the renderer, the registry and Letta are replaced by fakes.
import asyncio
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import db, engine_env, main
from app.config import settings
from app.main import app

KEY = "test-key-123"


@pytest.fixture(autouse=True)
def _configure(monkeypatch):
    monkeypatch.setattr(settings, "api_key", KEY)
    engine_env._font_cache.clear()
    yield
    engine_env._font_cache.clear()


# ------------------------------------------------------------------ fonts
def test_a_face_the_pdf_embeds_alone_is_ok():
    row = engine_env.classify("Calibri", {"Calibri", "Calibri-Bold"})
    assert row["ok"] and row["file"] == "Calibri, Calibri-Bold"


def test_a_face_the_pdf_does_not_embed_is_a_substitution():
    row = engine_env.classify("Calibri", {"Carlito", "Carlito-Bold"})
    assert not row["ok"] and "Carlito" in row["missing"]


def test_a_fallback_beside_the_face_means_letters_fell_back():
    row = engine_env.classify("Arial Narrow", {"ArialNarrow", "DejaVuSans"})
    assert not row["ok"] and "DejaVuSans" in row["missing"]


def test_probe_document_asks_for_the_face_in_every_slot():
    import io
    import zipfile
    xml = zipfile.ZipFile(io.BytesIO(engine_env.probe_docx("Arial Narrow", "АБВ"))).read("word/document.xml").decode()
    for slot in ("ascii", "hAnsi", "cs", "eastAsia"):
        assert f'w:{slot}="Arial Narrow"' in xml


def test_font_probe_reports_a_failed_render_and_does_not_cache_it():
    async def broken(_):
        raise RuntimeError("renderer answered 503")
    rows = asyncio.run(engine_env.font_rows(broken, now=0))
    assert all(not r["ok"] and r["file"] == "probe failed" for r in rows)
    assert not engine_env._font_cache


# ------------------------------------------------------------------ audit and drift
def test_audit_reads_the_pp_verify_result_line():
    rows = engine_env.audit_rows([
        {"code": "WHSOP_003_A05", "created_at": "2026-10-18T14:43:00", "verify": "checks…\nRESULT: PASS"},
        {"code": "QASOP_031", "created_at": "2026-10-17T09:00:00", "verify": "RESULT: FAIL"},
        {"code": "X_01", "created_at": "2026-10-16T09:00:00", "verify": ""},
    ])
    assert [r["ok"] for r in rows] == [True, False, False]
    assert rows[0]["run"] == "2026-10-18 14:43 WHSOP_003_A05"
    assert rows[2]["note"] == "no pp_verify result recorded"


def test_drift_names_each_block_that_differs_from_fleet_yaml():
    spec = {"house_rules": "RULES", "agents": [{"name": "gf_a", "persona": "P"}, {"name": "gf_b", "persona": "Q"}]}
    live = [{"name": "gf_a", "memory": {"blocks": [{"label": "gf_house_rules", "value": "RULES"},
                                                    {"label": "persona", "value": "P, edited on the server"}]}}]
    rows = engine_env.drift_rows(spec, "GLOSSARY", live)
    keys = {r["key"]: r for r in rows}
    assert keys["gf_a · persona"]["live"] == "23 chars"
    assert keys["gf_a · gf_glossary_mk"]["live"] == "absent"
    assert keys["gf_b"]["live"] == "missing"
    assert "gf_a · gf_house_rules" not in keys
    assert keys["memory blocks identical to fleet.yaml"] == {"key": "memory blocks identical to fleet.yaml",
                                                             "manifest": "3", "live": "1"}


# ------------------------------------------------------------------ the route
def test_route_requires_the_key():
    with TestClient(app) as c:
        assert c.get("/engine/environment").status_code == 401


def test_route_reports_every_part_measured(monkeypatch):
    async def fake_render(_blob, name="probe.docx"):
        return b"%PDF /BaseFont /ABCDEF+Calibri /BaseFont /ABCDEF+ArialNarrow"

    async def fake_docs(limit=6):
        return [{"code": "WHSOP_003_A05", "created_at": "2026-10-18T14:43:00", "verify": "RESULT: PASS"}]

    class FakeLetta:
        async def list_agents(self):
            return []

    monkeypatch.setattr(main, "_gotenberg", fake_render)
    monkeypatch.setattr(db, "documents_verify_recent", fake_docs)
    monkeypatch.setattr(main, "LettaClient", FakeLetta)
    with TestClient(app) as c:
        r = c.get("/engine/environment", headers={"X-API-Key": KEY})
    assert r.status_code == 200
    j = r.json()
    assert j["synced"] is True and j["hash"] == j["hashExpected"] != "none"
    assert [f["face"] for f in j["fonts"]] == ["Calibri", "Arial Narrow"] and all(f["ok"] for f in j["fonts"])
    assert j["glyphAudit"][0]["ok"] is True
    assert j["manifestDrift"][0]["live"] == "missing"          # no agent on the fake server


def test_route_survives_letta_and_registry_outages(monkeypatch):
    async def fake_render(_blob, name="probe.docx"):
        return b"%PDF /BaseFont /Calibri /BaseFont /ArialNarrow"

    async def no_db(limit=6):
        raise RuntimeError("pool not ready")

    class DownLetta:
        async def list_agents(self):
            raise RuntimeError("connection refused")

    monkeypatch.setattr(main, "_gotenberg", fake_render)
    monkeypatch.setattr(db, "documents_verify_recent", no_db)
    monkeypatch.setattr(main, "LettaClient", DownLetta)
    with TestClient(app) as c:
        j = c.get("/engine/environment", headers={"X-API-Key": KEY}).json()
    assert j["glyphAudit"][0]["ok"] is False and "registry" in j["glyphAudit"][0]["note"]
    assert j["manifestDrift"][0]["live"].startswith("unreachable")
