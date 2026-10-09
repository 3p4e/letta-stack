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

Later the same day (*"the pills are not consistent with the rest of the pills"*, *"use the same fonts for the same
class of text … in all depths on all documents"*, *"edit the signature block and make the content there be the same
formatting, size, font choices, colours … as it is on the certificates of quality"*) the kit took three more parts,
read the same way off the same CoQ:

* **DISP** — the iCoA's *Result vs Specification* row is the CoQ's section 04 row (`.disp-row`, same classes): its
  chips draw as the CoQ's. The iCoA's unticked chip carries Macedonian the CoQ's does not; it takes the CoQ's
  Macedonian face in the unticked chip's colour.
* **SIGN** — the signature block: every box, role, line, title, name, credential and date as the CoQ sets them, the
  block as tall as its boxes and set down at the foot of the page, as on the CoQ. Which box stands where is the builders' (QC Manager on
  the right: `build_v40.js`, `build_qcsp_imb.py`; the iCoA's base has it there already).
* **TYPE** — text of the same role, set as the CoQ sets it: face, size, weight, slant, spacing, case and colour.
  `TYPE` names each iCoA or specification element beside the CoQ element of the same role (the header, the
  section 01 labels and values, the table head, parameter, method, criterion and result, the notes, the footer). A
  text the CoQ has no counterpart for (the iCoA's subtotal rows, the specification's ± tolerance) keeps its own.

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
# the conformity row: the CoQ's section 04, the iCoA's "Result vs Specification"
DISP = ['.disp-row .grp', '.disp-row .lk-lbl', '.disp-row .lk-lbl .mk', '.disp-row .lk-lbl .bisep', '.disp-row .chip-sel',
        '.disp-row .chip-sel .bx', '.disp-row .chip-sel .mk', '.disp-row .chip-un', '.disp-row .chip-un .bx']

# the signature block: the grid's columns and its place at the foot of the page, then each box and its parts. Its
# bottom margin stays the document's own: the specification's footer is drawn over the page foot (position:absolute)
# and the template's margin keeps the block above it
GRID = ['display', 'grid-template-columns', 'column-gap', 'row-gap', 'padding-left', 'padding-right', 'padding-top',
        'padding-bottom', 'margin-left', 'margin-right', 'position', 'top', 'box-sizing', 'width', 'text-align',
        'justify-items', 'align-items']
SIGN_PROPS = [p for p in ALL if p not in ('height', 'min-height')] + [
    'flex-direction', 'position', 'margin-top', 'margin-bottom', 'text-align']
SIGN = [('.approval-grid > div', SIGN_PROPS), ('.approval-grid .ap-role', SIGN_PROPS),
        ('.approval-grid .ap-role .mk', SIGN_PROPS), ('.approval-grid .ap-sign', SIGN_PROPS + ['height']),
        ('.approval-grid .ap-line', SIGN_PROPS + ['height', 'width']), ('.approval-grid .ap-title', SIGN_PROPS),
        ('.approval-grid .ap-title .mk', SIGN_PROPS), ('.approval-grid .ap-name', SIGN_PROPS),
        ('.approval-grid .ap-cred', SIGN_PROPS), ('.approval-grid .ap-date-row', SIGN_PROPS),
        ('.approval-grid .ap-date-label', SIGN_PROPS), ('.approval-grid .ap-date-val', SIGN_PROPS)]

# text of the same role: (on the iCoA or specification, on the CoQ). A target starting "> " is a child of .page.
FONT = ['font-family', 'font-size', 'font-weight', 'font-style', 'letter-spacing', 'text-transform', 'color']
LBL, LBL_MK = '.gridrow .lk > .lk-lbl', '.gridrow .lk > .lk-lbl > .mk'
VAL, VAL_SM = '.gridrow .lk > .lk-val:not(.sm)', '.gridrow .lk > .lk-val.sm'
ATTR, ATTR_MK, ATTR_MONO = '.gridrow .lk > .attr-val', '.gridrow .attr-val > .mk', '.gridrow .attr-val > .attr-mono'
TH, TH_MK, TH_BISEP = 'table.results thead th', 'table.results thead th .mk', 'table.results thead th .bisep'
NO = 'table.results tbody tr:not(.row-group):not(.sub-row) > td:first-child'
NAME, NAME_MK, NAME_SUP = 'table.results tbody td > .p-name', 'table.results .p-name > .mk', 'table.results .p-name > sup'
SUB, SUB_MK = 'table.results tbody td > .p-sub', 'table.results .p-sub > .mk'
SUB_SUB, SUB_BISEP = 'table.results .p-sub > sub', 'table.results .p-sub > .bisep'
METH, METH_EQ = 'table.results tbody td > .p-method', 'table.results .p-method > .p-meth-eq'
SPEC, SPEC_MK = 'table.results tbody td > .p-spec', 'table.results .p-spec > .mk'
SPEC_SUP, SPEC_BISEP = 'table.results .p-spec > sup', 'table.results .p-spec > .bisep'
RES, RES_MK = 'table.results .r-cell > .r-val', 'table.results .r-val > .mk'
NUM, NUM_SEP = '.footer .foot-center-num', '.footer .foot-center-num > span'
TYPE = [
    # the header
    ('.header-bar .hb-title', '.header-bar .hb-title'), ('.header-bar .hb-mk-title', '.header-bar .hb-mk-title'),
    ('.header-bar .hb-sub', '.header-bar .hb-sub'), ('.header-bar .hb-mk-sub', '.header-bar .hb-mk-sub'),
    ('.header-bar .hb-code-lbl', '.header-bar .hb-code-lbl'), ('.header-bar .hb-code-lbl .mk', '.header-bar .hb-code-lbl .mk'),
    ('.header-bar .hb-code', '.header-bar .hb-code'), ('.header-bar .hb-issue', '.header-bar .hb-issue'),
    ('.header-bar .hb-issue b', '.header-bar .hb-issue b'),
    # section 01: the batch line (iCoA), the cultivar and potency (specification), the labels and values
    ('> .pb-main > .pb-name', '.pb-main > .pb-name'), ('> .pb-main > .pb-name > .bisep', '.pb-main > .pb-name > .bisep'),
    ('.product-banner .pb-main > .pb-name', '.pb-main > .pb-name > span:last-child'),
    ('.product-banner .pbp-val', '.pb-main .pbp-val > span'),
    ('.gridrow .lk > .lk-lbl', LBL), ('.gridrow .lk > .lk-lbl > .mk', LBL_MK),
    ('.gridrow .lk > .lk-val:not(.sm)', VAL), ('.gridrow .lk > .lk-val.sm', VAL_SM),
    ('.pb-code-item > .pcr-lbl', LBL), ('.pb-code-item > .pcr-lbl > .mk', LBL_MK), ('.pb-code-item > .pcr-val', VAL),
    ('.ig-cell > .ig-label', LBL), ('.ig-cell > .ig-label > .mk', LBL_MK), ('.ig-cell > .ig-val', ATTR),
    ('.ig-cell > .ig-val[style*="Roboto Mono"]', ATTR_MONO), ('.ig-cell > .ig-val > span:not(.mk)', ATTR_MONO),
    ('.ig-cell > .ig-val .mk', ATTR_MK),
    # the table head
    ('table.zr thead th', TH), ('table.zr thead th .mk', TH_MK),
    ('table.params thead th', TH), ('table.params thead th .mk', TH_MK), ('table.params thead th .bisep', TH_BISEP),
    # the rows: number, parameter, method, criterion, result
    ('table.zr .row-group .gn', NO), ('table.params tbody td:first-child', NO),
    ('table.zr .row-group .gt', NAME), ('table.zr .row-group .gt > .mk', NAME_MK),
    ('table.zr .p-name > .en', NAME), ('table.zr .p-name > .mk', NAME_MK),
    ('table.params tbody td > .p-name', NAME), ('table.params .p-name .mk', NAME_MK),
    ('table.params .p-name .p-tag', NAME_MK), ('table.params .p-name sup', NAME_SUP),
    ('table.params tbody td > .p-sub', SUB), ('table.params .p-sub .mk', SUB_MK), ('table.params .p-sub sub', SUB_SUB),
    ('table.params .p-sub .bisep', SUB_BISEP),
    ('table.zr td.pm', METH), ('table.zr tr.mi > td', METH), ('table.zr tr.mi .mi-l', LBL),
    ('table.zr tr.mi .mi-l > .mk', LBL_MK), ('table.zr tr.mi td > .mk', NAME_MK),
    ('table.params tbody td > .p-method', METH), ('table.params .p-method > .p-meth-eq', METH_EQ),
    ('table.zr td.ob', SPEC), ('table.zr td.ob > .mk', SPEC_MK),
    ('table.params tbody td > .p-spec', SPEC), ('table.params .p-spec .mk', SPEC_MK), ('table.params .p-spec sup', SPEC_SUP),
    ('table.params .p-spec .bisep', SPEC_BISEP),
    ('table.zr td.rv', RES), ('table.zr td.rv > .mk', RES_MK),
    # the note under the results, the footer
    ('> .pot-note', '.pot-note'), ('> .pot-note > .mk', '.pot-note > .mk'), ('> .pot-note > .bisep', '.pot-note > .bisep'),
    ('.footer .foot-left', '.footer .foot-left'), ('.footer .foot-center-num', NUM),
    ('.footer .foot-center-num > span', NUM_SEP, FONT + ['opacity']),
    ('.footer .foot-center-num > .fcn-cur', NUM, FONT + ['opacity']), ('.footer .foot-center-num > .fcn-tot', NUM, FONT + ['opacity']),
    # the iCoA's unticked "Does not conform" carries Macedonian; the CoQ's Macedonian face, the unticked chip's colour
    ('.disp-row .chip-un .mk', '.disp-row .chip-sel .mk'), ('.disp-row .chip-un .mk', '.disp-row .chip-un', ['color']),
]

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


def plan():
    """[target, CoQ element, pseudo, properties] for every rule of the kit, in the kit's order."""
    items = []
    for s in PILLS + BARS + DISP:
        items.append([s, s, None, ALL])
        items += [[s, s, '::before', PSEUDO], [s, s, '::after', PSEUDO]]
    items.append(['.selrow', '.selrow', None, ROW])
    # the CoQ's section 04 row stands on the page margin by its own margins, not by padding
    items.append(['.disp-row', '.disp-row', None, ROW + ['margin-left', 'margin-right']])
    items.append(['.approval-grid', '.approval-grid', None, GRID])
    items.append(['.approval-grid ~ .footer', '.approval-grid ~ .footer', None, ['margin-top']])
    for s, props in SIGN:
        items.append([s, s, None, props])
        items += [[s, s, '::before', PSEUDO], [s, s, '::after', PSEUDO]]
    for t in TYPE:
        items.append([t[0], t[1], None, t[2] if len(t) > 2 else FONT])
    return items


def computed(path):
    from playwright.sync_api import sync_playwright
    items = plan()
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        p = b.new_page()
        for pat in ('**/fonts.googleapis.com/**', '**/fonts.gstatic.com/**'):
            p.route(pat, lambda r: r.abort())
        p.goto('file://' + os.path.abspath(path))
        p.evaluate('() => document.fonts.ready')
        got = p.evaluate(JS, [[[src, ps, props] for _, src, ps, props in items]])
        b.close()
    missing = [src for (_, src, ps, _), (_, _, o) in zip(items, got) if o is None and ps is None]
    if missing:
        raise SystemExit('the reference CoQ has no %s' % ', '.join(missing))
    return [(t, ps, o) for (t, _, ps, _), (_, _, o) in zip(items, got)]


def css_of(out, source):
    lines = ['/* house kit — generated by tracker/house_kit.py --generate from %s.' % os.path.basename(source),
             '   The computed style of the CoQ pill row, heading bars, conformity row, signature block and text roles;',
             '   do not edit by hand. */']
    for sel, pseudo, o in out:
        if o is None:
            continue
        at = SCOPE[:-1] + ' > ' + sel[2:] if sel.startswith('> ') else SCOPE + sel
        if pseudo and o.get('content') in ('none', 'normal', ''):
            lines.append('%s%s{content:none !important;display:none !important}' % (at, pseudo))
            continue
        o = dict(o)
        cols = o.get('grid-template-columns', '').split()
        if len(cols) > 1 and len(set(cols)) == 1:
            # equal columns, as the CoQ declares them (1fr 1fr), not the pixels its page resolved them to
            o['grid-template-columns'] = 'repeat(%d,minmax(0,1fr))' % len(cols)
        if sel == '.approval-grid':
            o['width'] = 'auto'       # the block spans its page, whatever the page's own width rule
            o['margin-top'] = 'auto'  # and stands at the foot of the page, on the footer, as on the CoQ
            o['height'] = 'auto'      # as tall as its boxes (the specification template fixed it at 144 px)
        decl = ';'.join('%s:%s !important' % (k, v) for k, v in o.items() if v not in ('',))
        lines.append('%s%s{%s}' % (at, pseudo or '', decl))
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
