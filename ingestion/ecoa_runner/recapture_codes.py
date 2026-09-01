#!/usr/bin/env python3
"""Re-read the certificate number on the documents where extraction missed it.

42 certificates carry no document code. The CoQ cites every source by code and
date, so each of these blocks the Section 03 row it supplies - not because a
test is missing, but because one field on the page was not captured.

The code is NOT taken from the filename. There the same string is demonstrably
a human rendering rather than a transcription: it writes "051-1-LoD-26" where
the certificate prints "051-1-ГС/26", appends " MK" / " EN" to distinguish two
language variants of one DFL certificate, and gives an NGP form number in place
of a certificate number. A code is quoted verbatim on a released document, so it
is read from the page.

This is a narrow pass, not a re-extraction: page 1 only, one question, two
independent models. It writes a code only when both agree, because a WRONG code
on a CoQ is worse than a missing one - it cites a document that does not exist.
Where they differ, both readings are recorded for a person to settle, with the
filename's own rendering shown alongside as a hint.
"""
import os, re, sys, json, time, sqlite3, argparse, urllib.request, importlib.util
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location('ex', HERE + '/extract_ecoa_records.py')
EX = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(EX)

# The dataset id is a command-line default inside the extractor's main(), so it
# is not importable; it is restated here and overridable for a different corpus.
DS = os.environ.get('ECOA_DATASET_ID', 'dd3ea108a3fd11f1858cf58865604f65')

ASK = """You are reading a laboratory certificate of analysis.

Report ONLY the certificate's own document number - the number the issuing
laboratory printed to identify THIS certificate. It appears near the top, often
after Бр., Број, No., Реф., Ref., or on its own line beside the issue date.

Rules:
  * Transcribe it EXACTLY as printed, character for character, including the
    separators (/ or -) and the script. Macedonian certificates print Cyrillic
    letters: ППК, ГС, К, М. Do NOT transliterate them to Latin.
  * It is NOT the batch number, NOT the sample number, NOT an order or protocol
    number, NOT a method or standard number, NOT the accreditation number.
  * If the page shows no certificate number at all, return null.

Answer as JSON, nothing else: {"cert_code": "..."} or {"cert_code": null}
"""


def _post_openai(content, model='gpt-5'):
    body = {'model': model, 'messages': [{'role': 'user', 'content': content}]}
    # Same ladder the corpus run used: the OpenAI platform first, then the SAME
    # model through OpenRouter when its credit is exhausted. The model never
    # changes - a cheaper one was gated against ground truth and failed.
    ladder = [('https://api.openai.com/v1', os.environ.get('OPENAI_API_KEY')),
              ('https://api.openai.com/v1', os.environ.get('OPENAI_SERVICE_API_KEY')),
              ('https://openrouter.ai/api/v1',
               os.environ.get('OPEN_ROUTER_API_KEY')
               or os.environ.get('OPENROUTER_API_KEY'))]
    errs = []
    for base, key in ladder:
        if not key:
            continue
        try:
            r = urllib.request.Request(base + '/chat/completions',
                data=json.dumps(dict(body, model='openai/' + model
                                     if 'openrouter' in base else model)).encode(),
                headers={'Authorization': 'Bearer ' + key,
                         'Content-Type': 'application/json'})
            o = json.load(urllib.request.urlopen(r, timeout=300))
            return o['choices'][0]['message']['content']
        except urllib.error.HTTPError as e:
            errs.append('%s %s' % (base.split('/')[2], e.code))
            if e.code not in (401, 402, 403, 429):
                raise
        except Exception as e:
            errs.append('%s %s' % (base.split('/')[2], str(e)[:40]))
    raise RuntimeError('no usable endpoint: ' + '; '.join(errs))


