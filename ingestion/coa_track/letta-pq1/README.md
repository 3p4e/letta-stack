# PQ1 Water Testing Results — Letta deployment bundle

One-shot, idempotent bundle that runs on **KVM4** and:

1. Switches the Letta server's default embedding to **`voyage-3-large`** (1024d) — Voyage's strongest retrieval model.
2. Creates a Letta source `PQ1 Water Testing Results Report` with explicit Voyage `embedding_config` (regardless of server default).
3. Creates a stateful agent `pq1_water_qc_agent` on **GPT-4o** + Voyage embeddings.
4. Attaches the source to the agent.
5. Downloads the ~90 PDFs from the shared Google Drive folder using your service account, uploads each into the Letta source, and reports a summary.

Re-running is safe — every step finds-or-creates and skips already-uploaded files.

## Prerequisites on KVM4

```
/opt/letta-ingest/
  ├── sa.json         # Google service-account JSON (from your Windows path)
  └── secrets.env     # at minimum: VOYAGEAI_API_KEY, OPENAI_API_KEY
```

The service account's `client_email` must have **Viewer** access to the Drive folder
`https://drive.google.com/drive/folders/18KPrhRys1RaBhMEwVznZp39jTGNROeN2` (share it
yourself from the Drive UI — the script prints the SA email before it tries to list).

`secrets.env` keys the script reads (any of these names work):

- `VOYAGEAI_API_KEY` *or* `VOYAGE_API_KEY` (required)
- `OPENAI_API_KEY` *or* `OPENAI_SERVICE_API_KEY` (required)
- `LETTA_TOKEN` (optional; defaults to `${LETTA_SERVER_PASS}`)
- `LETTA_BASE` (optional; defaults to `http://localhost:8283`)
- `LETTA_STACK_DIR` (optional; defaults to `/opt/stacks/letta`)

## Run

```bash
ssh kvm4
# place /opt/letta-ingest/sa.json and /opt/letta-ingest/secrets.env first
# then:
cd /opt   # or wherever you cloned this repo
git clone -b claude/letta-server-research-7EeYF https://github.com/3p4e/coa_track.git pq1-deploy
cd pq1-deploy/scripts/letta-pq1
python3 -m pip install --quiet google-api-python-client google-auth requests
bash deploy.sh
```

The script logs every step. At the end it prints the source ID, agent ID, and an ingest summary
(`ok / skipped / failed`).

## Why this design

| Decision                                                                                                  | Rationale (from Open Brain) |
|-----------------------------------------------------------------------------------------------------------|------------------------------|
| Don't deploy a new Letta container                                                                        | Letta is already running (`letta:8283`, `letta-postgres`, `letta-mcp-rust:6507`, `letta-oss-ui:3001`, `letta-daemon:8420`). |
| Pass inline `embedding_config` on source create                                                           | Letta source creation requires it — the 2026-04-26 GOTCHA in Open Brain confirms this. Server default alone is insufficient. |
| One new agent (`pq1_water_qc_agent`), not three                                                           | Existing 30 agents are general-purpose; none are PQ1-specific. Three pipeline agents would duplicate the existing CoA Tracker pattern without adding value. |
| Don't reuse the empty `gmp-certificates` source                                                            | It was created 2026-04-26, never populated, and is described as a broader "CoAs + water + qualification reports" bucket. Mixing PQ1 data in would muddle retrieval. |
| voyage-3-large (1024d, OpenAI-compatible endpoint) instead of voyage-3                                    | Voyage's current top retrieval model; same 1024d as your existing pgvector schema so no DB migration. |

## Rollback

```bash
# revert .env change:
ls /opt/stacks/letta/.env.bak.* | tail -1 | xargs -I{} cp {} /opt/stacks/letta/.env
cd /opt/stacks/letta && docker compose up -d --no-deps letta

# delete the new agent + source (replace with the IDs deploy.sh printed):
curl -X DELETE -H "Authorization: Bearer ${LETTA_SERVER_PASS}" \
  http://localhost:8283/v1/agents/<AGENT_ID>
curl -X DELETE -H "Authorization: Bearer ${LETTA_SERVER_PASS}" \
  http://localhost:8283/v1/sources/<SOURCE_ID>
```

## Files in this bundle

- `deploy.sh` — orchestrator; runs on KVM4
- `ingest_pdfs.py` — Drive→Letta uploader called by `deploy.sh`
- `README.md` — this file
