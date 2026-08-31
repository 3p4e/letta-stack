#!/usr/bin/env python3
"""Corpus driver: the whole eCOA_DB run, tranche by tranche, priority first.

Order comes from priority_batches.tsv (Head of QC, 31.08) - a document belongs
to a batch when its filename starts with that batch's PP number (or cultivation
code for the 1024-era files). Priority documents run first, in list order; the
rest follow sorted by name.

Per tranche of TRANCHE documents:
  1. verify the extractor `prompts` fields are FLAT (trap 2) - abort if not
  2. ingest with integer run:1 + delete:true (traps 1, 6, 14)
  3. poll every document to a terminal state - DONE alone proves nothing
  4. quality gate per document: chunks > 0, no **ERROR** in indexed fields,
     quality_guard clean, questions AND keywords populated; one re-queue,
     then HELD (recorded, never silently skipped)
  5. two-pass runner over the tranche's documents (its own budget/quota stops)
  6. append records to records_corpus.json and continue

The driver is RESUMABLE: a document with a record in records_corpus.json is
never re-extracted, and one already chunked and gate-clean is not re-ingested.
A clean stop (OpenAI budget ceiling, all Gemini keys exhausted) halts the
driver with a resume note; re-running continues where it stopped.
"""
import os, sys, json, time, subprocess, urllib.request, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
B = os.environ['RAGFLOW_API_SERVER'].rstrip('/')
K = os.environ['RAGFLOW_API_KEY']
DS = os.environ.get('ECOA_DATASET_ID', 'dd3ea108a3fd11f1858cf58865604f65')
AID = os.environ.get('ECOA_AGENT_ID', 'c83609aea3fd11f1858cf58865604f65')
TRANCHE = int(os.environ.get('ECOA_TRANCHE', '20'))
OUT = os.environ.get('ECOA_RECORDS', HERE + '/records_corpus.json')
INGEST_TIMEOUT = 40 * 60

def req(p, data=None, method='GET'):
    r = urllib.request.Request(B + p, data=json.dumps(data).encode() if data is not None else None,
        method=method, headers={'Authorization': 'Bearer ' + K, 'Content-Type': 'application/json'})
    return json.load(urllib.request.urlopen(r, timeout=180))

def load(name, path):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

QG = load('qg', HERE + '/quality_guard.py')

def say(msg):
    print(msg, flush=True)

def all_docs():
    docs = []
    for pg in range(1, 6):
        dd = req('/api/v1/datasets/%s/documents?page=%d&page_size=100' % (DS, pg))['data']['docs']
        if not dd: break
        docs += dd
    return docs

def ordered_docs():
    # Files are named by PP number (P0500xx_...) OR by cultivation code
    # (CC112501_..., FB012601_1_... - '/' in a code becomes '_' in a filename),
    # so both codes from the manifest rank a document.
    rank = {}
    i = 0
    for line in open(HERE + '/priority_batches.tsv', encoding='utf-8'):
        line = line.strip()
        if not line or line.startswith('#'): continue
        parts = line.split('\t')
        if len(parts) < 3: continue
        cultiv, pp = parts[1].strip(), parts[2].strip()
        for v in {pp, cultiv, cultiv.replace('/', '_'), cultiv.split('/')[0]}:
            rank.setdefault(v, i)
        i += 1
    docs = all_docs()
    def base(x): return x['name'].split('/')[-1]
    def keys(x):
        segs = base(x).replace(',', '_').split('_')
        return (segs[0].strip(), '_'.join(segs[:2]).strip())
    def r(x):
        k1, k2 = keys(x)
        return rank.get(k2, rank.get(k1))
    prio = [x for x in docs if r(x) is not None]
    rest = [x for x in docs if r(x) is None]
    prio.sort(key=lambda x: (r(x), base(x)))
    rest.sort(key=lambda x: base(x))
    return prio, rest

def verify_prompts_flat():
    dsl = req('/api/v1/agents/' + AID)['data']['dsl']
    for nid in ('Extractor:eCoAQuestions', 'Extractor:eCoAKeywords'):
        pr = dsl['components'][nid]['obj']['params']['prompts']
        if not (isinstance(pr, list) and pr and isinstance(pr[0].get('content'), str)):
            raise SystemExit('ABORT: %s prompts field re-nested - fix before ingesting (trap 2)' % nid)

