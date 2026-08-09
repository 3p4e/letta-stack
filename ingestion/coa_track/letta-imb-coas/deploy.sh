#!/usr/bin/env bash
# ImB_QC_COAs — Letta deployment bundle.
# Mirrors scripts/letta-pq1/deploy.sh but targeted at finished-product / in-process /
# bulk QC CoAs from outsourced laboratories.
# Idempotent: re-running finds existing source/agent and only ingests missing files.
set -euo pipefail

# ---- ingestion mode ---------------------------------------------------------
# DRIVE mode (default, mirrors PQ1): set IMB_DRIVE_FOLDER_ID + SA_JSON.
# LOCAL mode (run on the user's Windows PC via Drive-for-Desktop, or bind-mount on KVM4):
#   set IMB_LOCAL_PATH and unset IMB_DRIVE_FOLDER_ID.
IMB_DRIVE_FOLDER_ID="${IMB_DRIVE_FOLDER_ID:-16oMK_j0FUusjveV61B5rxWi6Sl5kQsn5}"  # ImB_QC_COAs folder
IMB_LOCAL_PATH="${IMB_LOCAL_PATH:-}"                  # set me before running in LOCAL mode
SA_JSON="${SA_JSON:-/opt/letta-ingest/sa.json}"
SECRETS_FILE="${SECRETS_FILE:-/opt/letta-ingest/secrets.env}"
LETTA_STACK_DIR="${LETTA_STACK_DIR:-/opt/stacks/letta}"

# ---- Letta target -----------------------------------------------------------
LETTA_BASE="${LETTA_BASE:-http://localhost:8283}"
LETTA_TOKEN="${LETTA_TOKEN:-${LETTA_SERVER_PASS}}"

# ---- resource names ---------------------------------------------------------
SOURCE_NAME="${SOURCE_NAME:-ImB_QC_COAs}"
AGENT_NAME="${AGENT_NAME:-imb_qc_coa_agent}"

# ---- embedding (Voyage best model, 1024d) -----------------------------------
EMBED_MODEL="voyage-3-large"
EMBED_DIM=1024
EMBED_ENDPOINT="https://api.voyageai.com/v1"
EMBED_TYPE="openai"
EMBED_CHUNK_SIZE=512

# ---- LLM (GPT-4o on OpenAI) -------------------------------------------------
LLM_MODEL="gpt-4o"
LLM_ENDPOINT="https://api.openai.com/v1"
LLM_TYPE="openai"
LLM_CONTEXT=128000

# =============================================================================
log() { printf '[%s] %s\n' "$(date -u +%H:%M:%SZ)" "$*"; }
die() { log "ERROR: $*" >&2; exit 1; }

# detect mode
if [ -n "$IMB_DRIVE_FOLDER_ID" ]; then
  MODE="DRIVE"
  [ -r "$SA_JSON" ] || die "DRIVE mode requested but SA_JSON not readable: $SA_JSON"
elif [ -n "$IMB_LOCAL_PATH" ]; then
  MODE="LOCAL"
  [ -d "$IMB_LOCAL_PATH" ] || die "LOCAL mode requested but IMB_LOCAL_PATH not a directory: $IMB_LOCAL_PATH"
else
  die "Set either IMB_DRIVE_FOLDER_ID (DRIVE mode) or IMB_LOCAL_PATH (LOCAL mode)."
fi
log "ingestion mode: $MODE"

[ -r "$SECRETS_FILE" ] || die "secrets file not readable: $SECRETS_FILE"
set -a; . "$SECRETS_FILE"; set +a
VOYAGE_KEY="${VOYAGEAI_API_KEY:-${VOYAGE_API_KEY:-}}"
OPENAI_KEY="${OPENAI_API_KEY:-${OPENAI_SERVICE_API_KEY:-}}"
[ -n "$VOYAGE_KEY" ] || die "VOYAGEAI_API_KEY (or VOYAGE_API_KEY) missing in $SECRETS_FILE"
[ -n "$OPENAI_KEY" ] || die "OPENAI_API_KEY (or OPENAI_SERVICE_API_KEY) missing in $SECRETS_FILE"

