#!/usr/bin/env python3
"""Two-pass eCoA extraction runner.

Renders each certificate page at 300 DPI and reads it with TWO independent vision
models. Fields the two reads disagree on are set to null and flagged for review -
never silently resolved. Numbers are never taken from a PDF text layer.

Ground rule from the register audit: a TYMC exponent misread by one power of ten
turns a failing batch into a passing one. A single unverified read caused that.
"""
import os, io, re, json, base64, time, urllib.request, urllib.error, argparse, sys

RAG = os.environ['RAGFLOW_API_SERVER'].rstrip('/')
RAGKEY = os.environ['RAGFLOW_API_KEY']
DPI = 300

SUP = str.maketrans('⁰¹²³⁴⁵⁶⁷⁸⁹', '0123456789')

PARAM_KEYS = ["identification_a_macroscopic","identification_b_microscopic","identification_c_hplc",
    # Totals as defined in the product specification, Section 02.
    "total_thc","total_cbd","total_cbn",
    # Individual cannabinoids as actually printed on certificates. The totals are
    # DERIVED from these (Total THC = THC + THCA x 0.877), so collapsing them into
    # "other" loses the arithmetic and gives several rows the same key.
    "thc_free","thca","cbd_free","cbda","cbn_free","cbna",
    "foreign_matter","loss_on_drying","tamc","tymc",
    "bile_tolerant_gram_negative","salmonella","escherichia_coli","pseudomonas_aeruginosa",
    "staphylococcus_aureus","aflatoxin_b1","aflatoxins_total","ochratoxin_a","lead","cadmium",
    "arsenic","mercury","pesticide_residues","pesticide_residues_cumcs","other"]

