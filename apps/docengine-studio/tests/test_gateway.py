"""DocEngine Studio gateway contract tests (faked upstream; no network)."""
import json

import pytest

from app import services


# ------------------------------------------------------------------ auth basics

def test_anonymous_is_rejected(client):
    assert client.get("/api/me").status_code == 401


def test_principal_reports_capabilities(client, author):
    body = client.get("/api/me", headers=author).json()
    assert body["kind"] == "human"
    assert body["role"] == "author"
    assert "qms.author" in body["capabilities"]
    assert "qms.approve" not in body["capabilities"]


def test_viewer_cannot_build(client, viewer):
    r = client.post("/api/build", headers=viewer, json={"markdown": "x" * 30, "out_name": "t"})
    assert r.status_code == 403


# ------------------------------------------------------------------ registry

def test_registry_lifecycle_and_guards(client, author, approver):
    created = client.post(
        "/api/registry",
        headers=author,
        json={"title": "SOP Test 001", "doc_type": "sop", "language": "MK"},
    )
    assert created.status_code == 200, created.text
    doc = created.json()
    assert doc["status"] == "draft"
    doc_id = doc["id"]

    # illegal jump draft -> approved
    bad = client.post("/api/registry/%s/status" % doc_id, headers=author, json={"status": "approved"})
    assert bad.status_code == 409

    # legal path draft -> in_review -> approved
    assert client.post("/api/registry/%s/status" % doc_id, headers=author, json={"status": "in_review"}).status_code == 200
    approval = client.post(
        "/api/registry/%s/approvals" % doc_id,
        headers=approver,
        json={"decision": "approved", "comment": "ok"},
    )
    assert approval.status_code == 200, approval.text
    assert client.get("/api/registry/%s" % doc_id, headers=author).json()["status"] == "approved"


def test_effective_requires_approval_path(client, author):
    doc = client.post("/api/registry", headers=author, json={"title": "SOP Test 002"}).json()
    r = client.post("/api/registry/%s/status" % doc["id"], headers=author, json={"status": "effective"})
    assert r.status_code == 409


# ------------------------------------------------------------------ machine clients

def test_machine_client_is_scope_limited_and_cannot_approve(client, admin, author):
    scopes = client.get("/api/machine-scopes", headers=admin).json()["scopes"]
    assert "qms.approve" not in scopes
    assert "qms.sign" not in scopes

    r = client.post("/api/clients", headers=admin, json={"name": "ragflow-ingest", "scopes": ["qms.read"]})
    assert r.status_code == 200, r.text
    creds = r.json()
    token = "%s.%s" % (creds["client_id"], creds["client_secret"])
    machine = {"Authorization": "Bearer " + token}

    me = client.get("/api/me", headers=machine).json()
    assert me["kind"] == "machine"
    assert me["capabilities"] == ["qms.read"]

    # authoring is refused for a read-only machine client
    denied = client.post("/api/registry", headers=machine, json={"title": "hack"})
    assert denied.status_code == 403

    # approval is refused even for a machine holding more scopes
    r2 = client.post("/api/clients", headers=admin, json={"name": "risky", "scopes": ["qms.read", "qms.review"]})
    assert r2.status_code == 200
    assert "qms.approve" not in [s for s in ["qms.review", "qms.read"]]


def test_forbidden_scope_is_rejected(client, admin):
    r = client.post("/api/clients", headers=admin, json={"name": "bad", "scopes": ["qms.approve"]})
    assert r.status_code == 400


# ------------------------------------------------------------------ audit chain

def test_audit_chain_verifies_and_detects_tampering(client, author):
    client.post("/api/registry", headers=author, json={"title": "Audit Subject"})
    body = client.get("/api/audit", headers={"X-Auth-Request-User": "a", "X-Auth-Request-Role": "admin"}).json()
    assert body["chain"]["ok"] is True
    assert body["chain"]["events"] > 0

    from app import db
    with db.tx() as conn:
        conn.execute("UPDATE audit SET payload='{\"tampered\":true}' WHERE seq=(SELECT MIN(seq) FROM audit)")
    assert db.audit_verify()["ok"] is False


# ------------------------------------------------------------------ lanes

def test_official_lane_fails_closed_without_ragflow(client, admin):
    r = client.post("/api/ask", headers=admin, json={"question": "What is the CoA for batch X?", "intent": "coa_lookup"})
    assert r.status_code == 503
    assert r.json()["error"] == "lane_unavailable"
    # the refusal must be recorded
    events = client.get("/api/audit", headers=admin).json()["events"]
    assert any(e["event"] == "lane.refused" for e in events)


def test_advisory_lane_unavailable_is_503(client, admin):
    r = client.post("/api/ask", headers=admin, json={"question": "How do we calibrate?", "intent": "qa_query"})
    assert r.status_code == 503


