#!/usr/bin/env python3
"""Export the live Letta/KVM4 configuration state into versioned manifest files.

The point: agents, memory blocks, sources and tools live ONLY in the server's Postgres —
without these exports, config drift is invisible and there is no rollback reference.
Run after any deliberate config change, and periodically; commit the dated directory.

Requires env vars (names only, never commit values):
  LETTA_UI, LETTA_API_KEY            — Letta REST
  HOSTINGER_API_KEY (optional)       — Docker inventory snapshot

Usage: python3 export_manifests.py [outdir]   (default manifests/<YYYY-MM-DD>/)
Canonical home: https://github.com/3p4e/letta-stack scripts/export_manifests.py
"""
import json, os, sys, datetime, re, urllib.request

BASE = os.environ["LETTA_UI"].rstrip("/")
HDR = {"Authorization": "Bearer " + os.environ["LETTA_API_KEY"]}

DOC_FLEET = {
    "qms_docx_formatter", "pharma_docx_formatter", "qms_pipeline_orchestrator",
    "qms_sop_expert", "qms_gmp_auditor", "pp_annex_orchestrator", "pp_annex_translator",
    "pp_annex_body_formatter", "pp_annex_table_specialist", "pp_annex_auditor",
    "gmp_rag_agent", "eu_gmp_compliance_expert", "imb_qc_coa_agent",
    "ecoa-qc-agent", "pq1_water_qc_agent",
}

SECRET_PAT = re.compile(r"(sk-[A-Za-z0-9]{10,}|api[_-]?key\"?\s*[:=]\s*\"[A-Za-z0-9]{8,})", re.I)


def get(path):
    req = urllib.request.Request(BASE + path, headers=HDR)
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def scrub_check(obj, label):
    s = json.dumps(obj)
    if SECRET_PAT.findall(s):
        raise SystemExit(f"ABORT: {label} export contains what looks like a secret; not writing.")
    return obj


def main(outdir=None):
    day = datetime.date.today().isoformat()
    outdir = outdir or os.path.join(os.path.dirname(__file__), "..", "manifests", day)
    os.makedirs(outdir, exist_ok=True)

    agents = get("/v1/agents/?limit=100")
    slim = [{"id": a.get("id"), "name": a.get("name"),
             "model": (a.get("llm_config") or {}).get("model"),
             "embedding": (a.get("embedding_config") or {}).get("embedding_model"),
             "created": a.get("created_at"), "description": a.get("description")} for a in agents]
    json.dump(scrub_check(slim, "agents"), open(os.path.join(outdir, "agents.json"), "w"),
              indent=1, ensure_ascii=False)

    # Config only — deliberately NOT runtime state: `memory` is excluded (conversation-derived,
    # large, and restoring it from git would be wrong anyway).
    def cfg(a):
        return {
            "id": a.get("id"), "name": a.get("name"), "description": a.get("description"),
            "system": a.get("system"), "llm_config": a.get("llm_config"),
            "embedding_config": a.get("embedding_config"), "tags": a.get("tags"),
            "tool_rules": a.get("tool_rules"),
            "message_buffer_autoclear": a.get("message_buffer_autoclear"),
            "tools": [{"id": t.get("id"), "name": t.get("name")} for t in (a.get("tools") or [])],
            "sources": [{"id": s.get("id"), "name": s.get("name")} for s in (a.get("sources") or [])],
            "blocks": [{"id": b.get("id"), "label": b.get("label"),
                        "chars": len(b.get("value") or "")} for b in (a.get("blocks") or [])],
        }
    full = [cfg(a) for a in agents if a.get("name") in DOC_FLEET]
    json.dump(scrub_check(full, "doc-fleet"), open(os.path.join(outdir, "agents_doc_fleet_config.json"), "w"),
              indent=1, ensure_ascii=False)

    sources = get("/v1/sources/")
    json.dump(scrub_check(sources, "sources"), open(os.path.join(outdir, "sources.json"), "w"),
              indent=1, ensure_ascii=False)

    block = get("/v1/blocks/block-eed2112b-a1b4-4593-b607-9c16444fe254")
    json.dump(scrub_check(block, "pp_house_rules"), open(os.path.join(outdir, "block_pp_house_rules.json"), "w"),
              indent=1, ensure_ascii=False)

    tools = []
    for name in ("build_pp_document", "fetch_pp_document"):
        tools += get("/v1/tools/?name=" + name)
    json.dump(scrub_check(tools, "tools"), open(os.path.join(outdir, "tools_pp.json"), "w"),
              indent=1, ensure_ascii=False)

    if os.environ.get("HOSTINGER_API_KEY"):
        try:
            req = urllib.request.Request(
                "https://developers.hostinger.com/api/vps/v1/virtual-machines/1231216/docker",
                headers={"Authorization": "Bearer " + os.environ["HOSTINGER_API_KEY"]})
            with urllib.request.urlopen(req, timeout=60) as r:
                inv = json.load(r)
            json.dump(inv, open(os.path.join(outdir, "docker_inventory.json"), "w"), indent=1)
        except Exception as e:
            print("WARN: Hostinger inventory skipped:", e)

    counts = {"agents": len(slim), "doc_fleet_full": len(full), "sources": len(sources),
              "tools": len(tools), "block_chars": len(block.get("value", ""))}
    json.dump({"exported": day, **counts}, open(os.path.join(outdir, "SUMMARY.json"), "w"), indent=1)
    print("EXPORTED", outdir, counts)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
