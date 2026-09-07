#!/usr/bin/env python3
"""Third read of the certificates: does the page itself show what v11 prints?

Not an extraction — a presence test. For each value the workbook prints, the certificate's
text layer must contain it in one of the forms the laboratories use (decimal comma or point,
'x 10^2' / '×10²' / superscript, spaced or unspaced comparators, the Macedonian words for
conforms and absent). A page with no text layer is reported as such, never as a mismatch.
"""
import json, os, re, sys, collections, unicodedata
import pymupdf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocr import ocr_pdf

S = '/tmp/claude-0/-home-user-letta-stack/4877ce6e-ae82-551e-bf35-5698c379c3be/scratchpad'
PDFDIRS = [S + '/newpdf', S + '/certs']
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
    base = set(out)
    for x in list(base):
        out.add(x.replace('.', ','))                      # decimal comma
        out.add(x.replace(',', '.'))
        out.add(x.replace('x10^', ' x 10^'))
        out.add(x.replace('x10^', 'x 10^'))
        out.add(x.replace('x10^', ' x10^'))
        out.add(x.replace('<', '< '))
        out.add(x.replace('<', ''))
        m = re.match(r'^([\d.,]+)\s*x\s*10\^(\d)$', x)
        if m:                                             # 5.4x10^2 -> also 540 and 5,4x10²
            out.add(f'{m.group(1)} x 10{m.group(2)}')
            out.add(f'{m.group(1)}x10{m.group(2)}')
    return {re.sub(r'\s+', ' ', o).strip() for o in out if o}


CACHE = S + '/pagetext'
os.makedirs(CACHE, exist_ok=True)


def pdf_text(path):
    """The page's own text, from its text layer when it has one, else by OCR (mkd+eng).
    Cached, because OCR costs about eight seconds a document."""
    key = os.path.join(CACHE, re.sub(r'[^0-9A-Za-zА-Яа-я.\-]', '_', os.path.basename(path)) + '.txt')
    if os.path.exists(key):
        return open(key, encoding='utf-8').read()
    try:
        doc = pymupdf.open(path)
        t = '\n'.join(p.get_text() for p in doc)
        doc.close()
    except Exception:
        t = ''
    if len(t.strip()) < 200:
        try:
            t = '[OCR]\n' + ocr_pdf(path)
        except Exception as e:
            t = ''
    open(key, 'w', encoding='utf-8').write(t)
    return t


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
    # a counted range: "< 10^a и > 10^b". OCR renders the superscripts as °, o, or an inline
    # digit, so the page can be held to the structure — a '< 10' and a '> 10' joined by и —
    # and the exponents stay with the two-read record
    rng = re.match(r'^<\s*10\^?(\d?)\s*(?:и|u)\s*>\s*10\^?(\d?)$', norm(c['value']))
    if rng and t.startswith('[ocr]'):
        if re.search(r'<\s*10\S{0,2}\s*(?:и|u|и)\s*>\s*10', t):
            exp += 1
            continue
    m = re.match(r'^([\d.,]+)\s*x\s*10\^(\d)$', norm(c['value']))
    if m and t.startswith('[ocr]'):
        # OCR renders a superscript as °, o or an inline digit; the mantissa beside a '10' is
        # what the page can be held to, and the exponent stays for the two-read record
        mant = m.group(1)
        if any(f'{v} x 10' in t or f'{v}x10' in t for v in {mant, mant.replace('.', ','), mant.replace(',', '.')}):
            exp += 1
            continue
    miss += 1
    misses.append(c)
print(f'values checked against a page: {ok + miss + exp}   confirmed {ok}   structure confirmed, exponent not machine-readable {exp}   not found {miss}')
print(f'certificates without a text layer: {len(set(notexts))} ({notext} value(s))')
print(f'values whose certificate PDF is not local yet: {nofile}')
for m in misses[:40]:
    print(f"   [{m['cu']}/{m['p']}] #{m['det']} = {m['value']!r} on {m['code']} ({m['date']})")
json.dump(misses, open(S + '/page_misses.json', 'w'), ensure_ascii=False)
