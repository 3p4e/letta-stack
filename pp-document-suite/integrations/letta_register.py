#!/usr/bin/env python3
"""
letta_register.py — register the Purely Plant document builder as a Letta custom tool and attach it
to the document-facing agents. Uses the documented Letta REST API (see ../../openapi_letta.json,
Letta API v0.16.8) directly via `requests` — no SDK version guesswork.

Endpoints used:
  POST  /v1/tools/                                create the tool (json_schema auto-derived from source)
  GET   /v1/agents/                               resolve agent ids by name
  PATCH /v1/agents/{agent_id}/tools/attach/{id}   attach the tool to an agent

Config via ENVIRONMENT ONLY (never hard-code secrets):
  LETTA_BASE_URL   e.g. https://letta.example.internal   (required)
  LETTA_TOKEN      bearer token                          (if the server requires auth)
  LETTA_MODE       'rest' (default) | 'inprocess'        which tool variant to register
  PP_AGENTS        comma list of agent NAMES to attach to
                   (default: qms_docx_formatter,pharma_docx_formatter)
  QMS_API_BASE     build-service URL baked into the rest tool's runtime env (informational)

Run:  LETTA_BASE_URL=... LETTA_TOKEN=... python3 letta_register.py
"""
import os, sys, json, inspect, urllib.parse
import requests
import pp_tool


def _headers():
    h = {"Content-Type": "application/json"}
    tok = os.environ.get("LETTA_TOKEN") or os.environ.get("LETTA_API_KEY")
    if tok:
        h["Authorization"] = "Bearer " + tok
    # Reaching Letta behind a runner / Traefik: Host header for routing + optional extra headers
    # (e.g. a runner auth token). LETTA_HOST_HEADER=letta.internal  LETTA_EXTRA_HEADERS='X-Runner-Token: ...'
    host = os.environ.get("LETTA_HOST_HEADER")
    if host:
        h["Host"] = host
    for part in (os.environ.get("LETTA_EXTRA_HEADERS", "") or "").split(";"):
        if ":" in part:
            k, v = part.split(":", 1)
            if k.strip():
                h[k.strip()] = v.strip()
    return h


def _base():
    b = os.environ.get("LETTA_BASE_URL")
    if not b:
        sys.exit("LETTA_BASE_URL is required (e.g. https://letta.host). Refusing to guess.")
    return b.rstrip("/")


def create_tool(base, func, pip_requirements):
    """Create/upsert a Letta tool from a Python function's source. json_schema is auto-generated
    by Letta from the source_code + docstring, so the docstring IS the tool contract."""
    payload = {
        "source_code": inspect.getsource(func),
        "source_type": "python",
        "description": (func.__doc__ or "").strip().splitlines()[0],
        "tags": ["purely-plant", "docx", "pp-document-suite"],
        "pip_requirements": [{"name": p} for p in pip_requirements],
    }
    r = requests.post(base + "/v1/tools/", headers=_headers(), data=json.dumps(payload), timeout=60)
    r.raise_for_status()
    t = r.json()
    print("  created tool id=%s name=%s" % (t.get("id"), t.get("name")))
    return t


def agents_by_name(base):
    r = requests.get(base + "/v1/agents/", headers=_headers(), timeout=60)
    r.raise_for_status()
    out = {}
    for a in r.json():
        out[a.get("name")] = a.get("id")
    return out


def attach(base, agent_id, tool_id):
    url = "%s/v1/agents/%s/tools/attach/%s" % (base, urllib.parse.quote(agent_id), urllib.parse.quote(tool_id))
    r = requests.patch(url, headers=_headers(), timeout=60)
    r.raise_for_status()
    return True


def main():
    base = _base()
    mode = os.environ.get("LETTA_MODE", "rest").lower()
    if mode == "inprocess":
        func, pips = pp_tool.build_pp_document, ["python-docx", "lxml"]
        note = "in-process — Letta host needs $PP_SUITE_DIR + python-docx"
    else:
        func, pips = pp_tool.build_pp_document_via_api, ["requests"]
        note = "rest — Letta host only needs $QMS_API_BASE reachable"
    print("Registering '%s' (%s)" % (func.__name__, note))

    tool = create_tool(base, func, pips)
    tool_id = tool.get("id")

    want = [s.strip() for s in os.environ.get("PP_AGENTS", "qms_docx_formatter,pharma_docx_formatter").split(",") if s.strip()]
    have = agents_by_name(base)
    print("Attaching to agents: %s" % ", ".join(want))
    for name in want:
        aid = have.get(name)
        if not aid:
            print("  ! agent not found on server: %s (skipped)" % name); continue
        attach(base, aid, tool_id)
        print("  attached -> %s (%s)" % (name, aid))
    print("Done. Remember to put the house rules (navy #2B547E, 9-section SOP, MK-first, "
          "abbreviations never translated) into each agent's persona/core memory.")


if __name__ == "__main__":
    main()
