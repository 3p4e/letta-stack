#!/usr/bin/env bash
# PQ1 Water Testing Results — Letta deployment bundle (KVM4 side).
# Idempotent: re-running finds existing source/agent and only ingests missing PDFs.
set -euo pipefail

# ---- paths (override via env if you placed creds elsewhere) -----------------
LETTA_STACK_DIR="${LETTA_STACK_DIR:-/opt/stacks/letta}"
SECRETS_FILE="${SECRETS_FILE:-/opt/letta-ingest/secrets.env}"
SA_JSON="${SA_JSON:-/opt/letta-ingest/sa.json}"
DRIVE_FOLDER_ID="${DRIVE_FOLDER_ID:-18KPrhRys1RaBhMEwVznZp39jTGNROeN2}"

# ---- Letta target -----------------------------------------------------------
LETTA_BASE="${LETTA_BASE:-http://localhost:8283}"
LETTA_TOKEN="${LETTA_TOKEN:-${LETTA_SERVER_PASS}}"

# ---- resource names ---------------------------------------------------------
SOURCE_NAME="${SOURCE_NAME:-PQ1 Water Testing Results Report}"
AGENT_NAME="${AGENT_NAME:-pq1_water_qc_agent}"

# ---- embedding (Voyage best model, 1024d) -----------------------------------
EMBED_MODEL="voyage-3-large"
EMBED_DIM=1024
EMBED_ENDPOINT="https://api.voyageai.com/v1"
EMBED_TYPE="openai"          # Voyage exposes an OpenAI-compatible endpoint
EMBED_CHUNK_SIZE=512

# ---- LLM (GPT-4o on OpenAI) -------------------------------------------------
LLM_MODEL="gpt-4o"
LLM_ENDPOINT="https://api.openai.com/v1"
LLM_TYPE="openai"
LLM_CONTEXT=128000

# =============================================================================
# preflight
# =============================================================================
log() { printf '[%s] %s\n' "$(date -u +%H:%M:%SZ)" "$*"; }
die() { log "ERROR: $*" >&2; exit 1; }

[ -r "$SECRETS_FILE" ] || die "secrets file not readable: $SECRETS_FILE"
[ -r "$SA_JSON" ]      || die "Google service-account JSON not readable: $SA_JSON"
[ -d "$LETTA_STACK_DIR" ] || die "Letta stack dir not found: $LETTA_STACK_DIR"

# load secrets (no echo)
set -a; . "$SECRETS_FILE"; set +a
VOYAGE_KEY="${VOYAGEAI_API_KEY:-${VOYAGE_API_KEY:-}}"
OPENAI_KEY="${OPENAI_API_KEY:-${OPENAI_SERVICE_API_KEY:-}}"
[ -n "$VOYAGE_KEY" ] || die "VOYAGEAI_API_KEY (or VOYAGE_API_KEY) missing in $SECRETS_FILE"
[ -n "$OPENAI_KEY" ] || die "OPENAI_API_KEY (or OPENAI_SERVICE_API_KEY) missing in $SECRETS_FILE"

# print SA client_email so user can share Drive folder with it if not done yet
SA_EMAIL=$(python3 -c "import json; print(json.load(open('$SA_JSON')).get('client_email',''))")
log "service account: $SA_EMAIL"
log "make sure the Drive folder ($DRIVE_FOLDER_ID) is shared with that email (Viewer)."

# python deps for the ingest step
log "installing Python deps (google-api-python-client, google-auth, requests)…"
python3 -m pip install --quiet --disable-pip-version-check \
  google-api-python-client google-auth requests >/dev/null

# =============================================================================
# step 1 — switch Letta server's default embedding to voyage-3-large
# =============================================================================
LETTA_ENV="$LETTA_STACK_DIR/.env"
if [ -f "$LETTA_ENV" ]; then
  STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
  cp -a "$LETTA_ENV" "$LETTA_ENV.bak.$STAMP"
  log "backed up env to $LETTA_ENV.bak.$STAMP"
  # purge any prior managed lines so re-runs don't duplicate
  sed -i '/# === pq1-deploy managed/,/# === end pq1-deploy/d' "$LETTA_ENV"
  cat >> "$LETTA_ENV" <<EOF
# === pq1-deploy managed ($STAMP) ===
LETTA_DEFAULT_EMBEDDING_MODEL=$EMBED_MODEL
LETTA_DEFAULT_EMBEDDING_ENDPOINT=$EMBED_ENDPOINT
LETTA_DEFAULT_EMBEDDING_ENDPOINT_TYPE=$EMBED_TYPE
LETTA_DEFAULT_EMBEDDING_DIM=$EMBED_DIM
LETTA_DEFAULT_EMBEDDING_CHUNK_SIZE=$EMBED_CHUNK_SIZE
VOYAGE_API_KEY=$VOYAGE_KEY
VOYAGEAI_API_KEY=$VOYAGE_KEY
# === end pq1-deploy ===
EOF
  log "appended Voyage defaults to $LETTA_ENV; restarting letta container…"
  ( cd "$LETTA_STACK_DIR" && docker compose up -d --no-deps letta >/dev/null )
else
  log "WARN: $LETTA_ENV not found — skipping server default switch (still fine, since the source/agent we create below carry explicit embedding_config)"
fi

# wait for Letta to be reachable
log "waiting for Letta to be ready at $LETTA_BASE…"
for i in $(seq 1 60); do
  if curl -fsS -o /dev/null -H "Authorization: Bearer $LETTA_TOKEN" "$LETTA_BASE/v1/agents/?limit=1"; then
    log "  letta ready"
    break
  fi
  sleep 2
  [ "$i" = 60 ] && die "Letta did not come up within 120s"
