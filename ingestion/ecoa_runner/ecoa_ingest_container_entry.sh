#!/bin/bash
# ecoa-ingest container entrypoint: resumable; idles once the run has finished.
[ -f /work/ALLDONE ] && { echo "run already finished $(cat /work/ALLDONE)"; exec sleep infinity; }
command -v curl >/dev/null && command -v pgrep >/dev/null || { apt-get update -qq && apt-get install -y -qq curl procps >/dev/null; }
bash /work/app/ingestion/ecoa_runner/run_ecoa_ingest_kvm4.sh --foreground 2>&1 | tee -a /work/run.log
date -u '+%F %H:%M' > /work/ALLDONE
exec sleep infinity
