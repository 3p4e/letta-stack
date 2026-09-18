#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One documentation bundle per production batch.

    certificate of quality  ->  internal certificate of analysis  ->  every external
    certificate it cites, oldest first by issue date

The certificate of quality and the internal certificate are OUR OWN latest print — never
a copy found in Drive (Head of QC, 18.09.2026). The external certificates are the
laboratories' own documents, fetched as issued.

Every page of every EXTERNAL certificate is marked with the certificate of quality it
belongs to, its issue date, the true-copy certification and the Head of QC's signature.
The internal certificate is NOT marked: it names its own certificate of quality on its
face, and the Head of QC excluded it.

NOTHING ON A LABORATORY PAGE IS COVERED. Measuring the corners of a real bundle showed
8 of 9 pages have no empty corner — these reports run edge to edge — so the stamp is not
laid over the page at all. The page is scaled down a little, anchored to the top, and the
stamp goes in the clean strip that opens at the foot. The original is complete and
untouched; it simply prints a few per cent smaller.
"""
import argparse, io, os, sys
import pymupdf
from PIL import Image, ImageDraw, ImageFont

DPI = 300; MM = DPI / 25.4; PT = 72 / 25.4
DEJA  = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
DEJAB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def F(pt, b=False): return ImageFont.truetype(DEJAB if b else DEJA, max(1, int(pt*DPI/72)))
INK=(27,58,107,255); INK_M=(27,58,107,180); GOLD=(160,124,48,150)

W_MM, H_MM = 40.0, 14.5          # variant D, one point up on every line (18.09.2026)
SIG_H, SIG_A, SIG_DX = 8.6, 0.55, 2.0
STRIP_MM = 19.0                  # the clean band opened at the foot of the page

# A rubber stamp is pressed by a hand, not laid by a machine. Each impression is turned a
# degree or two and set down a millimetre or so off true. The wobble is DERIVED from the
# document and the page number, so it is different on every page and identical on every
# rebuild — a bundle regenerates byte for byte, and no two pages look stamped by a robot.
TILT_DEG, JIT_MM = 2.6, 1.6


def _wobble(key):
    h = 0
    for ch in key:
        h = (h * 131 + ord(ch)) & 0xFFFFFFFF
    f = lambda n: ((h >> n) & 0xFFFF) / 0xFFFF * 2 - 1      # -1 .. +1
    return f(0) * TILT_DEG, f(11) * JIT_MM, f(21) * JIT_MM


def make_stamp(coq, issued, sig_path):
    im = Image.new('RGBA', (int(W_MM*MM), int(H_MM*MM)), (0,0,0,0)); d = ImageDraw.Draw(im)
    w, h = im.size; m = int(1.5*MM)
    d.rounded_rectangle([1,1,w-2,h-2], radius=int(1.0*MM), outline=INK, width=int(0.38*MM))
    k = int(0.9*MM)
    d.rounded_rectangle([k,k,w-k,h-k], radius=int(0.7*MM), outline=(27,58,107,95), width=int(0.13*MM))
    y = m*0.90
    d.text((m,y),'ВЕРОДОСТОЈНО НА ОРИГИНАЛОТ',font=F(5.6,True),fill=INK); y += 2.35*MM
    d.text((m,y),'TRUE COPY OF THE ORIGINAL',font=F(4.5),fill=INK_M);     y += 2.40*MM
    d.line([(m,y),(w-m,y)],fill=GOLD,width=int(0.17*MM));                 y += 0.85*MM
    d.text((m,y), coq, font=F(6.6,True), fill=INK)
    d.text((m,y+3.15*MM), 'издаден · issued  '+issued, font=F(4.6), fill=INK_M)
    s = Image.open(sig_path).convert('RGBA')
    hh = int(SIG_H*MM); s = s.resize((int(s.width*hh/s.height), hh), Image.LANCZOS)
    s.putalpha(s.getchannel('A').point(lambda v: int(v*SIG_A)))
    im.alpha_composite(s, (int(w-m-s.width-SIG_DX*MM), int(h-m*0.5-s.height)))
    return im


def stamped(src, coq, issued, sig_path, doc_code=''):
    """Every page of `src`, shrunk to open a clean strip, with the stamp in the strip."""
    base = make_stamp(coq, issued, sig_path)
    old = pymupdf.open(src); out = pymupdf.open()
    strip = STRIP_MM * PT
    for page in old:
        R = page.rect
        new = out.new_page(width=R.width, height=R.height)
        k = (R.height - strip) / R.height                      # anchored to the top
        box = pymupdf.Rect(R.x0 + (R.width - R.width*k)/2, R.y0,
                           R.x0 + (R.width + R.width*k)/2, R.y0 + R.height*k)
        new.show_pdf_page(box, old, page.number)
        tilt, dx, dy = _wobble('%s|%s|%d' % (coq, doc_code, page.number))
        turned = base.rotate(tilt, resample=Image.BICUBIC, expand=True)
        buf = io.BytesIO(); turned.save(buf, 'PNG'); png = buf.getvalue()
        w_pt = turned.width / MM * PT; h_pt = turned.height / MM * PT
        pad = 4.0 * PT
        x1 = R.x1 - pad + dx*PT; y1 = R.y1 - pad + dy*PT
        new.insert_image(pymupdf.Rect(x1-w_pt, y1-h_pt, x1, y1), stream=png, overlay=True)
    old.close()
    return out


def build(coq_pdf, icoa_pdf, externals, coq, issued, sig_path, dest):
    """externals: [(path, code, date)] already in chronological order."""
    book = pymupdf.open()
    for p in (coq_pdf, icoa_pdf):
        d = pymupdf.open(p); book.insert_pdf(d); d.close()
    marks = [('%s — certificate of quality' % coq, 1),
             ('internal certificate of analysis', book.page_count)]
    for path, code, date in externals:
        s = stamped(path, coq, issued, sig_path, code)
        marks.append(('%s · %s' % (code, date), book.page_count + 1))
        book.insert_pdf(s); s.close()
    book.set_toc([[1, t, p] for t, p in marks])
    book.save(dest, deflate=True)
    n = book.page_count; book.close()
    return n, marks


if __name__ == '__main__':
    G = '/home/user/letta-stack/deliverables/qc_gap_analysis'
    B = '/tmp/claude-0/bundle'
    coq, issued = 'CoQ-PP_26-111', '25.08.2026'
    ext = [(B+'/8-0011-26.pdf',  '8/0011/26',  '20.01.2026'),
           (B+'/81-2026.pdf',    '81/2026',    '02.02.2026'),
           (B+'/220-4-K-26.pdf', '220-4-К/26', '25.08.2026'),
           (B+'/220-4-M-26.pdf', '220-4-М/26', '11.09.2026')]
    dest = G + '/bundles/CJ082501-1_P060022_T2_batch_documentation.pdf'
    n, marks = build(G+'/design_handoff/pdf/pages/CoQ-PP_26-111_P060022_CJ_Cap_Junky_Grade_I.pdf',
                     G+'/icoa_handoff/v3/pdf/pages/iCoA-PP_26-127_P060022_CJ_Cap_Junky_Retest_1.pdf',
                     ext, coq, issued, '/tmp/claude-0/sig_page_01.png', dest)
    print('%s  —  %d pages, %.1f MiB' % (os.path.basename(dest), n, os.path.getsize(dest)/1048576))
    for t, p in marks: print('   p%-3d %s' % (p, t))
