#!/usr/bin/env python3
"""
Rewire every Letta agent's llm_config to match agent_model_policy.py.

Runs on KVM4 against http://letta:8283. Reads the policy module, lists every
agent, and PATCHes each one whose current model differs from the target.
Idempotent — re-running after no policy change is a no-op.

Usage on KVM4:
    docker exec -it letta sh -c 'pip install requests' || true
    python3 scripts/letta-imb-coas/rewire_agents.py [--dry-run]

The script prints a per-agent diff and a final summary table.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request

# Make the policy importable when run from anywhere
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agent_model_policy import (
    AGENT_ROLES,
    MODELS,
    llm_config_for_model,
    model_for_agent,
)

LETTA_BASE = os.getenv("LETTA_BASE", "http://letta:8283")
LETTA_KEY = os.getenv("LETTA_MASTER_KEY") or os.getenv("LETTA_SERVER_PASS") or "${LETTA_SERVER_PASS}"
HEADERS = {"Authorization": f"Bearer {LETTA_KEY}", "Content-Type": "application/json"}


def _http(method: str, path: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{LETTA_BASE}{path}", data=data, method=method, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def list_agents() -> list[dict]:
    return _http("GET", "/v1/agents?limit=200")


def update_agent_llm_config(agent_id: str, llm_config: dict) -> dict:
    return _http("PATCH", f"/v1/agents/{agent_id}", {"llm_config": llm_config})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="show changes, don't apply")
    args = parser.parse_args()

    agents = list_agents()
    changed: list[tuple[str, str, str]] = []   # (name, from_model, to_model)
    unchanged: list[str] = []
    unknown: list[str] = []                    # agents not in AGENT_ROLES

    for a in agents:
        name = a["name"]
        cur = a.get("llm_config", {}).get("model", "?")
        target = model_for_agent(name)
        if name not in AGENT_ROLES:
            unknown.append(name)
        if cur == target:
            unchanged.append(name)
            continue
        changed.append((name, cur, target))
        if not args.dry_run:
            try:
                update_agent_llm_config(a["id"], llm_config_for_model(target))
            except Exception as e:
                print(f"  !! failed to update {name}: {e}")

    print(f"\n{'='*72}\nLetta agent rewire — {'DRY RUN' if args.dry_run else 'APPLIED'}\n{'='*72}")
    print(f"\nChanged ({len(changed)}):")
    for name, frm, to in changed:
        print(f"  {name:40s}  {frm:20s} -> {to}")
    print(f"\nAlready correct ({len(unchanged)}):")
    for n in unchanged:
        print(f"  {n}")
    if unknown:
        print(f"\n⚠ Agents missing from policy ({len(unknown)}) — default applied:")
        for n in unknown:
            print(f"  {n}  (defaulted to {model_for_agent(n)})")

    # Coverage summary by model
    by_model: dict[str, int] = {}
    for a in agents:
        target = model_for_agent(a["name"])
        by_model[target] = by_model.get(target, 0) + 1
    print(f"\nTarget distribution ({len(agents)} agents):")
    for m, n in sorted(by_model.items(), key=lambda x: -x[1]):
        prov = MODELS[m]["provider"]
        print(f"  {m:38s} ({prov:8s})  {n} agents")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
