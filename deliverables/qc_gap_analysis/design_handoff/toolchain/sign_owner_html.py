#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lay a deposited signature on a certificate the Head of QC sends back, and set how big
the hands are.

    python3 design_handoff/toolchain/sign_owner_html.py IN.html [IN2.html ...] \
        --out DIR --height 65 --overflow 12

His own files come back edited — a wider grid, a renamed role, a different spelling of a
name — and the desk's printers do not build them. So this works on the file as it arrives
and changes only what was asked for:

* a box whose printed name has a deposit and no ink yet gets that hand, at the same tilt
  discipline the fleet uses: a signature pressed by hand does not sit at 90 degrees;
* every hand on the page is then sized by one rule appended last, so the two boxes match
  each other exactly — the deposits are all 200 px tall, so a shared `max-height` renders
  them at the same height whatever the width of the hand;
* `--overflow` is how far below the rule the pen rests. A signature that stays inside its
  box is a stamp, not a signature.

The name beneath the box is the key, never its position in the grid. Both spellings of the
Analyst's name are accepted because the two families print it differently — `Hristina Cekikj`
in the desk's generator, `Hristina Cekic` in the Head of QC's own design.
"""
import argparse
import base64
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(os.path.dirname(HERE))
STORE = os.path.join(GAP, 'bundles', '_signatures', 'print')

# The name printed beneath the box -> the deposit that belongs to it.
DEPOSITED = {
    'Hristina Cekikj': 'an_01.png',
    'Hristina Cekic': 'an_01.png',
    'Blagoj Nikolov': 'qc',
    'Jovana Romevska Cvetkovski': 'qa',
}


def hash32(key):
    x = 0
    for ch in key:
        x = (x * 131 + ord(ch)) & 0xFFFFFFFF
    return x


def deposit(who, key):
    """One deposit, chosen by the document's own code so a reprint is identical."""
    if who.endswith('.png'):
        return os.path.join(STORE, who)
    files = sorted(f for f in os.listdir(STORE) if f.startswith(who + '_') and f.endswith('.png'))
    if not files:
        raise SystemExit('no deposited signature for ' + who + ' in ' + STORE)
    return os.path.join(STORE, files[hash32(who + '|' + key) % len(files)])


def uri(path):
    with open(path, 'rb') as fh:
        return 'data:image/png;base64,' + base64.b64encode(fh.read()).decode('ascii')


# The box, its name, and whether ink is already on it. Data URIs are stripped before the
# structure is read: an embedded signature is tens of kilobytes and a lazy quantifier over it
# backtracks for minutes.
BOX = re.compile(
    r'(<div class="ap-sign">)([\s\S]{0,600}?)(</div>)([\s\S]{0,600}?)'
    r'(<div class="ap-name">\s*([^<]+?)\s*</div>)')


def strip_uris(html):
    return re.sub(r'(data:[a-z/+;=-]*base64,)[A-Za-z0-9+/=]+', r'\1-', html)


def sign(html, code, height, overflow):
    """Return (html, laid, already, skipped-names)."""
    laid, already, skipped = [], [], []
    bare = strip_uris(html)
    # Work on the stripped copy to find the boxes, then apply the same edits by name to the
    # real document: the offsets differ, so the edit is done by a second, anchored pass.
    for m in BOX.finditer(bare):
        name = m.group(6).strip()
        who = DEPOSITED.get(name)
        if not who:
            skipped.append(name)
            continue
        if 'ap-img' in m.group(2):
            already.append(name)
            continue
        src = deposit(who, code)
        x = hash32(who + '|' + code)
        tilt = ((((x >> 3) & 0xFFFF) / 0xFFFF) * 2 - 1) * 2.4
        img = ('<img class="ap-img handwritten" style="transform:translateX(-50%%) rotate(%.2fdeg)"'
               ' alt="" src="%s">' % (tilt, uri(src)))
        # anchor on this box's own name, which is unique on the page
        pat = re.compile(r'(<div class="ap-sign">)((?:(?!</div>)[\s\S]){0,600}?)'
                         r'(</div>[\s\S]{0,600}?<div class="ap-name">\s*' + re.escape(name) + r'\s*</div>)')
        new, n = pat.subn(lambda mm: mm.group(1) + img + mm.group(2) + mm.group(3), html, count=1)
        if not n:
            raise SystemExit('could not place the hand above ' + name)
        html = new
        laid.append((name, os.path.basename(src)))

    css = ('<style id="__sig-size">\n'
           'html body div.page .ap-img.handwritten{max-height:%dpx !important;'
           'max-width:98%% !important;bottom:-%dpx !important}\n'
           'html body div.page .approval-grid .ap-sign{overflow:visible !important}\n'
           '</style>' % (height, overflow))
    if '</body>' not in html:
        raise SystemExit('no </body> to append the sizing rule to')
    html = html.replace('</body>', css + '\n</body>', 1)
    return html, laid, already, skipped


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('files', nargs='+')
    ap.add_argument('--out', required=True)
    ap.add_argument('--height', type=int, default=65,
                    help='how tall every hand prints, in page px (the deposits are all 200 px tall, '
                         'so one cap makes them equal)')
    ap.add_argument('--overflow', type=int, default=12,
                    help='how far below the rule the pen rests, in page px')
    a = ap.parse_args(argv[1:])
    os.makedirs(a.out, exist_ok=True)
    for f in a.files:
        html = open(f, encoding='utf-8').read()
        m = re.search(r'iCoA-PP_26-\d{3}|CoQ-PP_26-\d{3}', os.path.basename(f)) or \
            re.search(r'iCoA-PP_26-\d{3}|CoQ-PP_26-\d{3}', strip_uris(html))
        code = m.group(0) if m else os.path.basename(f)
        out, laid, already, skipped = sign(html, code, a.height, a.overflow)
        # read the result back rather than trusting the write
        bare = strip_uris(out)
        boxes = BOX.findall(bare)
        inked = sum(1 for b in boxes if 'ap-img' in b[1])
        dest = os.path.join(a.out, os.path.basename(f))
        with open(dest, 'w', encoding='utf-8') as fh:
            fh.write(out)
        print('%-18s %d box(es), %d inked   laid: %s   already: %s   no deposit: %s'
              % (code, len(boxes), inked,
                 ', '.join('%s (%s)' % t for t in laid) or '—',
                 ', '.join(already) or '—', ', '.join(skipped) or '—'))
        if inked != len(boxes):
            print('   WARNING: %d box(es) still bare' % (len(boxes) - inked))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
