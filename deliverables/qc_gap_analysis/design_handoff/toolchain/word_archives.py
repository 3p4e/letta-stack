#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The Word copies alone, in groups small enough to send.

    python3 design_handoff/toolchain/word_archives.py [--limit-mib 29] [--out dist/word]

`package_v40.py` builds the four archives the desk delivers, and each of them carries its
certificates in all three formats — PDF, HTML and Word. That is the package, and it stays the
package. But a chat attachment is capped at 30 MiB and every Word file is about a megabyte (the
export places the vector page as a 300 dpi image), so the Tranche 2 archive alone is 89 MiB and
cannot be sent that way.

This writes the Word copies on their own, grouped **exactly as the tranche archives group
them** — the membership is read back out of those archives rather than re-derived, so a
certificate can never land in a different tranche here than it does there. A group that would
still exceed the limit is split into numbered parts, and each part is a whole archive that opens
on its own: nothing is spanned, nothing needs reassembling.

The output is not committed. It duplicates content the four archives already carry, and 160 MiB
of that in the history would be paid for on every clone; this script is the cheaper record.
"""
import argparse
import os
import re
import shutil
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
HANDOFF = os.path.dirname(HERE)
DIST = os.path.join(HANDOFF, "dist")
DOCX = os.path.join(HANDOFF, "docx")
DATE = "2026-09-17"
# the archive each tranche's certificates are packaged in, and the label for this one
SOURCES = (("PP_CoQ_Tranche_1_%s.zip" % DATE, "Tranche_1"),
           ("PP_CoQ_Tranche_2_%s.zip" % DATE, "Tranche_2"),
           ("PP_CoQ_Tranche_3_%s.zip" % DATE, "Tranche_3"),
           ("PP_CoQ_Package_%s.zip" % DATE, "No_tranche"))


def membership(dist=DIST):
    """(label, round) -> [Word file name], read back out of the packaged archives.

    Reading it back is the point: the grouping cannot drift from the package's own.
    """
    out = {}
    for name, label in SOURCES:
        path = os.path.join(dist, name)
        if not os.path.exists(path):
            continue
        with zipfile.ZipFile(path) as zf:
            for n in zf.namelist():
                if n.endswith(".docx"):
                    rnd = "Retest" if "/Retest/" in n else "Release"
                    out.setdefault((label, rnd), []).append(os.path.basename(n))
    return {k: sorted(v) for k, v in out.items()}


def on_disk(root=DOCX):
    """Word file name -> its path in the build."""
    return {f: os.path.join(dp, f)
            for dp, _, fs in os.walk(root) for f in fs if f.endswith(".docx")}


def parts(files, sizes, limit):
    """Split a group into runs that each fit under the limit, in certificate order.

    >>> parts(["a", "b", "c"], {"a": 4, "b": 4, "c": 4}, 9)
    [['a', 'b'], ['c']]
    >>> parts(["a"], {"a": 99}, 9)
    [['a']]
    """
    out, cur, size = [], [], 0
    for f in files:
        if cur and size + sizes[f] > limit:
            out.append(cur)
            cur, size = [], 0
        cur.append(f)
        size += sizes[f]
    if cur:
        out.append(cur)
    return out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit-mib", type=float, default=29.0)
    ap.add_argument("--out", default=os.path.join(DIST, "word"))
    ap.add_argument("--dist", default=DIST)
    a = ap.parse_args(argv[1:])
    limit = int(a.limit_mib * 1024 * 1024)

    groups, src = membership(a.dist), on_disk()
    missing = sorted({f for v in groups.values() for f in v} - set(src))
    if missing:
        for f in missing[:8]:
            print("   no Word copy on disk for %s" % f)
        print("refusing to write a partial set — run export_docx_v40.py first")
        return 1

    shutil.rmtree(a.out, ignore_errors=True)
    os.makedirs(a.out)
    sizes = {f: os.path.getsize(p) for f, p in src.items()}
    total = 0
    for (label, rnd) in sorted(groups):
        runs = parts(groups[(label, rnd)], sizes, limit)
        for i, run in enumerate(runs, 1):
            tail = "" if len(runs) == 1 else "_part_%d_of_%d" % (i, len(runs))
            name = "PP_CoQ_Word_%s_%s%s_%s.zip" % (label, rnd, tail, DATE)
            path = os.path.join(a.out, name)
            with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
                for f in run:
                    zf.write(src[f], "%s/%s" % (os.path.splitext(name)[0], f))
            total += len(run)
            print("%-56s %3d docs  %5.1f MiB"
                  % (name, len(run), os.path.getsize(path) / 1048576))
    print("Word documents packaged: %d   (the build holds %d)" % (total, len(src)))
    return 0 if total == len(src) else 1


if __name__ == "__main__":
    import doctest
    import sys
    f, t = doctest.testmod()
    print("%d/%d doctests passed" % (t - f, t))
    raise SystemExit(main(sys.argv) if not f else 1)