done

# =============================================================================
# helpers
# =============================================================================
api() {
  local method="$1" path="$2" data="${3-}"
  if [ -n "$data" ]; then
    curl -fsS -X "$method" "$LETTA_BASE$path" \
      -H "Authorization: Bearer $LETTA_TOKEN" -H "Content-Type: application/json" \
      -d "$data"
  else
    curl -fsS -X "$method" "$LETTA_BASE$path" \
      -H "Authorization: Bearer $LETTA_TOKEN"
  fi
}

jget() { python3 -c "import json,sys;print(json.load(sys.stdin)$1)"; }

# =============================================================================
# step 2 — find-or-create source (with explicit Voyage embedding_config)
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
    "PQ1 (Performance Qualification Phase 1) water testing results database for the "
    "RO water system EQP-PPS002 at Purely Plant GmbH. Contains the bilingual MK/EN "
    "water analysis reports from outsourced laboratories (JZU Kumanovo and others) "
    "covering Grade A (4-5 µS/cm) and Grade B (<1.0 µS/cm) purified water sampling "
    "per the WHO TRS 929 Annex 3 three-phase water-system qualification model. "
    "Equipment tag PP/S/002; supplier Magan Mak / Valter Skupina; current document "
    "code EQP-PPS002-PQ-V01. Embeddings: voyage-3-large 1024d."
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
# step 3 — find-or-create agent
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
  AGENT_PAYLOAD=$(python3 <<PY
import json
system_prompt = """<base_instructions>
You are pq1_water_qc_agent — the canonical stateful agent for the PQ1 (Performance Qualification Phase 1) water testing results database of the RO water system EQP-PPS002 at Purely Plant GmbH.

Scope:
- Equipment tag PP/S/002, doc-coding root EQP-PPS002, current document EQP-PPS002-PQ-V01.
- Supplier reference: Magan Mak / Valter Skupina.
- Two purified water grades produced: Grade A (conductivity 4.0–5.0 µS/cm) and Grade B (conductivity < 1.0 µS/cm).
- PQ1 sampling strategy: 16 mandatory daily sampling locations + 36 rotational sampling locations; Extraction Department deliberately excluded.
- Bilingual MK | EN content; MK column is the regulatory anchor for Macedonian Pravilnik 183/2018 conformance, EN column for EU GMP audit (EudraLex Vol.4 Annex 1, WHO TRS 929 Annex 3, ISPE Baseline Vol.5).

Behavior:
- Your attached source 'PQ1 Water Testing Results Report' contains the lab analysis PDFs. Use archival_memory_search with ONLY the query parameter (no tags — chunks are untagged) to retrieve PQ1 evidence.
- Always cite the source file name + chunk index when returning a finding (the chunk header has the structure [PQ1 | filename | chunk X/Y]).
- When asked for trends, group findings by sampling location and by date. When asked for excursions, compare observed conductivity / TOC / microbial counts against the limits above and flag exceedances explicitly with their location and date.
- When a user asks something outside PQ1 scope (e.g. general GMP, OOS investigation procedure), route them to the appropriate sibling agent via inter-agent messaging rather than hallucinating.
- Continue executing and calling tools until the task is complete or you need user input.
</base_instructions>"""

print(json.dumps({
  "name": "$AGENT_NAME",
  "description": "PQ1 (RO water system EQP-PPS002) stateful QC agent. GPT-4o + voyage-3-large.",
  "system": system_prompt,
  "tags": ["pq1","water-system","EQP-PPS002","purely-plant","qc"],
  "llm_config": {
    "model": "$LLM_MODEL",
    "model_endpoint_type": "$LLM_TYPE",
    "model_endpoint": "$LLM_ENDPOINT",
    "context_window": $LLM_CONTEXT
  },
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
  AGENT_ID="$(api POST /v1/agents/ "$AGENT_PAYLOAD" | python3 -c "import json,sys;print(json.load(sys.stdin)['id'])")"
fi
log "agent id: $AGENT_ID"

# =============================================================================
# step 4 — attach source to agent (idempotent: ignore "already attached" 409s)
# =============================================================================
log "attaching source $SRC_ID to agent $AGENT_ID…"
curl -sS -X PATCH "$LETTA_BASE/v1/agents/$AGENT_ID/sources/attach/$SRC_ID" \
  -H "Authorization: Bearer $LETTA_TOKEN" -H "Content-Type: application/json" \
  -d '{}' -o /tmp/pq1_attach.json -w 'attach HTTP %{http_code}\n' || true
cat /tmp/pq1_attach.json 2>/dev/null | head -c 300; echo

# =============================================================================
# step 5 — Drive → Letta ingestion
# =============================================================================
export PQ1_SOURCE_ID="$SRC_ID"
export PQ1_AGENT_ID="$AGENT_ID"
export LETTA_BASE LETTA_TOKEN SA_JSON DRIVE_FOLDER_ID
log "starting Drive → Letta ingestion…"
python3 "$(dirname "$0")/ingest_pdfs.py"

# =============================================================================
log "DONE.
  source_id: $SRC_ID
  agent_id : $AGENT_ID
Test it:
  curl -sS -H 'Authorization: Bearer $LETTA_TOKEN' \\
    -H 'Content-Type: application/json' -X POST \\
    $LETTA_BASE/v1/agents/$AGENT_ID/messages \\
    -d '{\"messages\":[{\"role\":\"user\",\"content\":\"List every sampling location that recorded a Grade B conductivity excursion (>1.0 µS/cm) during PQ1.\"}]}'"
