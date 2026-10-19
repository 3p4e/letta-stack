#!/usr/bin/env bash
# Purely Plant document engine — render-environment font setup.
#
# Installs the FULL system Carlito + Montserrat font packages and removes any
# subset webfont copies from the user font directories that could shadow them.
#
# Why this exists: a build once shipped with Macedonian text scrambled in the
# PDF because ~/.fonts held subset webfont Carlito files (as few as 106 glyphs,
# no Cyrillic) that fontconfig preferred over the full 2 117-glyph system
# Carlito. Run this once per fresh container/session before any pp_report.py
# build; pp_verify.py's environment check (via pp_assets.check_environment())
# will also catch a recurrence, but this script prevents it outright.
#
# Usage: bash pp_setup_fonts.sh
set -euo pipefail

echo "== pp-document-suite: font environment setup =="

if command -v apt-get >/dev/null 2>&1; then
    apt-get install -y -q fonts-crosextra-carlito fonts-montserrat fonts-roboto-unhinted \
        >/tmp/pp_font_setup.log 2>&1 || {
        echo "!! apt-get install failed — see /tmp/pp_font_setup.log"; }
else
    echo "!! no apt-get on this system — install Carlito + Montserrat (full, not webfont-subset) manually"
fi

for d in "$HOME/.fonts" "$HOME/.local/share/fonts"; do
    [ -d "$d" ] || continue
    for f in "$d"/*.ttf "$d"/*.otf; do
        [ -f "$f" ] || continue
        n=$(python3 - "$f" <<'PY'
import sys
try:
    from fontTools.ttLib import TTFont
    print(len(TTFont(sys.argv[1], lazy=True).getBestCmap()))
except Exception:
    print(-1)
PY
)
        if [ "$n" != "-1" ] && [ "$n" -lt 300 ]; then
            echo "   quarantining subset font: $f ($n glyphs)"
            mkdir -p "$d/../pp_font_quarantine"
            mv "$f" "$d/../pp_font_quarantine/" 2>/dev/null || rm -f "$f"
        fi
    done
done

fc-cache -f >/dev/null 2>&1 || true

echo "-- verifying --"
python3 "$(dirname "$0")/pp_assets.py" || {
    echo "!! environment check FAILED — see output above"; exit 1; }
echo "== OK =="
