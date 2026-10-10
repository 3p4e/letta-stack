# -*- coding: utf-8 -*-
"""Render the CNP potency certificates from the on-disk download results.

One page each. The crop keeps 0.10-0.82 of the page height: that band carries the
control-book number ППКnnnnn and the issue date on one line, the sample name and
серија below it, and the whole results table — everything being verified, and enough
to name the certificate the crop came from.
"""
import base64, json, pathlib, re, subprocess, sys
from PIL import Image

TR = pathlib.Path("/root/.claude/projects/-home-user-letta-stack/"
                  "4877ce6e-ae82-551e-bf35-5698c379c3be/tool-results")
OUT = pathlib.Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
WANT = {re.sub(r"[^A-ZА-Я0-9]", "", c.upper()) for c in json.load(open(sys.argv[2]))}

seen, made = {}, []
for f in sorted(TR.glob("mcp-Google_Drive-download_file_content-*.txt")):
    try: d = json.load(open(f))
    except Exception: continue
    t = d.get("title", "")
    stem = t.rsplit(".", 1)[0]
    if stem.rsplit("_", 1)[-1] != "CNP": continue
    parts = stem.split(",")[0].split("_")
    cands = [re.sub(r"[^A-ZА-Я0-9]", "", "_".join(parts[i:]).strip().upper())
             for i in range(1, len(parts))]
    key = next((k for k in cands if k in WANT), None)
    if key is None or key in seen: continue
    seen[key] = t
    dst = OUT / key
    if (dst / "p1.png").exists(): made.append((key, "cached")); continue
    dst.mkdir(parents=True, exist_ok=True)
    pdf = dst / "doc.pdf"; pdf.write_bytes(base64.b64decode(d["content"]))
    subprocess.run(["pdftoppm", "-r", "200", "-png", str(pdf), str(dst / "raw")], check=True)
    for i, p in enumerate(sorted(dst.glob("raw-*.png")), 1):
        im = Image.open(p); w, h = im.size
        c = im.crop((0, int(h * 0.10), w, int(h * 0.82)))
        c.resize((1250, int(c.size[1] * 1250 / c.size[0]))).save(dst / f"p{i}.png")
        p.unlink()
    pdf.unlink()
    made.append((key, "rendered"))

for k, s in sorted(made): print(f"{s:9} {k:<12} {seen[k][:50]}")
print(f"\n{len(made)} of {len(WANT)} rendered")
miss = WANT - set(seen)
if miss: print("MISSING:", sorted(miss))
