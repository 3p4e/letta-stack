#!/usr/bin/env python3
"""Snapshot the page text of every document in RAGflow eCOA_INGEST — the complete re-ingestion of the eCoA database
(eCOA_PIPE, Claude Haiku 5.5 parser and extractors, 11.10.2026) — into ingestion/ragflow/cache/all_cert_texts_<date>.json,
in the shape of the 30.08 eCOA_DB cache (id, name, meta, text, n_chunks).

    RAGFLOW_API_SERVER=… RAGFLOW_API_KEY=… python3 ingestion/ecoa_runner/refresh_ingest_cache.py 2026-10-22

eCOA_DB (283 documents) is the retired set (Head of QC, 22.10.2026, DESK_CORRECTIONS #227).
"""
import concurrent.futures as cf
import json
import os
import sys
import urllib.request

DS = '71b9c168b4a311f1a370a99b32e82467'   # eCOA_INGEST
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main(stamp):
    base = (os.environ.get('RAGFLOW_API_SERVER') or os.environ['RAGFLOW_API']).rstrip('/') + '/api/v1'
    head = {'Authorization': 'Bearer ' + os.environ['RAGFLOW_API_KEY']}

    def get(u):
        return json.load(urllib.request.urlopen(urllib.request.Request(base + u, headers=head), timeout=120))

    docs, page = [], 1
    while True:
        d = get('/datasets/%s/documents?page=%d&page_size=100' % (DS, page))['data']['docs']
        if not d:
            break
        docs += d
        page += 1

    def one(x):
        ch = get('/datasets/%s/documents/%s/chunks?page=1&page_size=100' % (DS, x['id']))['data'].get('chunks') or []
        return {'id': x['id'], 'name': x['name'], 'meta': json.dumps(x.get('meta_fields') or {}, ensure_ascii=False),
                'text': '\n'.join(c.get('content', '') for c in ch), 'n_chunks': str(len(ch))}

    with cf.ThreadPoolExecutor(8) as ex:
        out = sorted(ex.map(one, docs), key=lambda r: r['name'])
    dest = os.path.join(ROOT, 'ingestion', 'ragflow', 'cache', 'all_cert_texts_%s.json' % stamp)
    json.dump(out, open(dest, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('%d documents, %d without text -> %s' % (len(out), sum(not r['text'].strip() for r in out), dest))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))
