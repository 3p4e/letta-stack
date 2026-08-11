# ImB_QC_COAs — Letta deployment bundle

Idempotent ingestion of the **In-process / Bulk / Finished-product QC Certificates
of Analysis** (electronic PDFs, scanned PDFs, DOCX) from outsourced laboratories
into Letta. Mirrors the proven `scripts/letta-pq1/` pattern.

Source folder on the user's PC (Drive-for-Desktop mount):

```
C:\Users\Agent Zero\My Drive\1. PP\DRAFTS_IN_PROGRESS\EQP_RO\ROPQ\ImB_QC_COAs
```

Letta resources created:

- **Source:** `ImB_QC_COAs` — embeddings **OpenAI `text-embedding-3-small`, 1536d, chunk 300**
- **Agent:** `imb_qc_coa_agent`

> **Correction (verified against the live server, 2026-08-10):** `deploy.sh` provisions
> the source with `voyage-3-large` (1024d), but the **live** `ImB_QC_COAs` source runs
> **OpenAI `text-embedding-3-small` (1536d)** and the server holds **no Voyage key**.
> Do not provision a Voyage key on the strength of this repo — check the live source
> config first. Re-creating the source with a different embedding model would orphan
> the existing 261 embedded files.

## Two ingestion modes

### Mode A — DRIVE (recommended, runs on KVM4)

Mirrors the PQ1 pipeline exactly. Best long-term option: a re-run keeps Letta
in sync with whatever the QC team drops into the Drive folder.

1. Share the Drive folder with the service-account email (Viewer):
   - Open the folder in Drive: right-click → Share
   - Add the `client_email` from `/opt/letta-ingest/sa.json` (the deploy script
     prints it before listing). Same SA already used for PQ1.
2. Grab the Drive folder ID from its URL
   (`drive.google.com/drive/folders/<THIS_PART>`).
3. SSH into KVM4 and run:

```bash
ssh kvm4
cd /opt/coa_track   # or wherever this repo is checked out
git checkout claude/letta-kvm4-connectivity-Bb49s
export IMB_DRIVE_FOLDER_ID="<paste folder id here>"
bash scripts/letta-imb-coas/deploy.sh
```

### Mode B — LOCAL (runs wherever the files are visible)

Use when you'd rather walk the local filesystem directly — typically from the
"Agent Zero" Windows PC via a Claude Code session that has read access to the
Drive-for-Desktop mount, or from KVM4 if you bind-mount the folder.

```bash
# from the local Claude Code session on the Windows PC (Git Bash / WSL):
export LETTA_BASE="http://<kvm4-host>:8283"     # or the tunnel address
export LETTA_TOKEN="${LETTA_SERVER_PASS}"
export IMB_LOCAL_PATH="/c/Users/Agent Zero/My Drive/1. PP/DRAFTS_IN_PROGRESS/EQP_RO/ROPQ/ImB_QC_COAs"
# point SECRETS_FILE at a file that has VOYAGEAI_API_KEY + OPENAI_API_KEY
export SECRETS_FILE="$HOME/.letta-ingest/secrets.env"
bash scripts/letta-imb-coas/deploy.sh
```

If you'd rather just ingest (source + agent already exist), call the worker
directly:

```bash
export LETTA_BASE LETTA_TOKEN
export IMB_SOURCE_ID="$(curl -fsS -H "Authorization: Bearer $LETTA_TOKEN" \
  $LETTA_BASE/v1/sources/ | python3 -c "import json,sys;d=json.load(sys.stdin);print(next(s['id'] for s in (d if isinstance(d,list) else d['data']) if s['name']=='ImB_QC_COAs'))")"
export IMB_LOCAL_PATH="/c/Users/Agent Zero/My Drive/1. PP/DRAFTS_IN_PROGRESS/EQP_RO/ROPQ/ImB_QC_COAs"
python3 scripts/letta-imb-coas/ingest_imb_coas.py
```

## Prerequisites recap

- KVM4 (DRIVE mode):
  - `/opt/letta-ingest/sa.json` (the same SA used by PQ1)
  - `/opt/letta-ingest/secrets.env` with `VOYAGEAI_API_KEY` + `OPENAI_API_KEY`
  - Drive folder shared with `sa.json`'s `client_email`
- LOCAL mode (any host):
  - Python 3 + `pip install requests`
  - A reachable Letta base URL + token
  - A `secrets.env` (only needed if running the full `deploy.sh`; the worker
    `ingest_imb_coas.py` only needs `LETTA_BASE`, `LETTA_TOKEN`,
    `IMB_SOURCE_ID`, `IMB_LOCAL_PATH`)

## File-type handling

| Extension | Behavior |
|-----------|----------|
| `.pdf` (electronic, has text layer) | Uploaded as-is; Letta extracts + chunks + embeds. |
| `.pdf` (scanned, no text layer)     | Uploaded as-is; Letta will store the file but extraction will be empty. The agent system prompt is configured to flag these so we know which need OCR re-ingest. |
| `.docx`                             | Uploaded as-is; Letta extracts text from the OOXML. |

A future enhancement is to detect scanned PDFs and OCR them with
`ocrmypdf`/Tesseract before upload (mirrors what `OCR_PIPELINE.md` already
does for the `QC_eCoA` flow).

## Verifying after ingest

```bash
# count files in the source
curl -fsS -H "Authorization: Bearer $LETTA_TOKEN" \
  "$LETTA_BASE/v1/sources/$IMB_SOURCE_ID/files?limit=2000" | python3 -c \
  "import json,sys;d=json.load(sys.stdin);print(len(d if isinstance(d,list) else d.get('data',d.get('files',[]))))"

# ask the agent something
curl -sS -H "Authorization: Bearer $LETTA_TOKEN" -H "Content-Type: application/json" \
  -X POST "$LETTA_BASE/v1/agents/<AGENT_ID>/messages" \
  -d '{"messages":[{"role":"user","content":"List every CoA in ImB_QC_COAs that contains an OOS result, with parameter, obtained value, A.C., and lab."}]}'
```

## Rollback

```bash
curl -X DELETE -H "Authorization: Bearer $LETTA_TOKEN" "$LETTA_BASE/v1/agents/<AGENT_ID>"
curl -X DELETE -H "Authorization: Bearer $LETTA_TOKEN" "$LETTA_BASE/v1/sources/<SOURCE_ID>"
```

## Files in this bundle

- `deploy.sh` — orchestrator (find-or-create source + agent, attach, run ingest)
- `ingest_imb_coas.py` — file walker + uploader (DRIVE or LOCAL mode)
- `README.md` — this file
