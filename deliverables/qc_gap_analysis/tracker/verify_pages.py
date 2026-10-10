#!/usr/bin/env python3
"""Third read of the certificates: does the page itself show what v11 prints?

Not an extraction — a presence test. For each value the workbook prints, the certificate's
own words must contain it in one of the forms the laboratories use (decimal comma or point,
'x 10^2' / '×10²' / superscript, spaced or unspaced comparators, the Macedonian words for
conforms and absent). A page that cannot be read is reported as such, never as a mismatch.

The page is read by page_read.py — its text layer where it has one, otherwise the policy
vision chain (AGENT_MODEL_POLICY.md). Classical OCR is never used; the reasons are in
page_read.py and the rule is enforced by scripts/policy_check.py.

    QC_WORK_DIR=<dir> python3 verify_pages.py [pdf-dir ...]

<dir> holds checklist.json (written by build_checklist.py), the page cache and the
written-out misses; the PDF directories default to <dir>/newpdf and <dir>/certs.
"""
import json, os, re, sys, collections, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from page_read import page_text

S = os.environ.get('QC_WORK_DIR') or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'work')
PDFDIRS = sys.argv[1:] or [S + '/newpdf', S + '/certs']
SUP = {'⁰':'0','¹':'1','²':'2','³':'3','⁴':'4','⁵':'5','⁶':'6','⁷':'7','⁸':'8','⁹':'9'}


def norm(t):
    # the superscripts are marked BEFORE NFKC, which would otherwise flatten ² to 2 and lose
    # the distinction between 10² and the digits 102
    t = str(t)
    for k, v in SUP.items():
        t = t.replace(k, '^' + v)
    t = unicodedata.normalize('NFKC', t)
    t = t.replace(' ', ' ').replace(' ', ' ').replace(' ', ' ')
    t = t.replace('×', 'x').replace('Х', 'x').replace('х', 'x')
    t = t.replace('≤', '<=').replace('≥', '>=')
    t = re.sub(r'\s+', ' ', t)
    return t.lower()


def candidates(v):
    """Every printed form of a value that the laboratories actually use."""
    v = norm(v).strip()
    v = re.sub(r'\s*ᴰ$|\s*ᴿ$', '', v)                    # desk marks
    out = {v}
    if re.match(r'^conforms', v):
        out |= {'одговара', 'conforms', 'сообразно'}
    if v in ('absent', 'отсутна', 'отсуства', 'отсуствува'):
        out |= {'отсут', 'отсус', 'absent', 'не е детектирано'}
    if v.startswith('<= loq') or v.startswith('< loq') or v == 'nd':
        out |= {'loq', 'nd', 'не е детектиран'}
    # the rewrites COMPOSE: a page prints "1,6 x 10^3" — decimal comma AND spaced
    # multiplication AND a spaced comparator at once — so the forms are closed over,
    # not generated one at a time from the workbook's own spelling
    rewrites = [
        lambda x: x.replace('.', ','),                    # decimal comma
        lambda x: x.replace(',', '.'),
        lambda x: x.replace('x10^', ' x 10^'),
        lambda x: x.replace('x10^', 'x 10^'),
        lambda x: x.replace('x10^', ' x10^'),
        lambda x: x.replace('<', '< '),
        lambda x: x.replace('>', '> '),
        lambda x: re.sub(r'\^(\d)', r'\1', x),             # exponent written inline
    ]
    for _ in range(3):
        for x in list(out):
            for f in rewrites:
                try:
                    out.add(f(x))
                except Exception:
                    pass
    return {re.sub(r'\s+', ' ', o).strip() for o in out if o}


CACHE = S + '/pagetext'


def pdf_text(path):
    return page_text(path, cache=CACHE)


checks = json.load(open(S + '/checklist.json'))
have = {}
for d in PDFDIRS:
    if os.path.isdir(d):
        for f in os.listdir(d):
            if f.lower().endswith('.pdf'):
                have.setdefault(f, os.path.join(d, f))
# a certificate is looked up by its code inside the filename
by_code = collections.defaultdict(list)
for f, p in have.items():
    by_code[re.sub(r'[^0-9A-Za-zА-Яа-я]', '', f.split('_', 1)[-1].split(',')[0]).lower()].append(p)

TEXT = {}
ok = miss = notext = nofile = exp = 0
misses, notexts = [], []
for c in checks:
    key = re.sub(r'[^0-9A-Za-zА-Яа-я]', '', c['code']).lower()
    paths = by_code.get(key) or by_code.get(key.replace('к', 'k')) or by_code.get(key.replace('k', 'к'))
    if not paths:
        nofile += 1
        continue
    p = paths[0]
    if p not in TEXT:
        TEXT[p] = norm(pdf_text(p))
    t = TEXT[p]
    if len(t) < 200:
        notext += 1
        notexts.append((c['code'], os.path.basename(p)))
        continue
    if any(cand in t for cand in candidates(c['value'])):
        ok += 1
        continue
    # a counted range: "< 10^a и > 10^b". A reading — as opposed to the document's own
    # text layer — can lose the exponent, so the page is held to the structure it does
    # carry, a '< 10' and a '> 10' joined by и, and the exponents stay with the two-read
    # record rather than being counted as confirmed
    rng = re.match(r'^<\s*10\^?(\d?)\s*(?:и|u)\s*>\s*10\^?(\d?)$', norm(c['value']))
    if rng and t.startswith('[vision'):
        if re.search(r'<\s*10\S{0,2}\s*(?:и|u|и)\s*>\s*10', t):
            exp += 1
            continue
    m = re.match(r'^([\d.,]+)\s*x\s*10\^(\d)$', norm(c['value']))
    if m and t.startswith('[vision'):
        # where a reading loses the superscript, the mantissa beside a '10' is what the
        # page can be held to, and the exponent stays for the two-read record
        mant = m.group(1)
        if any(f'{v} x 10' in t or f'{v}x10' in t for v in {mant, mant.replace('.', ','), mant.replace(',', '.')}):
            exp += 1
            continue
    miss += 1
    misses.append(c)
print(f'values checked against a page: {ok + miss + exp}   confirmed {ok}   structure confirmed, exponent not machine-readable {exp}   not found {miss}')
print(f'certificates that could not be read at all: {len(set(notexts))} ({notext} value(s))')
print(f'values whose certificate PDF is not local yet: {nofile}')
for m in misses[:40]:
    print(f"   [{m['cu']}/{m['p']}] #{m['det']} = {m['value']!r} on {m['code']} ({m['date']})")
json.dump(misses, open(S + '/page_misses.json', 'w'), ensure_ascii=False)
