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

**What changes.** Head of QC, 08.10.2026: on Tranches 1 and 2 *"everything … especially looks, parameters and values
must remain the same except for … the processing pill [and] the phenotype selection"*. So:
- **CoQ**: the page as sent (`FROZEN_T1_T2_2026-09-26.json`, `design_handoff/out`) with Hybrid ticked, Indica and Sativa
  not, OPM's tick with "· INDICA DOMINANT" — nothing else; the laboratory-line copy of 07.10.2026 is not folded in.
  Refused if its text differs from the PDF as sent outside the phenotype group, if it runs to a second page, or if its
  layout is worse than the page as sent.
- **iCoA**: the sent pages' HTML is not kept, their builders are. Each sent page is rebuilt unchanged by the tree that
  printed it (initials `6f0562b`; retests `9426a22`; the two loss-on-drying retests `9db4382`) and must equal the PDF
  as sent (same text, mean pixel difference < 0.01 at 100 dpi). The corrected page is built by the same tree; a retest,
  sent without the processing pill, takes it as the 30.09.2026 base writes it, ticked from the register. It must differ from the sent page
  only inside the phenotype row: no pixel outside it, no text outside it, and in it only the phenotype and processing
  words. A row that would pass the margin is scaled to fit, in place.

**Output** (*"when you finish only the batches … simply merge them into one document"*; *"PDF now"*):
`DELIVER_2026-10-08_T1_T2_Phenotype_Corrected/T1_T2_CoQ+iCoA_phenotype_corrected_2026-10-08.pdf`, by batch — initial CoQ,
its iCoA, retest CoQ, its iCoA — and `CHANGES.tsv`, what changed on each.

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
    PROC = ('<span class="grp"><span class="lk-lbl">Processing <span class="mk">\u041e\u0431\u0440\u0430\u0431\u043e\u0442\u043a\u0430</span></span>'
            '<span class="stack">%s%s</span></span>')
    def page(code, change):
        f = fb[code]
        if change:
            f = dict(f, **change)
        h = own.build(f['scope'].split(','), f)
        if change:
            # the processing pill (Head of QC, 30.09.2026), as the 30.09 base and builder write it, ticked from the
            # register; added to the tree that printed the page, so nothing else on it changes
            proc = str((by[code].get('spc') or {}).get('proc') or '').upper()
            if not any(w in proc for w in ('MACHINE', 'HAND')):
                raise SystemExit('%s: no processing method in the register' % code)
            grp = PROC % (own.chip('Machine', '\u041c\u0430\u0448\u0438\u043d\u0441\u043a\u0430', 'MACHINE' in proc),
                          own.chip('Hand', '', 'HAND' in proc))
            a = h.find('<div class="selrow">')
            b = h.find('\n</div>', a)
            if a < 0 or b < 0 or 'Processing <span' in h[a:b]:
                raise SystemExit('%s: no selrow to take the processing pill' % code)
            h = h[:b] + '\n' + grp + h[b:]
        return h
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
        if tag not in job['tags']:
            continue
        if it.get('src_html'):                    # a page printed from HTML that is kept: the signed LOD certificates
            h = open(it['src_html'], encoding='utf-8').read()
            h = chips(h, change['split']) if change else h
        else:
            h = page(it['coq'], change)
            if change and job['series'] == 'initial' and chips(page(it['coq'], None), change['split']) != h:
                raise SystemExit('%s: the chip edit is not what the builder makes' % it['icoa'])
        if change:
            # the CoQ's pill row, words and drawing (Head of QC, 07.10.2026: the pills on every document as on the CoQ)
            a = h.find('<div class="selrow">')
            b = h.find('</div>', a) + len('</div>')
            if a < 0 or h.count('<div class="selrow">') != 1 or '</body>' not in h:
                raise SystemExit('%s: no single pill row' % it['icoa'])
            h = h[:a] + it['row'] + h[b:]
            h = h.replace('</body>', '<style id="__pill-kit">\n' + job['kit'] + '</style>\n</body>', 1)
        p = os.path.join(job['html'], '%s__%s.html' % (it['icoa'], tag))
        open(p, 'w', encoding='utf-8').write(h)
        srcs.append(p)
        if change:
            fit.add(p)
