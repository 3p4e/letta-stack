import os, json, time, urllib.request, urllib.error, re, sys
B=os.environ['RAGFLOW_API_SERVER'].rstrip('/'); K=os.environ['RAGFLOW_API_KEY']
DS='dd3ea108a3fd11f1858cf58865604f65'
HERE=os.path.dirname(os.path.abspath(__file__))
def req(p,d=None,m='GET',t=180):
    r=urllib.request.Request(B+p,data=json.dumps(d).encode() if d is not None else None,method=m,
      headers={'Authorization':'Bearer '+K,'Content-Type':'application/json'})
    return json.load(urllib.request.urlopen(r,timeout=t))

docs=[]
for p in range(1,5):
    d=req('/api/v1/datasets/%s/documents?page=%d&page_size=100'%(DS,p))['data']['docs']
    if not d: break
    docs+=d
by={x['name']:x for x in docs}
want=[n for n in by if re.search(r'(320-0587|1032-1851|163-0271|628-1129|904-1589|946-1684)-25',n)]
seen=set()
for lab in ['FHM','CNP','_IJZ.','PP','NGP','DFL']:
    for n in sorted(by):
        if lab in n and n not in want and lab not in seen:
            want.append(n); seen.add(lab); break
print('PILOT SET (%d)'%len(want)); sys.stdout.flush()

res=[]
for i,name in enumerate(want,1):
    did=by[name]['id']; short=name.split('/')[-1]
    print('\n[%d/%d] %s'%(i,len(want),short)); sys.stdout.flush()
    # clear stale chunks first — re-ingest does NOT replace them
    try:
        cl=req('/api/v1/datasets/%s/documents/%s/chunks?page_size=200'%(DS,did))['data']['chunks']
        if cl:
            req('/api/v1/datasets/%s/documents/%s/chunks'%(DS,did),
                {'chunk_ids':[c['id'] for c in cl]},'DELETE')
        left=req('/api/v1/datasets/%s/documents/%s/chunks?page_size=200'%(DS,did))['data']['chunks']
        # an empty-body DELETE returns code 0 and deletes nothing - verify the count
        print('   cleared %d -> %d remaining'%(len(cl),len(left))); sys.stdout.flush()
        if left: print('   WARNING: clear failed, stale chunks remain'); sys.stdout.flush()
    except urllib.error.HTTPError as e:
        print('   clear -> HTTP %d %s'%(e.code,e.read().decode()[:120])); sys.stdout.flush()
    t0=time.time()
    try:
        req('/api/v1/documents/ingest',{'doc_ids':[did],'run':1},'POST')
    except urllib.error.HTTPError as e:
        print('   START FAILED',e.code,e.read().decode()[:150]); sys.stdout.flush(); continue
    st,ch,msg='UNKNOWN',0,''
    for _ in range(160):
        time.sleep(15)
        try: x=req('/api/v1/datasets/%s/documents?id=%s'%(DS,did))['data']['docs'][0]
        except Exception: continue
        st=x.get('run'); ch=x.get('chunk_count') or 0; msg=(x.get('progress_msg') or '')
        if st in ('DONE','FAIL','CANCEL'): break
    mins=(time.time()-t0)/60
    print('   -> %s  chunks=%d  %.1f min'%(st,ch,mins)); sys.stdout.flush()
    if st=='FAIL': print('   msg:',msg.strip().replace('\n',' | ')[-250:]); sys.stdout.flush()
    r={'name':short,'id':did,'run':st,'chunks':ch,'min':round(mins,1)}
    if st=='DONE' and ch:
        cks=req('/api/v1/datasets/%s/documents/%s/chunks?page_size=100'%(DS,did))['data']
        cl=cks.get('chunks',[])
        txt='\n'.join(c.get('content') or '' for c in cl)
        r['cyr']=len(re.findall(r'[А-Яа-яЀ-ӿ]',txt)); r['lat']=len(re.findall(r'[A-Za-z]',txt))
        m=re.findall(r'(\d[\d,\.]*)\s*[хx]\s*10\^?(\d)',txt)
        r['powers']=m[:6]
        print('   cyr=%d lat=%d  powers=%s'%(r['cyr'],r['lat'],m[:6])); sys.stdout.flush()
        json.dump(cl,open(HERE+'/pilot_%s.json'%re.sub(r'\W+','_',short)[:40],'w'),ensure_ascii=False,indent=1)
    res.append(r); json.dump(res,open(HERE+'/pilot2_results.json','w'),ensure_ascii=False,indent=1)

print('\n=== SUMMARY ===')
for r in res:
    print('%-7s chunks=%-3d %5.1fmin cyr=%-5s %s'%(r['run'],r['chunks'],r['min'],r.get('cyr','-'),r['name']))
