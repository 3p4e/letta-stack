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

Anything reading batch codes out of documents — ingestion, cross-checks, the gap
analysis — must key through here rather than re-deriving the rule, so that a change
to it changes every consumer at once.
"""
import re

__all__ = ["batch_key", "spelling_variants"]

_SPLIT = re.compile(r"[/_\-–—]")


def batch_key(raw):
    """Canonical key for a batch code as written anywhere.

    >>> [batch_key(x) for x in ("GG1024_01", "GG1024-01", "GG1024/01", "GG 1024_01")]
    ['GG1024/1', 'GG1024/1', 'GG1024/1', 'GG1024/1']
    >>> batch_key("GG1024_01/01"), batch_key("GG1024")
    ('GG1024/1/1', 'GG1024')
    >>> batch_key("JD012603-02V"), batch_key("JD012603-02")
    ('JD012603/2V', 'JD012603/2')
    """
    if raw is None:
        return None
    s = str(raw).strip().upper().replace(" ", "")
    if not s:
        return None
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
