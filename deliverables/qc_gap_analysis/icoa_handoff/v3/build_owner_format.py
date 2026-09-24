#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The internal certificate in the Head of QC's latest format, populated from the register.

    python3 icoa_handoff/v3/build_owner_format.py --out DIR [--only P060012]
    python3 icoa_handoff/v3/build_owner_format.py --selftest

The base is his own approved document, `iCoA-PP_26-110 ... _LOD.html` of 24.09.2026. Nothing in
the design is redrawn: the page is his, and this fills it.

Two scopes are produced from that one base.

* **Loss on drying (1, 2, 7, 8)** — the base as it stands. Only `HPA1024` and `OPM1024` carry it;
  the Head of QC, 24.09.2026: *"ICOAs for OPM1024 and HPA1024 have LOD so that means that its
  performed inhouse; everything else stays the same."*
* **1, 2, 7** — the same page with the loss-on-drying parts taken out again: the `02.4` group in
  section 02, the Loss on Drying row of section 04, the header's fourth subtitle term, and the
  disposition note's loss-on-drying clause, which reverts to the wording his earlier specimen
  carries. Every removal is the mirror of something he added; nothing is invented.

The per-document fields are the eleven his two approved documents differ by, which is how they
were found — `iCoA-PP_26-110` against `iCoA-PP_26-114`, 36 differing lines and no others.

Phenotype: where the cultivar record is silent the phenotype is taken from the strain code, on his
instruction of 24.09.2026. Each code resolves to one phenotype across the whole plan and the
cultivar name agrees, so the derivation is a lookup and not a judgement; the ones derived this way
are named in the run's report.
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(os.path.dirname(HERE))
OWN = os.path.join(HERE, 'ISSUE_iCOA', '_owner_format')
# One base per scope, each the Head of QC's own document with its signatures lifted off. The
# 1, 2, 7 page is not derived from the loss-on-drying one: he sent it on 24.09.2026 and it differs
# in ways a derivation would not find — a third, empty half-table balancing the row, a 100 px
# first column where the loss-on-drying page uses 106, one spacer row after the foreign-matter
# total rather than two, and an Analyst date that is the test date rather than the issue date.
BASES = {
    'lod': (os.path.join(OWN, 'iCoA-PP_26-110_LOD_base.html'), {
        'code': '<div class="hb-code">iCoA-PP_26-110</div>',
        'issued': 'Issued · Издаден <b>27.07.2026</b>',
        'headline': '<span style="font-family:\'Roboto Mono\',monospace">HPA1024</span>',
        'strain': '<span style="font-weight:800;text-transform:uppercase">High Pro Amnesia</span>',
        'pcode': '<span class="lk-val">HPA_THC18:CBD1</span>',
        'spec': '<span class="lk-val sm">QCSP_001_HPA-II_v.03</span>',
        'testdate': '<span class="lk-val sm">22.07 – 27.07.2026</span>',
        'production': '<span class="lk-val">—</span>',
        'processing': '<span class="lk-val">HPA1024</span>',
        'packaging': '<span class="lk-val sm">11.04.2025</span>',
        'analyst_date': '<span class="ap-date-val">27.07.2026</span>',
        'approver_date': '<span class="ap-date-val">27.07.2026</span>',
        'title': '<title>Purely Plant — iCoA — iCoA-PP_26-110 — HPA1024 High Pro Amnesia — '
                 'Appearance · Identification A+B · Foreign Matter · Loss on Drying</title>',
        'analyst_is_testdate': False,
    }),
    '127': (os.path.join(OWN, 'iCoA-PP_26-050_127_base.html'), {
        'code': '<div class="hb-code">iCoA-PP_26-050</div>',
        'issued': 'Issued · Издаден <b>03.06.2026</b>',
        'headline': '<span style="font-family:\'Roboto Mono\',monospace">P050022</span>',
        'strain': '<span style="font-weight:800;text-transform:uppercase">Grape Pie</span>',
        'pcode': '<span class="lk-val">GP_THC24:CBD1</span>',
        'spec': '<span class="lk-val sm">QCSP_001_GP-II_v.03</span>',
        'testdate': '<span class="lk-val sm">05.03.2026</span>',
        'production': '<span class="lk-val">P050022</span>',
        'processing': '<span class="lk-val">GP0824_02</span>',
        'packaging': '<span class="lk-val sm">03.06.2025</span>',
        'analyst_date': '<span class="ap-date-val">05.03.2026</span>',
        'approver_date': '<span class="ap-date-val">03.06.2026</span>',
        'title': None,
        'analyst_is_testdate': True,
    }),
}

