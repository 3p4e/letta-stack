#!/usr/bin/env python3
"""
verify_letta_connection.py — READ-ONLY smoke check for the Letta side of the integration.

Confirms, WITHOUT changing anything, that:
  1. a Letta server is reachable and the credentials authenticate;
  2. the target document agents exist (default: qms_docx_formatter, pharma_docx_formatter);
  3. whether the Purely Plant builder tool is already registered.

It never creates, attaches, or deletes anything (that is letta_register.py's job), and it never
prints the API key / token. Run this BEFORE letta_register.py to catch config problems early.

Config (environment only):
  LETTA_BASE_URL   Letta server base URL.
                   If unset and LETTA_API_KEY looks like an sk-let… cloud key -> https://api.letta.com.
  LETTA_TOKEN      bearer token; falls back to LETTA_API_KEY.
  PP_AGENTS        comma list of agent names to look for (default qms_docx_formatter,pharma_docx_formatter).
  PP_TOOL_NAME     tool name to look for (default build_pp_document / build_pp_document_via_api).

Exit code 0 = reachable + authenticated; non-zero otherwise.
"""
import os, sys, json
import urllib.request
import urllib.error


def _cfg():
    base = os.environ.get("LETTA_BASE_URL", "").rstrip("/")
    tok = os.environ.get("LETTA_TOKEN") or os.environ.get("LETTA_API_KEY")
    if not base:
        # cloud keys start with 'sk-let'; default to Letta Cloud when no explicit base is given
        if tok and tok.startswith("sk-let"):
            base = "https://api.letta.com"
        else:
            sys.exit("LETTA_BASE_URL is unset and no cloud key detected. Set LETTA_BASE_URL "
                     "(self-hosted) or LETTA_API_KEY (cloud). Refusing to guess.")
    if not tok:
        print("! no LETTA_TOKEN / LETTA_API_KEY set — trying unauthenticated (self-hosted only).")
    return base, tok


def _extra_headers():
    """Optional headers for reaching Letta behind a runner / Traefik:
      LETTA_HOST_HEADER   -> Host: <value>  (Traefik routes by Host when base is a runner URL/IP)
      LETTA_EXTRA_HEADERS -> 'K1: v1; K2: v2' (e.g. a runner auth header like X-Runner-Token)
    """
    out = []
    host = os.environ.get("LETTA_HOST_HEADER")
    if host:
        out.append(("Host", host))
    for part in (os.environ.get("LETTA_EXTRA_HEADERS", "") or "").split(";"):
        if ":" in part:
            k, v = part.split(":", 1)
            if k.strip():
                out.append((k.strip(), v.strip()))
    return out


def _get(base, path, tok, timeout=20):
    """GET helper using urllib (honours HTTPS_PROXY / proxy CA from the environment). Returns
    (status, parsed_json_or_text). Never logs the token."""
    url = base + path
    req = urllib.request.Request(url, method="GET")
    if tok:
        req.add_header("Authorization", "Bearer " + tok)
    req.add_header("Accept", "application/json")
    # Some fronts (e.g. Cloudflare on Letta Cloud) 403 the default Python-urllib UA; send a plain one.
    req.add_header("User-Agent", "pp-document-suite/1.6.2 (+letta-smoke-check)")
    for k, v in _extra_headers():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read().decode("utf-8", "replace")
            try:
                return r.status, json.loads(body)
            except Exception:
                return r.status, body
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:
        return None, "%s: %s" % (type(e).__name__, e)


def _redact_host(base):
    # show scheme+host only (host is not secret, but keep it tidy)
    try:
        from urllib.parse import urlparse
        u = urlparse(base); return "%s://%s" % (u.scheme, u.netloc)
    except Exception:
        return base


def main():
    base, tok = _cfg()
    print("Letta smoke check → %s  (auth: %s)" % (_redact_host(base), "yes" if tok else "no"))

    # 1. reachable + authenticated: list agents
    st, agents = _get(base, "/v1/agents/?limit=200", tok)
    if st is None:
        print("FAIL — cannot reach server: %s" % agents); return 2
    if st in (401, 403):
        print("FAIL — authenticated request rejected (HTTP %d). Check LETTA_TOKEN/LETTA_API_KEY." % st); return 3
    if st != 200 or not isinstance(agents, list):
        print("FAIL — unexpected response (HTTP %s): %s" % (st, str(agents)[:200])); return 4
    names = [a.get("name") for a in agents if isinstance(a, dict)]
    print("OK   — reachable & authenticated; %d agent(s) visible." % len(names))
    if names:
        print("  agents: %s" % ", ".join(n for n in names if n))

    # 2. target agents present?
    want = [s.strip() for s in os.environ.get("PP_AGENTS", "qms_docx_formatter,pharma_docx_formatter").split(",") if s.strip()]
    for n in want:
        print(("  ✓ agent present: %s" if n in names else "  ✗ agent MISSING: %s") % n)

    # 3. is the builder tool already registered? (query by name to avoid bulk-list edge cases)
    found = []
    for tname in [t for t in {os.environ.get("PP_TOOL_NAME"), "build_pp_document", "build_pp_document_via_api"} if t]:
        st2, tools = _get(base, "/v1/tools/?name=" + tname, tok)
        if st2 == 200 and isinstance(tools, list) and any(isinstance(t, dict) and t.get("name") == tname for t in tools):
            found.append(tname)
    print("  builder tool registered: %s" % (", ".join(sorted(found)) if found else "none yet (run letta_register.py)"))

    missing = [n for n in want if n not in names]
    if missing:
        print("RESULT: PARTIAL — connected, but missing agent(s): %s" % ", ".join(missing)); return 5
    print("RESULT: PASS — Letta reachable, authenticated, target agents present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
