#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The printed page's own geometry and typography, measured in the browser that prints it.

    python3 measure_page.py IN.html OUT.json

Loads the certificate exactly as print_v40.py does — the same Chromium, the same subset
house fonts inlined, Google blocked — and returns, for every element on the page, its
rectangle in CSS pixels relative to the page and its computed style: font family, size,
weight, style, colour, background, alignment, borders. The Word emitter builds from these
measurements, not from the class names, so the Word page is laid out where the PDF is.
"""
import glob, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); GAP = os.path.dirname(os.path.dirname(HERE))
ROOT = os.path.dirname(os.path.dirname(GAP))
sys.path.insert(0, os.path.join(GAP, "live_instrument"))
sys.path.insert(0, os.path.join(ROOT, "ingestion", "coa_track", "letta-imb-coas"))
import house_fonts                                                       # noqa: E402
from print_coq_pdfs import FAMILIES, SUBSETS, page_text, BLOCK           # noqa: E402

JS = r"""
() => {
  const page = document.querySelector('.page') || document.body;
  const P = page.getBoundingClientRect();
  const keep = new Set(['font-family','font-size','font-weight','font-style','color','background-color',
    'background-image','text-align','letter-spacing','text-transform','line-height','border-bottom-width',
    'border-bottom-color','border-top-width','border-top-color','border-left-width','border-right-width',
    'border-left-color','border-right-color','padding-top','padding-bottom','padding-left','padding-right',
    'display','vertical-align','white-space','opacity']);
  let id = 0;
  function walk(el) {
    const cs = getComputedStyle(el);
    if (cs.display === 'none') return null;
    const r = el.getBoundingClientRect();
    const st = {}; for (const k of keep) st[k] = cs.getPropertyValue(k);
    const node = {id: id++, tag: el.tagName.toLowerCase(), cls: (el.getAttribute('class')||''),
      x: r.left - P.left, y: r.top - P.top, w: r.width, h: r.height, st: st, kids: [], texts: []};
    if (el.tagName === 'IMG') { node.src = el.getAttribute('src'); node.style = el.getAttribute('style')||''; }
    if (el.tagName === 'TD' || el.tagName === 'TH') { node.colspan = el.colSpan; node.rowspan = el.rowSpan; }
    for (const ch of el.childNodes) {
      if (ch.nodeType === 3) {
        const t = ch.textContent; if (!t.trim()) continue;
        const rg = document.createRange(); rg.selectNodeContents(ch);
        const rects = Array.from(rg.getClientRects()).map(q => [q.left-P.left, q.top-P.top, q.width, q.height]);
        node.texts.push({t: t, rects: rects});
      } else if (ch.nodeType === 1) {
        const k = walk(ch); if (k) node.kids.push(k);
      }
    }
    return node;
  }
  return {page: {w: P.width, h: P.height}, tree: walk(page)};
}
"""


def measure_many(paths, chromium=None):
    """{path: measurement} for many pages in ONE browser with ONE font sheet.

    Launching a browser and subsetting the faces per page is what made a page cost three
    seconds; the faces are the same for every page of a fleet, so they are cut once.
    """
    from playwright.sync_api import sync_playwright
    css, _r, _s = house_fonts.font_face_css(page_text(list(paths)), FAMILIES, SUBSETS)
    chromium = chromium or (glob.glob("/opt/pw-browsers/chromium*/chrome-linux/chrome") or [None])[0]
    out = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=chromium) if chromium else pw.chromium.launch()
        page = browser.new_page()
        for pat in BLOCK:
            page.route(pat, lambda route: route.abort())
        for html in paths:
            page.goto("file://" + os.path.abspath(html))
            page.add_style_tag(content=css)
            page.emulate_media(media="print")
            page.evaluate("() => document.fonts.ready")
            out[html] = page.evaluate(JS)
        browser.close()
    return out


def measure(html, chromium=None, css=None):
    from playwright.sync_api import sync_playwright
    if css is None:
        css, _r, _s = house_fonts.font_face_css(page_text([html]), FAMILIES, SUBSETS)
    chromium = chromium or (glob.glob("/opt/pw-browsers/chromium*/chrome-linux/chrome") or [None])[0]
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=chromium) if chromium else pw.chromium.launch()
        page = browser.new_page()
        for pat in BLOCK:
            page.route(pat, lambda route: route.abort())
        page.goto("file://" + os.path.abspath(html))
        page.add_style_tag(content=css)
        page.emulate_media(media="print")
        page.evaluate("() => document.fonts.ready")
        data = page.evaluate(JS)
        browser.close()
    return data


if __name__ == "__main__":
    d = measure(sys.argv[1])
    json.dump(d, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False)
    def count(n): return 1 + sum(count(k) for k in n["kids"])
    print("page %.1f x %.1f px, %d elements" % (d["page"]["w"], d["page"]["h"], count(d["tree"])))