def test_lane_routes_listed(client, admin):
    routes = {r["intent"]: r for r in client.get("/api/routing/lanes", headers=admin).json()["routes"]}
    assert routes["coa_lookup"]["lane"] == "ragflow"
    assert routes["coa_lookup"]["fail_closed"] == 1
    assert routes["assistant_chat"]["lane"] == "letta"
    assert routes["assistant_chat"]["fail_closed"] == 0


def test_model_routes_enforce_producer_checker_split(client, admin):
    routes = {r["fn"]: r for r in client.get("/api/routing/models", headers=admin).json()["routes"]}
    assert routes["sop_section_authoring"]["provider"] == "moonshot"
    assert routes["qa_audit"]["provider"] == "deepseek"
    assert routes["qa_audit"]["temperature"] == 0.0

    from app import router as routing
    with pytest.raises(ValueError):
        routing.set_model_route("qa_audit", "moonshot", "alegretto", 0.5, None, "a")
    with pytest.raises(ValueError):
        routing.set_lane_route("coa_lookup", "letta", False, None, "a")


# ------------------------------------------------------------------ MCP

def test_mcp_initialize_and_scope_filtered_tools(client, admin, viewer):
    init = client.post("/mcp", headers=admin, json={"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    assert init.status_code == 200
    assert init.json()["result"]["serverInfo"]["name"] == "docengine-studio"

    admin_tools = {t["name"] for t in client.post(
        "/mcp", headers=admin, json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
    ).json()["result"]["tools"]}
    viewer_tools = {t["name"] for t in client.post(
        "/mcp", headers=viewer, json={"jsonrpc": "2.0", "id": 3, "method": "tools/list"}
    ).json()["result"]["tools"]}

    assert "docengine_build" in admin_tools
    assert "docengine_build" not in viewer_tools
    assert "docengine_ask" in admin_tools
    assert "docengine_ask" not in viewer_tools
    # read-only tool is visible to a viewer
    assert "docengine_registry_list" in viewer_tools


def test_mcp_never_exposes_approve_or_sign(client, admin):
    tools = {t["name"] for t in client.post(
        "/mcp", headers=admin, json={"jsonrpc": "2.0", "id": 4, "method": "tools/list"}
    ).json()["result"]["tools"]}
    assert not any("approve" in t or "sign" in t for t in tools)


def test_mcp_tool_call_denies_missing_capability(client, viewer):
    r = client.post("/mcp", headers=viewer, json={
        "jsonrpc": "2.0", "id": 5, "method": "tools/call",
        "params": {"name": "docengine_build", "arguments": {"markdown": "x" * 40}},
    })
    body = r.json()["result"]
    assert body["isError"] is True
    assert "missing capability" in body["content"][0]["text"]


def test_mcp_without_auth_is_rejected(client):
    r = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    assert r.status_code == 401


def test_mcp_resources_are_scope_gated(client, viewer, admin):
    v = {r["uri"] for r in client.post("/mcp", headers=viewer, json={"jsonrpc": "2.0", "id": 6, "method": "resources/list"}).json()["result"]["resources"]}
    a = {r["uri"] for r in client.post("/mcp", headers=admin, json={"jsonrpc": "2.0", "id": 7, "method": "resources/list"}).json()["result"]["resources"]}
    assert "docengine://lane-routes" in v
    assert "docengine://audit/head" not in v
    assert "docengine://audit/head" in a


# ------------------------------------------------------------------ upstream fake

def test_workflow_passthrough_records_job(client, author, monkeypatch):
    async def fake_start(self, body):
        return {"job_id": "11111111-1111-1111-1111-111111111111", "status": "queued"}

    from app import clients as cl
    monkeypatch.setattr(cl.DocEngineClient, "start_workflow", fake_start, raising=True)

    r = client.post("/api/workflows", headers=author, json={
        "questionnaire": "sop_master",
        "answers": {"a": "b"},
        "meta": {"title_mk": "Наслов", "title_en": "Title", "code": "SOP-001"},
    })
    assert r.status_code == 200, r.text
    assert r.json()["job_id"].startswith("1111")

    from app import db
    with db.tx() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE upstream_id=?", ("11111111-1111-1111-1111-111111111111",)).fetchone()
    assert row is not None


def test_build_reports_verify_failure(client, author, monkeypatch):
    async def fake_build(self, body):
        return {"__status__": 422, "detail": {"verify": "FAILED", "error": "verify FAILED"}}

    from app import clients as cl
    monkeypatch.setattr(cl.DocEngineClient, "build", fake_build, raising=True)

    r = client.post("/api/build", headers=author, json={"markdown": "x" * 40, "out_name": "t"})
    assert r.status_code == 200
    assert r.json()["ok"] is False
    assert r.json()["status"] == 422
