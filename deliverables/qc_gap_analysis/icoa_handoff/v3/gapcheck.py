#!/usr/bin/env python3
"""Report the vertical gap between every top-level block on the page."""
import glob, os, sys
from playwright.sync_api import sync_playwright
JS = r"""() => {
  const page = document.querySelector('.page');
  const pr = page.getBoundingClientRect();
  const out = []; let prev = null;
  page.querySelectorAll(':scope > *').forEach(e => {
    const b = e.getBoundingClientRect();
    const cs = getComputedStyle(e);
    const row = {cls: (e.className || e.tagName).slice(0, 26),
                 top: +(b.top - pr.top).toFixed(2), h: +b.height.toFixed(2),
                 mt: cs.marginTop, pt: cs.paddingTop, pb: cs.paddingBottom,
                 gap: prev === null ? null : +(b.top - prev).toFixed(2)};
    if (cs.position !== 'absolute') prev = b.bottom;
    out.push(row);
  });
  const hb = page.querySelector('.header-bar').getBoundingClientRect();
  const s1 = page.querySelector('.sec-label').getBoundingClientRect();
  return {rows: out, headerH: +hb.height.toFixed(2),
          headerToBand: +(s1.top - hb.bottom).toFixed(2)};
}"""
exe = (glob.glob('/opt/pw-browsers/chromium-*/chrome-linux/chrome') or [None])[0]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=exe)
    pg = b.new_page(viewport={'width': 900, 'height': 1200})
    for f in sys.argv[1:]:
        pg.goto('file://' + os.path.abspath(f)); pg.wait_for_timeout(150)
        m = pg.evaluate(JS)
        print('%s   header %.1f px tall, header->01 band gap %.2f px'
              % (os.path.basename(f)[:40], m['headerH'], m['headerToBand']))
        for r in m['rows'][:6]:
            print('   %-27s top %7.2f  h %6.2f  margin-top %-8s pad %s/%s%s'
                  % (r['cls'], r['top'], r['h'], r['mt'], r['pt'], r['pb'],
                     '   << GAP %.2f' % r['gap'] if r['gap'] and r['gap'] > 0.5 else ''))
    b.close()
