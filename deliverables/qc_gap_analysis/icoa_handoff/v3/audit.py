#!/usr/bin/env python3
"""HANDOFF §6 transparency audit + a type/size report, run on a real rendered page."""
import glob, os, sys
from playwright.sync_api import sync_playwright
AUDIT = r"""() => {
  const bad = [];
  document.querySelectorAll('.page *').forEach(e => {
    const s = getComputedStyle(e);
    ['backgroundImage','backgroundColor','boxShadow','textShadow','color',
     'borderTopColor','borderRightColor','borderBottomColor','borderLeftColor']
      .forEach(k => { if (/rgba\((?!0,\s*0,\s*0,\s*0\))/.test(s[k] || '')) bad.push(e.className + ' · ' + k); });
    if (+s.opacity < 1 && +s.opacity > 0) bad.push(e.className + ' · opacity');
    if (s.boxShadow !== 'none') bad.push(e.className + ' · boxShadow');
  });
  const sz = sel => { const e = document.querySelector(sel); return e ? getComputedStyle(e).fontSize : '-'; };
  return {bad: [...new Set(bad)],
    type: {'§03 tick': sz('.fnd .ck .ck-t'), '§03 gloss': sz('.fnd .ck .mk'),
           '§03 attr': sz('.fnd .fc-attr'), '§03 title': sz('.fnd .fa-t'),
           '§04 param': sz('table.rt tbody .p-name'), '§04 method': sz('table.rt tbody .p-method'),
           '§04 crit': sz('table.rt tbody .p-spec'), '§04 disp': sz('table.rt tbody .pp-res'),
           '§02 label': sz('.pp-grid .pp-l'), '§02 value': sz('.pp-grid .pp-v')},
    band: getComputedStyle(document.querySelector('.sec-label')).backgroundImage.slice(0, 150)};
}"""
def main(argv):
    files = argv[1:]
    exe = (glob.glob('/opt/pw-browsers/chromium-*/chrome-linux/chrome') or [None])[0]
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=exe); pg = b.new_page()
        for f in files:
            pg.goto('file://' + os.path.abspath(f)); pg.wait_for_timeout(120)
            m = pg.evaluate(AUDIT)
            print(os.path.basename(f))
            print('  transparency audit:', 'PASS — []' if not m['bad'] else 'FAIL ' + str(m['bad'][:6]))
            print('  type:', ' · '.join('%s %s' % (k, v) for k, v in m['type'].items()))
            print('  band:', m['band'][:130])
        b.close()
    return 0
raise SystemExit(main(sys.argv))