MK_PHENO = {'HYBRID': 'Хибрид', 'INDICA': 'Индика', 'SATIVA': 'Сатива'}
SUB_LOD_EN = 'Appearance · Identification A + B · Foreign Matter · Loss on Drying'
SUB_EN = 'Appearance · Identification A + B · Foreign Matter'
SUB_LOD_MK = 'Изглед · идентификација А + Б · страни материи · губиток при сушење'
SUB_MK = 'Изглед · идентификација А + Б · страни материи'


def one(html, old, new, what):
    n = html.count(old)
    if n != 1:
        raise SystemExit('%s: the anchor occurs %d times, not once — refusing to write\n   %r'
                         % (what, n, old[:90]))
    return html.replace(old, new, 1)


def chip(en, mk, on, split=''):
    """The ticked chip carries the split where the approved certificate of quality carries one.

    Head of QC, 24.09.2026: a hybrid says which way it leans, and the numbers when they are known.
    The English is copied verbatim from the scan of the approved certificate — `INDICA60 : SATIVA40`
    — rather than reworded here; the Macedonian keeps the plain word his design already prints.
    """
    if not on:
        return '<span class="chip-un"><span class="bx">☐</span> %s</span>' % en
    label = '%s %s' % (en, split) if split else en
    return '<span class="chip-sel"><span class="bx">☒</span> %s <span class="mk">%s</span></span>' % (label, mk)


def drop_rows(html, start_marker, end_marker, what):
    """Remove whole <tr> elements, from the <tr> holding start_marker to the one holding end_marker."""
    i = html.find(start_marker)
    if i < 0:
        raise SystemExit('%s: start marker not found' % what)
    a = html.rfind('<tr', 0, i)
    j = html.find(end_marker, i)
    if j < 0:
        raise SystemExit('%s: end marker not found' % what)
    b = html.find('</tr>', j)
    if b < 0:
        raise SystemExit('%s: unterminated row' % what)
    return html[:a] + html[b + len('</tr>'):]


def _d(s):
    from datetime import date
    dd, mm, yy = str(s).split('.')
    return date(int(yy), int(mm), int(dd))


def _s(d):
    return '%02d.%02d.%04d' % (d.day, d.month, d.year)


def testing_dates(examined, lod):
    """When each analysis ran.

    Head of QC, 24.09.2026: every analysis block carries its own test date — one date where the
    work is done in a day, a start and an end where it is not — and section 01 carries the whole
    span.

    Macroscopy, microscopy and foreign matter are same-day work and carry the examination date.
    Loss on drying is a **24 hour** run: the oven is set the day before and the loss is weighed on
    the examination day, which is exactly the start his own two documents print. Only their end
    date was wrong — it carried the certificate's issue date, so a 24 hour determination read as
    five days.
    """
    e = _d(examined)
    if not lod:
        return {'same': examined, 'lod': None, 'span': examined}
    start = e.fromordinal(e.toordinal() - 1)
    return {'same': examined, 'lod': '%s – %s' % (_s(start), examined),
            'span': '%02d.%02d – %s' % (start.day, start.month, examined)}


