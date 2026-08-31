#!/usr/bin/env python3
"""Assemble extraction records into a queryable table (SQLite + xlsx).

This is the layer that answers the enumeration questions. Vector retrieval cannot:
it returns top-k similar chunks, so "all THC results for all batches" over 79
batches silently returns a plausible subset. These are SQL questions.

  1. all Total THC results, all batches
  2. all Total THC results, per strain
  3. all analysis results for batch X
  4. latest release results for batch X
  5. batch / strain / THC / certificate code / link
  6. batches with more than one THC result (retests)

A value only enters the table when both independent reads agreed. Values held for
review are kept, flagged, and EXCLUDED from every answer until a human confirms them -
a missing number is recoverable, a wrong one is not.
"""
import json, sqlite3, os, sys, argparse, datetime, re

def parse_date(s):
    if not s: return None
    s = str(s).strip()
    for f in ('%d.%m.%Y', '%d.%m.%Y г.', '%Y-%m-%d', '%d/%m/%Y'):
        try: return datetime.datetime.strptime(s.rstrip(' год.'), f).date().isoformat()
        except Exception: pass
    m = re.search(r'(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})', s)
    if m: return '%s-%02d-%02d' % (m.group(3), int(m.group(2)), int(m.group(1)))
    return None


_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, 'common'))
sys.path.insert(0, os.path.join(_HERE, '..', 'common'))
try:
    from batch_id import batch_key
except Exception:
    batch_key = lambda x: (x or None)
try:
    from pp_batch import pp_batch      # Head of QC canonical form, 23.08.2026
except Exception:
    pp_batch = lambda x: (x or None)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
try:
    from extract_ecoa_records import norm_range
except Exception:
    norm_range = lambda v: None
# These two are in-repo and must NOT be wrapped in a silent fallback. A stubbed
# `governing` returns no criterion for any parameter, which makes every
# out-of-specification query return zero rows and the table look clean. An import
# error must stop the build, not quietly disable the acceptance criteria.
from pheur import governing, max_acceptable, classify_printed_limit
# Strain names are resolved against the controlled list, so a certificate typo
# ("Cap Junkie") groups with the strain it refers to rather than as its own.
from controlled import canonical_strain, canonical_unit

