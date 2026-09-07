#!/usr/bin/env python3
"""
Deploy kvm4-runner to KVM4 via the Hostinger VPS API.

Why this script exists
----------------------
The first deployment of kvm4-runner is a chicken-and-egg problem: we need a
command-runner on KVM4 to push files there, but to push files we need a
command-runner.  So this bootstrap inlines runner.py as a heredoc inside the
compose `command:`, deploys via the Hostinger compose API, and verifies the
runner answers on /health.  After that, every future update can flow through
the runner itself (no Hostinger API needed).

Inputs (env vars)
-----------------
HOSTINGER_API_KEY    required, account-level token
RUNNER_TOKEN         optional; if unset a fresh 48-char secret is generated
VM_ID                optional, defaults to 1231216 (KVM4)
RUNNER_HOST          optional, defaults to runner.srv1231216.hstgr.cloud

Usage
-----
    python3 deploy.py            # full deploy + verify
    python3 deploy.py --status   # show current stack status
    python3 deploy.py --logs     # tail container logs via Letta MCP-ish path
"""
from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

API_BASE = "https://developers.hostinger.com/api/vps/v1"
VM_ID = int(os.environ.get("VM_ID", "1231216"))
HOST = os.environ.get("RUNNER_HOST", "runner.srv1231216.hstgr.cloud")
API_KEY = os.environ.get("HOSTINGER_API_KEY") or sys.exit("HOSTINGER_API_KEY not set")
HERE = Path(__file__).resolve().parent


def http(method: str, path: str, body: dict | None = None, timeout: int = 60) -> dict:
    url = f"{API_BASE}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            # Hostinger sits behind Cloudflare which 403s the default
            # urllib User-Agent (error 1010).  Send a real-looking UA.
            "User-Agent": "kvm4-deploy/1.0 (+https://code.claude.com)",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        return {"_error": e.code, "_body": e.read().decode()[:500]}


def build_compose(runner_py: str, runner_token: str) -> str:
    """Build the bootstrap compose YAML with runner.py inlined.

    The heredoc terminator PYRUNNER must not appear inside runner.py — we
    verify that here so a future edit can't silently corrupt the deploy.
    """
    if "PYRUNNER" in runner_py:
        sys.exit("runner.py contains heredoc terminator 'PYRUNNER' — rename")
    # Indent runner.py for YAML literal block scalar
    indented = "\n".join("        " + line for line in runner_py.splitlines())
    return f"""services:
  kvm4-runner:
    image: python:3.12-slim
    container_name: kvm4-runner
    restart: unless-stopped
    environment:
      RUNNER_TOKEN: {runner_token}
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - /opt:/opt
      - /config:/config:ro
    working_dir: /app
    command:
      - sh
      - -c
      - |
        set -e
        mkdir -p /app
        cat > /app/runner.py <<'PYRUNNER'
{indented}
        PYRUNNER
        pip install -q --no-cache-dir 'fastapi>=0.110' 'uvicorn[standard]' \\
            'pydantic>=2' 'docker>=7'
        exec uvicorn runner:app --host 0.0.0.0 --port 8000
    labels:
      - traefik.enable=true
      - traefik.http.routers.kvm4-runner.rule=Host(`{HOST}`)
      - traefik.http.routers.kvm4-runner.tls.certresolver=letsencrypt
      - traefik.http.routers.kvm4-runner.entrypoints=websecure
      - traefik.http.services.kvm4-runner.loadbalancer.server.port=8000
    networks:
      - shared

networks:
  shared:
    external: true
"""


def wait_health(token: str, timeout: int = 240) -> bool:
    """Poll https://HOST/health until it returns 200 or timeout."""
    url = f"https://{HOST}/health"
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "deploy.py"})
            with urllib.request.urlopen(req, timeout=10) as r:
                if r.status == 200:
                    body = json.loads(r.read())
                    print(f"  health OK: {body}")
                    return True
        except Exception as e:
            print(f"  waiting... ({type(e).__name__}: {str(e)[:80]})")
        time.sleep(5)
    return False


def deploy() -> int:
    supplied = os.environ.get("RUNNER_TOKEN")
    token = supplied or secrets.token_urlsafe(36)
    print(f"VM_ID={VM_ID}  HOST={HOST}")
    # The token used to be echoed here AND again at the end. It grants
    # root-on-host-equivalent access, so it is now printed at most once, and only
    # when this run generated it — if the caller supplied RUNNER_TOKEN they
    # already hold it, and reprinting only widens where it can be captured
    # (scrollback, CI logs, shell history).

    runner_py = (HERE / "runner.py").read_text()
    compose = build_compose(runner_py, token)

    # Stack existence: GET /docker/<name> returns the empty stub
    # {"content":"","environment":null} for non-existent stacks, so check
    # whether content is actually populated rather than relying on _error.
    existing = http("GET", f"/virtual-machines/{VM_ID}/docker/kvm4-runner")
    if "_error" not in existing and (existing.get("content") or ""):
        print("Stack kvm4-runner already exists — overwriting via /update")
        upd = http(
            "POST",
            f"/virtual-machines/{VM_ID}/docker/kvm4-runner/update",
            {"content": compose, "environment": "# managed by deploy.py\n"},
        )
        print(f"  update: {upd}")
        if "_error" in upd:
            return 1
    else:
        print("Creating stack kvm4-runner...")
        # environment must be a string, not null; even an empty comment works
        created = http(
            "POST",
            f"/virtual-machines/{VM_ID}/docker",
            {
                "project_name": "kvm4-runner",
                "content": compose,
                "environment": "# managed by deploy.py\n",
            },
        )
        print(f"  create: {created}")
        if "_error" in created:
            return 1

    print(f"Waiting for https://{HOST}/health ...")
    if not wait_health(token):
        print("FAILED to reach /health within timeout")
        return 2

    # Smoke-test authed endpoint
    req = urllib.request.Request(
        f"https://{HOST}/info",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        info = json.loads(r.read())
    print(f"  /info returned {len(info.get('containers', []))} containers")
    print()
    print("DEPLOYED.  Set in your cloud session env:")
    print(f"  RUNNER_URL=https://{HOST}")
    if supplied:
        print("  RUNNER_TOKEN=<unchanged — the value you supplied in the environment>")
    else:
        print(f"  RUNNER_TOKEN={token}")
        print("  ^ generated for this deploy and shown ONCE. Store it like an SSH")
        print("    private key; it is root-on-host equivalent. Rotate by re-running")
        print("    this script with a new RUNNER_TOKEN in the environment.")
    return 0


def status() -> int:
    r = http("GET", f"/virtual-machines/{VM_ID}/docker/kvm4-runner")
    if "_error" in r:
        print(f"not deployed: {r}")
        return 1
    print(f"content_len={len(r.get('content','') or '')}")
    print(f"environment={r.get('environment')!r}")
    actions = http("GET", f"/virtual-machines/{VM_ID}/actions?limit=5")
    print("recent actions:", json.dumps(actions, indent=2)[:1000])
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", action="store_true")
    args = ap.parse_args()
    sys.exit(status() if args.status else deploy())