SYSTEM = """You are reading a scanned laboratory Certificate of Analysis for medical cannabis
flower, issued in the Republic of North Macedonia. It may be written in Macedonian Cyrillic,
in English, or bilingually. It may be an eCoA, iCoA, Certificate of Quality, Report of
Analysis or an in-house QC record.

Transcribe what is printed. Output ONLY a JSON object, no prose, no markdown fence.

THE EXPONENT RULE - the single most important instruction here.
Microbiological counts are printed in scientific notation: "4,2 x 10⁴ CFU/g". The exponent is
a small raised digit and the multiplication sign may be Cyrillic 'х' or Latin 'x'. Reading 10⁴
as 10³ understates the count tenfold and turns a failing batch into a passing one - this has
already happened in this laboratory's records. Look directly at the raised digit and read it.
Do not infer it from the magnitude you would expect. Do not default to 3.
If you cannot resolve the raised digit with certainty, set result_numeric to null and
exponent_uncertain to true. A null is correct; a guess is not.

OTHER RULES
- Never infer, estimate or complete a pattern. Transcribe only what is printed.
- Each row stands alone. Never carry a value from one row to another.
- Capture the acceptance limit printed ON THE SAME ROW. Never use a column header, another
  row, or Ph. Eur. from memory. A certificate may print a tighter limit than the
  specification; the printed limit governs. Not printed -> null.
- A microbiological criterion is often printed as TWO numbers, e.g.
  "<10^4, max 50 000 CFU/g". These are not alternatives: the first is the stated
  acceptance criterion, the second is the maximum acceptable count above which the
  result is out of specification (Ph. Eur. 5.1.8). Capture BOTH:
  limit_printed / limit_numeric = the stated criterion (10000),
  limit_max_printed / limit_max_numeric = the maximum acceptable count (50000).
  If only one number is printed, fill limit_* and leave limit_max_* null. Never
  derive the maximum yourself - only transcribe one that is printed.
- Preserve qualifiers verbatim: "N.D.", "BLQ", "<LOQ", "< 2", "Confirms", "Одговара",
  "Отсуство", "ОДГОВАРА".
- result_printed is exactly as printed. result_numeric is the same value as a plain number
  with the exponent EXPANDED: "4,2 x 10⁴" -> 42000, "5,1 х 10³" -> 5100, "9,4 %" -> 9.4.
  Not a measurement -> null.
- Identification A/B/C: if one method statement covers all three (e.g. "Identification and
  Qualitative and Quantitative Determination of Cannabinoids", or an HPLC retention-time
  identification), emit all three keys with the same printed result and method, coverage
  "collective", and covered_by holding that method text verbatim. If reported separately,
  coverage "explicit". If identification is not addressed at all, emit none of them.
- Cannabinoids: a certificate usually prints BOTH the individual compounds and the
  totals. Map them separately and never merge them:
    "Содржина на Δ9-THC" / "Delta-9-THC"        -> thc_free
    "Содржина на Δ9-THCA" / "THCA-A"            -> thca
    "Содржина на CBD"                           -> cbd_free
    "Содржина на CBDA"                          -> cbda
    "Содржина на CBN"                           -> cbn_free
    "Содржина на CBNA"                          -> cbna
    "Вкупно Δ9-THC" / "Total THC"               -> total_thc
    "Вкупно CBD" / "Total CBD"                  -> total_cbd
    "Вкупен CBN" / "Total CBN"                  -> total_cbn
  If only a total is printed, emit only the total. Never compute one from the other.
- Appearance / Изглед (macroscopic description of the flower) is part of
  Identification A in the specification - map it to identification_a_macroscopic,
  not to "other".
- Record the batch exactly as printed in batch_printed, and a Latin-folded form in
  batch_canonical (Cyrillic К -> K, etc).
- If the page is illegible or is not a certificate, return {"unreadable": true} and nothing else.

parameter must be one of: """ + " | ".join(PARAM_KEYS) + """

SCHEMA
{"batch_printed":str|null,"batch_canonical":str|null,"p_number":str|null,"strain":str|null,
 "cert_code":str|null,"date_of_issue":str|null,"date_of_sampling":str|null,"lab":str|null,
 "test_type":"release"|"retest"|"stability"|"in_process"|"unknown","overall_conclusion":str|null,
 "parameters":[{"parameter":str,"parameter_printed":str,"result_printed":str|null,
   "result_numeric":num|null,"unit":str|null,"operator":"="|"<"|"<="|">"|">="|null,
   "limit_printed":str|null,"limit_numeric":num|null,
   "limit_max_printed":str|null,"limit_max_numeric":num|null,"method":str|null,
   "exponent_uncertain":bool,"coverage":"explicit"|"collective","covered_by":str|null}]}"""


def render(pdf_bytes):
    import fitz
    doc = fitz.open(stream=pdf_bytes, filetype='pdf')
    out = []
    for page in doc:
        pix = page.get_pixmap(dpi=DPI)
        out.append(base64.b64encode(pix.tobytes('png')).decode())
    return out


def read_openai(images, model='gpt-5'):
    content = [{'type': 'text', 'text': 'Transcribe this certificate as JSON.'}]
    for b64 in images:
        content.append({'type': 'image_url',
                        'image_url': {'url': 'data:image/png;base64,' + b64, 'detail': 'high'}})
    body = {'model': model, 'messages': [{'role': 'system', 'content': SYSTEM},
                                         {'role': 'user', 'content': content}]}
    r = urllib.request.Request('https://api.openai.com/v1/chat/completions',
        data=json.dumps(body).encode(),
        headers={'Authorization': 'Bearer ' + os.environ['OPENAI_API_KEY'],
                 'Content-Type': 'application/json'})
    o = json.load(urllib.request.urlopen(r, timeout=900))
    return o['choices'][0]['message']['content'], o.get('usage', {})


