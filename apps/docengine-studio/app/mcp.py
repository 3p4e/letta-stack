# docengine_studio.app.mcp - Model Context Protocol surface (JSON-RPC 2.0 over HTTP).
#
# Deliberately purpose-built rather than wrapping the Rust letta-mcp bridge, which
# is documented as truncating and returning false aggregates (see
# server/runbooks/bridge_and_rest_quirks.md).
#
# Tool lists are filtered by the caller's capability scopes. Approve/sign tools do
# not exist here at all: regulated decisions stay with human principals.
from __future__ import annotations

from typing import Any

from . import router, services
from .security import Principal

PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "docengine-studio", "version": "0.1.0"}

# name -> (capability, description, input schema)
TOOLS: dict[str, dict] = {
    "docengine_list_questionnaires": {
        "capability": "qms.read",
        "description": "List the DocEngine Mode-A question banks (keys and titles).",
        "schema": {"type": "object", "properties": {}, "additionalProperties": False},
        "handler": lambda p, a: services.list_questionnaires(),
    },
    "docengine_get_questionnaire": {
        "capability": "qms.read",
        "description": "Fetch one question bank by key.",
        "schema": {"type": "object", "properties": {"key": {"type": "string"}}, "required": ["key"], "additionalProperties": False},
        "handler": lambda p, a: services.get_questionnaire(p["key"]),
    },
    "docengine_start_workflow": {
        "capability": "qms.author",
        "description": "Start a questionnaire -> SOP workflow. Returns a job id to poll.",
        "schema": {
            "type": "object",
            "properties": {
                "questionnaire": {"type": "string"},
                "answers": {"type": "object"},
                "meta": {"type": "object", "properties": {"title_mk": {"type": "string"}, "title_en": {"type": "string"}, "code": {"type": "string"}, "version": {"type": "string"}}},
                "document_id": {"type": "string"},
            },
            "required": ["questionnaire", "meta"],
            "additionalProperties": False,
        },
        "handler": lambda p, a: services.start_workflow(p, a),
    },
    "docengine_get_workflow": {
        "capability": "qms.read",
        "description": "Poll a workflow job by id (stage, status, error).",
        "schema": {"type": "object", "properties": {"job_id": {"type": "string"}}, "required": ["job_id"], "additionalProperties": False},
        "handler": lambda p, a: services.get_workflow(p["job_id"]),
    },
    "docengine_build": {
        "capability": "qms.build",
        "description": "Build a verified .docx from caller-supplied bilingual Markdown. A FAILed document is refused (HTTP 422 semantics) and never returned.",
        "schema": {
            "type": "object",
            "properties": {"markdown": {"type": "string"}, "out_name": {"type": "string"}, "meta": {"type": "object"}},
            "required": ["markdown"],
            "additionalProperties": False,
        },
        "handler": lambda p, a: services.build_document(p, a),
    },
    "docengine_list_documents": {
        "capability": "qms.read",
        "description": "List the DocEngine registry (only documents that passed verification exist here).",
        "schema": {"type": "object", "properties": {}, "additionalProperties": False},
        "handler": lambda p, a: services.list_certificates(),
    },
    "docengine_get_document": {
        "capability": "qms.read",
        "description": "Fetch a registry row including its verification report.",
        "schema": {"type": "object", "properties": {"document_id": {"type": "string"}}, "required": ["document_id"], "additionalProperties": False},
        "handler": lambda p, a: services.get_certificate(p["document_id"]),
    },
    "docengine_registry_list": {
        "capability": "qms.read",
        "description": "List Studio registry entries with lifecycle status (draft/in_review/approved/effective/superseded).",
        "schema": {"type": "object", "properties": {"status": {"type": "string"}, "limit": {"type": "integer"}}, "additionalProperties": False},
        "handler": lambda p, a: services.list_registry(p.get("status"), int(p.get("limit", 50))),
    },
    "docengine_ask": {
        "capability": "assistant.ask",
        "description": "Ask a question through the lane router. intent=official_evidence|coa_lookup uses the RAGFlow official lane and FAILS CLOSED (no answer if no verified evidence). intent=qa_query|assistant_chat|summarisation uses the Letta advisory lane and is labelled advisory.",
        "schema": {
            "type": "object",
            "properties": {
                "question": {"type": "string"},
                "intent": {"type": "string", "enum": ["official_evidence", "coa_lookup", "qa_query", "assistant_chat", "summarisation"]},
                "agent": {"type": "string"},
            },
            "required": ["question"],
            "additionalProperties": False,
        },
        "handler": lambda p, a: services.ask(p["question"], p.get("intent", "qa_query"), a, p.get("agent")),
    },
}