# A batch is filed under TWO codes: the cultivation code (GP0824_02) and the PP
# number (P050022). Certificates use whichever their laboratory was given, so
# without unification one physical batch splits into two - each looking
# half-tested, and its retests reading as separate histories. The Head of QC's
# manifest is the authority for the pairing; the cultivation code wins because
# it is the form the sec. 2.1 batch grammar validates.
def _load_batch_aliases():
    m = {}
    path = os.path.join(_HERE, 'priority_batches.tsv')
    if not os.path.exists(path):
        return m
    for line in open(path, encoding='utf-8'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.split('\t')
        if len(parts) < 3:
            continue
        cultiv, pp = parts[1].strip(), parts[2].strip()
        canon = pp_batch(cultiv) or cultiv
        if pp and pp != cultiv:
            m[pp.upper()] = canon
    return m

BATCH_ALIAS = _load_batch_aliases()

# A batch code is a short alpha prefix + digits, optionally a sub-lot and a
# verification V. Models sometimes append the strain or the lab to it
# ("BSS052501 - Blue Sunset Sherbet -"); keying that verbatim splits one batch
# across several rows, so isolate the code before handing it to batch_key.
_CODE = re.compile(r'\b([A-Z]{1,4}\s?\d{4,8}(?:\s?[-_/]\s?\d{1,3})?V?)\b')

# "мин. 5.00 %" / "min. 5.00" / "≥ 5.00" - a floor, never a ceiling.
_MINIMUM = re.compile(r'^\s*(?:мин|min|најмалку|не\s*помалку)\.?\s|^\s*[≥>]')

def clean_batch(raw):
    """Canonical batch per the Head of QC grammar (GG1024_01), falling back to
    the repo key only if no batch code can be isolated. A PP number resolves to
    its cultivation code so one batch never splits across two keys."""
    if not raw: return None
    v = pp_batch(raw)
    if not v:
        m = _CODE.search(str(raw).strip().upper())
        v = batch_key(m.group(1)) if m else None
    if not v: return None
    return BATCH_ALIAS.get(v.upper(), v)

SCHEMA = """
CREATE TABLE IF NOT EXISTS certificate (
  doc_id TEXT PRIMARY KEY, document TEXT, batch TEXT, batch_printed TEXT,
  p_number TEXT, strain TEXT, cert_code TEXT, date_of_issue TEXT, date_iso TEXT,
  lab TEXT, lab_accreditation TEXT, lab_accreditation_body TEXT, lab_standard TEXT,
  test_type TEXT, conclusion TEXT, accreditation_note TEXT,
  reads_agree INT, ragflow_url TEXT);
CREATE TABLE IF NOT EXISTS result (
  doc_id TEXT, batch TEXT, strain TEXT, cert_code TEXT, date_iso TEXT, lab TEXT,
  test_type TEXT, parameter TEXT, parameter_printed TEXT,
  result_printed TEXT, result_numeric REAL, unit TEXT,
  limit_printed TEXT, limit_numeric REAL,
  limit_max_printed TEXT, limit_max_numeric REAL,
  governing_limit REAL, governing_ref TEXT, printed_limit_disagrees INT,
  limit_status TEXT, limit_status_note TEXT,
  range_low REAL, range_high REAL, outside_range INT,
  exceeds_criterion INT, exceeds_max INT, limit_is_minimum INT, below_minimum INT,
  method TEXT, method_accredited INT, coverage TEXT, covered_by TEXT,
  confidence TEXT, reads_agree INT, read_a TEXT, read_b TEXT,
  FOREIGN KEY(doc_id) REFERENCES certificate(doc_id));
CREATE INDEX IF NOT EXISTS ix_res_batch ON result(batch);
CREATE INDEX IF NOT EXISTS ix_res_param ON result(parameter);
CREATE INDEX IF NOT EXISTS ix_res_strain ON result(strain);
"""

def build(records, dbpath, base_url=''):
    if os.path.exists(dbpath): os.remove(dbpath)
    db = sqlite3.connect(dbpath); db.executescript(SCHEMA)
    for r in records:
        if not (r.get('raw') or {}).get('A') and not (r.get('raw') or {}).get('B'):
            continue
        if not r.get('parameters') and not r.get('batch_canonical'):
            continue
        did = r.get('doc_id'); batch = clean_batch(r.get('batch_canonical'))
        strain = canonical_strain(r.get('strain'))
        diso = parse_date(r.get('date_of_issue'))
        url = ('%s/document/%s' % (base_url.rstrip('/'), did)) if base_url else None
        db.execute('INSERT OR REPLACE INTO certificate VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
            (did, r.get('document'), batch, r.get('batch_printed'), r.get('p_number'),
             strain, r.get('cert_code'), r.get('date_of_issue'), diso,
             r.get('lab'), r.get('lab_accreditation'), r.get('lab_accreditation_body'),
             r.get('lab_standard'), r.get('test_type'), r.get('overall_conclusion'),
             r.get('accreditation_note'), int(bool(r.get('reads_agree'))), url))
        for p in r.get('parameters') or []:
            # Compute the two flags here from the stored numbers rather than trusting
            # a field the extractor may or may not have written - the field was renamed
            # mid-project and older records carry the old name or none at all.
            rv, lv = p.get('result_numeric'), p.get('limit_numeric')
            conf_ok = p.get('confidence') == 'ok'
            # The GOVERNING criterion is Ph. Eur. cat. C / the product specification,
            # not whatever the certificate printed. A printed limit that disagrees is
            # a template defect to surface, never a threshold to judge against.
            gl, gref = governing(p.get('parameter'))
            # A criterion has a history. A certificate printing the criterion that
            # was in force when it was issued is correct for its date, not defective.
            lstat, lnote = classify_printed_limit(p.get('parameter'), lv, diso)
            disagrees = int(lstat == 'disagrees')
            mv = p.get('limit_max_numeric')
            if mv is None:
                mv = max_acceptable(p.get('parameter'))
            # A two-sided criterion (Total THC "19.8 - 24.2 %") is not a ceiling.
            rng = norm_range(p.get('limit_printed'))
            rlo, rhi = (rng if rng else (None, None))
            orange = int(rv < rlo or rv > rhi) if (conf_ok and rv is not None and rng) else None
            # A printed limit can be a FLOOR, not a ceiling: CNP potency
            # certificates print "мин. 5.00 %" against Total THC. Comparing a
            # result against it as a maximum flagged 26.32 % THC as exceeding
            # its criterion - eleven false findings, every one a good batch.
            is_min = int(bool(_MINIMUM.match(str(p.get('limit_printed') or ''))))
            use = gl if gl is not None else (None if is_min else lv)
            ec = int(rv > use) if (conf_ok and rv is not None and use is not None) else None
            bm = int(rv < lv) if (conf_ok and is_min and rv is not None and lv is not None) else None
            em = int(rv > mv) if (conf_ok and rv is not None and mv is not None) else None
            db.execute('INSERT INTO result VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                (did, batch, strain, r.get('cert_code'), diso, r.get('lab'),
                 r.get('test_type'), p.get('parameter'), p.get('parameter_printed'),
                 p.get('result_printed'), p.get('result_numeric'),
                 canonical_unit(p.get('unit')),
                 p.get('limit_printed'), p.get('limit_numeric'),
                 p.get('limit_max_printed'), p.get('limit_max_numeric'),
                 gl, gref, disagrees, lstat, lnote,
                 rlo, rhi, orange,
                 ec, em, is_min, bm,
                 p.get('method'),
                 (None if p.get('method_accredited') is None
                  else int(p['method_accredited'])),
                 p.get('coverage'), p.get('covered_by'),
                 p.get('confidence'), int(bool(p.get('reads_agree'))),
                 json.dumps(p.get('read_a'), ensure_ascii=False),
                 json.dumps(p.get('read_b'), ensure_ascii=False)))
    db.commit(); return db

