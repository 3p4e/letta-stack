#!/usr/bin/env bash
# Fetch the Cyrillic-capable faces both films need.
# Barlow Condensed is deliberately absent: it has no Cyrillic coverage and
# silently falls back, which is how Macedonian text ends up in the wrong face.
set -euo pipefail
cd "$(dirname "$0")" && mkdir -p fonts && cd fonts
B=https://raw.githubusercontent.com/google/fonts/main
curl -sSLo Oswald.ttf                 "$B/ofl/oswald/Oswald%5Bwght%5D.ttf"
curl -sSLo IBMPlexSans.ttf            "$B/ofl/ibmplexsans/IBMPlexSans%5Bwdth%2Cwght%5D.ttf"
curl -sSLo JetBrainsMono.ttf          "$B/ofl/jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf"
curl -sSLo PTSans-Regular.ttf         "$B/ofl/ptsans/PT_Sans-Web-Regular.ttf"
curl -sSLo PTSans-Bold.ttf            "$B/ofl/ptsans/PT_Sans-Web-Bold.ttf"
curl -sSLo IBMPlexMono-Regular.ttf    "$B/ofl/ibmplexmono/IBMPlexMono-Regular.ttf"
curl -sSLo IBMPlexMono-SemiBold.ttf   "$B/ofl/ibmplexmono/IBMPlexMono-SemiBold.ttf"
python3 - <<'PY'
from fontTools.ttLib import TTFont
import glob
need = "МКЌЃЏЊЉабвгдѓжзѕијќлљмнњопрстуфхцчџш"
for f in sorted(glob.glob("*.ttf")):
    t = TTFont(f, fontNumber=0, lazy=True)
    cmap = set().union(*(set(tb.cmap) for tb in t["cmap"].tables))
    miss = [c for c in need if ord(c) not in cmap]
    print(f"{f:<28}", "OK" if not miss else "MISSING " + "".join(miss))
PY
