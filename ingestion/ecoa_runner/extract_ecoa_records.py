#!/usr/bin/env python3
"""Two-pass eCoA extraction runner.

Renders each certificate page at 300 DPI and reads it with TWO independent vision
models. Fields the two reads disagree on are set to null and flagged for review -
never silently resolved. Numbers are never taken from a PDF text layer.

Ground rule from the register audit: a TYMC exponent misread by one power of ten
turns a failing batch into a passing one. A single unverified read caused that.
"""
import os, io, re, json, base64, time, urllib.request, urllib.error, argparse, sys, threading
from concurrent.futures import ThreadPoolExecutor

# Keys added mid-run land in a root-only file (never the repo): a session's
# environment is fixed at container start, but each tranche spawns a fresh
# runner process, which picks these up here. Environment always wins.
_KEYFILE = '/root/.ecoa_keys.env'
if os.path.exists(_KEYFILE):
    for _line in open(_KEYFILE):
        _line = _line.strip()
        if _line and not _line.startswith('#') and '=' in _line:
            _k, _v = _line.split('=', 1)
            os.environ.setdefault(_k.strip(), _v.strip())

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
Analysis, Result of Testing (РЕЗУЛТАТ ОД ИСПИТУВАЊЕ), Report of Testing (ИЗВЕШТАЈ ОД
ТЕСТИРАЊЕ) or an in-house QC record. These titles all name the SAME kind of document -
a laboratory's report of what it found - and every one of them is a Certificate of
Analysis for our purposes. The title never changes how you read the page.

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
- A row whose value cell is a SPECIFICATION, not a measurement - "мин. 5.00 %",
  "макс. 1.0 %", "15.1 - 18.5% of the labelled amount" - is a limit line. Put it in
  limit_printed and leave result_printed and result_numeric null. In-house CoAs print
  whole columns of these; reporting one as the batch's measured value is the worst
  single error this corpus has produced.
- Appearance / Изглед (macroscopic description of the flower) is part of
  Identification A in the specification - map it to identification_a_macroscopic,
  not to "other".
- Capture the ISSUING INSTITUTION in full, as printed. A Certificate of Quality must
  cite, for every result, who performed the test and under what accreditation:
    lab            full institution name as printed
    lab_department the testing department/unit, where named
    lab_address    postal address as printed
    lab_accreditation      the accreditation register number, e.g. "LT-017", "ЛТ-005"
    lab_accreditation_body the accrediting body, e.g. "Институт за акредитација на
                           Република Северна Македонија (ИАРСМ)" / "IARNM"
    lab_standard   the accreditation standard, e.g. "MKC EN ISO/IEC 17025:2018"
    signatories    list of {name, title} for every person who signed or approved
  These are usually in the certificate header, footer, or an accreditation statement.
  Any field not printed is null - never supply an accreditation number from memory.
- cert_code is THE DOCUMENT'S OWN IDENTIFYING NUMBER - the code by which this document
  is filed and cited. Every certificate has one and it is almost never missing. Do not
  require the document to call itself a "certificate": a laboratory issues the same
  document under many titles, and all of them are Certificates of Analysis for our
  purposes:
    "РЕЗУЛТАТ ОД ИСПИТУВАЊЕ"   Result of Testing    (CNP / Faculty of Pharmacy)
    "ИЗВЕШТАЈ ОД ТЕСТИРАЊЕ"    Report of Testing    (IJZ)
    "Certificate of Analysis" / "Извештај за анализа" / "Сертификат за анализа"
  The code follows a label, which varies by laboratory. All of these introduce it:
    "Број:"                              e.g. 752/2025
    "Бр."                                e.g. 163/0271/25
    "Број на главна контролна книга:"    e.g. ППК25050   (main control book number)
    "Реф. бр." / "No." / "Report No."
  Take the code that identifies THIS DOCUMENT - not the sample number, the protocol
  number, the batch, or the accreditation number. It may be Cyrillic; transcribe it in
  the script it is printed in. If you genuinely cannot find one, return null - but look
  in the header, the top-right box, and the line above the title before concluding that.
