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
BASE = os.path.join(HERE, 'ISSUE_iCOA', '_owner_format', 'iCoA-PP_26-110_LOD_base.html')

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


def chip(en, mk, on):
    if on:
        return '<span class="chip-sel"><span class="bx">☒</span> %s <span class="mk">%s</span></span>' % (en, mk)
    return '<span class="chip-un"><span class="bx">☐</span> %s</span>' % en


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


def build(base, f, lod):
    h = base
    h = one(h, '<div class="hb-code">iCoA-PP_26-110</div>',
            '<div class="hb-code">%s</div>' % f['code'], 'document code')
    h = one(h, 'Issued · Издаден <b>27.07.2026</b>',
            'Issued · Издаден <b>%s</b>' % f['issued'], 'issue date')
    h = one(h, '<span style="font-family:\'Roboto Mono\',monospace">HPA1024</span>',
            '<span style="font-family:\'Roboto Mono\',monospace">%s</span>' % f['headline'], 'headline batch')
    h = one(h, '<span style="font-weight:800;text-transform:uppercase">High Pro Amnesia</span>',
            '<span style="font-weight:800;text-transform:uppercase">%s</span>' % f['strain'], 'strain')

    for en in ('Hybrid', 'Indica', 'Sativa'):
        pat = re.compile(r'<span class="chip-(?:sel|un)">\s*<span class="bx">[☒☐]</span>\s*'
                         + en + r'(?:\s*<span class="mk">[^<]*</span>)?\s*</span>')
        found = pat.findall(h)
        if len(found) != 1:
            raise SystemExit('phenotype %s: %d chips, not one' % (en, len(found)))
        h = pat.sub(lambda m: chip(en, MK_PHENO[en.upper()], f['pheno'] == en.upper()), h, count=1)

    h = one(h, '<span class="lk-val">HPA_THC18:CBD1</span>',
            '<span class="lk-val">%s</span>' % f['pcode'], 'product code')
    h = one(h, '<span class="lk-val sm">QCSP_001_HPA-II_v.03</span>',
            '<span class="lk-val sm">%s</span>' % f['spec'], 'specification reference')
    h = one(h, '<span class="lk-val sm">22.07 – 27.07.2026</span>',
            '<span class="lk-val sm">%s</span>' % f['testdate'], 'test date')
    h = one(h, '<span class="lk-val">—</span>',
            '<span class="lk-val">%s</span>' % f['production'], 'production batch')
    h = one(h, '<span class="lk-val">HPA1024</span>',
            '<span class="lk-val">%s</span>' % f['processing'], 'processing batch')
    h = one(h, '<span class="lk-val sm">11.04.2025</span>',
            '<span class="lk-val sm">%s</span>' % f['packaging'], 'packaging date')
    h = h.replace('<span class="ap-date-val">27.07.2026</span>',
                  '<span class="ap-date-val">%s</span>' % f['issued'])

    sub = 'Appearance · Identification A+B · Foreign Matter' + (' · Loss on Drying' if lod else '')
    h = one(h, '<title>Purely Plant — iCoA — iCoA-PP_26-110 — HPA1024 High Pro Amnesia — '
               'Appearance · Identification A+B · Foreign Matter · Loss on Drying</title>',
            '<title>Purely Plant — iCoA — %s — %s %s — %s</title>'
            % (f['code'], f['headline'], f['strain'], sub), 'title')

    if lod:
        h = h.replace('22.07.2026 – 27.07.2026', f['lodwindow'])
        h = h.replace('7.9%', f['lod'])
    else:
        h = one(h, SUB_LOD_EN, SUB_EN, 'header subtitle')
        h = one(h, SUB_LOD_MK, SUB_MK, 'header subtitle, Macedonian')
        h = drop_rows(h, '<span class="gn">02.4</span>', 'Total Loss on Drying', 'the 02.4 group')
        h = drop_rows(h, '<span class="en">Loss on Drying</span>', '<span class="en">Loss on Drying</span>',
                      'the section 04 loss-on-drying row')
        for en, mk in (
            ('Tested <strong>in-house</strong>; loss on drying 22.07.2026 – 27.07.2026.',
             'Tested <strong>in-house</strong> on the packaging date.'),
            ('Испитано интерно; губиток при сушење 22.07.2026 – 27.07.2026.',
             'Испитано интерно на датумот на пакување.')):
            h = one(h, en, mk, 'disposition note')
        if 'Loss on Drying' in h or 'Губиток при сушење' in h:
            raise SystemExit('%s: loss on drying survives the removal' % f['code'])

    if '7' not in f['scope'].split(','):
        # Foreign matter is not on this certificate either: the whole 02.3 table, the note that
        # belongs to it, the section 04 row, and the third term of the header subtitle come off.
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
        h = one(h, SUB_MK, 'Изглед · идентификација А + Б', 'header subtitle without foreign matter, Macedonian')
        h = one(h, 'Appearance · Identification A+B · Foreign Matter',
                'Appearance · Identification A+B', 'title without foreign matter')
        if 'Foreign Matter' in h or 'Страни материи' in h:
            raise SystemExit('%s: foreign matter survives the removal' % f['code'])
    return h


