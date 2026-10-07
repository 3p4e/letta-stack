#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One look for the pills and the heading bars: the certificate of quality's, on the iCoA and the specification.

    python3 tracker/house_kit.py --generate     # read the CoQ, write design_handoff/toolchain/house_kit_2026-10-07.css
    python3 tracker/house_kit.py --check        # the committed kit still matches the CoQ it was read from

Head of QC, 07.10.2026: *"make all pills — phenotype, chemotype, processing — in all CoQ and iCoA and
specifications be the same as they are on the CoQs, with that design and formatting"*, and *"the heading bars in
all documents need to be the same visuals and same effects in full"*.

Two things make a pill or a bar look the way it does:

* **What it says** — `selrow()` writes the pill row exactly as `coq_build.js` `section01` does: a ticked chip for
  the register's phenotype, chemotype and processing, the Hybrid chip carrying the split
  (`INDICA60 : SATIVA40`, the figures in gold) or, on a certificate not yet issued, the leaning (`· INDICA DOMINANT`), and the
  Macedonian only where the CoQ prints it (`Machine Машинска`). Until now the iCoA added `Хибрид` to the Hybrid chip
  and wrote the leaning as plain words, and the specification stacked its own chips in two rows.
* **How it is drawn** — the CoQ's look is the sum of the package's stylesheet and the desk's layers over it (the
  heading bar is the 01.10.2026 bevel, `build_v40.js` `SEC_LABEL_BEVEL_LAYER`). Rather than copy those rules and
  their cascade, `--generate` lays the CoQ out in Chromium and reads the **computed** style of every pill and bar
  element and pseudo-element, and writes those values as one stylesheet. On the iCoA and the specification it is
  scoped to the pill row and the heading bars and out-ranks their own rules, so each draws as the CoQ does. The
  iCoA's pill row was also zoomed to 106 %; the kit sets it to 100 %, as on the CoQ.