def read_gemini(images, model='gemini-3.6-flash'):
    parts = [{'text': SYSTEM + '\n\nTranscribe this certificate as JSON.'}]
    for b64 in images:
        parts.append({'inline_data': {'mime_type': 'image/png', 'data': b64}})
    # Gemini 3 counts reasoning tokens against maxOutputTokens. A 2-page
    # certificate spent 5366 of 8192 on thoughts and the JSON came back truncated,
    # which looks identical to a failed read. Give the budget real headroom.
    body = {'contents': [{'parts': parts}],
            'generationConfig': {'temperature': 0, 'maxOutputTokens': 32768}}
    # Google free tier rate-limits hard (429). Rotate across every key we have
    # before giving up - a 429 on one project says nothing about the others.
    keys = [os.environ[v] for v in ('AZ_GEMINI_API_KEY', 'BN_GEMINI_API',
                                    'BN_GOOGLE_GEMINI_API_KEY') if os.environ.get(v)]
    if not keys:
        raise RuntimeError('no Gemini API key in environment')
    last = None
    o = None
    for n, key in enumerate(keys):
        r = urllib.request.Request(
            'https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent?key=%s' % (model, key),
            data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
        try:
            o = json.load(urllib.request.urlopen(r, timeout=900)); break
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (429, 503) and n < len(keys) - 1:
                print('   gemini key %d rate-limited (%d), trying next key' % (n + 1, e.code))
                sys.stdout.flush(); continue
            raise
    if o is None:
        raise last
    cand = o['candidates'][0]['content']['parts']
    return ''.join(p.get('text', '') for p in cand), o.get('usageMetadata', {})




_RANGE = re.compile(r'(-?\d+(?:[.,]\d+)?)\s*(?:-|–|—|to|до)\s*(-?\d+(?:[.,]\d+)?)')

def norm_range(v):
    """A two-sided criterion, e.g. Total THC "19.8 - 24.2 % of the labelled amount".

    Returns (low, high) or None. Without this a range parses to a single number or
    to None, and a result above the upper bound - the P050202 OOS - is never flagged.
    """
    if v is None: return None
    s = str(v).translate(SUP)
    if QUALITATIVE.search(s): return None
    m = _RANGE.search(s)
    if not m: return None
    lo, hi = (float(x.replace(',', '.')) for x in m.groups())
    return (lo, hi) if lo <= hi else (hi, lo)


def with_retry(fn, what, attempts=3, base=20):
    """Retry a vision read. A transient API failure must not be recorded as a
    failed read - that is indistinguishable from a genuine disagreement and
    would leave silent gaps across a corpus run."""
    last = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as e:
            last = e
            detail = ''
            if hasattr(e, 'read'):
                try: detail = e.read().decode()[:160]
                except Exception: pass
            print('   %s attempt %d/%d failed: %s %s' % (what, i + 1, attempts,
                  type(e).__name__, (detail or str(e))[:140])); sys.stdout.flush()
            if i < attempts - 1:
                time.sleep(base * (2 ** i))
    raise last


def parse_json(txt):
    if not txt: return None
    t = txt.strip()
    t = re.sub(r'^```(?:json)?\s*', '', t)
    t = re.sub(r'\s*```$', '', t)
    i, j = t.find('{'), t.rfind('}')
    if i < 0 or j < 0: return None
    try: return json.loads(t[i:j+1])
    except Exception: return None


# Qualitative criteria that contain a number which is NOT a limit:
# "Absence / 25 g", "Отсуство/1 g", "Conforms". Parsing 25 out of these and
# comparing a result against it manufactures exceedances that do not exist.
QUALITATIVE = re.compile(r'(absen|отсу|otsu|conform|соодветств|одговара|complies|negative|нема)', re.I)

def norm_num(v):
    """Expand a printed value to a number, superscripts included.

    Returns None for qualitative criteria and for prose - a measurement only.
    """
    if v is None: return None
    if isinstance(v, (int, float)): return float(v)
    s = str(v).translate(SUP).strip()
    if QUALITATIVE.search(s): return None
    letters = len(re.findall(r'[^\W\d_]', s, re.UNICODE))
    if letters > 12 and letters > len(s) * 0.35: return None   # prose, not a value
    m = re.search(r'(\d+(?:[.,]\d+)?)\s*[xх×✕*·•∙⋅]\s*10\s*\^?\s*(-?\d+)', s, re.I)
    if m: return float(m.group(1).replace(',', '.')) * (10 ** int(m.group(2)))
    m = re.search(r'10\s*\^?\s*(-?\d+)', s)
    if m:
        if re.search(r'\d\s*\S{0,2}\s*10\s*\^?\s*-?\d', s):
            return None      # a mantissa is present but its separator is unknown
        return float(10 ** int(m.group(1)))
    m = re.search(r'(-?\d+(?:[.,]\d+)?)', s)
    return float(m.group(1).replace(',', '.')) if m else None



sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'common'))
try:
    from pp_batch import pp_batch
