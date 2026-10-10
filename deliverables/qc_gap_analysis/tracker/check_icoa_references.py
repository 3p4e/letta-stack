#!/usr/bin/env python3
"""Every internal certificate a delivered certificate of quality cites is the right document.

    python3 tracker/check_icoa_references.py        # exit 1 on any finding

Head of QC, 28.09.2026: "check the references of the internal certificates of analysis being
referenced". For every CoQ in the Tranche 3 and out-of-tranche deliveries whose rows cite an iCoA:
the rows and section 03 print the iCoA's code and issue date; the iCoA page exists and prints that
code and date, the CoQ's production and processing batch and specification, the register's test
date on every analysis, and exactly the sections for the rows the CoQ credits to it (1, 2, 7 —
and 8 where loss on drying was in-house); test date <= iCoA issue <= CoQ issue; and no iCoA number
is one an approved scan already sent gives another lot. A CoQ whose rows 1, 2, 7 cite CNP has no
iCoA and is listed as such.
"""
import glob,re,json,csv,sys,collections,datetime,os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0,'tracker'); from check_certificate_claims import printed_text
import audit_empty_results as A
tm=A.tranche_map()
def tranche(c):
    for k in (c.get('pp'),c.get('cb'),(c.get('cb') or '').replace('＊','')):
        if k and k in tm: return tm[k]
reg=json.load(open('coq_artifact_data.json',encoding='utf-8'))['coqs']
byc={c['regcode']:c for c in reg}
scan={r['coq_code']:(r['batch'],r['icoa_cited']) for r in csv.DictReader(open('tracker/SCAN_INDEX_2026-09-25.tsv',encoding='utf-8'),delimiter='\t')}
sent_icoa={}
for code,(b,ic) in scan.items():
    for x in re.findall(r'iCoA-PP_26-\d{3}',ic or ''): sent_icoa.setdefault(x,[]).append((code,b))
T=lambda p: re.sub(r'\s+',' ',printed_text(open(p,encoding='utf-8').read()))
coqp={re.search(r'CoQ-PP_26-\d{3}',p).group(0):p for p in glob.glob('DELIVER_2026-09-2*/CoQ/*/HTML/*.html')}
icp={re.search(r'iCoA-PP_26-\d{3}',p).group(0):p for p in glob.glob('DELIVER_2026-09-2*/iCoA/*/HTML/*.html')}
d=lambda s: datetime.datetime.strptime(s,'%d.%m.%Y') if s and re.fullmatch(r'\d\d\.\d\d\.\d{4}',s) else None
findings=collections.defaultdict(list); rows=[]; notes=[]
gaps=set()
for g in glob.glob('DELIVER_2026-09-2*/REGISTER_GAPS.tsv'):
    for r in csv.reader(open(g,encoding='utf-8'),delimiter='\t'):
        if len(r)>=3: gaps.add((r[0],r[2]))