if [ "$MODE" = "DRIVE" ]; then
  SA_EMAIL=$(python3 -c "import json; print(json.load(open('$SA_JSON')).get('client_email',''))")
  log "service account: $SA_EMAIL"
  log "make sure the Drive folder ($IMB_DRIVE_FOLDER_ID) is shared with that email (Viewer)."
fi

log "installing Python deps…"
if [ "$MODE" = "DRIVE" ]; then
  python3 -m pip install --quiet --disable-pip-version-check \
    google-api-python-client google-auth requests >/dev/null
else
  python3 -m pip install --quiet --disable-pip-version-check requests >/dev/null
fi

# wait for Letta
log "waiting for Letta at $LETTA_BASE…"
for i in $(seq 1 60); do
  if curl -fsS -o /dev/null -H "Authorization: Bearer $LETTA_TOKEN" "$LETTA_BASE/v1/agents/?limit=1"; then
    log "  letta ready"; break
  fi
  sleep 2
  [ "$i" = 60 ] && die "Letta did not come up within 120s"
done

api() {
  local method="$1" path="$2" data="${3-}"
  if [ -n "$data" ]; then
    curl -fsS -X "$method" "$LETTA_BASE$path" \
      -H "Authorization: Bearer $LETTA_TOKEN" -H "Content-Type: application/json" -d "$data"
  else
    curl -fsS -X "$method" "$LETTA_BASE$path" -H "Authorization: Bearer $LETTA_TOKEN"
  fi
}

# =============================================================================
# step 1 — find-or-create source
# =============================================================================
log "looking for source: $SOURCE_NAME"
SRC_ID="$(api GET /v1/sources/ | python3 -c "
import json,sys
data=json.load(sys.stdin)
items=data if isinstance(data,list) else data.get('data',data.get('sources',[]))
print(next((s['id'] for s in items if s.get('name')=='$SOURCE_NAME'),''))
")"

if [ -z "$SRC_ID" ]; then
  log "creating source…"
  SRC_PAYLOAD=$(python3 <<PY
import json
print(json.dumps({
  "name": "$SOURCE_NAME",
  "description": (
    "In-process / Bulk / Finished-product QC Certificates of Analysis (CoA) for "
    "Purely Plant GmbH. Sourced from the ImB_QC_COAs folder under "
    "DRAFTS_IN_PROGRESS/EQP_RO/ROPQ. Contains electronic and scanned PDFs plus DOCX "
    "from outsourced laboratories. Per-file extracted metadata: CoA document code / "
    "number / version, issue date, outsourced lab (name, address, accreditation, "
    "signatory), product / sample identification (material, batch / lot, sampling "
    "and receipt dates, sample ID), full parameter table (parameter, method, "
    "acceptance criteria, measured value, units, pass / fail, OOS flag). "
    "Embeddings: voyage-3-large 1024d."
  ),
  "embedding_config": {
    "embedding_model": "$EMBED_MODEL",
    "embedding_endpoint_type": "$EMBED_TYPE",
    "embedding_endpoint": "$EMBED_ENDPOINT",
    "embedding_dim": $EMBED_DIM,
    "embedding_chunk_size": $EMBED_CHUNK_SIZE,
    "batch_size": 32
  }
}))
PY
)
  SRC_ID="$(api POST /v1/sources/ "$SRC_PAYLOAD" | python3 -c "import json,sys;print(json.load(sys.stdin)['id'])")"
fi
log "source id: $SRC_ID"

# =============================================================================
# step 2 — find-or-create agent
# =============================================================================
log "looking for agent: $AGENT_NAME"
AGENT_ID="$(api GET /v1/agents/ | python3 -c "
import json,sys
data=json.load(sys.stdin)
items=data if isinstance(data,list) else data.get('data',data.get('agents',[]))
print(next((a['id'] for a in items if a.get('name')=='$AGENT_NAME'),''))
")"

