#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The lots outside every tranche — their certificates of quality and internal certificates.

    node design_handoff/toolchain/build_v40.js               # the CoQ pages, from the register
    python3 tracker/build_nontranche_bundle_2026-09-27.py    # this: select, build iCoA, print, merge

Head of QC, 27.09.2026: "the certificates of quality, initial and or retest for the batches that do not
fall in any of the tranches, as well as their connected internal certificates of analysis ... one merged
PDF file per type". And the same day, of a lot absent from the sale list: it "is not meant for sale. But
that does not mean that you should not issue any certificate".

* **Selection** — every live record of `coq_artifact_data.json` that the 18.09 grouping
  (`drive_folders_2026-09-18.tsv`) places in no tranche: the six lots that left the tranches on 18.09
  (CLE072501, OPM092501, SJ092501, JD042601, CC042601, FB042601), FB032601, GG032601, JD022601 and the
  three P160 lots. None of their certificates has been issued (not among the 46 approved scans, not
  among the 44 pages of 24.09).
* **Pages** — exactly as `tracker/build_t3_bundle_2026-09-26.py` makes them, with its own functions:
  the CoQ page `build_v40.js` writes, and the Head of QC's internal-certificate page, scoped to what its
  CoQ credits to it. What the register cannot supply prints "—" and is listed in `REGISTER_GAPS.tsv`.
* **Output** — `DELIVER_2026-09-27_NoTranche/`: the pages, and two merged PDFs, the CoQs (initial,
  then retest) and the internal certificates (initial, then retest), one bookmark per certificate.
