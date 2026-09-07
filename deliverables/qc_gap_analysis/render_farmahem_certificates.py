# -*- coding: utf-8 -*-
"""Render the Farmahem certificates from the on-disk download results.

Same shape as the IPH renderer, with two differences forced by the documents:
these are two-page scans, and the crop keeps more of the head because the
Farmahem sheet carries its certificate number and the sample identity in the same
upper block. As always the crop must name its own certificate.
"""
import base64, json, pathlib, re, subprocess, sys
from PIL import Image

TR = pathlib.Path("/root/.claude/projects/-home-user-letta-stack/"
                  "4877ce6e-ae82-551e-bf35-5698c379c3be/tool-results")
OUT = pathlib.Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
WANT = {re.sub(r"[^A-Z0-9]", "", c.upper()) for c in json.load(open(sys.argv[2]))}

seen, made = {}, []
for f in sorted(TR.glob("mcp-Google_Drive-download_file_content-*.txt")):
    try: d = json.load(open(f))
    except Exception: continue
    t = d.get("title", "")
    stem = t.rsplit(".", 1)[0]
    if stem.rsplit("_", 1)[-1] != "FHM": continue
    # The batch key can itself carry an underscore (GRC102501_2_051-6-K-26), so the
    # first underscore is not the boundary. Try every split and take whichever
    # right-hand side is a code we are looking for.
    parts = stem.split(",")[0].split("_")
    cands = [re.sub(r"[^A-Z0-9]", "", "_".join(parts[i:]).strip().upper())
             for i in range(1, len(parts))]
    key = next((k for k in cands if k in WANT), None)
    if key is None or key in seen: continue
    seen[key] = t
    dst = OUT / key
    if (dst / "p1.png").exists(): made.append((key, "cached", "?")); continue
    dst.mkdir(parents=True, exist_ok=True)
    pdf = dst / "doc.pdf"; pdf.write_bytes(base64.b64decode(d["content"]))
    subprocess.run(["pdftoppm", "-r", "200", "-png", str(pdf), str(dst / "raw")], check=True)
    pages = sorted(dst.glob("raw-*.png"))
    for i, p in enumerate(pages, 1):
        im = Image.open(p); w, h = im.size
        c = im.crop((0, int(h * 0.05), w, int(h * 0.93)))
        c.resize((1200, int(c.size[1] * 1200 / c.size[0]))).save(dst / f"p{i}.png")
        p.unlink()
    pdf.unlink()
    made.append((key, "rendered", len(pages)))

for k, s, n in sorted(made): print(f"{s:9} {k:<14} {n}p  {seen[k][:50]}")
print(f"\n{len(made)} of {len(WANT)} certificates rendered")
missing = WANT - set(seen)
if missing: print("MISSING:", sorted(missing))