FIT_JS = """() => {
  const r = document.querySelector('div.page div.selrow');
  if (!r) return {k: 1};
  // the row keeps the height it has under the page's own style: the CoQ's taller pills are scaled into it, so
  // nothing below the row moves
  const kit = document.getElementById('__pill-kit');
  let h0 = null;
  if (kit) { kit.sheet.disabled = true; h0 = r.getBoundingClientRect().height; kit.sheet.disabled = false; }
  if (h0 === null && r.scrollWidth <= r.clientWidth + 0.5) return {k: 1};
  if (h0 !== null) { r.style.setProperty('height', h0 + 'px', 'important'); r.style.setProperty('min-height', h0 + 'px', 'important');
                     r.style.setProperty('max-height', h0 + 'px', 'important'); r.style.setProperty('overflow', 'visible', 'important'); }
  const cs = getComputedStyle(r);
  const avail = r.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
  const w = document.createElement('div');
  w.style.cssText = 'display:flex;align-items:center;gap:' + cs.columnGap + ';flex:0 0 auto;width:max-content;transform-origin:0 50%';
  Array.from(r.children).forEach(k => w.appendChild(k));
  r.appendChild(w);
  const inner = h0 === null ? Infinity : h0 - parseFloat(cs.paddingTop) - parseFloat(cs.paddingBottom) - 1;
  const k = Math.min(1, avail / w.scrollWidth, inner / w.getBoundingClientRect().height);
  w.style.transform = 'scale(' + k + ')';
  return {k: k, avail: avail, need: w.scrollWidth, h0: h0};
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
    tg = targets()
    tmp = tempfile.mkdtemp(prefix='t12pheno_')
    rows, bad = [], []

    # --- the CoQs: frozen page + phenotype; printed as on 07.10
    # Head of QC, 08.10.2026: on Tranches 1 and 2 "everything … must remain the same except … the processing pill
    # [and] the phenotype selection" — so the laboratory-line copy of 07.10.2026 is not folded in
    table = []
    hdir = os.path.join(tmp, 'CoQ')
    odir = os.path.join(tmp, 'sent', 'CoQ')
    os.makedirs(hdir)
    os.makedirs(odir)
    htmls, origs = [], []
    for t in tg:
        lab, done = open(t['page'], encoding='utf-8').read(), []
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

    # --- the pill row of the corrected iCoA: the corrected CoQ's own row, drawn with the CoQ's computed pill style
    # (house_kit, restricted to the pill row; read off a corrected OPM copy, whose Hybrid chip carries the leaning)
    H = load('H', os.path.join(HERE, 'house_kit.py'))
    for t, h in zip(tg, htmls):
        t['row'] = H.coq_selrow(open(h, encoding='utf-8').read())
    ref = next(h for t, h in zip(tg, htmls) if t['abbr'] in LEAN)
    H.plan = lambda: [[x, x, ps, H.PSEUDO if ps else H.ALL] for x in H.PILLS for ps in (None, '::before', '::after')] + \
        [['.selrow', '.selrow', None, H.ROW]]
    kit = H.css_of(H.computed(ref), ref)

    # --- the iCoAs: rebuilt by the builder that printed them, unchanged and corrected
    group = lambda t: 'retest-lod' if t['icoa'] in LOD_ICOA else t['series']
    # the sent page from the builder that printed it (the proof); the corrected page from the tree of 30.09.2026, which
    # carries the processing pill (Head of QC, 30.09.2026) — the sent retests predate it
    change = lambda t: {'pheno': 'HYBRID', 'split': ('· %s DOMINANT' % LEAN[t['abbr']]) if t['abbr'] in LEAN else ''}
    group = lambda t: 'retest-lod' if t['icoa'] in LOD_ICOA else t['series']
    # the retests are corrected in the tree that printed them: the 30.09 tree also carries the wide fades of
    # 28.09.2026, which would change their look
    JOBS = [('initial', 'initial', '6f0562b', ['sent', 'fix'], [t for t in tg if t['series'] == 'initial']),
            ('retest', 'retest', '9426a22', ['sent', 'fix'], [t for t in tg if group(t) == 'retest']),
            ('retest-lod', 'retest', '9db4382', ['sent', 'fix'], [t for t in tg if group(t) == 'retest-lod'])]
    sent_of, fix_of, html_of, scale_of, rev_of = {}, {}, {}, {}, {}
    for key, series, rev, tags, items in JOBS:
        tree = os.path.join(tmp, 'tree_' + rev)
        if not os.path.isdir(tree):
            os.makedirs(tree)
            arch = subprocess.run(['git', 'archive', rev] + TREE_PATHS, cwd=ROOT, check=True, capture_output=True).stdout
            subprocess.run(['tar', '-x', '-C', tree, '--exclude=*.pdf', '--exclude=*.xlsx', '--exclude=*.zip',
                            '--exclude=*.docx', '--exclude=*.png'], input=arch, check=True)
        job = {'series': series, 'tags': tags, 'html': os.path.join(tmp, 'icoa_html_' + key),
               'pdf': os.path.join(tmp, 'icoa_pdf_' + key), 'result': os.path.join(tmp, 'icoa_%s.json' % key),
               'kit': kit, 'items': [{'coq': t['coq'], 'icoa': t['icoa'], 'change': change(t), 'row': t['row']}
                                     for t in items]}
        os.makedirs(job['html'])
        os.makedirs(job['pdf'])
        jf = os.path.join(tmp, 'job_%s.json' % key)
        json.dump(job, open(jf, 'w'))
        subprocess.run([sys.executable, '-c', RUNNER, jf], cwd=os.path.join(tree, 'deliverables', 'qc_gap_analysis'), check=True)
        got = json.load(open(job['result']))
        for t in items:
            if 'sent' in tags:
                sent_of[t['icoa']] = got['pdf'][os.path.join(job['html'], '%s__sent.html' % t['icoa'])]
                rev_of[t['icoa']] = rev
            if 'fix' in tags:
                h = os.path.join(job['html'], '%s__fix.html' % t['icoa'])
                fix_of[t['icoa']], html_of[t['icoa']] = got['pdf'][h], h
                scale_of[t['icoa']] = (got['scale'].get(h) or {}).get('k', 1)
    for t in tg:
        rev = rev_of[t['icoa']]
        unchanged, fixed = sent_of[t['icoa']], fix_of[t['icoa']]
        if True:
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
            # a difference of one level in 255 is anti-aliasing at the row's edge, not a change anyone can see
            outside = [i for i in range(ps.height) if not k0 <= i < k1
                       and ps.samples[i * row:(i + 1) * row] != pf.samples[i * row:(i + 1) * row]
                       and max(abs(x - y) for x, y in zip(ps.samples[i * row:(i + 1) * row], pf.samples[i * row:(i + 1) * row])) > 1]
            if outside:
                i = outside[0]
                da = [(abs(x - y), j // ps.n) for j, (x, y) in enumerate(zip(ps.samples[i * row:(i + 1) * row],
                                                                             pf.samples[i * row:(i + 1) * row])) if x != y]
                bad.append('%s: the corrected page differs outside the phenotype row (%d pixel rows, first at %.0f pt; '
                           'band %.1f–%.1f pt; there %d px differ, x %d–%d px, at most %d of 255)'
                           % (t['icoa'], len(outside), i * 0.72, y0, y1, len({x for _, x in da}), min(x for _, x in da),
                              max(x for _, x in da), max(d for d, _ in da)))
            # text by position: above and below the row exactly as sent (a scaled row is painted as its own layer,
            # so content order is no guide); in the row, word by word
            W, H = s.rect.width, s.rect.height
            outside = lambda pg: [''.join(pg.get_text(clip=pymupdf.Rect(0, a_, W, b_)).split()) for a_, b_ in ((0, y0), (y1, H))]
            if outside(s) != outside(f):
                bad.append('%s: the iCoA text differs outside the phenotype row' % t['icoa'])
            words = lambda pg: [w[4] for w in sorted(pg.get_text('words', clip=pymupdf.Rect(0, y0, W, y1)), key=lambda w: (w[0], w[1]))]
            norm = lambda ws: [w.replace('☒☒', '☒').replace('☐☐', '☐') for w in ws]
            ws_, wf_ = norm(words(s)), norm(words(f))
            PH = ('HYBRID', 'INDICA', 'SATIVA', 'Хибрид', 'Индика', 'Сатива', 'DOMINANT', '·')
            rest = lambda ws: sorted(w for w in ws if not any(k in w for k in PH))
            lean = t['abbr'] in LEAN
            if not ('☒HYBRID' in wf_ and '☐INDICA' in wf_ and '☐SATIVA' in wf_
                    and '☒INDICA' not in wf_ and '☒SATIVA' not in wf_ and ('DOMINANT' in wf_) == lean):
                bad.append('%s: the phenotype row reads %s' % (t['icoa'], ' '.join(wf_)))
            got, sent_rest = rest(wf_), rest(ws_)
            extra = [w for w in got if w not in sent_rest]
            missing = [w for w in sent_rest if w not in got]
            extra = [w for w in extra if not (w in ('THC', 'CBD') and ('☒' + w in got or '☐' + w in got))]   # the shadow's copy
            # the one change besides the phenotype: a Hand chip the page as sent cut at the page edge ("☐H"), now whole
            # the processing pill (Head of QC, 30.09.2026) on a retest sent without it, and a Hand chip the page as
            # sent cut at the edge ("☐H") now whole
            PROC = ('PROCESSING', 'ОБРАБОТКА', '☒MACHINE', 'MACHINE', 'Машинска', '☐HAND', 'HAND', '☐H')
            if missing not in ([], ['☐H']) or any(w not in PROC for w in extra):
                bad.append('%s: chemotype/processing differ from as sent: lost %s, gained %s' % (t['icoa'], missing, extra))
            was = ['', ' '.join(w for w in ws_ if any(k in w for k in PH)), '']
            now = ['', ' '.join(w for w in wf_ if any(k in w for k in PH)), '']
            t['icoa_was'], t['icoa_now'], t['icoa_pdf'] = was[1], now[1], fixed
            t['fix_html'] = html_of[t['icoa']]
            sc = scale_of[t['icoa']]
            t['proof'] = '%s%s unchanged = sent (mean %.4f); corrected differs inside y %.0f–%.0f pt only%s' % (
                rev, '', mean, y0, y1,
                '; row fitted to the margin (scale %.3f)' % sc if sc < 1 else '')

    if bad:
        raise SystemExit('refused:\n  ' + '\n  '.join(bad))
    for t in tg:
        print('%-14s %-8s %-15s CoQ %s → %s' % (t['coq'], t['series'], t['icoa'], t['coq_was'], t['coq_now']))
        print('%-39s iCoA %s → %s · %s' % ('', t['icoa_was'], t['icoa_now'], t['proof']))
    print('%d CoQs and %d iCoAs: one A4 page each; the CoQ text equals the page as sent but for '
          'the phenotype, the iCoA builder reproduces each sent page and the corrected page differs only in its phenotype row'
          % (len(tg), len(tg)))
    if not a.apply:
        shutil.rmtree(tmp, ignore_errors=True)
        print('--check: nothing written')
        return 0

    # --- one PDF (Head of QC, 08.10.2026: "only the batches … you told you to correct … simply merge them into one
    # document"; "PDF now"): per batch, the initial CoQ and its iCoA, then the retest CoQ and its iCoA
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    batch_of = lambda t: re.match(r'CoQ-PP_26-\d{3}_([A-Za-z0-9]+)_', os.path.basename(sent_pdf('CoQ', t))).group(1)
    order = sorted(tg, key=lambda t: (batch_of(t), t['series'] != 'initial', t['coq']))
    book, toc, last = pymupdf.open(), [], None
    for t in order:
        if batch_of(t) != last:
            toc.append([1, batch_of(t), book.page_count + 1])
            last = batch_of(t)
        for name, pdf in ((t['coq'], t['coq_pdf']), (t['icoa'], t['icoa_pdf'])):
            with pymupdf.open(pdf) as d:
                toc.append([2, '%s (%s)' % (name, t['series']), book.page_count + 1])
                book.insert_pdf(d)
        t['folder'] = batch_of(t)
    book.set_toc(toc)
    book.set_metadata({'title': 'Purely Plant — Tranches 1 and 2, corrected copies: phenotype (and the processing pill '
                                'on the retest iCoAs) — not issued', 'producer': 'Purely Plant Quality Desk'})
    name = 'T1_T2_CoQ+iCoA_phenotype_corrected_%s.pdf' % STAMP
    book.save(os.path.join(OUT, name), garbage=4, deflate=True)
    n = book.page_count
    book.close()
    with open(os.path.join(OUT, 'CHANGES.tsv'), 'w', encoding='utf-8', newline='') as fh:
        w = csv.writer(fh, delimiter='\t', lineterminator='\n')
        w.writerow(['batch', 'coq', 'series', 'specification', 'coq phenotype as sent', 'coq phenotype corrected',
                    'icoa', 'icoa phenotype as sent', 'icoa phenotype corrected', 'proof'])
        for t in order:
            w.writerow([t['folder'], t['coq'], t['series'], t['spec'], t['coq_was'], t['coq_now'],
                        t['icoa'], t['icoa_was'], t['icoa_now'], t['proof']])
    shutil.rmtree(tmp, ignore_errors=True)
    print('written: %s/%s — %d batches, %d pages' % (os.path.relpath(OUT, GAP), name, len({t['folder'] for t in tg}), n))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
