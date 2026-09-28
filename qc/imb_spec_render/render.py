import os,subprocess,sys,glob
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,"/tmp/imb"); from prep import prep
CH="/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
def one(args):
    src,pdir,ppre=args
    base=os.path.basename(src)[:-5]
    p=f"{ppre}/{base}.html"; out=f"{pdir}/{base}.pdf"
    prep(src,p)
    r=subprocess.run([CH,"--headless=new","--disable-gpu","--no-sandbox",
        "--font-render-hinting=none","--no-pdf-header-footer",
        "--run-all-compositor-stages-before-draw","--virtual-time-budget=20000",
        f"--print-to-pdf={out}",p],capture_output=True,timeout=180)
    ok=os.path.exists(out) and os.path.getsize(out)>20000
    return base,ok,(os.path.getsize(out) if os.path.exists(out) else 0)
jobs=[(f,"pdf/T1","prep/T1") for f in sorted(glob.glob("T1/*.html"))]+ \
     [(f,"pdf/T2","prep/T2") for f in sorted(glob.glob("T2/*.html"))]
print("rendering",len(jobs))
bad=[]
with ThreadPoolExecutor(max_workers=4) as ex:
    for base,ok,sz in ex.map(one,jobs):
        if not ok: bad.append(base); print("  FAIL",base)
print("failures:",len(bad))
