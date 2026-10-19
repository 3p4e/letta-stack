import json,re,hashlib,collections,os,sys
src=open("extract.py").read().split("def to_docx")[0]; exec(src)
tree={x["id"]:x["path"] for x in json.load(open("tree.json"))}
rec={r["id"]:r for r in json.load(open("extract.json"))}
def sha(i):
    try: return hashlib.sha256(open("md/%s.md"%i,"rb").read()).hexdigest()
    except Exception: return None
def fname_cv(path):
    n=path.rsplit("/",1)[-1]
    m=re.match(r"\s*(QC[A-Z]{1,6}|QA[A-Z]{1,6}|QCSOP)[\s_]*0?(\d{1,3})(?:[\s_\-]*(A\d{1,2}))?",n)
    v=re.search(r"(?:_v|\bv\.?|ver\.?\s?)0?(\d)\b",n,re.I)
    if not (m and v): return None,None
    return normalize(m.group(1)+m.group(2)+(m.group(3) or "")),v.group(1)
cand=collections.defaultdict(list)
status=[]
for i,r in rec.items():
    c,v,src_="","",""
    if r.get("code") and r.get("version"): c,v,src_=r["code"],r["version"].lstrip("0") or "0","header"
    else:
        c2,v2=fname_cv(r["path"])
        if c2 and r.get("chars",0)>5000: c,v,src_=c2,v2,"filename"
    if c and r.get("chars",0)>1500: cand[c].append((int(float(v)),v,i,src_))
    else: status.append((i,"uncoded" if not r.get("error") else "error",""))
scans=collections.defaultdict(list)
for i,p in tree.items():
    if p.lower().endswith(".pdf"):
        n=p.rsplit("/",1)[-1]; m=re.match(r"\s*(QC[A-Z]{1,6}|QA[A-Z]{1,6})[\s_]*0?(\d{1,3})(?:[\s_\-]*(A\d{1,2}))?",n)
        if m: scans[normalize(m.group(1)+m.group(2)+(m.group(3) or ""))].append(i)
rows=[];ingest=[]
for c,lst in sorted(cand.items()):
    top=max(x[0] for x in lst)
    for ver in sorted({x[1] for x in lst if x[0]!=top}): rows.append((c,ver,"older_version","",""))
    cur=[x for x in lst if x[0]==top]; shas={sha(x[2]) for x in cur}
    v=cur[0][1]
    if len(shas)>1: rows.append((c,v,"ambiguous",",".join(x[2] for x in cur),",".join(scans.get(c,[])))); continue
    st="paired" if scans.get(c) else "docx_only"
    rows.append((c,v,st,cur[0][2],",".join(scans.get(c,[])))); ingest.append((c,v,cur[0][2],scans.get(c,[]),cur[0][3]))
for c,ids in sorted(scans.items()):
    if c not in cand: rows.append((c,"?","scan_only","",",".join(ids)))
os.makedirs("db3_md",exist_ok=True)
for c,v,i,sc,s in ingest:
    r=rec[i]; body=open("md/%s.md"%i,encoding="utf8").read()
    fm="---\ncode: %s\nversion: %s\ntitle_mk: %s\ntitle_en: %s\neffective_date: \ndepartment: %s\nsource_name: %s\ndrive_docx_id: %s\ndrive_scan_ids: %s\ncode_source: %s\n---\n\n"%(
        c,v,json.dumps(r.get("title_mk") or "",ensure_ascii=False),json.dumps(r.get("title_en") or "",ensure_ascii=False),
        re.match(r"[A-Z]{2}",c).group(0) if False else c[:2],json.dumps(tree[i].rsplit("/",1)[-1],ensure_ascii=False),i,",".join(sc),s)
    open("db3_md/%s_v%s.md"%(c,v),"w",encoding="utf8").write(fm+body)
with open("MANIFEST.tsv","w") as f:
    f.write("code\tversion\tstatus\tdocx_id\tscan_ids\n")
    for r in rows: f.write("\t".join(r)+"\n")
    for i,s,_ in status: f.write("\t\t%s\t%s\t%s\n"%(s,i,tree[i].split("GmbH - ",1)[-1][-80:]))
print(collections.Counter(r[2] for r in rows),"uncoded/err",collections.Counter(s for _,s,_ in status),"to ingest",len(ingest),"files",len(os.listdir("db3_md")))
