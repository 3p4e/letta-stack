#!/usr/bin/env python3
"""Patch docker-compose YAML files to join each service to the external `shared` network.

Reads compose files from before/, writes patched versions to after/. Adds:
  - `shared` to every service's `networks:` list (skipping services with `network_mode: host`)
  - top-level `networks: { shared: { external: true } }`

Run with: python3 patch_compose_for_shared_network.py
"""
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("Need PyYAML: pip install pyyaml")

ROOT = Path(__file__).parent
BEFORE = ROOT / "before"
AFTER = ROOT / "after"
AFTER.mkdir(exist_ok=True)


def patch(path: Path) -> dict:
    with path.open() as fh:
        try:
            data = yaml.safe_load(fh)
        except yaml.YAMLError as e:
            return {"file": path.name, "error": f"YAML parse failed: {str(e).splitlines()[0]}"}
    if not isinstance(data, dict) or "services" not in data:
        return {"file": path.name, "error": "not a compose file"}

    added_services = []
    skipped_host = []
    for name, svc in data["services"].items():
        if not isinstance(svc, dict):
            continue
        if svc.get("network_mode") == "host":
            skipped_host.append(name)
            continue
        nets = svc.get("networks")
        if nets is None:
            svc["networks"] = ["shared"]
            added_services.append(name)
        elif isinstance(nets, list):
            if "shared" not in nets:
                nets.append("shared")
                added_services.append(name)
        elif isinstance(nets, dict):
            if "shared" not in nets:
                nets["shared"] = None
                added_services.append(name)

    top_nets = data.setdefault("networks", {}) or {}
    if not isinstance(top_nets, dict):
        return {"file": path.name, "error": "top-level networks is not a mapping"}
    if "shared" not in top_nets:
        top_nets["shared"] = {"external": True}
    data["networks"] = top_nets

    out_path = AFTER / path.name
    with out_path.open("w") as fh:
        yaml.safe_dump(data, fh, sort_keys=False, default_flow_style=False)
    return {
        "file": path.name,
        "patched_services": added_services,
        "skipped_host_mode": skipped_host,
        "out": str(out_path.relative_to(ROOT)),
    }


def main() -> None:
    results = []
    for yml in sorted(BEFORE.glob("*.yml")):
        results.append(patch(yml))
    for r in results:
        if "error" in r:
            print(f"!! {r['file']}: {r['error']}")
            continue
        print(f"OK {r['file']:40s} patched={r['patched_services']}  host_skip={r['skipped_host_mode']}")


if __name__ == "__main__":
    main()