# The six questions, as SQL. Confirmed values only.
QUERIES = {
 '1_all_thc': """SELECT batch, strain, result_numeric AS thc_pct, cert_code, date_iso, lab
                 FROM result WHERE parameter='total_thc' AND confidence='ok'
                 ORDER BY batch, date_iso""",
 '2_thc_per_strain': """SELECT strain, COUNT(*) n, ROUND(MIN(result_numeric),2) min_thc,
                 ROUND(AVG(result_numeric),2) avg_thc, ROUND(MAX(result_numeric),2) max_thc
                 FROM result WHERE parameter='total_thc' AND confidence='ok' AND strain IS NOT NULL
                 GROUP BY strain ORDER BY strain""",
 '5_batch_register': """SELECT DISTINCT c.batch, c.strain, r.result_numeric AS thc_pct,
                 c.cert_code, c.date_iso, c.ragflow_url
                 FROM certificate c LEFT JOIN result r
                   ON r.doc_id=c.doc_id AND r.parameter='total_thc' AND r.confidence='ok'
                 ORDER BY c.strain, c.batch""",
 '6_retests': """SELECT batch, strain, COUNT(*) n_results,
                 GROUP_CONCAT(result_numeric||' ('||COALESCE(date_iso,'?')||')', ' | ') series
                 FROM result WHERE parameter='total_thc' AND confidence='ok'
                 GROUP BY batch HAVING COUNT(*)>1 ORDER BY batch""",
 'OUT_OF_SPEC_outside_range': """SELECT batch, cert_code, parameter, result_numeric,
                 range_low, range_high, date_iso FROM result
                 WHERE outside_range=1 AND confidence='ok' ORDER BY batch""",
 'printed_limit_disagrees_with_PhEur': """SELECT batch, cert_code, lab, parameter,
                 limit_printed, limit_numeric AS printed, governing_limit AS should_be, governing_ref
                 FROM result WHERE printed_limit_disagrees=1 ORDER BY parameter, batch""",
 'printed_limit_superseded_not_defective': """SELECT batch, cert_code, date_iso, lab, parameter,
                 limit_printed, governing_limit AS now_is, limit_status_note
                 FROM result WHERE limit_status='superseded' ORDER BY parameter, batch""",
 'results_from_NON_ACCREDITED_methods': """SELECT batch, cert_code, lab, parameter,
                 result_printed, method
                 FROM result WHERE method_accredited=0 AND confidence='ok'
                 ORDER BY batch, cert_code, parameter""",
 'BELOW_MINIMUM': """SELECT batch, cert_code, parameter, result_printed, limit_printed
                 FROM result WHERE below_minimum=1 AND confidence='ok' ORDER BY batch""",
 'needs_review': """SELECT batch, cert_code, parameter, read_a, read_b
                 FROM result WHERE confidence!='ok' ORDER BY batch, parameter""",
 'exceeds_stated_criterion': """SELECT batch, cert_code, parameter, result_numeric,
                 limit_numeric AS criterion, limit_max_numeric AS max_acceptable, date_iso
                 FROM result WHERE exceeds_criterion=1 AND confidence='ok' ORDER BY batch""",
 'OUT_OF_SPEC_exceeds_max': """SELECT batch, cert_code, parameter, result_numeric,
                 limit_max_numeric AS max_acceptable, date_iso
                 FROM result WHERE exceeds_max=1 AND confidence='ok' ORDER BY batch""",
}

def q_for_batch(db, batch):   # questions 3 and 4
    rows = db.execute("""SELECT date_iso, cert_code, parameter, result_printed, limit_printed,
                         over_limit, confidence FROM result
                         WHERE batch=? ORDER BY date_iso DESC, parameter""", (batch,)).fetchall()
    return rows

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--records', required=True)
    ap.add_argument('--db', default=os.path.dirname(os.path.abspath(__file__)) + '/ecoa.sqlite')
    ap.add_argument('--base-url', default=os.environ.get('RAGFLOW_API_SERVER', ''))
    a = ap.parse_args()
    recs = json.load(open(a.records))
    db = build(recs, a.db, a.base_url)
    n_c = db.execute('SELECT COUNT(*) FROM certificate').fetchone()[0]
    n_r = db.execute('SELECT COUNT(*) FROM result').fetchone()[0]
    n_ok = db.execute("SELECT COUNT(*) FROM result WHERE confidence='ok'").fetchone()[0]
    print('%s\n%d certificates, %d results (%d confirmed, %d held for review)'
          % (a.db, n_c, n_r, n_ok, n_r - n_ok))
    for name, sql in QUERIES.items():
        rows = db.execute(sql).fetchall()
        print('\n--- %s : %d row(s) ---' % (name, len(rows)))
        for row in rows[:12]:
            print('   ', ' | '.join('' if v is None else str(v)[:38] for v in row))