def _post_gemini(img, model='gemini-3.6-flash'):
    parts = [{'text': ASK}, {'inline_data': {'mime_type': 'image/png', 'data': img}}]
    body = {'contents': [{'parts': parts}],
            'generationConfig': {'temperature': 0, 'maxOutputTokens': 4096}}
    keys = [os.environ[v] for v in ('AZ_GEMINI_API_KEY', 'BN_GEMINI_API',
                                    'BN_GOOGLE_GEMINI_API_KEY', 'EP_GEMINI_API',
                                    'UC_GEMINI_API') if os.environ.get(v)]
    last = None
    for k in keys:
        try:
            r = urllib.request.Request(
                'https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent'
                % model, data=json.dumps(body).encode(),
                headers={'x-goog-api-key': k, 'Content-Type': 'application/json'})
            o = json.load(urllib.request.urlopen(r, timeout=300))
            return o['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            last = e
    raise RuntimeError('every Gemini key failed: %s' % last)


def _code(txt):
    try:
        v = (EX.parse_json(txt) or {}).get('cert_code')
    except Exception:
        m = re.search(r'"cert_code"\s*:\s*("([^"]*)"|null)', txt or '')
        v = m.group(2) if m and m.group(2) else None
    v = (v or '').strip()
    return v or None


# --- adjudication -------------------------------------------------------------
# Three witnesses exist for a certificate number: the two model reads, and the
# digits in the controlled filename. The filename is not a transcription of the
# LETTERS - it renders Cyrillic ГС as "LoD" and Cyrillic К as Latin K - but its
# DIGITS are the ones the filer typed off the document, and they settle a
# transposition that neither model can settle alone.
#
# Two rules, both evidence-based, both refusing to guess:
#
#   HOMOGLYPH  the reads differ only by Latin/Cyrillic lookalikes. The
#              certificate is Macedonian and the suffix letter abbreviates a
#              Macedonian word - К канабиноиди, М микробиологија, ГС губиток при
#              сушење - and every Farmahem code the two-pass pipeline captured
#              WITH agreement is Cyrillic. Take the Cyrillic reading.
#   DIGITS     the reads differ in their digits and exactly one of them matches
#              the digit string in the filename. Take that one.
#
# Anything else stays for a person. A wrong code on a released document cites a
# certificate that does not exist.
# <batch>_<code>, <dd.mm.yyyy>_<lab>.pdf - the same convention the date
# recovery validated at 219/219.
NAME = re.compile(r'^(?P<rest>.+?),\s*(?P<date>\d{2}\.\d{2}\.\d{4})_(?P<lab>[^.]+)\.pdf$')

HOMOGLYPH = {'K': 'К', 'M': 'М', 'H': 'Н', 'P': 'Р', 'C': 'С', 'T': 'Т',
             'A': 'А', 'B': 'В', 'E': 'Е', 'O': 'О', 'X': 'Х'}


def _homoglyph_fold(s):
    return ''.join(HOMOGLYPH.get(ch, ch) for ch in (s or ''))


def _digits(s):
    return re.sub(r'\D', '', s or '')


def adjudicate(rec):
    """(code, basis) for a disagreement, or (None, reason) when unresolved."""
    a, b = rec.get('read_a'), rec.get('read_b')
    if a is None and b is None:
        return None, 'the page prints no certificate number'
    if a and b and _homoglyph_fold(a) == _homoglyph_fold(b):
        # Prefer whichever reading is already Cyrillic.
        cyr = b if any(ch in 'КМНРСТАВЕОХ' for ch in b) else a
        return cyr, 'homoglyph only; Macedonian certificate, Cyrillic taken'
    m = NAME.match(rec['document'])
    fd = _digits(m.group('rest')) if m else ''
    if fd:
        # The filename's leading digits are the batch prefix, so the code's
        # digits are a SUFFIX of them, not the whole string.
        hits = [x for x in (a, b) if x and _digits(x) and fd.endswith(_digits(x))]
        if len(hits) == 1:
            other = b if hits[0] is a else a
            why = ('digits match the filename; the other read does not'
                   if other else 'digits match the filename; the other read '
                                 'found no number')
            return hits[0], why
    return None, 'unresolved - both readings differ beyond a rule'


def targets(db):
    return db.execute("SELECT doc_id, document, batch, lab FROM certificate "
                      "WHERE cert_code IS NULL ORDER BY document").fetchall()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default=os.path.join(HERE, 'ecoa.sqlite'))
    ap.add_argument('--out', default=os.path.join(HERE, 'recaptured_codes.json'))
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--apply', action='store_true',
                    help='write codes where both models agree')
    ap.add_argument('--adjudicate', action='store_true',
                    help='also settle disagreements by the documented rules '
                         '(no further reading, no cost)')
    a = ap.parse_args()
    db = sqlite3.connect(a.db)
    todo = targets(db)
    if a.limit:
        todo = todo[:a.limit]
    print('%d certificate(s) with no document code\n' % len(todo))

    # Resume: a pass interrupted mid-way must not pay for what it already read.
    done = {}
    if os.path.exists(a.out):
        # A failed read is not progress: caching it would make one transient
        # error permanent. Only completed reads count as done.
        done = {r['doc_id']: r for r in json.load(open(a.out)) if 'error' not in r}
        print('%d already read; resuming\n' % len(done))

    out = list(done.values())
    for did, name, batch, lab in todo:
        if did in done:
            continue
        print('%-54s ' % name[:54], end=''); sys.stdout.flush()
        try:
            pdf = urllib.request.urlopen(urllib.request.Request(
                '%s/api/v1/datasets/%s/documents/%s' % (EX.RAG, DS, did),
                headers={'Authorization': 'Bearer ' + EX.RAGKEY}), timeout=180).read()
            img = EX.render(pdf)[0]
            with ThreadPoolExecutor(max_workers=2) as pool:
                fa = pool.submit(_post_openai, [
                    {'type': 'text', 'text': ASK},
                    {'type': 'image_url', 'image_url': {
                        'url': 'data:image/png;base64,' + img, 'detail': 'high'}}])
                fb = pool.submit(_post_gemini, img)
                ca, cb = _code(fa.result()), _code(fb.result())
        except Exception as e:
            print('ERROR %s' % str(e)[:60])
            out.append({'doc_id': did, 'document': name, 'error': str(e)[:200]})
            json.dump(out, open(a.out, 'w'), ensure_ascii=False, indent=1)
            continue
        # Both models returning null is not a failure: it is agreement that the
        # page prints no certificate number. Some documents genuinely carry
        # none - PP's own Report of Analysis is filed as NO-DOC-CODE - and that
        # is a finding for the CoQ ("issued without a document code"), not a
        # gap to keep re-reading.
        if ca is None and cb is None:
            verdict, agree = 'NO CODE ON PAGE', False
        elif ca == cb:
            verdict, agree = 'AGREE', True
        else:
            verdict, agree = 'DISAGREE', False
        print('%-22s %-22s %s' % (ca or '-', cb or '-', verdict))
        out.append({'doc_id': did, 'document': name, 'batch': batch, 'lab': lab,
                    'read_a': ca, 'read_b': cb, 'agree': agree,
                    'no_code_on_page': ca is None and cb is None})
        json.dump(out, open(a.out, 'w'), ensure_ascii=False, indent=1)

    ok = [r for r in out if r.get('agree')]
    for r in out:
        if 'read_a' in r:
            r['no_code_on_page'] = r['read_a'] is None and r['read_b'] is None
    none = [r for r in out if r.get('no_code_on_page')]
    dis = [r for r in out if 'agree' in r and not r['agree']
           and not r.get('no_code_on_page')]
    print('\n%d code(s) agreed, %d certificate(s) print no code, %d disagreed, '
          '%d errored' % (len(ok), len(none), len(dis),
                          sum(1 for r in out if 'error' in r)))
    for r in dis:
        print('   DISAGREE  %-46s A %-18s B %s'
              % (r['document'][:46], r['read_a'] or '-', r['read_b'] or '-'))
    for r in none:
        print('   NO CODE   %s' % r['document'][:60])
    if a.adjudicate:
        print('\nADJUDICATION')
        for r in dis + none:
            code, basis = adjudicate(r)
            r['adjudicated'] = code
            r['basis'] = basis
            print('   %-46s %-16s %s'
                  % (r['document'][:46], code or '(none)', basis))
        json.dump(out, open(a.out, 'w'), ensure_ascii=False, indent=1)
        settled = [r for r in dis + none if r.get('adjudicated')]
        left = [r for r in dis if not r.get('adjudicated')]
        print('\n   %d settled by rule, %d certificate(s) print no code, '
              '%d left for a person' % (len(settled), len(none), len(left)))
        ok = ok + settled

    if a.apply:
        for r in ok:
            code = r.get('adjudicated') or r['read_a']
            db.execute("UPDATE certificate SET cert_code=? WHERE doc_id=?",
                       (code, r['doc_id']))
            db.execute("UPDATE result SET cert_code=? WHERE doc_id=?",
                       (code, r['doc_id']))
        db.commit()
        print('Wrote %d code(s). Disagreements are left for a person to settle.' % len(ok))
    else:
        print('Dry run. Re-run with --apply to write the agreed codes.')


if __name__ == '__main__':
    main()
