# -*- coding: utf-8 -*-
"""Render the IPH physico-chemical certificates from the on-disk download results.

The download result never enters context: it is a JSON file on disk holding the PDF
as base64. Decoding and rendering it locally is what makes forty-four documents
affordable. Every page is cropped to drop the repeated letterhead and footer, which
are identical on every page of every certificate and carry nothing to verify.
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
    if stem.rsplit("_", 1)[-1] != "IJZ": continue
    # The batch key can itself carry an underscore (FB012601_1_2362-2026), so the
    # first underscore is not the boundary — splitting there yields the code
    # "1_2362-2026", which matches nothing and silently drops the certificate.
    # Try every split and take whichever right-hand side is a code we want,
    # exactly as the Farmahem and CNP renderers already do.
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
        # 0.098-0.94 drops the letterhead and the boilerplate footer, which are identical
        # on every page of every certificate. It deliberately keeps the "Broj: NNNN/YYYY"
        # line: a crop that cannot name its own certificate cannot be checked against the
        # document it came from, and mixing two up is the error this exercise exists to
        # catch.
        c = im.crop((0, int(h * 0.098), w, int(h * 0.94)))
        c.resize((1300, int(c.size[1] * 1300 / c.size[0]))).save(dst / f"p{i}.png")
        p.unlink()
    pdf.unlink()
    made.append((key, "rendered", len(pages)))

for k, s, n in made: print(f"{s:9} {k:<10} {n} pages   {seen[k][:52]}")
print(f"\n{len(made)} certificates, {len(WANT)-len(made)} not found")
missing = WANT - set(seen)
if missing: print("MISSING:", sorted(missing))