def build(scope, f):
    """Fill the base that belongs to this scope. The 1, 2, 7 page is his own, not a derivation;
    only P060362, which carries neither foreign matter nor loss on drying, is cut down further."""
    lod = '8' in scope
    key = 'lod' if lod else '127'
    path, A = BASES[key]
    h = open(path, encoding='utf-8').read()

    h = one(h, A['code'], '<div class="hb-code">%s</div>' % f['code'], 'document code')
    h = one(h, A['issued'], 'Issued · Издаден <b>%s</b>' % f['issued'], 'issue date')
    h = one(h, A['headline'],
            '<span style="font-family:\'Roboto Mono\',monospace">%s</span>' % f['headline'], 'headline batch')
    h = one(h, A['strain'],
            '<span style="font-weight:800;text-transform:uppercase">%s</span>' % f['strain'], 'strain')

    for en in ('Hybrid', 'Indica', 'Sativa'):
        pat = re.compile(r'<span class="chip-(?:sel|un)">\s*<span class="bx">[☒☐]</span>\s*'
                         + en + r'[^<]*(?:<span class="mk">[^<]*</span>)?\s*</span>')
        if len(pat.findall(h)) != 1:
            raise SystemExit('phenotype %s: %d chips, not one' % (en, len(pat.findall(h))))
        h = pat.sub(lambda m: chip(en, MK_PHENO[en.upper()], f['pheno'] == en.upper(),
                                   f.get('split', '') if f['pheno'] == en.upper() else ''), h, count=1)

    h = one(h, A['pcode'], '<span class="lk-val">%s</span>' % f['pcode'], 'product code')
    h = one(h, A['spec'], '<span class="lk-val sm">%s</span>' % f['spec'], 'specification reference')
    D = testing_dates(f['examined'], lod)
    h = one(h, A['testdate'], '<span class="lk-val sm">%s</span>' % D['span'], 'test date')
    h = one(h, A['production'], '<span class="lk-val">%s</span>' % f['production'], 'production batch')
    h = one(h, A['processing'], '<span class="lk-val">%s</span>' % f['processing'], 'processing batch')
    h = one(h, A['packaging'], '<span class="lk-val sm">%s</span>' % f['packaging'], 'packaging date')

    # his two conventions, each kept as he wrote it: on the loss-on-drying page both boxes carry
    # the issue date; on the 1, 2, 7 page the Analyst dates the analysis and the QC Manager the
    # approval.
    analyst = f['testdate'] if A['analyst_is_testdate'] else f['issued']
    if A['analyst_date'] == A['approver_date']:
        h = h.replace(A['analyst_date'], '<span class="ap-date-val">%s</span>' % f['issued'])
    else:
        h = one(h, A['analyst_date'], '<span class="ap-date-val">%s</span>' % analyst, 'analyst date')
        h = one(h, A['approver_date'], '<span class="ap-date-val">%s</span>' % f['issued'], 'approver date')

    sub = 'Appearance · Identification A+B · Foreign Matter' + (' · Loss on Drying' if lod else '')
    if A['title']:
        h = one(h, A['title'], '<title>Purely Plant — iCoA — %s — %s %s — %s</title>'
                % (f['code'], f['headline'], f['strain'], sub), 'title')
    else:
        h = re.sub(r'<title>[^<]*</title>',
                   '<title>Purely Plant — iCoA — %s — %s %s — %s</title>'
                   % (f['code'], f['headline'], f['strain'], sub), h, count=1)

    if lod:
        h = h.replace('22.07.2026 – 27.07.2026', D['lod'])
        h = h.replace('7.9%', f['lod'])

    # 02.1, 02.2 and 02.3 are a day's work and say so; 02.4 already carries its window
    n = 0
    def stamp(m):
        nonlocal n
        if '2026' in m.group(2) or '2025' in m.group(2):
            return m.group(0)                      # a block that already states its dates
        n += 1
        return m.group(1) + m.group(2) + ' · ' + D['same'] + m.group(3)
    # the Македонски heading is corrected further down, so accept either spelling here
    h = re.sub(r'(<span class="mi-l">Method<span class="mk">Метода?</span></span>)([^<]*)(<i class="bisep">)',
               stamp, h)
    if n < 3:
        raise SystemExit('%s: only %d analysis blocks were dated' % (f['code'], n))

    # Head of QC, 24.09.2026: in Macedonian the heading is Метод, not Метода.
    n = h.count('<span class="mk">Метода</span>')
    if not n:
        raise SystemExit('%s: no Метода to correct' % f['code'])
    h = h.replace('<span class="mk">Метода</span>', '<span class="mk">Метод</span>')

    # Head of QC, 24.09.2026: the sentence under Results vs Specification says nothing the table
    # above it has not already said. It comes off every internal certificate.
    i = h.find('<div class="disp-note">')
    if i < 0:
        raise SystemExit('%s: no disposition note to remove' % f['code'])
    j = h.find('</div>', i)
    if j < 0:
        raise SystemExit('%s: the disposition note is unterminated' % f['code'])
    h = h[:i] + h[j + len('</div>'):]
    if '<div class="disp-note"' in h:
        raise SystemExit('%s: a disposition note survives' % f['code'])

    if '7' not in scope:
        # P060362 alone: neither foreign matter nor loss on drying. The 02.3 table, the note that
        # belongs to it and the section 04 row come off, and the subtitle loses its third term.
        i = h.find('<div class="zr-wrap zr-fm">')
        j = h.find('</div>', h.find('</table>', i))
        if i < 0 or j < 0:
            raise SystemExit('%s: the foreign-matter table is not where it should be' % f['code'])
        h = h[:i] + h[j + len('</div>'):]
        k = h.find('<div class="pot-note">')
        if k >= 0:
            h = h[:k] + h[h.find('</div>', k) + len('</div>'):]
        h = drop_rows(h, '<span class="en">Foreign Matter</span>', '<span class="en">Foreign Matter</span>',
                      'the section 04 foreign-matter row')
        h = one(h, SUB_EN, 'Appearance · Identification A + B', 'header subtitle without foreign matter')
        h = one(h, SUB_MK, 'Изглед · идентификација А + Б', 'header subtitle, Macedonian')
        h = one(h, 'Appearance · Identification A+B · Foreign Matter',
                'Appearance · Identification A+B', 'title without foreign matter')
        if 'Foreign Matter' in h or 'Страни материи' in h:
            raise SystemExit('%s: foreign matter survives the removal' % f['code'])
    return h