recs=sorted([c for c in reg if tranche(c) not in A.FROZEN and not c.get('withdrawn') and c['regcode'] in coqp],key=lambda c:c['regcode'])
for c in recs:
    k=c['regcode']; ic=c.get('icoa_code'); cited=[r for r in c['rows'] if r.get('doc')==ic]
    nos=[r['no'] for r in cited]
    if not cited:
        rows.append((k,c.get('pp') or c.get('cb'),'— (no iCoA: '+', '.join(sorted({r['doc'] for r in c['rows'] if r['no'] in ('1','2','7')}))+')','','','','',''))
        continue
    ct=T(coqp[k])
    for r in cited:
        if r.get('dd')!=c.get('icoa_issue'): findings['CoQ row date != iCoA issue'].append((k,r['no'],r.get('dd'),c.get('icoa_issue')))
        if str(r.get('res')).strip() not in ('Conforms','Conforms to monograph') and not str(r.get('res')).startswith(('Conforms','6.','7.','8.','9.','1')): findings['row result'].append((k,r['no'],r.get('res')))
    m=re.search(re.escape(ic)+r' · (\d\d\.\d\d\.\d{4})',ct)
    if not m: findings['section 03 does not cite the iCoA with a date'].append(k)
    elif m.group(1)!=c.get('icoa_issue'): findings['section 03 date != iCoA issue'].append((k,m.group(1),c.get('icoa_issue')))
    p=icp.get(ic)
    if not p: findings['no iCoA page'].append((k,ic)); continue
    it=T(p)
    iss=re.search(r'Issued · Издаден (\d\d\.\d\d\.\d{4})',it); td=re.search(r'Test Date Датум на испитување (\S+)',it)
    prod=re.search(r'Production Batch № Производна серија № (\S+)',it); proc=re.search(r'Processing Batch № Процесна серија № (\S+)',it)
    if not iss or iss.group(1)!=c.get('icoa_issue'): findings['iCoA issue date'].append((k,ic,iss and iss.group(1),c.get('icoa_issue')))
    want=c.get('icoa_tested')
    if '8' in nos and d(c.get('icoa_issue')):
        # loss on drying in-house: a 24-hour window closing on the iCoA's issue date (CLAUDE.md §4)
        want=(d(c['icoa_issue'])-datetime.timedelta(days=1)).strftime('%d.%m')+' – '+c['icoa_issue']
        tdm=re.search(r'Test Date Датум на испитување (\d\d\.\d\d – \d\d\.\d\d\.\d{4})',it)
        td=tdm or td
    if not want and (k,'test date') in gaps and td and td.group(1)=='—':
        notes.append('%s: no test date — no packaging date on record (REGISTER_GAPS)' % k)
    elif not td or td.group(1)!=want: findings['iCoA test date != register'].append((k,ic,td and td.group(1),want))
    pp=c.get('pp') or '—'; cb=c.get('cb') or '—'
    if not prod or prod.group(1)!=(pp if re.match(r'^[PJ]\d{5,6}$',pp) else '—'): findings['production batch'].append((k,prod and prod.group(1),pp))
    if not proc or proc.group(1)!=cb: findings['processing batch'].append((k,proc and proc.group(1),cb))
    for lab in ('QCSP_001_','_THC'):
        pass
    for x in re.findall(r'QCSP_001_\S+',it):
        if x not in ct: findings['spec differs from CoQ'].append((k,x))
    mdates=set(re.findall(r'(?:loupe|100–400×|balance 0\.0001 g) · (\d\d\.\d\d\.\d{4})',it))
    if mdates and mdates!={c.get('icoa_tested')} and '8' not in nos: findings['analysis dates != test date'].append((k,mdates,c.get('icoa_tested')))
    sec={'1':'02.1','2':'02.2','7':'02.3'}
    printed=[n for n,s in sec.items() if (s+' ') in it]
    if '8' in nos and 'Loss on Drying' not in it and 'LOSS ON DRYING' not in it.upper(): findings['LoD credited, not on iCoA'].append(k)
    if sorted(printed)!=sorted([n for n in nos if n in sec]): findings['iCoA sections != CoQ credits'].append((k,printed,nos))
    tst,ii,ci=d(c.get('icoa_tested')),d(c.get('icoa_issue')),d(c.get('issue'))
    if not tst and (k,'test date') in gaps:
        tst=ii
    if not (tst and ii and ci and tst<=ii<=ci): findings['date order test<=iCoA issue<=CoQ issue'].append((k,c.get('icoa_tested'),c.get('icoa_issue'),c.get('issue')))
    if ic in sent_icoa and not any(b in (c.get('pp'),c.get('cb')) for _,b in sent_icoa[ic]): findings['number also on a sent scan of another lot'].append((k,ic,sent_icoa[ic]))
    rows.append((k,c.get('pp') or c.get('cb'),ic,c.get('icoa_issue'),c.get('icoa_tested'),', '.join(nos),c.get('issue'),'ok'))
print('delivered CoQs read:',len(recs),'citing an iCoA:',sum(1 for r in rows if r[2].startswith('iCoA')))
if '-v' in sys.argv:
    for r in rows: print('  %s  %-10s %-15s issued %-10s tested %-10s rows %-8s CoQ %s' % r[:7])
for n in notes: print('  note: '+n)
print('findings:',{k:len(v) for k,v in findings.items()} or 'none')
for k,v in findings.items(): print(' ',k,v[:6])
codes=[r[2] for r in rows if r[2].startswith('iCoA')]; dup=[x for x,n in collections.Counter(codes).items() if n>1]
print('duplicate codes:',dup or 'none')
sys.exit(1 if findings or dup else 0)
