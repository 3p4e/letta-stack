#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Print the owner-format internal certificates and merge them per delivery tranche.

    python3 icoa_handoff/v3/print_owner_format.py
    python3 icoa_handoff/v3/print_owner_format.py --src DIR --out DIR

Pages render through `live_instrument/print_coq_pdfs.render`, the same printer both certificate
fleets already use, so the export settings are the package's own — A4, zero margins, background
graphics, Google blocked and the faces inlined.

Each page is merged into its tranche the moment it is rendered and its own PDF is then deleted.
The container runs with very little free disk, and keeping 44 page PDFs alongside two merged ones
is what exhausted it before; this never holds more than one.

The tranche is the Drive-folder grouping the Head of QC set on 18.09.2026, read through
`merge_tranche_retests.tranche_lots` so there is one definition of it and not two.
"""
import argparse
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(os.path.dirname(HERE))
ROOT = os.path.dirname(os.path.dirname(GAP))
sys.path.insert(0, os.path.join(GAP, 'live_instrument'))
sys.path.insert(0, os.path.join(ROOT, 'ingestion', 'coa_track', 'letta-imb-coas'))
sys.path.insert(0, HERE)
from print_coq_pdfs import render                                    # noqa: E402
from merge_tranche_retests import tranche_lots, lot_of, seq, label   # noqa: E402

TRANCHES = (('T1', 'Tranche_1'), ('T2', 'Tranche_2'))


def main(argv):
    import pymupdf
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', default=os.path.join(GAP, 'DELIVER_2026-09-24', 'iCoA_T1_T2_owner_format'))
    ap.add_argument('--out', default=os.path.join(GAP, 'DELIVER_2026-09-24'))
    ap.add_argument('--tmp', default=os.path.join(HERE, 'pdf', '_owner_pages'))
    a = ap.parse_args(argv[1:])

    lots = tranche_lots()
    srcs = sorted(glob.glob(os.path.join(a.src, '*.html')), key=lambda p: seq(os.path.basename(p)))
    if not srcs:
        raise SystemExit('no certificates in %s' % a.src)
    os.makedirs(a.tmp, exist_ok=True)

    unplaced = [os.path.basename(p) for p in srcs
                if not any(lot_of(os.path.basename(p)) in lots[t] for t, _ in TRANCHES)]
    if unplaced:
        raise SystemExit('no tranche holds these lots, refusing to print a partial set:\n  %s'
                         % '\n  '.join(unplaced))

    made = []
    for t, name in TRANCHES:
        sel = [p for p in srcs if lot_of(os.path.basename(p)) in lots[t]]
        out, toc = pymupdf.open(), []
        for src in sel:
            page = render([src], a.tmp)[0]
            d = pymupdf.open(page)
            out.insert_pdf(d)
            toc.append([1, label(os.path.basename(src)), out.page_count])
            d.close()
            os.remove(page)                      # one page PDF on disk at a time, never 44
        dest = os.path.join(a.out, 'iCoA_%s_retest_owner_format_2026-09-24.pdf' % t)
        out.set_toc(toc)
        out.set_metadata({'title': 'Purely Plant — Internal Certificates of Analysis — %s retests'
                                   % name.replace('_', ' '),
                          'producer': 'Purely Plant Quality Desk'})
        out.save(dest, garbage=4, deflate=True)
        out.close()
        made.append((name, len(toc), dest))
        print('  %-10s %2d certificates  %s (%.1f MiB)'
              % (name, len(toc), os.path.basename(dest), os.path.getsize(dest) / 1048576.0))
    os.rmdir(a.tmp) if not os.listdir(a.tmp) else None

    if sum(n for _, n, _ in made) != len(srcs):
        raise SystemExit('printed %d pages from %d certificates — refusing a short set'
                         % (sum(n for _, n, _ in made), len(srcs)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