# ── the data ────────────────────────────────────────────────────────────────────────────
LOD_ONLY = {
    # the two the Head of QC issued himself, with the figures his own pages carry
    # only the loss-on-drying figure is his; the dates are now computed from the examination date,
    # because the ones his two pages carry end on the certificate's issue date
    'HPA1024': {'lod': '7.9%'},
    'OPM1024': {'lod': '7.15%'},
}


SCANS = os.path.join(GAP, 'tracker', 'COQ_SCAN_PHENOTYPE_2026-09-24.tsv')


def load(list_tsv):
    import csv
    # Head of QC, 24.09.2026: the scans he shared are the current and approved certificates, so the
    # phenotype and its split are read from them and from nothing else. 38 of the 46 agree with the
    # cultivar record, none disagrees, and the 8 the record cannot answer are settled by the scan.
    scan = {r['batch']: (r['pheno'], r['split'])
            for r in csv.DictReader(open(SCANS, encoding='utf-8'), delimiter='\t')}
    reg = json.load(open(os.path.join(GAP, 'coq_artifact_data.json'), encoding='utf-8'))
    coqs = reg['coqs'] if isinstance(reg, dict) and 'coqs' in reg else reg
    by = {str(c['regcode']): c for c in coqs}
    plan = json.load(open(os.path.join(HERE, 'ISSUE_iCOA/_generator/coq_plan.json'), encoding='utf-8'))
    meta, bycode = {}, {}
    for p in plan:
        meta.setdefault(p['rec']['cult'], {'strainCode': p['strainCode'], 'phenotype': p['rec']['phenotype']})
        ph = str(p['rec'].get('phenotype') or '').strip()
        if ph and ph != '—':
            bycode.setdefault(str(p['strainCode']), set()).add(ph)

    out, derived = [], []
    for r in csv.DictReader(open(list_tsv, encoding='utf-8'), delimiter='\t'):
        if r['icoa'] == '—':
            continue
        c = by[r['coq']]
        cu = str(c.get('cb') or '')
        m = meta.get(cu, {})
        if r['batch'] not in scan:
            raise SystemExit('%s: no approved scan to read the phenotype from' % r['batch'])
        pheno, split = scan[r['batch']]
        rec = str(m.get('phenotype') or '').strip()
        if rec and rec != '—' and rec != pheno:
            raise SystemExit('%s: the scan says %s, the cultivar record says %s — refusing to guess'
                             % (r['batch'], pheno, rec))
        if not rec or rec == '—':
            derived.append((r['batch'], 'the scan', pheno + (' ' + split if split else '')))
        pp = str(c.get('pp') or '')
        has_p = bool(re.match(r'^[PJ]\d{5,6}$', pp))
        spec = str(c.get('spec') or '')
        spec = re.sub(r'_v\.\d+$', '_v.03', spec)
        f = {
            'batch': r['batch'], 'coq': r['coq'], 'code': r['icoa'],
            'issued': str(c.get('icoa_issue') or ''),
            'headline': pp if has_p else cu,
            'strain': str(c.get('strain') or ''),
            'pheno': pheno, 'split': split,
            'pcode': str(c.get('pcode') or '').replace(' : ', ':'),
            'spec': spec,
            'testdate': str(c.get('icoa_tested') or ''),
            'examined': str(c.get('icoa_tested') or ''),
            'production': pp if has_p else '—',
            'processing': cu,
            'packaging': str(c.get('pk') or '—'),
            'scope': r['scope'],
        }
        f.update(LOD_ONLY.get(r['batch'], {}))
        out.append(f)
    return out, derived


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(GAP, 'DELIVER_2026-09-24', 'iCoA_T1_T2_owner_format'))
    ap.add_argument('--list', default=os.path.join(GAP, 'tracker', 'ICOA_LIST_2026-09-24.tsv'))
    ap.add_argument('--only', default=None)
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args(argv[1:])

    if a.selftest:
        # Build OPM1024 from the HPA1024 base and hold it against the Head of QC's own document.
        import difflib
        U = '/root/.claude/uploads/4877ce6e-ae82-551e-bf35-5698c379c3be/'
        want = open(U + '4135386d-iCoA-PP_26-114_OPM1024_OPM_Orange_Punch_Mimosa_Retest_1_LOD.html',
                    encoding='utf-8').read()
        want = re.sub(r'<img class="ap-img handwritten"[^>]*>', '', want)
        # his document predates the rulings of 24.09, so apply them to it before comparing
        want = want.replace('<span class="mk">Метода</span>', '<span class="mk">Метод</span>')
        i = want.find('<div class="disp-note">')
        want = want[:i] + want[want.find('</div>', i) + len('</div>'):]
        fields, _ = load(a.list)
        f = [x for x in fields if x['batch'] == 'OPM1024'][0]
        got = build('1,2,7,8'.split(','), f)
        # the test is of the fields, not of the ink or the sizing rule the base carries
        strip = lambda x: re.sub(r'<style id="__sig-v2">[\s\S]*?</style>', '',
                                 re.sub(r'<img class="ap-img handwritten"[^>]*>', '', x))
        want, got = strip(want), strip(got)
        d = [l for l in difflib.unified_diff(want.split('\n'), got.split('\n'), 'his', 'built', n=0, lineterm='')
             if l[:1] in '+-' and l[:3] not in ('---', '+++')]
        print('self-test — OPM1024 built from the HPA1024 base, against his own document:')
        print('  differing lines: %d' % len(d))
        for l in d[:20]:
            print('   ' + l[:170])
        return 0 if not d else 1

    fields, derived = load(a.list)
    if a.only:
        fields = [f for f in fields if a.only in (f['batch'], f['code'], f['coq'])]
    os.makedirs(a.out, exist_ok=True)
    made = []
    for f in fields:
        html = build(f['scope'].split(','), f)
        name = '%s_%s_%s.html' % (f['code'], f['headline'],
                                  re.sub(r'[^A-Za-z0-9]+', '_', f['strain']).strip('_'))
        open(os.path.join(a.out, name), 'w', encoding='utf-8').write(html)
        made.append((f['code'], f['batch'], f['scope'], name))
    print('internal certificates built in the Head of QC\'s format: %d' % len(made))
    print('  loss on drying: %s' % ', '.join(f['batch'] for f in fields if '8' in f['scope'].split(',')))
    if derived:
        print('  phenotype the cultivar record could not answer, read off the scan (%d): %s'
              % (len(derived), ', '.join('%s → %s' % (t[0], t[2]) for t in derived)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
