#!/usr/bin/env python3
"""DB3: read each downloaded Word file's own header (code, version, titles) and its text.
Writes md/<id>.md (text only) and extract.json (one record per file). Opens no PDF/scan."""
import glob, json, os, re, subprocess, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
tree = {x["id"]: x["path"] for x in json.load(open(HERE + "/tree.json"))}
_LOOK = str.maketrans("АВСЕНІЈКМОРТХУаесорху", "ABCEHIJKMOPTXYaecopxy")
_CODE = re.compile(r"^(?P<fam>[A-Z]{2,8}?|[A-Z]{2}COA)(?P<num>\d{1,3}|0?XXX|0XX)(?:A(?P<annex>\d{1,2}))?$")


def normalize(raw):
    s = re.sub(r"[\s_\-./]", "", (raw or "").translate(_LOOK).upper())
    m = _CODE.match(s)
    if not m:
        return None
    fam = m["fam"].replace("COA", "CoA") if m["fam"].endswith("COA") else m["fam"]
    out = fam + (m["num"].replace("0XX", "XXX").replace("0XXX", "XXX") if "X" in m["num"] else "%03d" % int(m["num"]))
    return out + ("A%02d" % int(m["annex"]) if m["annex"] else "")


def to_docx(path):
    if path.endswith(".docx"):
        return path
    out = os.path.join(HERE, "conv")
    os.makedirs(out, exist_ok=True)
    subprocess.run(["soffice", "--headless", "--convert-to", "docx", "--outdir", out, path],
                   capture_output=True, timeout=180)
    p = os.path.join(out, os.path.basename(path)[:-4] + ".docx")
    return p if os.path.exists(p) else None


def header_paras(path):
    z = zipfile.ZipFile(path)
    seen, out = set(), []
    for n in sorted(x for x in z.namelist() if re.match(r"word/header\d*\.xml", x)):
        x = z.read(n).decode("utf8", "replace")
        for p in re.findall(r"<w:p[ >].*?</w:p>", x, re.S):
            t = "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", p)).strip()
            if t and t not in seen:
                seen.add(t)
                out.append(t)
    return out


def read_header(paras):
    code = ver = None
    for i, t in enumerate(paras):
        if re.search(r"Code of document", t, re.I):
            for u in paras[i + 1:i + 4]:
                c = normalize(u)
                if c:
                    code = c
                    break
        m = re.search(r"(?:Верзија|Version|Ver)[^0-9]*?(\d+(?:\.\d+)?)", t, re.I)
        if m and not ver:
            ver = m.group(1)
    titles = [t for t in paras if not re.search(r"Име на документ|Name of document|Документ бр|Code of document|Верзија|Version", t)
              and not normalize(t)]
    return code, ver, titles


os.makedirs(HERE + "/md", exist_ok=True)
recs = []
for f in sorted(glob.glob(HERE + "/dl/*.docx") + glob.glob(HERE + "/dl/*.doc")):
    fid = os.path.basename(f).rsplit(".", 1)[0]
    rec = {"id": fid, "path": tree.get(fid, "?"), "ext": f.rsplit(".", 1)[-1]}
    try:
        dx = to_docx(f)
        if not dx:
            rec["error"] = "doc conversion failed"
            recs.append(rec)
            continue
        paras = header_paras(dx)
        code, ver, titles = read_header(paras)
        rec.update(code=code, version=ver, title_mk=titles[0] if titles else None,
                   title_en=titles[1] if len(titles) > 1 else None)
        md = subprocess.run(["pandoc", dx, "-t", "gfm", "--wrap=none"], capture_output=True, text=True, timeout=120).stdout
        rec["chars"] = len(md)
        open("%s/md/%s.md" % (HERE, fid), "w", encoding="utf8").write(md)
    except Exception as e:  # noqa: BLE001 - recorded, never silent
        rec["error"] = repr(e)[:120]
    recs.append(rec)
json.dump(recs, open(HERE + "/extract.json", "w"), ensure_ascii=False, indent=1)
print(len(recs), "files;", sum(1 for r in recs if r.get("code")), "with a header code;",
      sum(1 for r in recs if r.get("code") and r.get("version")), "with code+version;",
      sum(1 for r in recs if r.get("error")), "errors")
