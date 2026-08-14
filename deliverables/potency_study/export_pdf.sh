#!/usr/bin/env bash
# Export Potency_Atlas.html to a print-ready A4 PDF via headless Chromium.
# Uses the file's own @media print rules (light palette, no dark hero,
# no sticky nav/theme button, break-inside:avoid on cards/rows).
set -euo pipefail
cd "$(dirname "$0")"
CHROME="${CHROME:-/opt/pw-browsers/chromium-1194/chrome-linux/chrome}"
"$CHROME" --headless --no-sandbox --disable-gpu \
  --print-to-pdf=Potency_Atlas.pdf --print-to-pdf-no-header --no-pdf-header-footer \
  --virtual-time-budget=20000 "file://$PWD/Potency_Atlas.html"
echo "wrote Potency_Atlas.pdf ($(du -h Potency_Atlas.pdf | cut -f1), $(pdfinfo Potency_Atlas.pdf | awk '/^Pages/{print $2}') pages)"