"""
import csv, glob, importlib.util, json, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
spec = importlib.util.spec_from_file_location('t3', os.path.join(HERE, 'build_t3_bundle_2026-09-26.py'))
T3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(T3)

STAMP = '2026-09-27'
OUT = os.path.join(GAP, 'DELIVER_%s_NoTranche' % STAMP)


def main():
    import pymupdf
    reg = json.load(open(os.path.join(GAP, 'coq_artifact_data.json'), encoding='utf-8'))
    tm = T3.tranche_map()

    def tranche(c):
        for k in (c.get('pp'), c.get('cb'), (c.get('cb') or '').replace('＊', '')):
            if k and k in tm:
                return tm[k]

    recs = [c for c in reg['coqs'] if tranche(c) is None and not c.get('withdrawn')]
    series = {'Initial': sorted([c for c in recs if 'retest' not in c['t']], key=lambda c: c['regcode']),
              'Retest': sorted([c for c in recs if 'retest' in c['t']], key=lambda c: c['regcode'])}
    codes = [c['icoa_code'] for c in recs]
    if len(set(codes)) != len(codes):
        raise SystemExit('two of these records share an internal-certificate number')
    held = {c['icoa_code'] for c in reg['coqs'] if tranche(c) is not None}
    clash = sorted(set(codes) & held)
    if clash:
        raise SystemExit('internal-certificate numbers also held in a tranche: %s' % ', '.join(clash))

    coq_html = {os.path.basename(p)[:13]: p for p in glob.glob(os.path.join(T3.COQ_OUT, '**', '*.html'),
                                                               recursive=True)}
    shutil.rmtree(OUT, ignore_errors=True)
    gaps, docs, no_icoa = [], [], []
    for s, rs in series.items():
        cdir, idir = os.path.join(OUT, 'CoQ', s, 'HTML'), os.path.join(OUT, 'iCoA', s, 'HTML')
        os.makedirs(cdir), os.makedirs(idir)
        for c in rs:
            src = coq_html.get(c['regcode'])
            if not src:
                raise SystemExit('%s: build_v40.js wrote no page for it' % c['regcode'])
            scope, extra = T3.scope_of(c)
            text = open(src, encoding='utf-8').read()
            if scope and c['icoa_code'] not in text:
                raise SystemExit('%s: the CoQ page does not cite %s — rerun build_v40.js' % (c['regcode'], c['icoa_code']))
            if 'GMP Certified' in text:
                raise SystemExit('%s: the page still carries the GMP line — rerun build_v40.js' % c['regcode'])
            dst = os.path.join(cdir, os.path.basename(src))
            shutil.copy2(src, dst)
            docs.append(('CoQ %s' % s, os.path.basename(src)[:-5], dst))
            T3.coq_gaps(c, gaps)
        for c in rs:
            scope, extra = T3.scope_of(c)
            if not scope:
                cited = sorted({str(r.get('doc')) for r in c['rows'] if r['no'] in ('1', '2', '7')})
                no_icoa.append((c['regcode'], c['icoa_code'], ', '.join(cited)))
                continue
            if extra:
                gaps.append((c['regcode'], c['icoa_code'], 'rows %s credited to the internal certificate, '
                             'which has no section for them' % ', '.join(extra)))
            f = T3.fields(c, gaps, scope)
            T3.check_pair(f, open(coq_html[c['regcode']], encoding='utf-8').read())
            dst = os.path.join(idir, T3.name_of(f))
            open(dst, 'w', encoding='utf-8').write(T3.house_stack(T3.own.build(f['scope'].split(','), f)))
            docs.append(('iCoA %s' % s, T3.name_of(f)[:-5], dst))

    pdf_of = {}
    coq_css = T3.house_css([h for s_, _, h in docs if s_.startswith('CoQ')])
    for hdir in dict.fromkeys(os.path.dirname(h) for _, _, h in docs):
        pdir = os.path.join(os.path.dirname(hdir), 'PDF')
        os.makedirs(pdir, exist_ok=True)
        srcs = [h for _, _, h in docs if os.path.dirname(h) == hdir]
        css = coq_css if os.sep + 'CoQ' + os.sep in hdir else ''
        pdf_of.update(zip(srcs, T3.render(srcs, pdir, None, css, T3.layout_probe)))
    T3.assert_layout()
    for pdf in pdf_of.values():
        T3.assert_house_fonts(pdf)
    for pdf in pdf_of.values():
        d = pymupdf.open(pdf)
        d.subset_fonts()
        d.save(pdf + '.tmp', garbage=4, deflate=True, deflate_fonts=True)
        d.close()
        os.replace(pdf + '.tmp', pdf)

    made = []
    for fam, title in (('CoQ', 'certificates of quality'), ('iCoA', 'internal certificates of analysis')):
        m, toc = pymupdf.open(), []
        for s in ('Initial', 'Retest'):
            sec = [(l, h) for sec_, l, h in docs if sec_ == '%s %s' % (fam, s)]
            if not sec:
                continue
            toc.append([1, '%s %s' % (fam, s), m.page_count + 1])
            for l, h in sec:
                toc.append([2, l, m.page_count + 1])
                d = pymupdf.open(pdf_of[h])
                m.insert_pdf(d)
                d.close()
        m.set_toc(toc)
        m.set_metadata({'title': 'Purely Plant — lots outside every tranche — %s, initial and retest' % title,
                        'producer': 'Purely Plant Quality Desk'})
        dest = os.path.join(OUT, 'NoTranche_%s_Initial_Retest_%s.pdf' % (fam, STAMP))
        m.save(dest, garbage=4, deflate=True)
        made.append((os.path.relpath(dest, GAP), m.page_count, os.path.getsize(dest) / 1048576.0))
        m.close()

    for name, head, rows in (('NO_INTERNAL_CERTIFICATE.tsv', ['coq', 'internal certificate number not issued', 'rows 1, 2, 7 cite'], no_icoa),
                             ('REGISTER_GAPS.tsv', ['coq', 'icoa', 'field the register does not hold — printed as "—"'], gaps),
                             ('CONTENTS.tsv', ['section', 'document'], [(s, l) for s, l, _ in docs])):
        with open(os.path.join(OUT, name), 'w', encoding='utf-8', newline='') as fh:
            w = csv.writer(fh, delimiter='\t')
            w.writerow(head)
            w.writerows(rows)

    n = {k: sum(1 for s, _, _ in docs if s == k) for k in dict.fromkeys(s for s, _, _ in docs)}
    print('documents: %s' % ', '.join('%s %d' % kv for kv in n.items()))
    for p, n_, mib in made:
        print('merged PDF: %s — %d pages (%.1f MiB)' % (p, n_, mib))
    print('no internal certificate: %s' % (', '.join('%s (%s)' % (a, b) for a, _, b in no_icoa) or 'none'))
    print('register gaps printed as "—": %d' % len(gaps))
    for g in gaps:
        print('   %s  %s  %s' % g)
    return 0


if __name__ == '__main__':
    sys.exit(main())
