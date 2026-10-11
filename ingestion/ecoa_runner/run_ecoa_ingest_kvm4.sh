#!/bin/bash
# Unattended eCOA_INGEST load on KVM4: fetch the verified corpus, then ingest it through eCOA_PIPE
# one certificate at a time (the host has no swap), two passes. Resumable: re-running skips what is
# already downloaded and what eCOA_INGEST already holds.
#
#   export RAGFLOW_API_KEY=...   # the owning tenant's key
#   bash ingestion/ecoa_runner/run_ecoa_ingest_kvm4.sh            # starts in the background
#   tail -f /opt/ecoa_ingest/run.log                              # progress (GATE-OK / HELD lines)
set -euo pipefail
: "${RAGFLOW_API_KEY:?set RAGFLOW_API_KEY first}"
export RAGFLOW_API_SERVER="${RAGFLOW_API_SERVER:-https://ragflow.srv1231216.hstgr.cloud}"
WORK="${ECOA_WORK:-/opt/ecoa_ingest}"; HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$WORK"
if [ "${1:-}" != "--foreground" ]; then
  nohup setsid bash "$0" --foreground >> "$WORK/run.log" 2>&1 < /dev/null &
  echo "started in background; log: $WORK/run.log"; exit 0
fi
if pgrep -f "migrate_to_ecoa_pipe.py run" >/dev/null; then echo "another ingest is running - refusing to start a second"; exit 1; fi
[ -d "$WORK/venv" ] || python3 -m venv "$WORK/venv"
"$WORK/venv/bin/pip" install -q openpyxl==3.1.5
PY="$WORK/venv/bin/python"
echo "=== $(date -u '+%F %H:%M') fetch"
"$PY" "$HERE/fetch_ecoa_corpus.py" "$WORK/pdf" || echo "fetch reported problems - continuing with what verified"
export ECOA_PDF_DIR="$WORK/pdf" ECOA_RUN_LOG="$WORK/migrate.log"
cd "$HERE"
for pass in 1 2; do
  echo "=== $(date -u '+%F %H:%M') pass $pass"
  ls "$ECOA_PDF_DIR" | sort | while read -r f; do
    timeout 2700 "$PY" migrate_to_ecoa_pipe.py run "$f" 2>&1 | grep -E "GATE|HELD|FAILED|UNPARSED" | sed "s/^/$(date -u +%H:%M) /" || true
  done
done
echo "=== $(date -u '+%F %H:%M') ALLDONE"
"$PY" migrate_to_ecoa_pipe.py status 2>&1 | tail -5 || true
