#!/usr/bin/env python3
"""After the pipeline: make the P-number retrievable in both spellings, and teach
the extractors the rule for next time.

IJZ prints the zero of a P-number as a letter O ("Серија: PO60052"). The parser
transcribes what is printed, so the keywords carry PO60052 and a query for
P060052 misses the chunk. Two fixes:
  keywords  - every chunk of the new documents gets the digit-zero form added
              to important_keywords (chunk update API, verified by re-read)
  prompts   - the questions and keywords extractors get the rule in their
              sys_prompt, so future ingests write both forms themselves
"""
import os, sys, json, re, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
B = os.environ['RAGFLOW_API_SERVER'].rstrip('/'); K = os.environ['RAGFLOW_API_KEY']
DS = 'dd3ea108a3fd11f1858cf58865604f65'
AID = 'c83609aea3fd11f1858cf58865604f65'
PO = re.compile(r'\bPO(\d{5})(?=\D|$)')
RULE = ("\n\nP-NUMBERS: a packaged-lot number is the letter P followed by six digits (P060052). "
        "Some laboratories print its first zero as a letter O (PO60052). Where the certificate prints "
        "such a form, write BOTH the printed form and the digit-zero form (PO60052 and P060052).")


def req(p, data=None, method=None):
    body = json.dumps(data).encode() if data is not None else None
    r = urllib.request.Request(B + p, data=body, method=method or ('POST' if body else 'GET'),
                               headers={'Authorization': 'Bearer ' + K, 'Content-Type': 'application/json'})
    try:
        return json.load(urllib.request.urlopen(r, timeout=120))
    except urllib.error.HTTPError as e:
        return {'HTTPError': e.code, 'body': e.read()[:300].decode('utf8', 'replace')}


def all_docs():
    docs = []
    for pg in range(1, 8):
        dd = req('/api/v1/datasets/%s/documents?page=%d&page_size=100' % (DS, pg))['data']['docs']
        if not dd: break
        docs += dd
    return docs


def keywords():
    fixed = skipped = 0
    for d in all_docs():
        if d['create_date'] < '2026-09-01' or d.get('run') != 'DONE': continue
        for c in req('/api/v1/datasets/%s/documents/%s/chunks?page=1&page_size=100' % (DS, d['id']))['data'].get('chunks') or []:
            kw = [k.strip() for k in (c.get('important_keywords') or []) if k and k.strip()]
            text = ' '.join(kw) + ' ' + (c.get('content') or '')
            add = sorted({'P0' + m for m in PO.findall(text)} - set(kw))
            if not add:
                skipped += 1; continue
            r = req('/api/v1/datasets/%s/documents/%s/chunks/%s' % (DS, d['id'], c['id']),
                    {'important_keywords': kw + add}, 'PUT')
            back = req('/api/v1/datasets/%s/documents/%s/chunks?page=1&page_size=100' % (DS, d['id']))['data']['chunks']
            got = next((x for x in back if x['id'] == c['id']), {}).get('important_keywords') or []
            ok = all(a in [g.strip() for g in got] for a in add)
            print('%-48s +%s -> %s %s' % (d['name'][:48], add, r.get('code', r), 'verified' if ok else 'NOT VERIFIED'))
            fixed += ok
    print('keywords: %d chunk(s) extended, %d already fine' % (fixed, skipped))


def prompts():
    d = req('/api/v1/agents/' + AID)['data']
    if isinstance(d, list): d = d[0]
    dsl = d['dsl']
    if isinstance(dsl, str): dsl = json.loads(dsl)
    C = dsl['components']; changed = []
    for nid in ('Extractor:eCoAQuestions', 'Extractor:eCoAKeywords'):
        p = C[nid]['obj']['params']
        pr = p['prompts']
        while isinstance(pr, list) and pr and isinstance(pr[0], dict) and isinstance(pr[0].get('content'), list):
            pr = pr[0]['content']
        assert isinstance(pr, list) and isinstance(pr[0].get('content'), str)
        p['prompts'] = pr
        if 'P-NUMBERS:' not in p['sys_prompt']:
            p['sys_prompt'] = p['sys_prompt'].rstrip() + RULE; changed.append(nid)
    if not changed:
        print('prompts: rule already present'); return
    r = req('/api/v1/agents/' + AID, {'title': d['title'], 'dsl': dsl}, 'PUT')
    print('prompts PUT -> %s; rule added to %s' % (r.get('code', r), changed))
    v = req('/api/v1/agents/' + AID)['data']
    if isinstance(v, list): v = v[0]
    vd = v['dsl'] if not isinstance(v['dsl'], str) else json.loads(v['dsl'])
    for nid in changed:
        print('  verified %s: %s' % (nid, 'P-NUMBERS:' in vd['components'][nid]['obj']['params']['sys_prompt']))


if __name__ == '__main__':
    {'keywords': keywords, 'prompts': prompts}[sys.argv[1]]()
