#!/usr/bin/env python3
"""
Apply agent_model_policy via direct Letta REST API (port 8283).

Run from KVM4 (any host in the letta_stack docker network can reach it,
including the Hostinger web terminal which has docker exec access):

    docker exec letta python3 -            <<- this won't work, letta image
                                              has the libs but no script path
    # easier: run on host with curl-based fallback (below)

Easiest from web terminal:
    cd /opt/stacks/letta && \
    docker exec -i -e LETTA_BASE=http://localhost:8283 \\
        -e LETTA_MASTER_KEY=${LETTA_SERVER_PASS} \\
        letta python3 - < /path/to/rewire_via_rest.py
OR just clone the repo and run with python3 on the host.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agent_model_policy import (
    AGENT_ROLES, MODELS, PROVIDERS,
    llm_config_for_model, model_for_agent,
)

LETTA_BASE = os.getenv("LETTA_BASE", "http://localhost:8283")
LETTA_KEY = os.getenv("LETTA_MASTER_KEY") or os.getenv("LETTA_SERVER_PASS") or "${LETTA_SERVER_PASS}"
HEADERS = {"Authorization": f"Bearer {LETTA_KEY}", "Content-Type": "application/json"}


def http(method: str, path: str, body=None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{LETTA_BASE}{path}", data=data, method=method, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"_error": e.code, "_body": e.read().decode()[:500]}


def main() -> int:
    dry = "--apply" not in sys.argv

    print(f"LETTA_BASE={LETTA_BASE}")
    print(f"Mode: {'DRY-RUN' if dry else 'APPLY'}")

    agents = http("GET", "/v1/agents?limit=500")
    if isinstance(agents, dict) and "_error" in agents:
        print(f"List agents failed: {agents}")
        return 1
    print(f"Found {len(agents)} agents\n")

    changed = []
    unchanged = []
    failed = []

    for a in agents:
        name = a["name"]
        cur_model = a.get("llm_config", {}).get("model")
        cur_type = a.get("llm_config", {}).get("model_endpoint_type")
        target_model = model_for_agent(name)
        target_cfg = llm_config_for_model(target_model)
        target_type = target_cfg["model_endpoint_type"]

        if cur_model == target_model and cur_type == target_type:
            unchanged.append((name, cur_model))
            continue

        if not dry:
            result = http("PATCH", f"/v1/agents/{a['id']}", {"llm_config": target_cfg})
            if isinstance(result, dict) and "_error" in result:
                failed.append((name, cur_model, target_model, target_type, result["_body"]))
                continue
        changed.append((name, cur_model, target_model, cur_type, target_type))

    # Report
    print(f"\nChanged ({len(changed)}):")
    for name, frm, to, ft, tt in changed:
        print(f"  {name:40s}  {frm:20s} ({ft:10}) -> {to:20s} ({tt})")

    print(f"\nAlready correct ({len(unchanged)})")
    if failed:
        print(f"\nFAILED ({len(failed)}):")
        for name, frm, to, tt, err in failed:
            print(f"  {name:40s}  {frm} -> {to} ({tt}): {err[:200]}")

    # Distribution summary
    final = {}
    for a in agents:
        target = model_for_agent(a["name"])
        final[target] = final.get(target, 0) + 1
    print(f"\nTarget distribution ({len(agents)} agents):")
    for m, n in sorted(final.items(), key=lambda x: -x[1]):
        prov = MODELS[m]["provider"]
        env_var = PROVIDERS[prov]["env_var"]
        print(f"  {m:35} ({prov:8s})  {n:3} agents  (auth env: {env_var})")

    print(f"\n{'Run with --apply to make changes' if dry else 'Done.'}")
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
