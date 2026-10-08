#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tranches 1 and 2: corrected copies that carry the phenotype the specifications now state, next to the pages as sent.

    python3 tracker/build_t1_t2_phenotype_corrected_2026-10-08.py --check    # builds and compares, writes nothing
    python3 tracker/build_t1_t2_phenotype_corrected_2026-10-08.py --apply

Head of QC, 08.10.2026, after the specification edits (every OPM grade Hybrid · Indica dominant; KC-I, HPA-I/II/III,
BG-I/II, BSS-III Hybrid): *"check the COQs and iCOAs for the batches above and see what does it say for the phenotype
and make it unified … give me last versions for download"*. Asked how, he chose **corrected copies**: only the
phenotype changes, and the pages as sent are untouched, as with the laboratory lines on 07.10.2026. He chose
**HYBRID only**: OPM alone shows · INDICA DOMINANT. And the order: *"then for T3 first … and only after you do any
work to the t1 and t2 COQs and iCOAs"*.

**Which.** The Tranche 1/2 CoQs whose specification is one of those grades, read from the register and the frozen
snapshot. There are 23, with 23 iCoAs: 12 initial and 11 retest.

**CoQ.** Each copy is built from the page as sent (`FROZEN_T1_T2_2026-09-26.json`, `design_handoff/out`):
- the laboratory lines are corrected as in the copies of 07.10.2026 (`build_t1_t2_lab_lines_corrected_2026-10-07.py`);
- in the phenotype group, Hybrid is ticked and Indica and Sativa are not (the markup the Tranche 3 pages use);
- OPM's tick also carries "· INDICA DOMINANT".

The copy is printed as on 07.10. It is refused if its text differs from the PDF as sent in anything but the laboratory
lines and the phenotype group, if it runs to a second page, or if its layout is worse than the page as sent.

**iCoA.** The sent T1/T2 iCoAs were printed from HTML that is not kept. Their builders are, so each page is rebuilt:
- the **initials** with the tree of 30.09.2026 (`6f0562b`): `build_t3_bundle.fields` → `own.build` → `house_stack`;
- the **retests** with the tree of 24.09.2026 (`9426a22`): `build_owner_format`;
- both through the same `print_coq_pdfs.render`.

Each page is rebuilt twice:
- **unchanged**, it must equal the PDF as sent: the same text, and a mean pixel difference under 0.01 at 100 dpi. This
  proves the builder.
- **with the phenotype changed** (`pheno` HYBRID; `split` "· INDICA DOMINANT" for OPM, as the builder already prints a
  split), it must differ from the sent page only inside the phenotype row: no pixel outside that band, and no text
  outside the phenotype group.

