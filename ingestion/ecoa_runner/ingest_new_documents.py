#!/usr/bin/env python3
"""Ingest the new IJZ-MB certificates into eCOA_DB with the corpus-run model setup.

  python3 ingest_new.py setup            # restore the agent's models (OpenAI parser / questions)
  python3 ingest_new.py run NAME [NAME]  # upload + ingest + gate the named PDFs (from ./newpdf)
  python3 ingest_new.py run --all        # every PDF in ./newpdf not yet in the dataset
  python3 ingest_new.py status           # list the new documents and their state
"""
import os, sys, json, time, urllib.request, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
B = os.environ['RAGFLOW_API_SERVER'].rstrip('/'); K = os.environ['RAGFLOW_API_KEY']
DS = 'dd3ea108a3fd11f1858cf58865604f65'
AID = 'c83609aea3fd11f1858cf58865604f65'
VLM = 'gpt-4.1@openai-vlm@OpenAI'            # the corpus-run parser (apply_full.py, proven 30.08)
QMODEL = 'gpt-4o-mini@openai-vlm@OpenAI'      # gpt-4.1-mini cannot be registered on this tenant (add_llm 102)
KWMODEL = 'kimi-k2.6@MOONSHOT_API@Moonshot'    # moonshot-v1-128k now answers 'Not found the model / Permission denied' (04.09)
PDFDIR = os.environ.get('ECOA_PDF_DIR', HERE + '/incoming_pdfs')
LOG = HERE + '/ingest_new_documents.log'


def say(m):
    print(m, flush=True)
    open(LOG, 'a').write(time.strftime('%H:%M:%S ') + m + '\n')


def req(p, data=None, method=None, raw=None, ctype=None):
    body = raw if raw is not None else (json.dumps(data).encode() if data is not None else None)
    h = {'Authorization': 'Bearer ' + K}
    h['Content-Type'] = ctype or 'application/json'
    r = urllib.request.Request(B + p, data=body, method=method or ('POST' if body is not None else 'GET'), headers=h)
    try:
        return json.load(urllib.request.urlopen(r, timeout=300))
    except urllib.error.HTTPError as e:
        return {'HTTPError': e.code, 'body': e.read()[:400].decode('utf8', 'replace')}


def get_dsl():
    d = req('/api/v1/agents/' + AID)['data']
    if isinstance(d, list): d = d[0]
    dsl = d['dsl']
    if isinstance(dsl, str): dsl = json.loads(dsl)
    return d['title'], dsl


def setup():
    title, dsl = get_dsl()
    json.dump(dsl, open(HERE + '/agent_dsl_before_%s.json' % time.strftime('%Y%m%d-%H%M%S'), 'w'), ensure_ascii=False, indent=1)
    C = dsl['components']
    changed = []
    setups = C['Parser:eCoAParse']['obj']['params']['setups']
    for kind, s in setups.items():
        if s.get('parse_method', '').startswith(('openai/', 'gpt')) or 'OpenRouter' in str(s.get('parse_method', '')):
            if s['parse_method'] != VLM: changed.append('%s.parse_method %s -> %s' % (kind, s['parse_method'], VLM)); s['parse_method'] = VLM
        if isinstance(s.get('vlm'), dict) and s['vlm'].get('llm_id') != VLM:
            changed.append('%s.vlm %s -> %s' % (kind, s['vlm'].get('llm_id'), VLM)); s['vlm']['llm_id'] = VLM
    q = C['Extractor:eCoAQuestions']['obj']['params']
    if q.get('llm_id') != QMODEL:
        changed.append('questions %s -> %s' % (q.get('llm_id'), QMODEL)); q['llm_id'] = QMODEL
    kw = C['Extractor:eCoAKeywords']['obj']['params']
    if kw.get('llm_id') != KWMODEL:
        changed.append('keywords %s -> %s' % (kw.get('llm_id'), KWMODEL)); kw['llm_id'] = KWMODEL
    for nid in ('Extractor:eCoAQuestions', 'Extractor:eCoAKeywords'):
        pr = C[nid]['obj']['params']['prompts']
        # trap 2: the field comes back re-nested ([{content:[{content:str}]}]); send it flat
        while isinstance(pr, list) and pr and isinstance(pr[0], dict) and isinstance(pr[0].get('content'), list):
            pr = pr[0]['content']
        assert isinstance(pr, list) and pr and isinstance(pr[0].get('content'), str), 'prompts unreadable on ' + nid
        if C[nid]['obj']['params']['prompts'] != pr:
            changed.append('%s prompts flattened -> %r' % (nid, pr[0]['content'][:60]))
            C[nid]['obj']['params']['prompts'] = pr
    if not changed:
        say('setup: nothing to change'); return
    r = req('/api/v1/agents/' + AID, {'title': title, 'dsl': dsl}, 'PUT')
    say('setup PUT -> code %s' % r.get('code', r))
    for c in changed: say('  ' + c)
    _, v = get_dsl()
    s = v['components']['Parser:eCoAParse']['obj']['params']['setups']['pdf']
    say('verified: pdf.parse_method=%s vlm=%s questions=%s keywords=%s' % (
        s['parse_method'], s['vlm']['llm_id'],
        v['components']['Extractor:eCoAQuestions']['obj']['params']['llm_id'],
        v['components']['Extractor:eCoAKeywords']['obj']['params']['llm_id']))


