#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Measure the certificate's real layout: page overflow, section heights, wrapped cells.

    python3 measure.py [certificate.html ...]

The page is pinned to 794 x 1123 with the footer absolutely placed at the bottom, so the
number that matters is the gap between the last flow content and the footer's top edge.
A negative gap means the content has run under the footer.
"""
import glob
import json
import os
import sys

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
JS = r"""
() => {
  const page = document.querySelector('.page');
  const foot = document.querySelector('.footer');
  const r = e => e ? e.getBoundingClientRect() : null;
  const pr = r(page);
  // last element in normal flow before the absolutely-placed footer
  let lastBottom = 0, lastWhat = '';
  page.querySelectorAll(':scope > *').forEach(e => {
    if (e.classList.contains('footer')) return;
    const b = r(e);
    if (b.bottom > lastBottom) { lastBottom = b.bottom; lastWhat = e.className; }
  });
  const bands = [...document.querySelectorAll('.sec-label')].map(e => {
    const b = r(e); return {no: e.querySelector('.sec-no')?.textContent, top: b.top - pr.top,
                            h: +b.height.toFixed(2)};
  });
  const sec = {};
  bands.forEach((band, i) => {
    const next = bands[i + 1];
    sec[band.no] = +(((next ? next.top : lastBottom - pr.top) - band.top)).toFixed(2);
  });
  // §04 rows: one line each?
  const rows = [...document.querySelectorAll('table.rt tbody tr')].map(tr => {
    const b = r(tr);
    // Count real line boxes: a Range over the cell's contents reports one rect per line,
    // which is exact. Deriving lines from height/line-height misreads a bare <td> whose
    // height is the row height, not the text's.
    const cells = [...tr.children].map(td => {
      const rng = document.createRange(); rng.selectNodeContents(td);
      const rects = [...rng.getClientRects()].filter(x => x.width > 0.5 && x.height > 0.5)
                      .sort((a, b) => a.top - b.top);
      // Rect tops differ between a 9px lead and its 7.4px gloss ON THE SAME LINE, because a
      // rect starts at the ascent, not the baseline. Cluster by vertical OVERLAP instead:
      // two rects share a line when they overlap by more than half the shorter one.
      const lines = [];
      rects.forEach(x => {
        const hit = lines.find(l => {
          const ov = Math.min(l.bottom, x.bottom) - Math.max(l.top, x.top);
          return ov > 0.5 * Math.min(l.bottom - l.top, x.height);
        });
        if (hit) { hit.top = Math.min(hit.top, x.top); hit.bottom = Math.max(hit.bottom, x.bottom); }
        else lines.push({top: x.top, bottom: x.bottom});
      });
      return {txt: (td.textContent || '').trim().slice(0, 24), lines: Math.max(1, lines.length)};
    });
    return {h: +b.height.toFixed(2), maxLines: Math.max(...cells.map(c => c.lines)),
            wrapped: cells.filter(c => c.lines > 1).map(c => c.txt)};
  });
  // §03 tick boxes: any clipped label?
  const clipped = [...document.querySelectorAll('.ck-t')].filter(e =>
      e.scrollWidth > e.clientWidth + 1).map(e => e.textContent.trim().slice(0, 28));
  const boxes = document.querySelectorAll('.fnd .ck').length;
  const ticked = document.querySelectorAll('.fnd .ck-on').length;
  // dead space right of each option grid
  const dead = [...document.querySelectorAll('.fc-opts')].map(g => {
    const kids = [...g.children]; if (!kids.length) return 0;
    const right = Math.max(...kids.map(k => r(k).right));
    return +(r(g).right - right).toFixed(1);
  });
  return {pageH: +pr.height.toFixed(2), footTop: +(r(foot).top - pr.top).toFixed(2),
          contentBottom: +(lastBottom - pr.top).toFixed(2),
          clearance: +(r(foot).top - lastBottom).toFixed(2), lastWhat,
          overflow: +Math.max(0, page.scrollHeight - page.clientHeight).toFixed(2),
          sections: sec, rows, boxes, ticked, clipped, maxDead: Math.max(...dead)};
}
"""


def main(argv):
    files = argv[1:] or sorted(glob.glob(os.path.join(HERE, "ISSUE_iCOA", "INITIAL", "*.html")))[:1]
    exe = (glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome") or [None])[0]
    worst = None
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=exe)
        pg = b.new_page(viewport={"width": 900, "height": 1200})
        for f in files:
            pg.goto("file://" + os.path.abspath(f))
            pg.wait_for_timeout(120)
            m = pg.evaluate(JS)
            bad = [r for r in m["rows"] if r["maxLines"] > 1]
            flag = []
            if m["clearance"] < 0:
                flag.append("CONTENT UNDER FOOTER")
            if m["overflow"] > 0:
                flag.append("OVERFLOW %.1f" % m["overflow"])
            if bad:
                flag.append("§04 WRAPPED: " + "; ".join(sum((r["wrapped"] for r in bad), [])))
            if m["clipped"]:
                flag.append("CLIPPED: " + ", ".join(m["clipped"][:3]))
            print("%-52s clear %6.2f px  §01 %5.1f §02 %5.1f §03 %5.1f §04 %5.1f  "
                  "boxes %d/%d  deadmax %.1f %s"
                  % (os.path.basename(f)[:52], m["clearance"],
                     m["sections"].get("01", 0), m["sections"].get("02", 0),
                     m["sections"].get("03", 0), m["sections"].get("04", 0),
                     m["ticked"], m["boxes"], m["maxDead"],
                     "  ** " + " | ".join(flag) if flag else ""))
            if worst is None or m["clearance"] < worst[1]:
                worst = (os.path.basename(f), m["clearance"])
        b.close()
    if len(files) > 1:
        print("\ntightest page: %s at %.2f px clearance" % worst)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