except Exception:
    pp_batch = lambda v: None


def squash(v):
    """Compare free text ignoring case, spacing, punctuation and superscript form."""
    if v is None: return None
    t = str(v).translate(SUP).lower()
    t = re.sub(r'[\s\.,;:"\u201c\u201d\u2019\-]+', '', t)
    return t


def reconcile(a, b):
    """Merge two independent reads. Any disagreement -> null + flagged."""
    out = {'reads_agree': True, 'review': []}
    if not a or not b:
        return {'reads_agree': False, 'review': ['one or both reads failed'],
                'parameters': [], 'record': a or b or {}}
    # Identity fields must match exactly - a wrong batch or certificate code is fatal.
    for f in ('batch_canonical','strain','cert_code','date_of_issue'):
        va, vb = a.get(f), b.get(f)
        if f == 'batch_canonical':
            # Compare the CANONICAL code, not the raw string. One model writing
            # "Blue Gelato BG1024" and the other "BG1024" is the same batch; nulling
            # it discards a field both reads got right.
            ca, cb = pp_batch(va), pp_batch(vb)
            if ca and cb and ca == cb:
                out[f] = ca
                continue
            if ca or cb:
                va, vb = ca or va, cb or vb
        if squash(va) == squash(vb):
            out[f] = va or vb
        elif va is None or vb is None:
            # One read did not report the field. An omission is not a contradiction:
            # take the value that was read, but record that it rests on a single read.
            out[f] = va if va is not None else vb
            out.setdefault('notes', []).append('%s read by only one model' % f)
        else:
            out[f] = None; out['reads_agree'] = False
            out['review'].append('%s: %r vs %r' % (f, va, vb))
    # Descriptive fields: keep the fuller reading, never block on wording.
    for f in ('lab','overall_conclusion','test_type'):
        va, vb = a.get(f), b.get(f)
        out[f] = va if len(str(va or '')) >= len(str(vb or '')) else vb
        if squash(va) != squash(vb):
            out.setdefault('notes', []).append('%s differs in wording between reads' % f)
    # Pair the two reads' rows WITHIN each parameter. Keying on the printed label
    # alone splits a matched pair when the models word it differently; keying on the
    # parameter alone silently drops the extra rows when a certificate legitimately
    # reports several (six cannabinoids, four heavy metals). So: group by parameter,
    # match on the printed label where it agrees, then pair the remainder in order.
    def _group(rows):
        g = {}
        for p in rows or []:
            g.setdefault(p.get('parameter'), []).append(p)
        return g
    ga, gb = _group(a.get('parameters')), _group(b.get('parameters'))
    pa, pb = {}, {}
    for param in set(ga) | set(gb):
        ra, rb = list(ga.get(param, [])), list(gb.get(param, []))
        used_b = set()
        pairs = []
        for x in ra:                                   # 1. exact label match
            lx = squash(x.get('parameter_printed'))
            hit = next((j for j, y in enumerate(rb)
                        if j not in used_b and squash(y.get('parameter_printed')) == lx), None)
            if hit is not None:
                used_b.add(hit); pairs.append((x, rb[hit]))
            else:
                pairs.append((x, None))
        left = [y for j, y in enumerate(rb) if j not in used_b]
        for i, (x, y) in enumerate(pairs):             # 2. pair leftovers in order
            if y is None and left:
                pairs[i] = (x, left.pop(0))
        for y in left:
            pairs.append((None, y))
        for n, (x, y) in enumerate(pairs):
            key = (param, n)
            if x is not None: pa[key] = x
            if y is not None: pb[key] = y
    params = []
    for key in sorted(set(pa) | set(pb)):
        x, y = pa.get(key), pb.get(key)
        pname = key[0]
        if not x or not y:
            params.append({'parameter': pname,
                           'parameter_printed': (x or y or {}).get('parameter_printed'),
                           'result_numeric': None, 'confidence': 'review',
                           'reads_agree': False,
                           'note': 'reported by only one read (%s)' % ('A' if x else 'B')})
            out['reads_agree'] = False
            lbl = ((x or y or {}).get('parameter_printed') or '-')
            out['review'].append('%s (%s): present in only one read' % (pname, lbl)); continue
        rx, ry = norm_num(x.get('result_numeric') if x.get('result_numeric') is not None else x.get('result_printed')), \
                 norm_num(y.get('result_numeric') if y.get('result_numeric') is not None else y.get('result_printed'))
        lx, ly = norm_num(x.get('limit_numeric') if x.get('limit_numeric') is not None else x.get('limit_printed')), \
                 norm_num(y.get('limit_numeric') if y.get('limit_numeric') is not None else y.get('limit_printed'))
        # Agreement is decided on the NUMBERS, not on notation. "4,9 x 10^4" and
        # "4,9 x 10⁴" are the same reading; flagging them wastes reviewer attention
        # on the cases that are fine and buries the ones that are not.
        mx = norm_num(x.get('limit_max_numeric') if x.get('limit_max_numeric') is not None else x.get('limit_max_printed'))
        my_ = norm_num(y.get('limit_max_numeric') if y.get('limit_max_numeric') is not None else y.get('limit_max_printed'))
        agree = (rx == ry) and (lx == ly) and (mx == my_)
        if rx is None and ry is None:
            agree = squash(x.get('result_printed')) == squash(y.get('result_printed'))
        rec = {'parameter': pname,
               'parameter_printed': x.get('parameter_printed') or y.get('parameter_printed'),
               'result_printed': x.get('result_printed') if agree else None,
               'result_numeric': rx if agree else None,
               'limit_printed': x.get('limit_printed') if agree else None,
               'limit_numeric': lx if agree else None,
               'limit_max_printed': x.get('limit_max_printed') if agree else None,
               'limit_max_numeric': mx if agree else None,
               'unit': x.get('unit'), 'method': x.get('method'),
               'coverage': x.get('coverage'), 'covered_by': x.get('covered_by'),
               'exponent_uncertain': bool(x.get('exponent_uncertain') or y.get('exponent_uncertain')),
               'reads_agree': agree, 'confidence': 'ok' if agree else 'review',
               'read_a': {'result': x.get('result_printed'), 'limit': x.get('limit_printed')},
               'read_b': {'result': y.get('result_printed'), 'limit': y.get('limit_printed')}}
        # Two distinct questions, and conflating them is how a compliant batch gets
        # called a deviation. "Exceeds the stated criterion" is a signal to look;
        # "exceeds the maximum acceptable count" is out of specification.
        if agree and rx is not None and lx is not None:
            rec['exceeds_criterion'] = rx > lx
        if agree and rx is not None and mx is not None:
            rec['exceeds_max'] = rx > mx
        if not agree:
            out['reads_agree'] = False
            # Show WHICH field differs. Printing only results made a genuine
            # limit disagreement look identical and therefore spurious - a
            # reviewer who sees that twice stops reading the flags.
            bits = []
            if rx != ry:
                bits.append('result A=%r B=%r' % (x.get('result_printed'), y.get('result_printed')))
            if mx != my_:
                bits.append('max A=%r(%s) B=%r(%s)' % (x.get('limit_max_printed'), mx,
                                                       y.get('limit_max_printed'), my_))
            if lx != ly:
                bits.append('limit A=%r(%s) B=%r(%s)' % (x.get('limit_printed'), lx,
                                                         y.get('limit_printed'), ly))
            if not bits:
                bits.append('A=%r B=%r' % (x.get('result_printed'), y.get('result_printed')))
            out['review'].append('%s (%s): %s'
                                 % (pname, x.get('parameter_printed') or '-', '; '.join(bits)))
        params.append(rec)
    out['parameters'] = params
    for f in ('batch_printed','p_number','date_of_sampling'):
        out[f] = a.get(f) if a.get(f) == b.get(f) else None
    return out


