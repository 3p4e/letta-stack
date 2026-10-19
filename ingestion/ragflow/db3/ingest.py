import os,sys,json,time,subprocess,glob
B=os.environ["RAGFLOW_API_SERVER"].rstrip("/");K=os.environ["RAGFLOW_API_KEY"];DS="880312c6cb1411f18ed047989fb7f345"
H=["-H","Authorization: Bearer "+K]
def api(m,p,body=None):
    a=["curl","-s","-m","120","-X",m,B+p]+H
    if body is not None: a+=["-H","Content-Type: application/json","-d",json.dumps(body)]
    return json.loads(subprocess.run(a,capture_output=True,text=True).stdout)
def avail_mb():
    import urllib.request
    q=json.dumps({"cmd":"awk '/MemAvailable/{print int($2/1024)}' /proc/meminfo","timeout":20}).encode()
    r=urllib.request.Request(os.environ["RUNNER_URL"].rstrip("/")+"/shell",q,{"Authorization":"Bearer "+os.environ["RUNNER_TOKEN"],"Content-Type":"application/json"})
    return int(json.load(urllib.request.urlopen(r,timeout=40))["output"].strip())
def _old_avail_mb(): return int(subprocess.run("python3 -c \"print([int(l.split()[1])//1024 for l in open('/proc/meminfo') if l.startswith('MemAvailable')][0])\"",shell=True,capture_output=True,text=True).stdout)
def docs():
    out=[];pg=1
    while True:
        d=api("GET","/api/v1/datasets/%s/documents?page=%d&page_size=100"%(DS,pg))["data"]["docs"]
        out+=d
        if len(d)<100: return out
        pg+=1
have={d["name"] for d in docs()}
files=sorted(glob.glob("db3_md/*.md"))
todo=[f for f in files if os.path.basename(f) not in have]
assert avail_mb()>1200,'KVM4 memory low'
print(len(files),"files;",len(todo),"to upload",flush=True)
BATCH=int(sys.argv[1]) if len(sys.argv)>1 else 10
for k in range(0,len(todo),BATCH):
    b=todo[k:k+BATCH]
    a=["curl","-s","-m","300","-X","POST",B+"/api/v1/datasets/%s/documents"%DS]+H
    for f in b: a+=["-F","file=@"+f]
    r=json.loads(subprocess.run(a,capture_output=True,text=True).stdout)
    if r.get("code")!=0: print("UPLOAD FAIL",str(r)[:200]);break
    ids=[d["id"] for d in r["data"]]
    r2=api("POST","/api/v1/datasets/%s/chunks"%DS,{"document_ids":ids}); print("batch",k//BATCH+1,"uploaded",len(ids),"parse",r2.get("code"),flush=True)
    t=time.time()
    while time.time()-t<1500:
        time.sleep(15)
        cur={d["id"]:d for d in docs() if d["id"] in ids}
        if all(d["run"] in("DONE","FAIL") for d in cur.values()): break
        if avail_mb()<1200: print("MEMORY GUARD: stop, avail",avail_mb(),flush=True);sys.exit(2)
    print("  ",{s:sum(1 for d in cur.values() if d["run"]==s) for s in ("DONE","FAIL")},"avail MB",avail_mb(),flush=True)
print("finished")
