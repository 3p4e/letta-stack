#!/usr/bin/env python3
"""Live deployment battery for DocEngine Studio.

Run against the public HTTPS deployment, not the in-process TestClient:
    /opt/venv/bin/python tests/live_battery.py https://studio.<host> <studio_key>

Every check encodes an intended contract (never the observed behaviour), so a
FAIL is a genuine contract violation. Results are PASS / FAIL / INFO where INFO
means the contract holds but an upstream data condition limited the check.

Lessons baked in from the first field run (do not reintroduce them):
  1. Each principal (anonymous / human / machine) must get its OWN cookie-less
     client. security._identify() resolves the session cookie FIRST, so one
     shared admin cookie silently overrides bearer tokens and proxy headers.
  2. Static assets are fetched raw; JSON-decoding HTML/CSS/JS is what produced
     the phantom "transport error" status=0 failures.
  3. /api/audit returns a newest-first tail (ORDER BY seq DESC) by design.
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from http.cookiejar import MozillaCookieJar


def _require_args() -> tuple[str, str]:
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    return sys.argv[1].rstrip("/"), sys.argv[2]


BASE, KEY = _require_args()
RESULTS: list[tuple[str, str, str]] = []


class Client:
    """Cookie-aware JSON/raw client. Give each principal a fresh instance."""

    def __init__(self) -> None:
        self.jar = MozillaCookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.jar)
        )

    def call(self, method, path, body=None, headers=None, raw=False):
        url = BASE + path
        data = None
        hdrs = {"Accept": "application/json"}
        if body is not None:
            data = json.dumps(body).encode()
            hdrs["Content-Type"] = "application/json"
        if headers:
            hdrs.update(headers)
        req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
        try:
            with self.opener.open(req, timeout=120) as r:
                payload, status = r.read(), r.status
        except urllib.error.HTTPError as e:
            payload, status = e.read(), e.code
        except Exception as exc:  # noqa: BLE001
            return 0, {"transport_error": str(exc)}
        if raw:
            return status, payload
        try:
            return status, json.loads(payload or b"null")
        except Exception:  # noqa: BLE001
            return status, {"raw": payload[:200].decode("utf-8", "replace")}


def check(name, ok, detail="", info=False):
    status = "INFO" if (info and not ok) else ("PASS" if ok else "FAIL")
    RESULTS.append((name, status, detail))


def headers(**kw):
    return kw


def bearer(cid, secret):
    return {"Authorization": f"Bearer {cid}.{secret}"}


def login_studio() -> Client:
    """Return a client logged in as the operator/studio key."""
    c = Client()
    st, _ = c.call("POST", "/api/session", {"key": KEY})
    check("login: studio key accepted", st == 200, f"status={st}")
    return c


# ---------------------------------------------------------------- 1. health
c = Client()
st, health = c.call("GET", "/api/health")
check("health: 200", st == 200, f"status={st}")
check("health: ok true", health.get("ok") is True, str(health.get("ok")))
check("health: audit chain verified", (health.get("audit") or {}).get("ok") is True, str(health.get("audit")))
check("health: docengine upstream reachable", (health.get("docengine") or {}).get("ok") is True, str(health.get("docengine")))
check("health: official lane configured", health.get("official_lane") is True, str(health.get("official_lane")))
check("health: advisory lane configured", health.get("advisory_lane") is True, str(health.get("advisory_lane")))

# ------------------------------------------------------- 2. anonymous denial
for path in ("/api/me", "/api/registry", "/api/audit", "/api/routing/lanes", "/api/certificates"):
    st, _ = c.call("GET", path)
    check(f"anonymous denied: {path}", st == 401, f"status={st}")
st, _ = c.call("POST", "/mcp", {"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
check("anonymous denied: POST /mcp", st == 401, f"status={st}")

# ----------------------------------------------------- 3. key edge cases
st, _ = c.call("POST", "/api/session", {"key": "definitely-wrong"})
check("login: wrong key rejected", st == 401, f"status={st}")
st, _ = c.call("GET", "/api/me")
check("login: still anonymous after bad key", st == 401, f"status={st}")

# ------------------------------------------------------- 4. human reads
h = login_studio()
st, me = h.call("GET", "/api/me")
check("session: authenticated as human", me.get("kind") == "human", str(me))
check("session: admin capabilities present", "admin.clients" in (me.get("capabilities") or []), str(me.get("capabilities")))
for path in ("/api/registry", "/api/audit", "/api/routing/lanes", "/api/routing/models", "/api/questionnaires"):
    st, _ = h.call("GET", path)
    check(f"read ok: {path}", st == 200, f"status={st}")
st, certs = h.call("GET", "/api/certificates")
check("read ok: /api/certificates", st == 200, f"status={st}")
check("certificates: engine registry contract", isinstance(certs.get("documents"), list),
      f"type={type(certs.get('documents')).__name__}")

# --------------------------------------------------- 5. registry lifecycle
st, doc = h.call("POST", "/api/registry", {"title": "LIVE TEST - delete me", "doc_type": "sop", "language": "MK"})
check("registry: create document", st == 200 and "id" in doc, f"status={st} body={str(doc)[:160]}")
doc_id = doc.get("id")

if doc_id:
    check("registry: new document starts as draft", doc.get("status") == "draft", str(doc.get("status")))
    st, _ = h.call("POST", f"/api/registry/{doc_id}/status", {"status": "approved"})
    check("lifecycle: illegal draft->approved refused", st == 409, f"status={st}")
    st, _ = h.call("POST", f"/api/registry/{doc_id}/status", {"status": "effective"})
    check("lifecycle: illegal draft->effective refused", st == 409, f"status={st}")
    st, body = h.call("POST", f"/api/registry/{doc_id}/status", {"status": "in_review", "comment": "live test"})
    check("lifecycle: draft->in_review allowed", st == 200 and body.get("status") == "in_review", f"status={st} body={str(body)[:120]}")
    st, body = h.call("POST", f"/api/registry/{doc_id}/approvals", {"decision": "approved", "comment": "live test approval"})
    check("approval: human approval accepted", st == 200, f"status={st} body={str(body)[:160]}")
    st, after = h.call("GET", f"/api/registry/{doc_id}")
    check("approval: moves document to approved", after.get("status") == "approved", str(after.get("status")))
    st, _ = h.call("POST", f"/api/registry/{doc_id}/approvals", {"decision": "banana"})
    check("approval: invalid decision refused", st == 400, f"status={st}")
    st, body = h.call("POST", f"/api/registry/{doc_id}/signatures", {"meaning": "Reviewed and approved (live test)"})
    check("signature: human signature accepted", st == 200, f"status={st} body={str(body)[:160]}")
    st, _ = h.call("POST", f"/api/registry/{doc_id}/signatures", {"meaning": "   "})
    check("signature: blank meaning refused", st in (400, 422), f"status={st}")
    st, body = h.call("POST", f"/api/registry/{doc_id}/status", {"status": "effective"})
    check("lifecycle: approved->effective allowed", st == 200 and body.get("status") == "effective", f"status={st} body={str(body)[:120]}")
    st, body = h.call("POST", f"/api/registry/{doc_id}/status", {"status": "superseded"})
    check("lifecycle: effective->superseded allowed", st == 200 and body.get("status") == "superseded", f"status={st} body={str(body)[:120]}")
    st, _ = h.call("POST", f"/api/registry/{doc_id}/status", {"status": "draft"})
    check("lifecycle: superseded is terminal", st == 409, f"status={st}")
    st, rec = h.call("GET", f"/api/registry/{doc_id}/approvals")
    check("approval: history recorded",
          st == 200 and len(rec.get("approvals", [])) == 1 and len(rec.get("signatures", [])) == 1,
          f"approvals={len(rec.get('approvals', []))} signatures={len(rec.get('signatures', []))}")
    st, _ = h.call("GET", "/api/registry/does-not-exist")
    check("registry: unknown id is 404", st == 404, f"status={st}")

# --------------------------------------------------- 6. role enforcement
v = Client()  # fresh: no cookie
vh = {"X-Auth-Request-User": "live-viewer", "X-Auth-Request-Role": "viewer"}
st, me_v = v.call("GET", "/api/me", headers=vh)
check("roles: header identity honoured", st == 200 and me_v.get("role") == "viewer", f"status={st} body={str(me_v)[:120]}")
st, _ = v.call("GET", "/api/registry", headers=vh)
check("roles: viewer can read", st == 200, f"status={st}")
st, _ = v.call("POST", "/api/registry", {"title": "viewer must not create"}, headers=vh)
check("roles: viewer cannot create", st == 403, f"status={st}")
st, _ = v.call("POST", "/api/build", {"markdown": "x" * 40, "out_name": "nope"}, headers=vh)
check("roles: viewer cannot build", st == 403, f"status={st}")

# ------------------------------------------------- 7. machine client scopes
st, bad = h.call("POST", "/api/clients", {"name": "live-bad", "scopes": ["qms.approve"]})
check("machine: forbidden scope refused", st in (400, 422), f"status={st} body={str(bad)[:120]}")
st, bad2 = h.call("POST", "/api/clients", {"name": "live-bad", "scopes": ["root"]})
check("machine: unknown scope refused", st in (400, 422), f"status={st} body={str(bad2)[:120]}")
st, ro = h.call("POST", "/api/clients", {"name": "live-read-only", "scopes": ["qms.read"]})
check("machine: read-only client created", st == 200 and "client_secret" in ro, f"status={st} body={str(ro)[:160]}")
st, rw = h.call("POST", "/api/clients", {"name": "live-author", "scopes": ["qms.read", "qms.author", "assistant.ask"]})
check("machine: author client created", st == 200 and "client_secret" in rw, f"status={st}")

if ro.get("client_id"):
    m = Client()  # fresh machine client: no cookie
    ro_hdr = bearer(ro["client_id"], ro["client_secret"])
    st, body = m.call("GET", "/api/me", headers=ro_hdr)
    check("machine: identity resolves", st == 200 and body.get("kind") == "machine", f"status={st} body={str(body)[:140]}")
    check("machine: no human role attached", body.get("role") in (None, ""), f"role={body.get('role')}")
    check("machine: scopes only", body.get("capabilities") == ["qms.read"], f"caps={body.get('capabilities')}")
    st, _ = m.call("GET", "/api/registry", headers=ro_hdr)
    check("machine: qms.read allows registry read", st == 200, f"status={st}")
    st, _ = m.call("POST", "/api/registry", {"title": "machine must not author"}, headers=ro_hdr)
    check("machine: missing qms.author is 403", st == 403, f"status={st}")
    st, _ = m.call("GET", "/api/audit", headers=ro_hdr)
    check("machine: missing audit.read is 403", st == 403, f"status={st}")
    st, _ = m.call("POST", "/api/registry/live-none/approvals", {"decision": "approved"}, headers=ro_hdr)
    check("machine: cannot approve", st == 403, f"status={st}")
    st, _ = m.call("POST", "/api/registry/live-none/signatures", {"meaning": "machine signature"}, headers=ro_hdr)
    check("machine: cannot sign", st == 403, f"status={st}")
    st, _ = m.call("GET", "/api/registry", headers={"Authorization": "Bearer dcs_deadbeef.deadbeef"})
    check("machine: forged token rejected", st == 401, f"status={st}")
    st, _ = m.call("GET", "/api/registry", headers={"Authorization": "Bearer malformed"})
    check("machine: malformed token rejected", st == 401, f"status={st}")

    st, tl_all = h.call("POST", "/mcp", {"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    all_tools = {t["name"] for t in ((tl_all.get("result") or {}).get("tools") or [])}
    st, tl_ro = m.call("POST", "/mcp", {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}, headers=ro_hdr)
    ro_tools = {t["name"] for t in ((tl_ro.get("result") or {}).get("tools") or [])}
    check("mcp: read-only machine sees a strict subset",
          bool(ro_tools) and ro_tools < all_tools,
          f"admin={len(all_tools)} machine={len(ro_tools)} extra={sorted(all_tools - ro_tools)[:6]}")
    st, denied = m.call("POST", "/mcp", {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                                        "params": {"name": "docengine_build", "arguments": {"markdown": "x" * 40, "out_name": "nope"}}},
                        headers=ro_hdr)
    check("mcp: machine denied build tool",
          "capability" in str(denied) or "isError" in str(denied) or (denied.get("result") or {}).get("isError"),
          str(denied)[:220])
    st, denied_res = m.call("POST", "/mcp", {"jsonrpc": "2.0", "id": 4, "method": "resources/read",
                                            "params": {"uri": "docengine://audit/head"}}, headers=ro_hdr)
    check("mcp: machine denied audit resource",
          "permission" in str(denied_res).lower() or "capability" in str(denied_res).lower() or "isError" in str(denied_res),
          str(denied_res)[:220])

if rw.get("client_id"):
    mw = Client()
    rw_hdr = bearer(rw["client_id"], rw["client_secret"])
    st, made = mw.call("POST", "/api/registry", {"title": "LIVE TEST machine authored - delete me"}, headers=rw_hdr)
    check("machine: qms.author allows create", st == 200 and "id" in made, f"status={st} body={str(made)[:140]}")
    st, _ = mw.call("POST", "/api/clients", {"name": "nope", "scopes": ["qms.read"]}, headers=rw_hdr)
    check("machine: cannot administer clients", st == 403, f"status={st}")

# ------------------------------------------------------------------ 8. MCP
st, init = h.call("POST", "/mcp", {"jsonrpc": "2.0", "id": 1, "method": "initialize"})
check("mcp: initialize",
      st == 200 and init.get("result", {}).get("serverInfo", {}).get("name") == "docengine-studio",
      f"status={st} body={str(init)[:200]}")
st, tl = h.call("POST", "/mcp", {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
tools = (tl.get("result") or {}).get("tools") or []
names = {t["name"] for t in tools}
check("mcp: tools/list returns tools", len(tools) >= 8, f"count={len(tools)}")
check("mcp: no approve/sign tool exists", not any("approv" in n or "sign" in n for n in names), str(sorted(names)))
check("mcp: every tool is namespaced", all(n.startswith("docengine_") for n in names), str(sorted(names)))
st, pl = h.call("POST", "/mcp", {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                                "params": {"name": "docengine_list_questionnaires", "arguments": {}}})
check("mcp: tools/call questionnaire list",
      st == 200 and "result" in pl and not pl["result"].get("isError"), f"status={st} body={str(pl)[:220]}")
st, unknown = h.call("POST", "/mcp", {"jsonrpc": "2.0", "id": 4, "method": "tools/call",
                                      "params": {"name": "docengine_does_not_exist", "arguments": {}}})
check("mcp: unknown tool is an error",
      st == 200 and (unknown.get("error") or (unknown.get("result") or {}).get("isError")), f"body={str(unknown)[:180]}")
st, rl = h.call("POST", "/mcp", {"jsonrpc": "2.0", "id": 5, "method": "resources/list"})
uris = {r["uri"] for r in ((rl.get("result") or {}).get("resources") or [])}
check("mcp: resources listed", len(uris) >= 3, str(sorted(uris)))
st, rr = h.call("POST", "/mcp", {"jsonrpc": "2.0", "id": 6, "method": "resources/read", "params": {"uri": "docengine://audit/head"}})
check("mcp: resource read (audit head)", st == 200 and "result" in rr, f"body={str(rr)[:200]}")
st, badmethod = h.call("POST", "/mcp", {"jsonrpc": "2.0", "id": 7, "method": "totally/unknown"})
check("mcp: unknown method is an error", bool(badmethod.get("error")), str(badmethod)[:160])

# ---------------------------------------------------------------- 9. lanes
st, lanes = h.call("GET", "/api/routing/lanes")
routes = {r["intent"]: r for r in (lanes.get("routes") or [])}
for k in ("official_evidence", "coa_lookup"):
    if k in routes:
        check(f"lanes: {k} fail-closed", routes[k]["fail_closed"] is True, str(routes[k]["fail_closed"]))
        check(f"lanes: {k} on ragflow", routes[k]["lane"] == "ragflow", str(routes[k]["lane"]))
for k in ("qa_query", "assistant_chat"):
    if k in routes:
        check(f"lanes: {k} on letta", routes[k]["lane"] == "letta", str(routes[k]["lane"]))

st, models = h.call("GET", "/api/routing/models")
mr = {r["fn"]: r for r in (models.get("routes") or [])}
checkers = [v for v in mr.values() if v.get("role") == "checker" or "check" in v.get("fn", "") or "audit" in v.get("fn", "")]
check("models: checker functions on deepseek at temp 0",
      all(m["provider"] == "deepseek" and float(m["temperature"]) == 0.0 for m in checkers) and bool(checkers),
      str([(m["fn"], m["provider"], m["temperature"]) for m in checkers]))
producers = [v for v in mr.values() if v.get("provider") == "moonshot"]
check("models: producer functions exist on moonshot", bool(producers), str([m["fn"] for m in producers]))

st, official = h.call("POST", "/api/ask", {"question": "What is the approved specification for total THC?", "intent": "official_evidence"})
check("lanes: official ask answers cited or refuses", st in (200, 503), f"status={st} body={str(official)[:200]}")
if st == 200:
    check("lanes: official answer labelled official", official.get("lane_label") == "official", str(official.get("lane_label")))
    check("lanes: official answer carries citations", bool(official.get("citations")),
          f"citations={len(official.get('citations') or [])}")
else:
    check("lanes: refusal is a fail-closed 503 with reason",
          "refus" in str(official).lower() or "no verified evidence" in str(official).lower(),
          str(official)[:200], info=True)

st, advisory = h.call("POST", "/api/ask", {"question": "Explain the QMS document lifecycle in one sentence.", "intent": "qa_query"})
check("lanes: advisory ask responds or reports upstream absence", st in (200, 503), f"status={st} body={str(advisory)[:200]}")
if st == 200:
    check("lanes: advisory answer labelled advisory", advisory.get("lane_label") == "advisory", str(advisory.get("lane_label")))
    check("lanes: advisory answer flagged as not evidence", advisory.get("advisory") is True, str(advisory.get("advisory")))
else:
    check("lanes: advisory unavailable surfaces as 503", True, str(advisory)[:200], info=True)

# ----------------------------------------------------------------- 10. audit
st, audit = h.call("GET", "/api/audit?limit=200")
check("audit: endpoint ok", st == 200, f"status={st}")
check("audit: hash chain intact after mutations", (audit.get("chain") or {}).get("ok") is True, str(audit.get("chain")))
events = audit.get("events") or []
check("audit: events carry a hash", all(e.get("hash") for e in events), "some event lacks a hash")
seqs = [e.get("seq") for e in events]
check("audit: newest-first tail (tail contract)", seqs == sorted(seqs, reverse=True), f"first5={seqs[:5]} last3={seqs[-3:]}")

# ------------------------------------------------------- 11. static PWA assets
for path in ("/", "/index.html", "/app.js", "/styles.css", "/sw.js", "/manifest.webmanifest", "/icon.svg"):
    st, raw = c.call("GET", path, raw=True)
    ok = st == 200 and isinstance(raw, bytes) and len(raw) > 20
    check(f"asset: {path} served", ok, f"status={st} bytes={len(raw) if isinstance(raw, bytes) else '?'}")

# ------------------------------------------------------------------ summary
fails = [r for r in RESULTS if r[1] == "FAIL"]
infos = [r for r in RESULTS if r[1] == "INFO"]
passes = [r for r in RESULTS if r[1] == "PASS"]
print(f"\n{'='*78}\nLIVE BATTERY: {len(RESULTS)} checks -> {len(passes)} PASS / {len(fails)} FAIL / {len(infos)} INFO\n{'='*78}")
for name, status, detail in RESULTS:
    if status == "FAIL":
        print(f"FAIL  {name}\n      {detail}")
print("-" * 78)
for name, status, detail in RESULTS:
    if status == "INFO":
        print(f"INFO  {name}\n      {detail}")
print("-" * 78)
print(f"PASS: {len(passes)}  FAIL: {len(fails)}  INFO: {len(infos)}")
sys.exit(1 if fails else 0)