def gate(doc_id, expect_prefix):
    ch = (req('/api/v1/datasets/%s/documents/%s/chunks?page=1&page_size=100' % (DS, doc_id))['data'].get('chunks') or [])
    if not ch: return False, 'no chunks'
    for c in ch:
        blob = str(c.get('important_keywords')) + str(c.get('questions'))
        if 'ERROR' in blob: return False, 'error text in indexed fields'
        ok, probs = QG.check(c.get('content') or '')
        if not ok: return False, '; '.join(probs)
        if not c.get('questions'): return False, 'questions empty'
        if not c.get('important_keywords'): return False, 'keywords empty'
    return True, 'ok'

def start_ingest(tranche):
    verify_prompts_flat()
    req('/api/v1/documents/ingest',
        {'doc_ids': [x['id'] for x in tranche], 'run': 1, 'delete': True}, 'POST')


def wait_and_gate(tranche):
    ids = [x['id'] for x in tranche]
    deadline = time.time() + INGEST_TIMEOUT
    while time.time() < deadline:
        time.sleep(20)
        cur = {x['id']: x for x in all_docs() if x['id'] in ids}
        term = [x for x in cur.values()
                if x.get('run') in ('DONE', 'FAIL') and float(x.get('progress') or 0) in (1.0, -1.0)]
        if len(term) == len(ids): break
    held = []
    retry = []
    for x in tranche:
        ok, why = gate(x['id'], x['name'].split('/')[-1].split('_')[0])
        if not ok: retry.append((x, why))
    if retry:
        say('  re-queue %d failed doc(s): %s' % (len(retry), [x['name'][-40:] for x, _ in retry]))
        req('/api/v1/documents/ingest', {'doc_ids': [x['id'] for x, _ in retry], 'run': 1, 'delete': True}, 'POST')
        time.sleep(120)
        for x, _ in retry:
            ok, why = gate(x['id'], '')
            if not ok:
                held.append({'document': x['name'], 'doc_id': x['id'], 'held': why})
                say('  HELD (ingest): %s - %s' % (x['name'][-50:], why))
    return held

def run_runner(tranche):
    names = [x['name'].split('/')[-1].replace('.pdf', '') for x in tranche]
    out = HERE + '/_tranche_records.json'
    if os.path.exists(out): os.remove(out)
    cmd = [sys.executable, '-u', HERE + '/extract_ecoa_records.py',
           '--dataset', DS, '--out', out, '--match'] + names
    p = subprocess.run(cmd, capture_output=True, text=True)
    tail = (p.stdout or '')[-2000:]
    say(tail)
    stopped = 'RUN STOPPED CLEANLY' in (p.stdout or '')
    recs = json.load(open(out)) if os.path.exists(out) else []
    return recs, stopped

def main():
    done_docs = set()
    corpus = []
    if os.path.exists(OUT):
        corpus = json.load(open(OUT))
        done_docs = {r.get('document') for r in corpus}
        say('resuming: %d record(s) already extracted' % len(corpus))
    prio, rest = ordered_docs()
    queue = [x for x in prio + rest
             if x['name'].split('/')[-1] not in done_docs]
    say('corpus: %d document(s) to process (%d priority first)' %
        (len(queue), sum(1 for x in queue if x in prio)))
    held_all = []
    tranches = [queue[i:i + TRANCHE] for i in range(0, len(queue), TRANCHE)]
    if tranches:
        start_ingest(tranches[0])
    for i, tr in enumerate(tranches):
        say('\n===== TRANCHE %d/%d: %d docs, starting %s' %
            (i + 1, len(tranches), len(tr), tr[0]['name'][-45:]))
        held = wait_and_gate(tr)
        # Ingest-ahead: the NEXT tranche parses in RAGFlow while this one is
        # being extracted - the single task executor is otherwise idle then.
        if i + 1 < len(tranches):
            start_ingest(tranches[i + 1])
        held_all += held
        held_ids = {h['doc_id'] for h in held}
        runnable = [x for x in tr if x['id'] not in held_ids]
        recs, stopped = run_runner(runnable)
        corpus += recs
        json.dump(corpus, open(OUT, 'w'), ensure_ascii=False, indent=1)
        say('tranche done: %d records (corpus %d); %d held' % (len(recs), len(corpus), len(held)))
        if stopped:
            say('\n== DRIVER HALTED on a clean runner stop (budget or Gemini quota).')
            say('   Re-run run_corpus.py to resume where it stopped.')
            break
    json.dump(held_all, open(HERE + '/held_ingest.json', 'w'), ensure_ascii=False, indent=1)
    say('\nHELD at ingest: %d  (held_ingest.json)' % len(held_all))
    say('records total: %d -> %s' % (len(corpus), OUT))

if __name__ == '__main__':
    main()