RESOURCES = {
    "docengine://lane-routes": {"capability": "qms.read", "description": "Lane routing table (official vs advisory, fail-closed flags)."},
    "docengine://model-routes": {"capability": "qms.read", "description": "Model routing table (producer vs checker provider per function)."},
    "docengine://audit/head": {"capability": "audit.read", "description": "Hash-chain head and verification status."},
}


def _visible_tools(principal: Principal) -> list[dict]:
    return [
        {"name": name, "description": spec["description"], "inputSchema": spec["schema"]}
        for name, spec in TOOLS.items()
        if principal.can(spec["capability"])
    ]


def _visible_resources(principal: Principal) -> list[dict]:
    return [
        {"uri": uri, "name": uri.split("://", 1)[1], "description": spec["description"], "mimeType": "application/json"}
        for uri, spec in RESOURCES.items()
        if principal.can(spec["capability"])
    ]


def _read_resource(uri: str, principal: Principal) -> Any:
    spec = RESOURCES.get(uri)
    if not spec:
        raise KeyError("unknown resource: " + uri)
    if not principal.can(spec["capability"]):
        raise PermissionError("missing capability: " + spec["capability"])
    if uri == "docengine://lane-routes":
        return router.all_lane_routes()
    if uri == "docengine://model-routes":
        return router.all_model_routes()
    from . import db
    return db.audit_verify()


async def call_tool(name: str, arguments: dict, principal: Principal) -> Any:
    spec = TOOLS.get(name)
    if not spec:
        raise KeyError("unknown tool: " + name)
    if not principal.can(spec["capability"]):
        raise PermissionError("missing capability: %s for tool %s" % (spec["capability"], name))
    return await spec["handler"](arguments or {}, principal.sub)


def _err(code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": None, "error": {"code": code, "message": message}}


async def handle(payload: dict, principal: Principal) -> dict:
    """Handle one JSON-RPC request (single or batch entry)."""
    rid = payload.get("id")
    method = payload.get("method")
    params = payload.get("params") or {}

    def ok(result: Any) -> dict:
        return {"jsonrpc": "2.0", "id": rid, "result": result}

    if method == "initialize":
        return ok({
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {"listChanged": False}, "resources": {"subscribe": False, "listChanged": False}},
            "serverInfo": SERVER_INFO,
            "instructions": "Purely Plant DocEngine. Official intents fail closed. Approvals and signatures are human-only and unavailable over MCP.",
        })
    if method == "ping":
        return ok({})
    if method == "tools/list":
        return ok({"tools": _visible_tools(principal)})
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}
        try:
            result = await call_tool(name, args, principal)
        except PermissionError as e:
            return ok({"content": [{"type": "text", "text": str(e)}], "isError": True})
        except KeyError as e:
            return ok({"content": [{"type": "text", "text": str(e)}], "isError": True})
        except services.LaneUnavailable as e:
            # Official-lane refusals surface as errors, never as an answer.
            return ok({"content": [{"type": "text", "text": "lane refused: " + str(e)}], "isError": True})
        return ok({"content": [{"type": "text", "text": _json_dumps(result)}], "structuredContent": result, "isError": False})
    if method == "resources/list":
        return ok({"resources": _visible_resources(principal)})
    if method == "resources/read":
        uri = params.get("uri")
        try:
            data = _read_resource(uri, principal)
        except PermissionError as e:
            return _err(-32001, str(e))
        except KeyError as e:
            return _err(-32002, str(e))
        return ok({"contents": [{"uri": uri, "mimeType": "application/json", "text": _json_dumps(data)}]})
    return _err(-32601, "method not found: " + str(method))


def _json_dumps(value: Any) -> str:
    import json
    return json.dumps(value, default=str, ensure_ascii=False, indent=2)


async def dispatch(body: Any, principal: Principal) -> Any:
    """Dispatch a JSON-RPC body: dict or batch list. Notifications return None."""
    if isinstance(body, list):
        out = []
        for item in body:
            resp = await handle(item, principal) if isinstance(item, dict) else _err(-32600, "invalid request")
            if resp.get("id") is not None or "error" in resp:
                out.append(resp)
        return out or None
    if not isinstance(body, dict):
        return _err(-32600, "invalid request")
    resp = await handle(body, principal)
    if body.get("id") is None and "error" not in resp:
        return None
    return resp
