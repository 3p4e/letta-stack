# letta-stack — infrastructure-as-code & runbooks for the KVM4 Letta server

Single home for everything about the **Letta stack on VPS 1231216 (crimson.blaze /
srv1231216.hstgr.cloud)** that previously lived only on the server or scattered across project
repos. Created 2026-08-08 following the handover-verification session
(`3p4e/CoA_TRACK` → `docs/ops/LETTA_HANDOVER_VERIFICATION_2026-08-08.md`).

GitHub repo: https://github.com/3p4e/letta-stack — this Drive folder is its human/document layer.

## What lives here (and what does not)

| Here | Not here |
|---|---|
| **The pp-document-suite engine — MASTER as of 2026-08-08** (`pp-document-suite/`; owner-directed cutover from ACME_SOP, see below) | **Secrets** — env-var NAMES only, values never |
| Compose files, deployment Dockerfiles, tool-registration scripts (`infra/`) | Postgres/pgvector **database dumps** — schedule `pg_dump` on the VPS with local rotation; dumps are too large and too sensitive for git |
| **Versioned manifests of live config** — agents, sources, blocks, tools (`manifests/<date>/`) | QC/QMS document CONTENT (SOPs, CoAs, specs) — that stays in the project repos (CoA_TRACK, ACME_SOP); this repo holds the machinery, not the paperwork |
| Runbooks: engine sync, access quirks, render routes, verifications (`runbooks/`) · the handover + Letta OpenAPI (`docs/`) | |
| The PP Doc Wiz app (`apps/ppdocwiz/`) · ingestion & QC-gate tooling from the CoA_TRACK thread (`ingestion/`) · the export tool (`scripts/`) | |

## Engine master cutover — 2026-08-08

By owner decision, **this repo is the home of all Letta-server work and development going
forward**, including the `pp-document-suite` engine master (copied here from
`3p4e/ACME_SOP` @ `e9872c9`; script hashes `build_from_md.py a8a35700` · `pp_report.py 1be84f35` ·
`pp_format.py 1d54edab` · `pp_verify.py a2060978` — identical to the live Letta volume).
The ACME_SOP copy is now a frozen mirror: a deprecation pointer must be added there (pending —
that repo is not writable from this session yet). All engine changes start here.

## The stack (verified live 2026-08-08)

`letta` compose project: `letta` :8283 (engine Mode A on the `/root/.letta` volume) ·
`letta-postgres` (pgvector — THE RAG store; all archives are `native`) · `letta-mcp-rust` :6507
(MCP bridge) · `qms-api` :8500 · `suma-api` :8501. Adjacent: `gotenberg` :3000 (DOCX→PDF —
reachable in-stack as `http://gotenberg:3000`), `qdrant` (SUMA only, NOT the Letta RAG),
`traefik`, `dockge`. 66 agents, 9 RAG sources, 2 registered PP document tools.

## Working rules

1. **Every deliberate config change** on the live server (agent, block, source, tool) is followed
   by `python3 scripts/export_manifests.py` and a commit — drift must be visible in diffs.
2. **Manifests are additive by date** — never rewrite a past export.
3. Credentials via env vars: `LETTA_UI`, `LETTA_API_KEY`, `HOSTINGER_API_KEY` (see
   `runbooks/bridge_and_rest_quirks.md` for the access paths and their quirks).
4. Engine changes flow (post-cutover): **this repo's `pp-document-suite/`** → hash-gated volume
   sync (`runbooks/engine_sync.md`) → manifest export → commit. The ACME_SOP copy is a frozen
   mirror and receives no edits.

## Companion Google Drive folder (this folder)

Human/document layer: runbook exports, the handover, manifests snapshot, recovery patches,
deliverable PDFs. Git remains the source of truth for anything text/config.

## Baseline manifest — 2026-08-08

66 agents (15 doc/RAG-fleet configs in full) · 9 sources · `pp_house_rules`
(block-eed2112b…, 1 963 chars, path-corrected) · `build_pp_document` / `fetch_pp_document`.
Known live facts of record: port 8787 Drive sidecar absent (defunct); PQ1 source embedding is
text-embedding-3-large (cross-search incompatible); `qms_docx_formatter` Gotenberg address is
`http://gotenberg:3000`.