def all_docs():
    docs = []
    for pg in range(1, 8):
        dd = req('/api/v1/datasets/%s/documents?page=%d&page_size=100' % (DS, pg))['data']['docs']
        if not dd: break
        docs += dd
    return docs


def upload(name):
    b = b'----ragflow' + str(int(time.time() * 1000)).encode()
    parts = [b'--' + b,
             ('Content-Disposition: form-data; name="file"; filename="%s"' % name).encode(),
             b'Content-Type: application/pdf\r\n',
             open(os.path.join(PDFDIR, name), 'rb').read(),
             b'--' + b + b'--\r\n']
    r = req('/api/v1/datasets/%s/documents' % DS, raw=b'\r\n'.join(parts), ctype='multipart/form-data; boundary=' + b.decode())
    if r.get('code') != 0: say('  upload FAILED %s: %s' % (name, str(r)[:300])); return None
    return r['data'][0]['id']


def gate(doc_id):
    QG = importlib.util.spec_from_file_location('qg', HERE + '/quality_guard.py')
    m = importlib.util.module_from_spec(QG); QG.loader.exec_module(m)
    ch = (req('/api/v1/datasets/%s/documents/%s/chunks?page=1&page_size=100' % (DS, doc_id))['data'].get('chunks') or [])
    if not ch: return False, 'no chunks'
    for c in ch:
        blob = str(c.get('important_keywords')) + str(c.get('questions'))
        if 'ERROR' in blob: return False, 'error text in indexed fields'
        ok, probs = m.check(c.get('content') or '')
        if not ok: return False, '; '.join(probs)
        if not c.get('questions'): return False, 'questions empty'
        if not c.get('important_keywords'): return False, 'keywords empty'
    return True, 'ok (%d chunk(s))' % len(ch)


def run(names, timeout=40 * 60):
    have = {d['name']: d for d in all_docs()}
    ids = {}
    for n in names:
        if n in have:
            say('already in dataset: %s (run=%s chunks=%s)' % (n, have[n].get('run'), have[n].get('chunk_count')))
            ids[n] = have[n]['id']; continue
        did = upload(n)
        if did: ids[n] = did; say('uploaded %s -> %s' % (n, did))
    if not ids: return
    r = req('/api/v1/documents/ingest', {'doc_ids': list(ids.values()), 'run': 1, 'delete': True}, 'POST')
    say('ingest queued %d doc(s) -> %s' % (len(ids), str(r)[:200]))
    deadline = time.time() + timeout
    pending = set(ids.values())
    while pending and time.time() < deadline:
        time.sleep(20)
        cur = {d['id']: d for d in all_docs() if d['id'] in pending}
        for did, d in cur.items():
            if d.get('run') in ('DONE', 'FAIL') and float(d.get('progress') or 0) in (1.0, -1.0):
                pending.discard(did)
                ok, why = gate(did) if d.get('run') == 'DONE' else (False, 'run=FAIL')
                msg = (d.get('progress_msg') or '').strip().splitlines()
                say('%-8s %-48s %s | %s' % ('GATE-OK' if ok else 'HELD', d['name'][:48], why, (msg[-1][:160] if msg else '')))
    for did in pending:
        say('TIMEOUT still running: %s' % did)


def status():
    for d in sorted(all_docs(), key=lambda x: x['create_date']):
        if d['create_date'] > '2026-09-01':
            msg = (d.get('progress_msg') or '').strip().splitlines()
            print('%-48s run=%-6s prog=%-5s chunks=%s | %s' % (d['name'][:48], d.get('run'), d.get('progress'), d.get('chunk_count'), (msg[-1][:150] if msg else '')))


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'setup': setup()
    elif cmd == 'upload':   # upload only, no parse - the parser waits for OpenAI credit
        have = {d['name'] for d in all_docs()}
        for n in sorted(os.listdir(PDFDIR)):
            if n in have: say('already in dataset: ' + n); continue
            did = upload(n); say('uploaded %s -> %s' % (n, did))
    elif cmd == 'status': status()
    elif cmd == 'run':
        names = sorted(os.listdir(PDFDIR)) if sys.argv[2] == '--all' else sys.argv[2:]
        run(names)
