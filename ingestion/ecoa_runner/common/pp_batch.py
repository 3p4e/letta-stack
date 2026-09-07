"""Canonical batch form per the Head of QC determination of 23.08.2026
(PP-QC-eCoA Reconciliation and Findings Log, section 2.1).

    BASE         = 1-4 letters + 4-8 digits                 GG1024
    BATCH SUFFIX = FIRST separator (- _ / space) + digits    written "_"
    SUB-LOT      = a SECOND separator + digits               written "/"

    GG1024/01, GG1024-01, GG1024 01, GG1024_01   ->  GG1024_01   (one batch)
    GG1024_01/01                                 ->  GG1024_01/01 (distinct sub-lot)

Leading zeros are RETAINED - the ruling writes GG1024_01, not GG1024_1.

Two markers carry identity and must survive:
  * a trailing V marks a verification sample   JD012603_02V != JD012603_02
  * a trailing asterisk is a real batch indicator, ruled 23.08.2026:
    JD112501 and JD112501* are two different batches and are never merged.

This differs from ingestion/common/batch_id.py, which writes every separator as
"/" and strips leading zeros. The two agree on which codes are the same batch;
they disagree on how to write it. Use batch_key() to GROUP, this to DISPLAY.
"""
import re

# Batch codes are ALWAYS Latin (Head of QC). A Cyrillic letter inside one is a
# transcription artefact - certificates print 197-1-К/26 with a Cyrillic К - so
# fold the visual look-alikes to Latin and REJECT anything containing a Cyrillic
# letter that has no Latin twin (ППК25050 is a control-book number, not a batch).
_HOMOGLYPH = {
    'А':'A','В':'B','С':'C','Е':'E','Н':'H','К':'K','Ќ':'K','М':'M','О':'O',
    'Р':'P','Т':'T','Х':'X','У':'Y','І':'I','Ј':'J','Ѕ':'S','Ԛ':'Q','Ѵ':'V',
}
# Farmahem's loss-on-drying suffix ГС transliterates to LoD/GS, not the visual GC.
# Special-cased BEFORE the general fold, per the ruling of 23.08.2026.
_SPECIAL = (('ГС', 'GS'),)
_CYRILLIC = re.compile(r'[\u0400-\u04FF]')


def _to_latin(s):
    """Fold Cyrillic look-alikes to Latin; return None if any remain."""
    for src, dst in _SPECIAL:
        s = s.replace(src, dst)
    s = ''.join(_HOMOGLYPH.get(ch, ch) for ch in s)
    return None if _CYRILLIC.search(s) else s


# A P-number is P + six digits. IJZ certificates print the second character as a
# letter O ("Серија: PO60052" on 552/1083/26, 01.09.2026) - the digit zero in the
# laboratory's typeface. Fold it before matching: 'PO' + five digits is a P-number.
_P_LETTER_O = re.compile(r'\bPO(\d{5})(?=\D|$)')
_SEP = r'[-_/\s]'
_CODE = re.compile(
    r'([A-Z]{1,4})\s*(\d{4,8})'              # base - Latin only
    r'(?:' + _SEP + r'*(\d{1,3}))?'          # batch suffix
    r'(?:' + _SEP + r'*(\d{1,3}))?'          # sub-lot
    r'\s*(V)?\s*(\*|＊)?',               # verification / asterisk (incl. fullwidth)
    re.IGNORECASE)


def pp_batch(raw):
    """Canonical printed form, or None if no batch code is present."""
    if not raw:
        return None
    txt = _to_latin(str(raw).upper().replace('＊', '*'))
    if txt is None:
        return None          # contains a Cyrillic letter with no Latin equivalent
    txt = _P_LETTER_O.sub(r'P0\1', txt)
    m = _CODE.search(txt)
    if not m:
        return None
    alpha, digits, suffix, sublot, ver, star = m.groups()
    out = '%s%s' % (alpha, digits)
    if suffix:
        out += '_%s' % suffix
    if sublot:
        out += '/%s' % sublot
    if ver:
        out += 'V'
    if star:
        out += '*'
    return out
