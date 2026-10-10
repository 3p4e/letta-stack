#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Canonical batch identity for Purely Plant production batches.

One batch reaches us spelled several ways. The register, the certificate itself,
the scan filename and the folder name frequently disagree about punctuation, and
the disagreement is never meaningful. Two rules from the owner govern it:

  1. **The separator before a sub-lot index carries no meaning.** `GG1024_01`,
     `GG1024-01`, `GG1024/01` and `GG 1024_01` are one batch. A document that
     records `GG1024_01` as `GG1024/01` has recorded it wrongly, not differently.
     Leading zeros on the index are equally insignificant.

  2. **A sub-lot index is part of a batch code, so a batch carrying one can carry
     another.** `GG1024_01/01` is sub-lot 01 of batch `GG1024_01` — a distinct
     record from its parent, and `GG1024_01/02` may exist alongside it.

The two rules only look like they conflict. At the first level every separator
means the same thing, so a genuine second-level sub-lot must be written as two
segments; a single segment is never ambiguous. That is why the key normalises
*every* segment rather than stripping one and stopping — stripping one level would
key `GG1024_01/01` as `GG1024_01/1` while its parent keys as `GG1024/1`, so parent
and child would no longer nest.

A trailing V marks a verification sample and belongs to the identity: `JD012603/2V`
is a different record from `JD012603/2`.

  3. **A trailing asterisk is a mark on the lot, and it belongs to the identity —
     but its GLYPH does not.** The company writes `GG012601*`, and the Head of QC's
     own batch list writes it that way too, so `GG012601*` is not `GG012601` and the
     key keeps the mark. What varies without meaning is which star character was
     typed: a vision model reading a Cyrillic page returns the fullwidth `＊`
     (U+FF0A) where the paper prints `*`, the same homoglyph reflex that returns
     `ТНС` for `THC`. Nine records in the corpus carry the fullwidth form. Every
     star glyph therefore folds to ASCII `*` here, so that the desk's `SCR012601＊`
     and the batch list's `SCR012601*` are one batch — before this, they were two,
     and 90 kg of delivered Scrambler sat in the tracker under no name at all.

     Whether a starred lot and its unstarred namesake are the same batch is NOT a
     question this function may answer: it is a fact about the floor, and it is
     recorded in ingestion/ecoa_runner/identity_decisions.tsv when a person rules.

     A person has ruled. Head of QC, 16.09.2026, on JD112501 / JD112501*: "if both THC
     results are assigned with the same P number production batch, that means it is the
     same batch, but two samples have been sent for the parameter" — a starred
     cultivation batch is a second SAMPLE of one packaged lot, not a second lot. The
     ruling is data, not code: identity_decisions.tsv rows with field `batch_alias`
     name each starred spelling and the lot it is a sample of, and batch_key applies
     them after normalising, so `JD112501*` and `JD112501` key alike — and so do
     `GG012601*`, `JD012601*`, `SCR012601*` and `FB012602*`, each the only spelling its
     P lot has on the batch list, applied by the desk as a consequence of the same
     ruling (their rows say so, and OI-28 asks for the word that confirms it). A star on
     a spelling NOT in that file still keeps the mark: the rule has not changed, the
     rulings have been recorded.

Anything reading batch codes out of documents — ingestion, cross-checks, the gap
analysis — must key through here rather than re-deriving the rule, so that a change
to it changes every consumer at once.
"""
import csv
import os
import re

__all__ = ["batch_key", "spelling_variants"]

_SPLIT = re.compile(r"[/_\-–—]")
# Star homoglyphs. The paper prints ASCII '*'; readers return the fullwidth, the
# heavy asterisk or the low asterisk depending on the surrounding script.
_STARS = "＊✱﹡∗*"
# A P-number is P + six digits; IJZ certificates print its zero as a letter O
# ("PO60052" on 552/1083/26). Fold it so both spellings key alike.
_P_LETTER_O = re.compile(r"^PO(\d{5})(?=\D|$)")


def batch_key(raw):
    """Canonical key for a batch code as written anywhere.

    >>> [batch_key(x) for x in ("GG1024_01", "GG1024-01", "GG1024/01", "GG 1024_01")]
    ['GG1024/1', 'GG1024/1', 'GG1024/1', 'GG1024/1']
    >>> batch_key("GG1024_01/01"), batch_key("GG1024")
    ('GG1024/1/1', 'GG1024')
    >>> batch_key("JD012603-02V"), batch_key("JD012603-02")
    ('JD012603/2V', 'JD012603/2')
    >>> batch_key("PO60052")          # letter O printed for the zero of a P-number
    'P060052'
    >>> batch_key("XX000001＊") == batch_key("XX000001*")     # fullwidth star folded
    True
    >>> batch_key("XX000001*") == batch_key("XX000001")       # the mark itself is kept …
    False
    >>> batch_key("SCR012601*") == batch_key("SCR012601")     # … unless a person has ruled
    True
    >>> batch_key("JD112501＊")                                # (identity_decisions.tsv, batch_alias)
    'JD112501'
    """
    k = _raw_key(raw)
    if k is None:
        return None
    return _aliases().get(k, k)


_DECISIONS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ecoa_runner",
                          "identity_decisions.tsv")
_ALIASES = None


def _aliases():
    """The rulings: a starred spelling -> the lot it is a sample of, keyed both ways through
    _raw_key so that any star glyph and any separator spelling reaches the same ruling."""
    global _ALIASES
    if _ALIASES is None:
        _ALIASES = {}
        try:
            with open(_DECISIONS, encoding="utf-8") as fh:
                for row in csv.DictReader(fh, delimiter="\t"):
                    if (row.get("field") or "").strip() == "batch_alias":
                        _ALIASES[_raw_key(row["was"])] = _raw_key(row["confirmed_value"])
        except FileNotFoundError:
            pass
    return _ALIASES


def _raw_key(raw):
    """batch_key before the rulings: the spelling rules alone."""
    if raw is None:
        return None
    s = str(raw).strip().upper().replace(" ", "")
    if not s:
        return None
    for _st in _STARS:
        s = s.replace(_st, "*")
    s = _P_LETTER_O.sub(r"P0\1", s)
    suffix = ""
    if s.endswith("V"):
        s, suffix = s[:-1], "V"
    head, *tail = _SPLIT.split(s)
    seg = [t.lstrip("0") or "0" if t.isdigit() else t for t in tail]
    return "/".join([head] + seg) + suffix


def spelling_variants(codes):
    """Group observed spellings by the batch they name.

    Returns {key: sorted set of distinct spellings seen}. A key with more than one
    spelling is a batch that documents record inconsistently — which is not an
    error in itself, but is where a filename-keyed pipeline silently splits one
    batch into several.
    """
    out = {}
    for c in codes:
        k = batch_key(c)
        if k:
            out.setdefault(k, set()).add(str(c).strip())
    return {k: sorted(v) for k, v in out.items()}


if __name__ == "__main__":
    import doctest
    fails, ran = doctest.testmod()
    print(f"{ran - fails}/{ran} doctests passed")
    raise SystemExit(1 if fails else 0)
