#!/usr/bin/env python3
"""Sample the rendered 01/02/03/04 band pixel row by row and report the vertical steps.

A hard line is a large brightness jump between ADJACENT pixel rows. Rendering at device
scale 4 approximates print resolution, where the renderer resolves each gradient stop
instead of anti-aliasing it away.
"""
import glob, os, sys
from playwright.sync_api import sync_playwright
import pymupdf  # noqa - not used, kept for env parity
from PIL import Image

def profile(png, label):
    im = Image.open(png).convert('RGB')
    w, h = im.size
    x = int(w * 0.965)   # right of the band title, no glyphs in this column
    rows = [sum(im.getpixel((x, y))) / 3.0 for y in range(h)]
    steps = [(y, round(rows[y] - rows[y - 1], 1)) for y in range(1, h)]
    big = [s for s in steps if abs(s[1]) >= 8]
    print('  %-8s %d rows  max |step| %.1f  steps >=8: %d %s'
          % (label, h, max(abs(s[1]) for s in steps), len(big),
             '  at rows ' + ', '.join('%d(%+.0f)' % s for s in big[:8]) if big else ''))
    return len(big), max(abs(s[1]) for s in steps)

def main(argv):
    cert = os.path.abspath(argv[1])
    exe = (glob.glob('/opt/pw-browsers/chromium-*/chrome-linux/chrome') or [None])[0]
    out = []
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=exe)
        pg = b.new_page(viewport={'width': 900, 'height': 1200}, device_scale_factor=4)
        pg.goto('file://' + cert); pg.wait_for_timeout(150)
        el = pg.query_selector('.sec-label')
        png = '/tmp/band_%s.png' % argv[2]
        el.screenshot(path=png)
        out = profile(png, argv[2])
        b.close()
    return out

if __name__ == '__main__':
    main(sys.argv)