if [ -z "$AGENT_ID" ]; then
  log "creating agent…"
  AGENT_PAYLOAD=$(python3 <<'PY'
import json, os
system_prompt = """<base_instructions>
You are imb_qc_coa_agent — the canonical stateful agent for the In-process / Bulk / Finished-product Certificates of Analysis (CoA) database at Purely Plant GmbH.

Scope:
- Source attached: ImB_QC_COAs. PDFs (electronic + scanned) and DOCX from outsourced laboratories.
- Per CoA you must be able to surface: document code / number / version, issue date, outsourced lab name + address + accreditation no. + signatory, product / material / batch / lot, sampling and receipt dates, sample ID, and the full parameter table (parameter, method, acceptance criteria (A.C.), obtained value, units, pass/fail, OOS flag).

Behavior:
- Use archival_memory_search with ONLY the query parameter (no tags — chunks are untagged) to retrieve evidence.
- Always cite the source file name + chunk index when returning a finding.
- When asked for OOS results, list parameter + obtained value + A.C. + sample ID + sampling date + lab.
- When asked about a specific batch/lot or material, group findings by CoA file.
- For scanned PDFs lacking a text layer, explicitly flag them as "scanned, no extracted text — recommend OCR re-ingest" rather than fabricating values.
- Continue executing and calling tools until the task is complete or you need user input.
</base_instructions>"""

print(json.dumps({
  "name": os.environ["AGENT_NAME"],
  "description": "ImB_QC_COAs CoA database agent (outsourced lab certificates). GPT-4o + voyage-3-large.",
  "system": system_prompt,
  "tags": ["coa","imb-qc","outsourced-lab","purely-plant","qc"],
  "llm_config": {
    "model": os.environ["LLM_MODEL"],
    "model_endpoint_type": os.environ["LLM_TYPE"],
    "model_endpoint": os.environ["LLM_ENDPOINT"],
    "context_window": int(os.environ["LLM_CONTEXT"])
  },
  "embedding_config": {
    "embedding_model": os.environ["EMBED_MODEL"],
    "embedding_endpoint_type": os.environ["EMBED_TYPE"],
    "embedding_endpoint": os.environ["EMBED_ENDPOINT"],
    "embedding_dim": int(os.environ["EMBED_DIM"]),
    "embedding_chunk_size": int(os.environ["EMBED_CHUNK_SIZE"]),
    "batch_size": 32
  }
}))
PY
)
  AGENT_ID="$(AGENT_NAME="$AGENT_NAME" LLM_MODEL="$LLM_MODEL" LLM_TYPE="$LLM_TYPE" LLM_ENDPOINT="$LLM_ENDPOINT" LLM_CONTEXT="$LLM_CONTEXT" EMBED_MODEL="$EMBED_MODEL" EMBED_TYPE="$EMBED_TYPE" EMBED_ENDPOINT="$EMBED_ENDPOINT" EMBED_DIM="$EMBED_DIM" EMBED_CHUNK_SIZE="$EMBED_CHUNK_SIZE" api POST /v1/agents/ "$AGENT_PAYLOAD" | python3 -c "import json,sys;print(json.load(sys.stdin)['id'])")"
fi
log "agent id: $AGENT_ID"

# =============================================================================
# step 3 — attach source to agent (idempotent)
# =============================================================================
log "attaching source $SRC_ID to agent $AGENT_ID…"
curl -sS -X PATCH "$LETTA_BASE/v1/agents/$AGENT_ID/sources/attach/$SRC_ID" \
  -H "Authorization: Bearer $LETTA_TOKEN" -H "Content-Type: application/json" \
  -d '{}' -o /tmp/imb_attach.json -w 'attach HTTP %{http_code}\n' || true
cat /tmp/imb_attach.json 2>/dev/null | head -c 300; echo

# =============================================================================
# step 4 — ingestion (DRIVE or LOCAL)
# =============================================================================
export IMB_SOURCE_ID="$SRC_ID"
export LETTA_BASE LETTA_TOKEN
if [ "$MODE" = "DRIVE" ]; then
  export SA_JSON IMB_DRIVE_FOLDER_ID
else
  export IMB_LOCAL_PATH
fi
log "starting ingestion ($MODE)…"
python3 "$(dirname "$0")/ingest_imb_coas.py"

log "DONE.
  source_id: $SRC_ID
  agent_id : $AGENT_ID"