# ── the data ────────────────────────────────────────────────────────────────────────────
LOD_ONLY = {
    # the two the Head of QC issued himself, with the figures his own pages carry
    'HPA1024': {'lod': '7.9%', 'lodwindow': '22.07.2026 – 27.07.2026', 'testdate': '22.07 – 27.07.2026'},
    'OPM1024': {'lod': '7.15%', 'lodwindow': '23.07.2026 – 27.07.2026', 'testdate': '23.07 – 27.07.2026'},
}


def load(list_tsv):
    import csv
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
        pheno = str(m.get('phenotype') or '').strip()
        if not pheno or pheno == '—':
            cand = sorted(bycode.get(str(m.get('strainCode') or ''), []))
            if len(cand) != 1:
                raise SystemExit('%s: the strain code gives %d phenotypes, not one' % (r['batch'], len(cand)))
            pheno = cand[0]
            derived.append((r['batch'], str(m.get('strainCode')), pheno))
        pp = str(c.get('pp') or '')
        has_p = bool(re.match(r'^[PJ]\d{5,6}$', pp))
        spec = str(c.get('spec') or '')
        spec = re.sub(r'_v\.\d+$', '_v.03', spec)
        f = {
            'batch': r['batch'], 'coq': r['coq'], 'code': r['icoa'],
            'issued': str(c.get('icoa_issue') or ''),
            'headline': pp if has_p else cu,
            'strain': str(c.get('strain') or ''),
            'pheno': pheno,
            'pcode': str(c.get('pcode') or '').replace(' : ', ':'),
            'spec': spec,
            'testdate': str(c.get('icoa_tested') or ''),
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
    base = open(BASE, encoding='utf-8').read()

    if a.selftest:
        # Build OPM1024 from the HPA1024 base and hold it against the Head of QC's own document.
        import difflib
        U = '/root/.claude/uploads/4877ce6e-ae82-551e-bf35-5698c379c3be/'
        want = open(U + '4135386d-iCoA-PP_26-114_OPM1024_OPM_Orange_Punch_Mimosa_Retest_1_LOD.html',
                    encoding='utf-8').read()
        want = re.sub(r'<img class="ap-img handwritten"[^>]*>', '', want)
        fields, _ = load(a.list)
        f = [x for x in fields if x['batch'] == 'OPM1024'][0]
        got = build(base, f, lod=True)
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
        lod = '8' in f['scope'].split(',')
        html = build(base, f, lod)
        name = '%s_%s_%s.html' % (f['code'], f['headline'],
                                  re.sub(r'[^A-Za-z0-9]+', '_', f['strain']).strip('_'))
        open(os.path.join(a.out, name), 'w', encoding='utf-8').write(html)
        made.append((f['code'], f['batch'], f['scope'], name))
    print('internal certificates built in the Head of QC\'s format: %d' % len(made))
    print('  loss on drying: %s' % ', '.join(f['batch'] for f in fields if '8' in f['scope'].split(',')))
    if derived:
        print('  phenotype taken from the strain code (%d): %s'
              % (len(derived), ', '.join('%s %s→%s' % t for t in derived)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
