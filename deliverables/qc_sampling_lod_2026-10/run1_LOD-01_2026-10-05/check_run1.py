#!/usr/bin/env python3
"""Run 1 of LOD-01 (05.10.2026), recalculated from the laboratory's workbook — for information only.

    python3 check_run1.py        # writes RUN1_CHECK.tsv next to this file

Run 1 is invalidated by DEV-01 (m_B and the portion weighed on the precision balance, d = 1 mg) and is
not reported; LOD-01R gives the results. This recalculates every row from the raw weighings in
`T1_and_T2_LOD_Analysis.xlsx` (m_B, m0, G2 on each balance), not from the workbook's formulas, and checks
the workbook's own LoD against it.

* LoD % = (G1 - G2) / m0 x 100, G1 = m_B + m0 (a02.2). The result pair is G1 and G2 on the precision
  balance (DEV-01, section C); the AUW220D G2 gives the two-balance comparison DEV-01 section D asks for.
* Ph. Eur. General Notices: the quantity actually taken may deviate by not more than 10 % from the
  1.000 g stated, so 0.900-1.100 g.
"""
import os
import statistics as st
from decimal import Decimal as D

import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'T1_and_T2_LOD_Analysis.xlsx')
OUT = os.path.join(HERE, 'RUN1_CHECK.tsv')
P3, A4 = 'T1&T2_G2=3dec. ', 'T1&T2_G2=4dec.'      # sheet names as in the workbook
Q, S, W, G = 17, 19, 23, 7                          # m_B, m0 (net), G2, %MCDO (= LoD %)


def main():
    v = openpyxl.load_workbook(SRC, data_only=True)
    a, b = v[P3], v[A4]
    rows = []
    for r in range(5, 51):
        mb, m0, g2p = (D(str(a.cell(r, c).value)) for c in (Q, S, W))
        assert (mb, m0) == (D(str(b.cell(r, Q).value)), D(str(b.cell(r, S).value))), 'row %d: m_B/m0 differ' % r
        g2a = D(str(b.cell(r, W).value))
        g1 = mb + m0
        lp, lx = (g1 - g2p) / m0 * 100, (g1 - g2a) / m0 * 100
        assert abs(float(lp) - a.cell(r, G).value) < 1e-9 and abs(float(lx) - b.cell(r, G).value) < 1e-9, r
        note = []
        if not D('0.900') <= m0 <= D('1.100'):
            note.append('m0 outside 0.900-1.100 g')
        if m0.as_tuple().exponent < -3:
            note.append('m0 has 4 decimals - not a precision-balance reading')
        rows.append([str(r - 4), a.cell(r, 5).value, str(mb), str(m0), str(g1), str(g2p), str(g2a),
                     '%.2f' % lp, '%.2f' % lx, '%+.2f' % ((g2a - g2p) * 1000), '; '.join(note)])
    lod = [float(x[7]) for x in rows]
    dg = [float(x[9]) for x in rows]
    with open(OUT, 'w', encoding='utf-8') as fh:
        fh.write('\t'.join(['no', 'sample_id', 'm_B_g', 'm0_g', 'G1_g', 'G2_precision_g', 'G2_AUW220D_g',
                            'LoD_pct_precision_pair', 'LoD_pct_G2_on_AUW220D', 'G2_AUW_minus_precision_mg',
                            'note']) + '\n')
        for x in rows:
            fh.write('\t'.join(x) + '\n')
        fh.write('# run 1 is invalidated (DEV-01) and not reported; LOD-01R gives the results\n')
        fh.write('# LoD, precision pair, n=%d: %.2f-%.2f %%, mean %.2f %%; none above 11.7 %%\n'
                 % (len(lod), min(lod), max(lod), st.mean(lod)))
        fh.write('# G2_AUW - G2_precision, n=%d: mean %+.2f mg, SD %.2f mg, range %+.2f to %+.2f mg (DEV-01 section D)\n'
                 % (len(dg), st.mean(dg), st.stdev(dg), min(dg), max(dg)))
    print(open(OUT, encoding='utf-8').read().split('\n# ', 1)[1])


if __name__ == '__main__':
    main()