- Some laboratories mark individual results as obtained by a NON-ACCREDITED method,
  usually with an asterisk on the row and a legend below the table, e.g.
  "Со * се означени резултати од тестирање добиени со неакредитирани методи".
  This matters: a Certificate of Quality cites the laboratory's accreditation against
  each result, and a result the laboratory itself marks as non-accredited must not be
  presented as an accredited determination. For every parameter set
  method_accredited false when the row carries such a marker, true when the certificate
  makes an accreditation statement and the row is NOT marked, and null when the
  certificate says nothing either way. Record the legend verbatim in
  accreditation_note on the certificate.
- Record the batch exactly as printed in batch_printed, and a Latin-folded form in
  batch_canonical (Cyrillic К -> K, etc).
- If the page is illegible or is not a certificate, return {"unreadable": true} and nothing else.

parameter must be one of: """ + " | ".join(PARAM_KEYS) + """

SCHEMA
{"batch_printed":str|null,"batch_canonical":str|null,"p_number":str|null,"strain":str|null,
 "cert_code":str|null,"date_of_issue":str|null,"date_of_sampling":str|null,
 "lab":str|null,"lab_department":str|null,"lab_address":str|null,
 "lab_accreditation":str|null,"lab_accreditation_body":str|null,"lab_standard":str|null,
 "signatories":[{"name":str,"title":str}]|null,
 "test_type":"release"|"retest"|"stability"|"in_process"|"unknown","overall_conclusion":str|null,
 "accreditation_note":str|null,
 "parameters":[{"parameter":str,"parameter_printed":str,"result_printed":str|null,
   "result_numeric":num|null,"unit":str|null,"operator":"="|"<"|"<="|">"|">="|null,
   "limit_printed":str|null,"limit_numeric":num|null,
   "limit_max_printed":str|null,"limit_max_numeric":num|null,"method":str|null,
   "exponent_uncertain":bool,"coverage":"explicit"|"collective","covered_by":str|null,
   "method_accredited":bool|null}]}"""


# --- Spend and quota safeguards ------------------------------------------------
# The OpenAI balance is small and prepaid; running dry mid-corpus must stop the
# run cleanly, never produce half-read documents. Costs are metered from each
# response's own usage block at published per-token prices and the run stops
# BEFORE the document that would cross the ceiling. The ceiling deliberately
# sits under the real balance so the arbiter pass and retries keep headroom.
# Every document is written to --out as it completes, so a stopped run resumes
# by re-running with the remaining documents.
OPENAI_PRICES = {'gpt-5': (1.25, 10.0), 'gpt-4.1': (2.0, 8.0), 'gpt-4.1-mini': (0.4, 1.6),
                 'gpt-5-mini': (0.25, 2.0), 'openai/gpt-5-mini': (0.25, 2.0),
                 'openai/gpt-5': (1.25, 10.0), 'google/gemini-3.6-flash': (0.30, 2.50)}
OPENAI_BUDGET_USD = float(os.environ.get('OPENAI_BUDGET_USD', '5.50'))
# The meter must survive process boundaries: each tranche is a fresh process,
# so an in-memory total guards per-tranche only. Totals persist per POOL in
# /root/.ecoa_spend.json and every fresh runner resumes the count.
_SPEND_FILE = '/root/.ecoa_spend.json'
try:
    _ALL = json.load(open(_SPEND_FILE))
except Exception:
    _ALL = {}
for _pool in ('openai', 'openrouter'):
    _ALL.setdefault(_pool, {'usd': 0.0, 'calls': 0})
SPEND = _ALL['openai']          # legacy alias; reporting sums both pools
CEILINGS = {'openai': float(os.environ.get('OPENAI_BUDGET_USD', '5.50')),
            'openrouter': float(os.environ.get('OPENROUTER_BUDGET_USD', '4.40'))}
_SPEND_LOCK = threading.Lock()


def _save_spend():
    try:
        json.dump(_ALL, open(_SPEND_FILE, 'w'))
    except Exception:
        pass


class BudgetExhausted(RuntimeError):
    pass


# Print a spend alert at every whole dollar (Head of QC, 31.08: alert at $1
# steps). The driver's log carries these to the user between tranches.
ALERT_STEP_USD = float(os.environ.get('OPENAI_ALERT_STEP_USD', '1.0'))


def _meter(model, usage, pool='openrouter'):
    pin, pout = OPENAI_PRICES.get(model, (2.0, 10.0))
    usd = (usage.get('prompt_tokens', 0) * pin + usage.get('completion_tokens', 0) * pout) / 1e6
    p = _ALL[pool]
    with _SPEND_LOCK:
        before = p['usd']
        p['usd'] += usd; p['calls'] += 1
        _save_spend()
    if int(p['usd'] / ALERT_STEP_USD) > int(before / ALERT_STEP_USD):
        print('   $$ SPEND ALERT: %s pool $%.2f of $%.2f (%d calls)'
              % (pool, p['usd'], CEILINGS[pool], p['calls'])); sys.stdout.flush()
    if p['usd'] >= CEILINGS[pool]:
        raise BudgetExhausted('%s spend $%.2f reached the $%.2f ceiling after %d calls'
                              % (pool, p['usd'], CEILINGS[pool], p['calls']))
    return usd


# All Gemini keys exhausted in one document = the free tier is done for the day.
# Continuing would burn OpenAI spend on read A with no read B to confirm it.
class GeminiExhausted(RuntimeError):
    pass


def render(pdf_bytes):
    import fitz
    doc = fitz.open(stream=pdf_bytes, filetype='pdf')
    out = []
    for page in doc:
        pix = page.get_pixmap(dpi=DPI)
        out.append(base64.b64encode(pix.tobytes('png')).decode())
    return out


def read_openai(images, model='gpt-5'):
    """Read A. THE MODEL NEVER CHANGES (Head of QC, 31.08: do not lower the
    quality of the pipeline). What changes is who serves it: the OpenAI
    platform first, and when its credit is exhausted (401/402/403/429), the
    SAME model through OpenRouter, metered against that pool's own ceiling.
    gpt-5-mini was gated against ground truth and FAILED (3 divergences,
    one a TAMC exponent) - it is not permitted here."""
    content = [{'type': 'text', 'text': 'Transcribe this certificate as JSON.'}]
    for b64 in images:
        content.append({'type': 'image_url',
                        'image_url': {'url': 'data:image/png;base64,' + b64, 'detail': 'high'}})
    def _call(base, key, mdl):
        body = {'model': mdl, 'messages': [{'role': 'system', 'content': SYSTEM},
                                           {'role': 'user', 'content': content}]}
        r = urllib.request.Request(base + '/chat/completions',
            data=json.dumps(body).encode(),
            headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
        return json.load(urllib.request.urlopen(r, timeout=900))
    try:
        o = _call('https://api.openai.com/v1', os.environ['OPENAI_API_KEY'], model)
        u = o.get('usage', {})
        u['cost_usd'] = round(_meter(model, u, pool='openai'), 4)
        return o['choices'][0]['message']['content'], u
    except urllib.error.HTTPError as e:
        if e.code not in (401, 402, 403, 429):
            raise
        ork = os.environ.get('OPEN_ROUTER_API_KEY') or os.environ.get('OPENROUTER_API_KEY')
        if not ork:
            raise
        print('   OpenAI platform refused (%d) - read A continuing on OpenRouter, same model' % e.code)
        sys.stdout.flush()
        o = _call('https://openrouter.ai/api/v1', ork, 'openai/' + model)
        u = o.get('usage', {})
        u['served_by'] = 'openrouter:openai/' + model
        u['cost_usd'] = round(_meter('openai/' + model, u, pool='openrouter'), 4)
        return o['choices'][0]['message']['content'], u


def _relay_gemini(images):
    """Backstop for Google free-tier exhaustion: the Gemini family served
    through relay providers, so read B stays a non-OpenAI vendor and the
    cross-vendor guarantee holds. Relays bill their own credit - the OpenAI
    budget meter is untouched. Order: OpenRouter first, CometAPI second
    (its gemini-3.6-flash returned empty on the live probe, so it leads with
    2.5-flash). Returns (text, usage) or None when nothing answers.
    """
    content = [{'type': 'text', 'text': SYSTEM + '\n\nTranscribe this certificate as JSON.'}]
    for b64 in images:
        content.append({'type': 'image_url',
                        'image_url': {'url': 'data:image/png;base64,' + b64}})
    relays = []
    ork = os.environ.get('OPEN_ROUTER_API_KEY') or os.environ.get('OPENROUTER_API_KEY')
    if ork:
        relays.append(('openrouter', 'https://openrouter.ai/api/v1/chat/completions', ork,
                       [m for m in (os.environ.get('OPENROUTER_GEMINI_MODEL'),
                                    'google/gemini-3.6-flash', 'google/gemini-2.5-flash') if m]))
    ck = os.environ.get('COMETAPI_API_KEY')
    if ck:
        relays.append(('cometapi', 'https://api.cometapi.com/v1/chat/completions', ck,
                       ['gemini-2.5-flash', 'gemini-3.6-flash']))
    for relay, url, key, models in relays:
        for m in models:
            body = {'model': m, 'temperature': 0, 'max_tokens': 32768,
                    'messages': [{'role': 'user', 'content': content}]}
            r = urllib.request.Request(url, data=json.dumps(body).encode(),
                headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
            try:
                o = json.load(urllib.request.urlopen(r, timeout=900))
                txt = o['choices'][0]['message']['content']
                if txt:
                    print('   read B served by %s (%s) - Google free tier exhausted' % (relay, m))
                    sys.stdout.flush()
                    u = o.get('usage', {}); u['served_by'] = '%s:%s' % (relay, m)
                    if relay == 'openrouter':
                        u['cost_usd'] = round(_meter(m, u), 4)
                    return txt, u
            except Exception as e:
                print('   %s %s failed: %s' % (relay, m, str(e)[:80])); sys.stdout.flush()
    return None


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
    # GEMINI_API_KEY is deliberately absent: Google reports it leaked; it is dead.
    keys = [os.environ[v] for v in ('AZ_GEMINI_API_KEY', 'BN_GEMINI_API',
                                    'BN_GOOGLE_GEMINI_API_KEY', 'EP_GEMINI_API',
                                    'UC_GEMINI_API')
            if os.environ.get(v)]
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
            if e.code in (429, 503):
                o = _relay_gemini(images)
                if o is None:
                    raise GeminiExhausted('all %d Gemini keys rate-limited; no OpenRouter fallback available' % len(keys))
                return o
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


# The certificate proves itself: every CNP potency page prints the free form, the
# acid form and the total, and states the conversion in its own footnote. Rule R4
# of the legacy-corpus rectification register (30.08.2026): this check alone found
# two ten-fold corruptions (ППК25117 total 1.58 for 15.38; ППК25139 THCA 0.52 for
# 26.52) with no external reference of any kind. A mismatch never picks a side -
# all three rows go to review, because of the three R4 flags raised so far, zero
# were the laboratory's fault (register E2: a flag means open the page).
TOTALS = (('total_thc', 'thc_free', 'thca', 0.877),
          ('total_cbd', 'cbd_free', 'cbda', 0.877),
          ('total_cbn', 'cbn_free', 'cbna', 0.876))
R4_TOL = 0.06


def arithmetic_check(rec):
    by = {}
    for p in rec.get('parameters') or []:
        by.setdefault(p.get('parameter'), p)
    for tot, free, acid, k in TOTALS:
        t, f, a = by.get(tot), by.get(free), by.get(acid)
        if not (t and f and a):
            continue
        tv, fv, av = t.get('result_numeric'), f.get('result_numeric'), a.get('result_numeric')
        if tv is None or fv is None or av is None:
            continue    # an N.D. component cannot be assumed zero
        want = fv + av * k
        if abs(tv - want) > R4_TOL:
            note = ('%s_mismatch: printed %s but %s + %s x %s = %.2f'
                    % (tot, tv, fv, av, k, want))
            for x in (t, f, a):
                x['confidence'] = 'review'
                x['arithmetic_mismatch'] = note
            rec.setdefault('review', []).append(note)
    return rec


# A value cell that is a specification band, not a measurement (register E5):
# "мин. 5.00 %", "15.1 - 18.5% of the labelled amount". Reported as the batch's
# measured value, these produce a confident wrong number - so they go to review
# even when both models transcribed them identically.
SPEC_LINE = re.compile(r'^\s*(?:мин|макс|min|max)\.?\s', re.I)
SPEC_RANGE = re.compile(r'^\s*\d+(?:[.,]\d+)?\s*[–—−-]\s*\d+(?:[.,]\d+)?\s*%')


def spec_line_guard(rec):
    for p in rec.get('parameters') or []:
        v = p.get('result_printed')
        if v and (SPEC_LINE.search(str(v)) or SPEC_RANGE.match(str(v))):
            p['confidence'] = 'review'
            p['spec_line_suspect'] = True
            rec.setdefault('review', []).append(
                '%s: result cell reads as a specification line: %r' % (p.get('parameter'), v))
    return rec


def _accred(xa, xb):
    """Merge the two reads' accreditation markers, resolving toward not-accredited."""
    if xa is False or xb is False:
        return False
    if xa is True and xb is True:
        return True
    return None


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
    for f in ('lab','lab_department','lab_address','lab_accreditation',
              'lab_accreditation_body','lab_standard','overall_conclusion','test_type'):
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
    # The two models sometimes KEY the same printed row differently - one maps
    # all 29 pesticide compounds to pesticide_residues, the other to "other".
    # Grouping by key would leave 29+29 unpaired rows all held for review
    # (observed on every IJZ full-panel report, tranche 1 of the corpus run).
    # Unify first: when the same printed label carries different keys and one of
    # them is "other", both take the more specific key.
    # One model transcribes the non-accredited marker into the label
    # ("* HCB"), the other does not ("HCB") - same printed row. Strip markers
    # before comparing labels, for unification and pairing alike.
    def _plabel(v):
        return (squash(v) or '').strip('*＊•· ')
    def _label_keys(rows):
        m = {}
        for p in rows or []:
            m.setdefault(_plabel(p.get('parameter_printed')), set()).add(p.get('parameter'))
        return m
    la, lb = _label_keys(a.get('parameters')), _label_keys(b.get('parameters'))
    for rows, other_map in ((a.get('parameters'), lb), (b.get('parameters'), la)):
        for p in rows or []:
            if p.get('parameter') != 'other':
                continue
            keys = other_map.get(_plabel(p.get('parameter_printed'))) or set()
            specific = [k for k in keys if k and k != 'other']
            if len(specific) == 1:
                p['parameter'] = specific[0]
    ga, gb = _group(a.get('parameters')), _group(b.get('parameters'))
    pa, pb = {}, {}
    for param in set(ga) | set(gb):
        ra, rb = list(ga.get(param, [])), list(gb.get(param, []))
        used_b = set()
        pairs = []
        for x in ra:                                   # 1. exact label match
            lx = _plabel(x.get('parameter_printed'))
            hit = next((j for j, y in enumerate(rb)
                        if j not in used_b and _plabel(y.get('parameter_printed')) == lx), None)
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
        # Per-field agreement. The RESULT and the printed LIMIT are separate
        # questions: both models reading 0,081 while only one bothers with the
        # certificate's MaxDK column is an agreed measurement with an unusable
        # printed limit - not a disagreement about the batch. The governing
        # criterion comes from Ph. Eur./the specification in build_table anyway,
        # so a limit the reads disagree on is nulled, noted, and never blocks
        # the result. Tranche 1 of the corpus run held 68% of its results on
        # exactly this before the split.
        res_agree = (rx == ry)
        if rx is None and ry is None:
            res_agree = squash(x.get('result_printed')) == squash(y.get('result_printed'))
        lim_agree = (lx == ly) and (mx == my_)
        agree = res_agree
        rec = {'parameter': pname,
               'parameter_printed': x.get('parameter_printed') or y.get('parameter_printed'),
               'result_printed': x.get('result_printed') if res_agree else None,
               'result_numeric': rx if res_agree else None,
               'limit_printed': x.get('limit_printed') if lim_agree else None,
               'limit_numeric': lx if lim_agree else None,
               'limit_max_printed': x.get('limit_max_printed') if lim_agree else None,
               'limit_max_numeric': mx if lim_agree else None,
               'unit': x.get('unit'), 'method': x.get('method'),
               'coverage': x.get('coverage'), 'covered_by': x.get('covered_by'),
               # A result the laboratory marks as non-accredited must never be cited
               # under its accreditation. Where the reads differ, take the RESTRICTIVE
               # answer: claiming accreditation the row does not carry is the harmful
               # direction, and withholding one that it does carry is merely cautious.
               'method_accredited': _accred(x.get('method_accredited'), y.get('method_accredited')),
               'exponent_uncertain': bool(x.get('exponent_uncertain') or y.get('exponent_uncertain')),
               'reads_agree': res_agree and lim_agree,
               'confidence': 'ok' if res_agree else 'review',
               'limit_disagrees_between_reads': (res_agree and not lim_agree) or None,
               'read_a': {'result': x.get('result_printed'), 'limit': x.get('limit_printed')},
               'read_b': {'result': y.get('result_printed'), 'limit': y.get('limit_printed')}}
        # Two distinct questions, and conflating them is how a compliant batch gets
        # called a deviation. "Exceeds the stated criterion" is a signal to look;
        # "exceeds the maximum acceptable count" is out of specification.
        if res_agree and not lim_agree:
            out.setdefault('notes', []).append(
                '%s: limit read differently (%r vs %r) - result confirmed, limit dropped'
                % (pname, x.get('limit_printed'), y.get('limit_printed')))
        if res_agree and lim_agree and rx is not None and lx is not None:
            rec['exceeds_criterion'] = rx > lx
        if res_agree and lim_agree and rx is not None and mx is not None:
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
    # Signatories: keep the fuller list; an approver named by only one read is still
    # evidence of attribution, and the raw reads remain available for audit.
    sa, sb = a.get('signatories') or [], b.get('signatories') or []
    out['signatories'] = sa if len(sa) >= len(sb) else sb
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
        # The two reads are independent vendors by design; running them in
        # parallel changes nothing about reconciliation and roughly halves the
        # per-document wall clock.
        stop = None
        with ThreadPoolExecutor(max_workers=2) as pool:
            fa = pool.submit(with_retry, lambda: read_openai(imgs), 'read A (gpt-5)')
            fb = pool.submit(with_retry, lambda: read_gemini(imgs), 'read B (gemini)')
            try: ta, ua = fa.result()
            except (BudgetExhausted, GeminiExhausted) as e: stop = e; ta, ua = '', {}
            except Exception as e: ta, ua = '', {'error': str(e)[:120]}
            try: tb, ub = fb.result()
            except (BudgetExhausted, GeminiExhausted) as e: stop = e; tb, ub = '', {}
            except Exception as e: tb, ub = '', {'error': str(e)[:120]}
        if stop is not None:
            print('\n== RUN STOPPED CLEANLY: %s' % stop)
            print('   %d document(s) completed and saved; re-run to resume with the rest.' % len(results))
            break
        A, B = parse_json(ta), parse_json(tb)
        if tb and B is None:
            ub = dict(ub or {}); ub['error'] = 'response did not parse as JSON (%d chars, likely truncated)' % len(tb)
        if ta and A is None:
            ua = dict(ua or {}); ua['error'] = 'response did not parse as JSON (%d chars, likely truncated)' % len(ta)
        print('   read A (gpt-5): %s | read B (gemini-3.6-flash): %s | %.0fs'
              % ('ok' if A else 'FAILED %s' % ua.get('error',''),
                 'ok' if B else 'FAILED %s' % ub.get('error',''), time.time()-t0)); sys.stdout.flush()
        rec = spec_line_guard(arithmetic_check(reconcile(A, B)))
        rec['document'] = short; rec['doc_id'] = did
        rec['raw'] = {'A': A, 'B': B}
        results.append(rec)
        ok = sum(1 for p in rec.get('parameters', []) if p.get('confidence') == 'ok')
        rv = sum(1 for p in rec.get('parameters', []) if p.get('confidence') == 'review')
        print('   agreed=%d  needs review=%d  batch=%s' % (ok, rv, rec.get('batch_canonical'))); sys.stdout.flush()
        for line in rec.get('review', [])[:6]: print('     ! ' + line); sys.stdout.flush()
        json.dump(results, open(outpath, 'w'), ensure_ascii=False, indent=1)
    print('\nOpenAI spend this run: $%.2f over %d call(s) (ceiling $%.2f)'
          % (SPEND['usd'], SPEND['calls'], OPENAI_BUDGET_USD))
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