def run(doc_ids, names, outpath):
    results = []
    for did, name in zip(doc_ids, names):
        short = name.split('/')[-1]
        print('\n=== %s' % short); sys.stdout.flush()
        pdf = urllib.request.urlopen(urllib.request.Request(
            '%s/api/v1/datasets/%s/documents/%s' % (RAG, DS, did),
            headers={'Authorization': 'Bearer ' + RAGKEY}), timeout=180).read()
        imgs = render(pdf)
        print('   %d page(s) rendered at %d DPI' % (len(imgs), DPI)); sys.stdout.flush()
        t0 = time.time()
        try: ta, ua = with_retry(lambda: read_openai(imgs), 'read A (gpt-5)')
        except Exception as e: ta, ua = '', {'error': str(e)[:120]}
        try: tb, ub = with_retry(lambda: read_gemini(imgs), 'read B (gemini)')
        except Exception as e: tb, ub = '', {'error': str(e)[:120]}
        A, B = parse_json(ta), parse_json(tb)
        if tb and B is None:
            ub = dict(ub or {}); ub['error'] = 'response did not parse as JSON (%d chars, likely truncated)' % len(tb)
        if ta and A is None:
            ua = dict(ua or {}); ua['error'] = 'response did not parse as JSON (%d chars, likely truncated)' % len(ta)
        print('   read A (gpt-5): %s | read B (gemini-3.6-flash): %s | %.0fs'
              % ('ok' if A else 'FAILED %s' % ua.get('error',''),
                 'ok' if B else 'FAILED %s' % ub.get('error',''), time.time()-t0)); sys.stdout.flush()
        rec = reconcile(A, B)
        rec['document'] = short; rec['doc_id'] = did
        rec['raw'] = {'A': A, 'B': B}
        results.append(rec)
        ok = sum(1 for p in rec.get('parameters', []) if p.get('confidence') == 'ok')
        rv = sum(1 for p in rec.get('parameters', []) if p.get('confidence') == 'review')
        print('   agreed=%d  needs review=%d  batch=%s' % (ok, rv, rec.get('batch_canonical'))); sys.stdout.flush()
        for line in rec.get('review', [])[:6]: print('     ! ' + line); sys.stdout.flush()
        json.dump(results, open(outpath, 'w'), ensure_ascii=False, indent=1)
    return results


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--dataset', default='dd3ea108a3fd11f1858cf58865604f65')
    ap.add_argument('--match', nargs='+', required=True)
    ap.add_argument('--out', default=os.path.dirname(os.path.abspath(__file__)) + '/records.json')
    a = ap.parse_args()
    DS = a.dataset
    docs = []
    for p in range(1, 6):
        d = json.load(urllib.request.urlopen(urllib.request.Request(
            '%s/api/v1/datasets/%s/documents?page=%d&page_size=100' % (RAG, DS, p),
            headers={'Authorization': 'Bearer ' + RAGKEY}), timeout=90))['data']['docs']
        if not d: break
        docs += d
    sel = [x for x in docs if any(m in x['name'] for m in a.match)]
    print('selected %d document(s)' % len(sel))
    run([x['id'] for x in sel], [x['name'] for x in sel], a.out)
