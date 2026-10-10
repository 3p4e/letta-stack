"""Post-ingest quality guards for eCOA_DB.

RAGFlow reports run=DONE and chunk_count>0 for a document whose text the vision
model invented. On P050192_NGP-QCG-SOP-024 F3 it produced 87 characters of
Sakha-alphabet Cyrillic - letters that do not exist in Macedonian - and marked it
successful. Status flags cannot be trusted; the text has to be inspected.
"""
import re, unicodedata

# Macedonian Cyrillic alphabet. Anything outside this (plus Russian letters that
# appear in practice) is a sign the model invented text rather than read it.
MK = set('абвгдѓежзѕијклљмнњопрстќуфхцчџш')
RU_TOLERATED = set('ыэёъьщйю')          # seen in scanned Russian-era boilerplate
FOREIGN_FLAG = set('үһҥөқғұїєѣіѵ')      # Turkic / archaic - never Macedonian

MIN_CHARS = 300          # every genuine certificate in the pilot gave 1000-4400
MIN_ALNUM_RATIO = 0.55   # mojibake is punctuation- and capital-heavy


def check(text, name=''):
    """Return (ok, [reasons]). Cheap, deterministic, no model calls."""
    problems = []
    t = (text or '').strip()

    if len(t) < MIN_CHARS:
        problems.append('only %d chars (expected >=%d) - probable failed or hallucinated parse'
                        % (len(t), MIN_CHARS))

    letters = [c for c in t.lower() if unicodedata.category(c).startswith('L')]
    if letters:
        foreign = [c for c in letters if c in FOREIGN_FLAG]
        if foreign:
            problems.append('contains %d non-Macedonian Cyrillic letters (%s) - fabricated text'
                            % (len(foreign), ''.join(sorted(set(foreign)))[:10]))

    # Mojibake signature. Cyrillic decoded as Latin lookalikes collapses word
    # boundaries, producing very long mixed-case/digit tokens such as
    # "J3YHHCTHTYT3AJABHO3IPABJEHAPCMAKEIOHMJA". A capital-heavy heading is NOT a
    # signature - genuine English certificates (PP, DFL) are full of them, and an
    # earlier version of this check flagged both as garbage.
    monsters = [w for w in re.findall(r'[A-Za-z0-9]{22,}', t)
                if re.search(r'[A-Z]', w) and re.search(r'[a-z]', w)]
    if len(monsters) >= 3:
        problems.append('%d run-together tokens (e.g. %r) - looks like mojibake OCR'
                        % (len(monsters), monsters[0][:32]))

    if t:
        alnum = sum(c.isalnum() or c.isspace() for c in t) / len(t)
        if alnum < MIN_ALNUM_RATIO:
            problems.append('only %.0f%% alphanumeric - garbled' % (alnum * 100))

    return (not problems), problems


def summarise(text):
    t = text or ''
    return {'chars': len(t),
            'cyrillic': len(re.findall(r'[Ѐ-ӿ]', t)),
            'latin': len(re.findall(r'[A-Za-z]', t))}