Output, `DELIVER_2026-10-08_T1_T2_Phenotype_Corrected/`, one folder per batch. Each certificate is there on its own,
not merged (Head of QC, 08.10.2026: *"give only those batches' Word documents and PDF, I will merge them into one
myself"*):
- the CoQs and the iCoAs, under the file names they were sent with, each as PDF and Word;
- the specification sheets they cite, as PDF and Word.

`CHANGES.tsv` says what changed on each.

The iCoA PDF is the corrected page as its own printer makes it: outside the phenotype row it is identical to the page
as sent, Type 3 house faces included. Its Word copy is made from the same page printed in Google's static instances of
those fonts, because Word cannot hold a Type 3 font as text. The text is the same, and glyph advances differ by a
fraction of a point.

Nothing in the register, `design_handoff/out` or the delivered folders changes, so `check_frozen_records.py` holds.
"""
import argparse
import csv
import difflib
import glob
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(GAP))
SNAP = os.path.join(HERE, 'FROZEN_T1_T2_2026-09-26.json')
SENT = os.path.join(GAP, 'DELIVER_2026-09-30_All')
STAMP = '2026-10-08'
OUT = os.path.join(GAP, 'DELIVER_%s_T1_T2_Phenotype_Corrected' % STAMP)
CONVERT = os.path.join(GAP, 'design_handoff', 'toolchain', 'pdf_to_docx_exact.py')
CODE = re.compile(r'(?:CoQ|iCoA)-PP_26-\d{3}')
# the grades the specifications now print Hybrid for (specs/build_qcsp_imb.py PHENOTYPE_RULING); None = every grade
RULED = {'OPM': None, 'KC': {'I'}, 'HPA': {'I', 'II', 'III'}, 'BG': {'I', 'II'}, 'BSS': {'III'}}
LEAN = {'OPM': 'INDICA'}
# the tree that printed each sent page: initials 30.09 (processing pill); retests 24.09 15:45; the two retests
# with in-house loss on drying 24.09 16:44, when their window came to close on the CoQ's issue date
TREES = {'initial': '6f0562b', 'retest': '9426a22', 'retest-lod': '9db4382'}
LOD_ICOA = {'iCoA-PP_26-110', 'iCoA-PP_26-114'}
TREE_PATHS = ['deliverables/qc_gap_analysis/icoa_handoff/v3', 'deliverables/qc_gap_analysis/live_instrument',
              'deliverables/qc_gap_analysis/tracker', 'deliverables/qc_gap_analysis/intake_tranches_2026-09-18',
              'deliverables/qc_gap_analysis/coq_artifact_data.json', 'deliverables/qc_gap_analysis/batch_dates_2026-09-10.csv',
              'ingestion/coa_track/letta-imb-coas']
RATIO = ('<span class="ratio" style="font-size:.86em;letter-spacing:.3px">· %s '
         '<b style="color:#FFD98A;font-weight:800">DOMINANT</b></span>')

# run inside an old tree: build each iCoA unchanged and corrected, print both
RUNNER = r'''
import importlib.util, json, os, sys
job = json.load(open(sys.argv[1]))
sys.path.insert(0, 'live_instrument'); sys.path.insert(0, os.path.join('..', '..', 'ingestion', 'coa_track', 'letta-imb-coas'))
sys.path.insert(0, os.path.join('icoa_handoff', 'v3'))
from print_coq_pdfs import render
reg = json.load(open('coq_artifact_data.json', encoding='utf-8'))
by = {c['regcode'][:13]: c for c in reg['coqs']}
if job['series'] == 'initial':
    spec = importlib.util.spec_from_file_location('b3', os.path.join('tracker', 'build_t3_bundle_2026-09-26.py'))
    b3 = importlib.util.module_from_spec(spec); spec.loader.exec_module(b3)
    def page(code, change):
        c = by[code]
        scope, _ = b3.scope_of(c)                       # the rows the CoQ credits to its iCoA, as that bundle read them
        f = b3.fields(c, [], tuple(scope) or ('1', '2', '7'))
        if change:
            f = dict(f, **change)
        return b3.house_stack(b3.own.build(f['scope'].split(','), f))
else:
    import build_owner_format as own
    fields, _ = own.load(os.path.join('tracker', 'ICOA_LIST_2026-09-24.tsv'))
    fb = {f['coq']: f for f in fields}
    def page(code, change):
        f = fb[code]
        if change:
            f = dict(f, **change)
        return own.build(f['scope'].split(','), f)
import re
def chips(html, split):
    # the phenotype chips as this builder's chip() writes them: Hybrid ticked (with its split) and its Macedonian,
    # Indica and Sativa not
    a = html.find('<span class="grp"><span class="lk-lbl">Phenotype'); b = html.find('<span class="grp">', a + 10)
    grp = html[a:b]
    pat = lambda w: r'<span class="chip-(?:sel|un)"><span class="bx">[\u2612\u2610]</span> %s[^<]*(?:<span class="mk">[^<]*</span>)?</span>' % w
    new = re.sub(pat('Hybrid'), lambda m: '<span class="chip-sel"><span class="bx">\u2612</span> %s <span class="mk">\u0425\u0438\u0431\u0440\u0438\u0434</span></span>'
                 % ('Hybrid %s' % split if split else 'Hybrid'), grp, count=1)
    for w in ('Indica', 'Sativa'):
        new = re.sub(pat(w), lambda m, w=w: '<span class="chip-un"><span class="bx">\u2610</span> %s</span>' % w, new, count=1)
    return html[:a] + new + html[b:]
srcs, fit = [], set()
for it in job['items']:
    for tag, change in (('sent', None), ('fix', it['change'])):
        if it.get('src_html'):                    # a page printed from HTML that is kept: the signed LOD certificates
            h = open(it['src_html'], encoding='utf-8').read()
            h = chips(h, change['split']) if change else h
        else:
            h = page(it['coq'], change)
            if change and chips(page(it['coq'], None), change['split']) != h:
                raise SystemExit('%s: the chip edit is not what the builder makes' % it['icoa'])
        p = os.path.join(job['html'], '%s__%s.html' % (it['icoa'], tag))
        open(p, 'w', encoding='utf-8').write(h)
        srcs.append(p)
        if change and job['series'] == 'initial':
            fit.add(p)
FIT_JS = """() => {
  const r = document.querySelector('div.page div.selrow');
  if (!r || r.scrollWidth <= r.clientWidth + 0.5) return {k: 1};
  const cs = getComputedStyle(r);
  const avail = r.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
  const w = document.createElement('div');
  w.style.cssText = 'display:flex;align-items:center;gap:' + cs.columnGap + ';flex:0 0 auto;width:max-content;transform-origin:0 50%';
  Array.from(r.children).forEach(k => w.appendChild(k));
  r.appendChild(w);
  const k = Math.min(1, avail / w.scrollWidth);
  w.style.transform = 'scale(' + k + ')';
  return {k: k, avail: avail, need: w.scrollWidth};
}"""
scale = {}
out = render(srcs, job['pdf'], probe=lambda src, pg: scale.__setitem__(src, pg.evaluate(FIT_JS)) if src in fit else None)
json.dump({'pdf': dict(zip(srcs, out)), 'scale': scale}, open(job['result'], 'w'))
'''


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def targets():
    reg = json.load(open(os.path.join(GAP, 'coq_artifact_data.json'), encoding='utf-8'))
    pages = {CODE.search(p).group(0): os.path.join(GAP, p) for p in json.load(open(SNAP, encoding='utf-8'))['pages']}
    out = []
    for c in reg['coqs']:
        code = c['regcode'][:13]
        m = re.match(r'QCSP_001_([A-Z0-9]+)-([IVX]+)_v\.01$', c.get('spec') or '')
        if code in pages and m and m.group(1) in RULED and (RULED[m.group(1)] is None or m.group(2) in RULED[m.group(1)]):
            out.append({'coq': code, 'icoa': c['icoa_code'], 'abbr': m.group(1), 'spec': c['spec'], 'page': pages[code],
                        'series': 'retest' if 'retest' in c['t'] else 'initial'})
    if len(out) != 23 or len({t['icoa'] for t in out}) != 23:
        raise SystemExit('expected 23 CoQs with 23 iCoAs, found %d' % len(out))
    return sorted(out, key=lambda t: (t['series'] != 'initial', t['coq']))


def sent_pdf(kind, t):
    got = glob.glob(os.path.join(SENT, kind, t['series'].capitalize(), 'T[12]', (t[kind.lower()] if kind == 'CoQ'
                                                                                 else t['icoa']) + '_*.pdf'))
    if len(got) != 1:
        raise SystemExit('%d sent %s PDFs for %s' % (len(got), kind, t['coq']))
    return got[0]


def flat(pdf):
    import pymupdf
    with pymupdf.open(pdf) as d:
        return ''.join(''.join(p.get_text() for p in d).split())


def pheno_cut(text, start, end):
    """(the text before the phenotype group, the group, the text after) — on text with the spaces taken out."""
    i = text.find(start)
    j = text.find(end, i + len(start))
    if i < 0 or j < 0:
        raise SystemExit('no phenotype group (%s … %s)' % (start, end))
    return text[:i + len(start)], text[i + len(start):j], text[j:]


def coq_markup(html, t):
    """The phenotype group with Hybrid ticked; Indica and Sativa not; OPM's tick with its leaning."""
    a = html.find('<span class="grp"><span class="lk-lbl">Phenotype')
    b = html.find('<span class="grp">', a + 10)
    if a < 0 or b < 0 or html.count('<span class="lk-lbl">Phenotype') != 1:
        raise SystemExit('%s: no single phenotype group' % t['coq'])
    grp = html[a:b]
    if grp.count('☒') != 1:
        raise SystemExit('%s: the phenotype group ticks %d chips' % (t['coq'], grp.count('☒')))
    chip = lambda on, word, extra='': ('<span class="chip-%s"><span class="bx">%s</span> %s%s</span>'
                                       % ('sel' if on else 'un', '☒' if on else '☐', word, extra))
    lean = (' ' + RATIO % LEAN[t['abbr']]) if t['abbr'] in LEAN else ''
    new = re.sub(r'<span class="chip-(?:sel|un)"><span class="bx">[☒☐]</span> Hybrid[^<]*(?:<span class="ratio"[\s\S]*?</span>)?</span>',
                 lambda m: chip(True, 'Hybrid', lean), grp, count=1)
    for w in ('Indica', 'Sativa'):
        new = re.sub(r'<span class="chip-(?:sel|un)"><span class="bx">[☒☐]</span> %s</span>' % w,
                     lambda m, w=w: chip(False, w), new, count=1)
    if new.count('☒') != 1 or '☒</span> Hybrid' not in new or new == grp:
        raise SystemExit('%s: the phenotype group did not take the change' % t['coq'])
    return html[:a] + new + html[b:], grp, new


def main(argv):
    import pymupdf
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args(argv[1:])
    if not (a.apply or a.check):
        ap.error('pass --check or --apply')
    B = load('B', os.path.join(HERE, 'build_t3_bundle_2026-09-26.py'))
    L = load('L', os.path.join(HERE, 'build_t1_t2_lab_lines_corrected_2026-10-07.py'))
    tg = targets()
    tmp = tempfile.mkdtemp(prefix='t12pheno_')
    rows, bad = [], []

    # --- the CoQs: frozen page + laboratory lines (07.10) + phenotype; printed as on 07.10
    table = L.swaps()
    hdir = os.path.join(tmp, 'CoQ')
    odir = os.path.join(tmp, 'sent', 'CoQ')
    os.makedirs(hdir)
    os.makedirs(odir)
    htmls, origs = [], []
    for t in tg:
        lab, done = L.correct(t['page'], table)
        new, was, now = coq_markup(lab, t)
        dst = os.path.join(hdir, os.path.basename(t['page']))
        open(dst, 'w', encoding='utf-8').write(new)
        htmls.append(dst)
        origs.append(shutil.copyfile(t['page'], os.path.join(odir, os.path.basename(t['page']))))
        t['lab_lines'] = '; '.join('%s %s ×%d' % d for d in done) or '—'
    geo = {}
    probe = lambda s, page: geo.__setitem__(s, page.evaluate(B.LAYOUT_JS))
    B.render(origs, os.path.join(tmp, 'sent_pdf'), css=B.house_css(origs), probe=probe)
    made = B.render(htmls, os.path.join(tmp, 'coq_pdf'), css=B.house_css(htmls), probe=probe)
    olds = [x[2] for x in table] + [x[3] for x in table]
    strip = lambda s: re.sub('|'.join(re.escape(''.join(o.split())) for o in olds), '', s)
    for t, h, o, pdf in zip(tg, htmls, origs, made):
        B.assert_house_fonts(pdf)
        g, n = geo[o], geo[h]
        if pymupdf.open(pdf).page_count != 1:
            bad.append('%s prints more than one page' % t['coq'])
        if n['h'] > max(1123, g['h']) or len(n['lab']) != len(g['lab']) or \
                any(b > max(2, x) for x, b in zip(g['lab'], n['lab'])):
            bad.append('%s: layout worse than as sent (%s → %s)' % (t['coq'], g, n))
        was = pheno_cut(strip(flat(sent_pdf('CoQ', t))), 'PHENOTYPEФЕНОТИП', 'CHEMOTYPE')
        now = pheno_cut(strip(flat(pdf)), 'PHENOTYPEФЕНОТИП', 'CHEMOTYPE')
        if (was[0], was[2]) != (now[0], now[2]):
            sm = difflib.SequenceMatcher(None, was[0] + was[2], now[0] + now[2], autojunk=False)
            bad.append('%s: the CoQ differs beyond the laboratory lines and the phenotype: %s' % (t['coq'], '; '.join(
                '%r→%r' % ((was[0] + was[2])[i1:i2], (now[0] + now[2])[j1:j2])
                for op, i1, i2, j1, j2 in sm.get_opcodes() if op != 'equal')[:300]))
        # as the Tranche 3 pages print it (CoQ-PP_26-019): upper case, each glyph doubled by the text shadow
        want = '☒☒HYBRIDHYBRID' + ('·INDICA·INDICADOMINANTDOMINANT' if t['abbr'] in LEAN else '') + \
            '☐☐INDICAINDICA☐☐SATIVASATIVA'
        if now[1] != want:
            bad.append('%s: the phenotype group reads %r, not %r' % (t['coq'], now[1], want))
        t['coq_was'], t['coq_now'], t['coq_pdf'] = was[1], now[1], pdf

    # --- the iCoAs: rebuilt by the builder that printed them, unchanged and corrected
    group = lambda t: 'retest-lod' if t['icoa'] in LOD_ICOA else t['series']
    for key, rev in TREES.items():
        series = 'retest' if key.startswith('retest') else 'initial'
        items = [t for t in tg if group(t) == key]
        if not items:
            continue
        tree = os.path.join(tmp, 'tree_' + rev)
        os.makedirs(tree)
        arch = subprocess.run(['git', 'archive', rev] + TREE_PATHS, cwd=ROOT, check=True, capture_output=True).stdout
        subprocess.run(['tar', '-x', '-C', tree, '--exclude=*.pdf', '--exclude=*.xlsx', '--exclude=*.zip',
                        '--exclude=*.docx', '--exclude=*.png'], input=arch, check=True)
        job = {'series': series, 'html': os.path.join(tmp, 'icoa_html_' + key),
               'pdf': os.path.join(tmp, 'icoa_pdf_' + key), 'result': os.path.join(tmp, 'icoa_%s.json' % key),
               'items': [{'coq': t['coq'], 'icoa': t['icoa'],
                          'change': {'pheno': 'HYBRID', 'split': ('· %s DOMINANT' % LEAN[t['abbr']]) if t['abbr'] in LEAN else ''}}
                         for t in items]}
        os.makedirs(job['html'])
        os.makedirs(job['pdf'])
        jf = os.path.join(tmp, 'job_%s.json' % key)
        json.dump(job, open(jf, 'w'))
        subprocess.run([sys.executable, '-c', RUNNER, jf], cwd=os.path.join(tree, 'deliverables', 'qc_gap_analysis'), check=True)
        got = json.load(open(job['result']))
        res, scales = got['pdf'], got['scale']
        for t in items:
            unchanged = res[os.path.join(job['html'], '%s__sent.html' % t['icoa'])]
            fixed = res[os.path.join(job['html'], '%s__fix.html' % t['icoa'])]
            sent = sent_pdf('iCoA', t)
            s, u, f = (pymupdf.open(x)[0] for x in (sent, unchanged, fixed))
            ps, pu, pf = (x.get_pixmap(dpi=100, alpha=False) for x in (s, u, f))
            mean = sum(abs(x - y) for x, y in zip(ps.samples, pu.samples)) / float(len(ps.samples))
            if flat(sent) != flat(unchanged) or mean >= 0.01:
                bad.append('%s: the %s builder does not reproduce the page as sent (mean %.4f)' % (t['icoa'], rev, mean))
                continue
            # the phenotype row: from the PHENOTYPE label's top to the next row's top, full width
            ws = s.get_text('words')
            lab = [w for w in ws if w[4] == 'PHENOTYPE']
            nxt = [w for w in ws if w[4] == 'PRODUCT']
            if len(lab) != 1 or not nxt:
                bad.append('%s: no phenotype row to hold the change to' % t['icoa'])
                continue
            y0, y1 = lab[0][1] - 9, min(w[1] for w in nxt) - 2
            row = ps.width * ps.n
            k0, k1 = int(y0 / 72.0 * 100), int(y1 / 72.0 * 100) + 1
            outside = [i for i in range(ps.height) if not k0 <= i < k1
                       and ps.samples[i * row:(i + 1) * row] != pf.samples[i * row:(i + 1) * row]]
            if outside:
                bad.append('%s: the corrected page differs outside the phenotype row (%d pixel rows, first at %.0f pt)'
                           % (t['icoa'], len(outside), outside[0] * 0.72))
            # text by position: above and below the row exactly as sent (a scaled row is painted as its own layer,
            # so content order is no guide); in the row, word by word
            W, H = s.rect.width, s.rect.height
            outside = lambda pg: [''.join(pg.get_text(clip=pymupdf.Rect(0, a_, W, b_)).split()) for a_, b_ in ((0, y0), (y1, H))]
            if outside(s) != outside(f):
                bad.append('%s: the iCoA text differs outside the phenotype row' % t['icoa'])
            words = lambda pg: [w[4] for w in sorted(pg.get_text('words', clip=pymupdf.Rect(0, y0, W, y1)), key=lambda w: (w[0], w[1]))]
            ws_, wf_ = words(s), words(f)
            PH = ('HYBRID', 'INDICA', 'SATIVA', 'Хибрид', 'Индика', 'Сатива', 'DOMINANT', '·')
            rest = lambda ws: sorted(w for w in ws if not any(k in w for k in PH))
            lean = t['abbr'] in LEAN
            if not ('☒HYBRID' in wf_ and '☐INDICA' in wf_ and '☐SATIVA' in wf_ and 'Хибрид' in wf_
                    and '☒INDICA' not in wf_ and '☒SATIVA' not in wf_ and ('DOMINANT' in wf_) == lean):
                bad.append('%s: the phenotype row reads %s' % (t['icoa'], ' '.join(wf_)))
            got, sent_rest = rest(wf_), rest(ws_)
            extra = [w for w in got if w not in sent_rest]
            missing = [w for w in sent_rest if w not in got]
            # the one change besides the phenotype: a Hand chip the page as sent cut at the page edge ("☐H"), now whole
            if missing not in ([], ['☐H']) or any(w not in ('☐HAND', 'HAND') for w in extra):
                bad.append('%s: chemotype/processing differ from as sent: lost %s, gained %s' % (t['icoa'], missing, extra))
            was = ['', ' '.join(w for w in ws_ if any(k in w for k in PH)), '']
            now = ['', ' '.join(w for w in wf_ if any(k in w for k in PH)), '']
            t['icoa_was'], t['icoa_now'], t['icoa_pdf'] = was[1], now[1], fixed
            t['fix_html'] = os.path.join(job['html'], '%s__fix.html' % t['icoa'])
            sc = (scales.get(os.path.join(job['html'], '%s__fix.html' % t['icoa'])) or {}).get('k', 1)
            t['proof'] = '%s%s unchanged = sent (mean %.4f); corrected differs inside y %.0f–%.0f pt only%s' % (
                rev, '', mean, y0, y1,
                '; row fitted to the margin (scale %.3f)' % sc if sc < 1 else '')

    # --- the iCoA's Word source: the corrected page printed in the static house faces. The PDF delivered is the
    # corrected page as the old printer makes it, identical to the page as sent outside the phenotype row; its
    # house faces are Type 3 there, which Word cannot hold as text, so the Word copy is made from the same page in
    # Google's static instances of the same fonts (the same text; glyph advances differ by a fraction of a point)
    fix_html = [t['fix_html'] for t in tg if 'icoa_pdf' in t]
    prints = B.print_copies(fix_html)
    initial = {q for q, h in zip(prints, fix_html) if '/icoa_html_initial/' in h}
    fit_js = re.search(r'FIT_JS = """([\s\S]*?)"""', RUNNER).group(1)
    static = dict(zip(fix_html, B.render(prints, os.path.join(tmp, 'icoa_static'), None, '',
                                         lambda src, pg: pg.evaluate(fit_js) if src in initial else None)))
    for t in tg:
        if 'icoa_pdf' not in t:
            continue
        pdf = static[t['fix_html']]
        with pymupdf.open(pdf) as d:
            if d.page_count != 1:
                bad.append('%s prints %d pages in the static faces' % (t['icoa'], d.page_count))
            if any(x[2] == 'Type3' for x in d[0].get_fonts()):
                bad.append('%s still prints a Type 3 font' % t['icoa'])
            pa = d[0].get_pixmap(dpi=100, alpha=False).samples
        with pymupdf.open(t['icoa_pdf']) as d:
            pb = d[0].get_pixmap(dpi=100, alpha=False).samples
        mean = sum(abs(x - y) for x, y in zip(pa, pb)) / float(len(pa))
        if sorted(w[4] for w in pymupdf.open(pdf)[0].get_text('words')) != \
                sorted(w[4] for w in pymupdf.open(t['icoa_pdf'])[0].get_text('words')) or mean > 6.0:
            bad.append('%s: the static-face print is not the corrected page (mean %.3f)' % (t['icoa'], mean))
        t['icoa_word_src'] = pdf
        t['proof'] += '; Word from the static-face print (same text, mean %.2f)' % mean

    if bad:
        raise SystemExit('refused:\n  ' + '\n  '.join(bad))
    for t in tg:
        print('%-14s %-8s %-15s CoQ %s → %s' % (t['coq'], t['series'], t['icoa'], t['coq_was'], t['coq_now']))
        print('%-39s iCoA %s → %s · %s' % ('', t['icoa_was'], t['icoa_now'], t['proof']))
    print('%d CoQs and %d iCoAs: one A4 page each; the CoQ text equals the page as sent but for the laboratory lines and '
          'the phenotype, the iCoA builder reproduces each sent page and the corrected page differs only in its phenotype row'
          % (len(tg), len(tg)))
    if not a.apply:
        shutil.rmtree(tmp, ignore_errors=True)
        print('--check: nothing written')
        return 0

    # --- per batch, each certificate on its own (Head of QC: "give only those batches' Word documents and PDF, I will
    # merge them into one myself"): the CoQs and iCoAs, and the specification sheets they cite
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    sheets = os.path.join(GAP, 'specs', 'QCSP_001_ImB')
    made = []
    for t in tg:
        batch = re.match(r'CoQ-PP_26-\d{3}_([A-Za-z0-9]+)_', os.path.basename(sent_pdf('CoQ', t))).group(1)
        d = os.path.join(OUT, batch)
        os.makedirs(d, exist_ok=True)
        for kind, src, word_src in (('CoQ', t['coq_pdf'], t['coq_pdf']), ('iCoA', t['icoa_pdf'], t['icoa_word_src'])):
            dst = os.path.join(d, os.path.basename(sent_pdf(kind, t)))
            shutil.copyfile(src, dst)
            made.append((word_src, dst))
        spec = glob.glob(os.path.join(sheets, 'PDF', t['spec'] + '_*.pdf'))
        if len(spec) != 1:
            raise SystemExit('%d sheets for %s' % (len(spec), t['spec']))
        for ext, sub in (('.pdf', 'PDF'), ('.docx', 'DOCX')):
            src = os.path.join(sheets, sub, os.path.basename(spec[0])[:-4] + ext)
            shutil.copyfile(src, os.path.join(d, os.path.basename(src)))
        t['folder'] = batch
    for word_src, pdf in made:
        subprocess.run([sys.executable, CONVERT, word_src, pdf[:-4] + '.docx'], check=True, stdout=subprocess.DEVNULL)
    with open(os.path.join(OUT, 'CHANGES.tsv'), 'w', encoding='utf-8', newline='') as fh:
        w = csv.writer(fh, delimiter='\t', lineterminator='\n')
        w.writerow(['folder', 'coq', 'series', 'specification', 'coq phenotype as sent', 'coq phenotype corrected',
                    'laboratory lines replaced', 'icoa', 'icoa phenotype as sent', 'icoa phenotype corrected', 'proof'])
        for t in tg:
            w.writerow([t['folder'], t['coq'], t['series'], t['spec'], t['coq_was'], t['coq_now'], t['lab_lines'],
                        t['icoa'], t['icoa_was'], t['icoa_now'], t['proof']])
    shutil.rmtree(tmp, ignore_errors=True)
    print('written: %s — %d batch folders, %d certificates, each as PDF and Word, with the sheets they cite'
          % (os.path.relpath(OUT, GAP), len({t['folder'] for t in tg}), len(made)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