What the kit leaves alone: the spacing between sections (margins), the page geometry, and every other element.
The CoQ itself is the source and is not touched.
"""
import argparse
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
KIT = os.path.join(GAP, 'design_handoff', 'toolchain', 'house_kit_2026-10-07.css')
# the reference: a Tranche 3 CoQ whose Hybrid chip carries a leaning and whose processing chip carries Macedonian
REFERENCE = 'CoQ-PP_26-008_'
SCOPE = 'html:not(#_k1):not(#_k2):not(#_k3):not(#_k4) body .page '

ALL = ['display', 'align-items', 'justify-content', 'column-gap', 'row-gap', 'flex-wrap', 'white-space',
       'height', 'min-height', 'line-height', 'vertical-align', 'box-sizing',
       'font-family', 'font-size', 'font-weight', 'font-style', 'letter-spacing', 'text-transform', 'color',
       'opacity', 'background-color', 'background-image', 'background-size', 'background-position',
       'background-repeat', 'border-top', 'border-right', 'border-bottom', 'border-left', 'border-radius',
       'box-shadow', 'text-shadow', 'zoom', 'transform', 'filter', 'mix-blend-mode', 'mask-image',
       '-webkit-mask-image', 'overflow', 'text-decoration-line', 'padding-top', 'padding-right', 'padding-bottom',
       'padding-left', 'margin-left', 'margin-right']
PSEUDO = ALL + ['content', 'position', 'top', 'right', 'bottom', 'left', 'width', 'z-index']
# the row itself: how its chips are laid out, never its band or its height (the page around it is the document's)
ROW = ['display', 'align-items', 'justify-content', 'column-gap', 'row-gap', 'flex-wrap', 'white-space', 'zoom',
       'padding-left', 'padding-right']

PILLS = ['.selrow .grp', '.selrow .lk-lbl', '.selrow .lk-lbl .mk', '.selrow .chip-sel', '.selrow .chip-sel .bx',
         '.selrow .chip-sel .mk', '.selrow .chip-sel .ratio', '.selrow .chip-sel .ratio b', '.selrow .stack',
         '.selrow .chip-un', '.selrow .chip-un .bx']
BARS = ['.sec-label', '.sec-label .sec-no', '.sec-label .mk']

JS = """([items]) => { const out = [];
  for (const [sel, pseudo, props] of items) {
    const e = document.querySelector(sel);
    if (!e) { out.push([sel, pseudo, null]); continue; }
    const c = getComputedStyle(e, pseudo); const o = {};
    for (const p of props) o[p] = c.getPropertyValue(p);
    out.push([sel, pseudo, o]); }
  return out; }"""


# ---------------------------------------------------------------------- what the pills say (coq_build.js section01)
def chip(on, label, extra=''):
    return '<span class="chip-%s"><span class="bx">%s</span> %s%s</span>' % (
        'sel' if on else 'un', '☒' if on else '☐', label, extra)


GOLD = '<b style="color:#FFD98A;font-weight:800">%s</b>'


def selrow(pheno, dominance, chemo, proc, lean):
    """The pill row, as the CoQ prints it for the same register fields (`spc.pheno/dominance/chemo/proc`)."""
    ph = str(pheno or '').strip().upper()
    dom = str(dominance or '').strip()
    ratio = ''
    dm = re.match(r'^(INDICA|SATIVA)\s+(\d+)\s*:\s*(INDICA|SATIVA)\s+(\d+)$', dom, re.I)
    if dm:
        ratio = (' <span class="ratio" style="font-size:.86em;letter-spacing:.3px">' + dm.group(1).upper() +
                 GOLD % dm.group(2) + ' : ' + dm.group(3).upper() + GOLD % dm.group(4) + '</span>')
    dl = re.match(r'^(INDICA|SATIVA)-DOMINANT$', dom, re.I)
    if not dm and dl and lean:
        ratio = (' <span class="ratio" style="font-size:.86em;letter-spacing:.3px">· ' + dl.group(1).upper() +
                 ' ' + GOLD % 'DOMINANT' + '</span>')
    is_h, is_i, is_s = ph == 'HYBRID', ph == 'INDICA', ph == 'SATIVA'
    pheno_html = chip(is_h, 'Hybrid', ratio if is_h else '') + \
        '<span class="stack">' + chip(is_i, 'Indica') + chip(is_s, 'Sativa') + '</span>'
    chem = '<span class="stack">' + chip(chemo == 'THC', 'THC') + chip(chemo == 'CBD', 'CBD') + '</span>'
    p = str(proc or '').upper()
    prc = '<span class="stack">' + chip('MACHINE' in p, 'Machine <span class="mk">Машинска</span>') + \
        chip('HAND' in p, 'Hand') + '</span>'
    return ('<div class="selrow">\n'
            '    <span class="grp"><span class="lk-lbl">Phenotype <span class="mk">Фенотип</span></span>' + pheno_html + '</span>\n'
            '    <span class="grp"><span class="lk-lbl">Chemotype <span class="mk">Хемотип</span></span>' + chem + '</span>\n'
            '    <span class="grp"><span class="lk-lbl">Processing <span class="mk">Обработка</span></span>' + prc + '</span>\n'
            '  </div>')


def coq_selrow(html):
    """The pill row a CoQ page prints, as markup."""
    i = html.find('<div class="selrow">')
    j = html.find('</div>', i)
    if i < 0 or j < 0:
        raise SystemExit('no pill row on the page')
    return html[i:j + len('</div>')]


# ---------------------------------------------------------------------- how they are drawn
def reference():
    got = glob.glob(os.path.join(GAP, 'design_handoff', 'out', 'ISSUE_COQ', REFERENCE + '*.html'))
    if len(got) != 1:
        raise SystemExit('the reference CoQ %s* is not built (node design_handoff/toolchain/build_v40.js)' % REFERENCE)
    return got[0]


def computed(path):
    from playwright.sync_api import sync_playwright
    items = []
    for s in PILLS + BARS:
        items.append([s, None, ALL])
        items += [[s, '::before', PSEUDO], [s, '::after', PSEUDO]]
    items.append(['.selrow', None, ROW])
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        p = b.new_page()
        for pat in ('**/fonts.googleapis.com/**', '**/fonts.gstatic.com/**'):
            p.route(pat, lambda r: r.abort())
        p.goto('file://' + os.path.abspath(path))
        p.evaluate('() => document.fonts.ready')
        out = p.evaluate(JS, [items])
        b.close()
    missing = [s for s, ps, o in out if o is None and ps is None]
    if missing:
        raise SystemExit('the reference CoQ has no %s' % ', '.join(missing))
    return out


def css_of(out, source):
    lines = ['/* house kit — generated by tracker/house_kit.py --generate from %s.' % os.path.basename(source),
             '   The computed style of the CoQ pill row and heading bars; do not edit by hand. */']
    for sel, pseudo, o in out:
        if o is None:
            continue
        if pseudo and o.get('content') in ('none', 'normal', ''):
            lines.append('%s%s%s{content:none !important;display:none !important}' % (SCOPE, sel, pseudo))
            continue
        decl = ';'.join('%s:%s !important' % (k, v) for k, v in o.items() if v not in ('',))
        lines.append('%s%s%s{%s}' % (SCOPE, sel, pseudo or '', decl))
    return '\n'.join(lines) + '\n'


def kit_style():
    return '<style id="__house-kit">\n' + open(KIT, encoding='utf-8').read() + '</style>\n'


def apply(page, row):
    """The page with the CoQ's pill row in place of its own and the kit last in its body."""
    if page.count('<div class="selrow">') != 1:
        raise SystemExit('expected one pill row, found %d' % page.count('<div class="selrow">'))
    i = page.find('<div class="selrow">')
    j = page.find('</div>', i) + len('</div>')
    page = page[:i] + row + page[j:]
    if '</body>' not in page:
        raise SystemExit('no </body> to carry the kit')
    return page.replace('</body>', kit_style() + '</body>', 1)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--generate', action='store_true')
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args(argv[1:])
    src = reference()
    css = css_of(computed(src), src)
    if a.generate:
        with open(KIT, 'w', encoding='utf-8') as fh:
            fh.write(css)
        print('written %s (%d rules) from %s' % (os.path.relpath(KIT, GAP), css.count('{'), os.path.basename(src)))
    elif a.check:
        if open(KIT, encoding='utf-8').read() != css:
            raise SystemExit('house kit out of date: the CoQ draws its pills or bars differently — rerun --generate')
        print('house kit matches %s' % os.path.basename(src))
    else:
        ap.error('pass --generate or --check')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
