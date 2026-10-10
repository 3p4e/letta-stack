#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One documentation bundle per production batch, per testing round.

    certificate of quality  ->  internal certificate of analysis  ->  every external
    certificate that certificate of quality cites, oldest first by issue date

A lot gets a bundle for EACH round it has: one for the initial release certificate and
one for the retest certificate. They are different bundles — a different certificate of
quality on page 1, a different internal certificate behind it, and a different set of
external certificates, because the two rounds cite different documents. Every stamp in a
bundle bears THAT bundle's certificate code and issue date (Head of QC, 18.09.2026).

The certificate of quality and the internal certificate are OUR OWN latest print, never a
copy found in Drive. The external certificates are the laboratories' own documents.

THE PAGE IS NOT TOUCHED. Pages are copied verbatim — no scaling, no re-rendering — so a
page keeps its size, its orientation and its text layer. The microbiology certificate of
the first pilot is a landscape page carrying /Rotate=270, and re-rendering it turned it on
its side; copying it does not. The stamp is laid over the page as a layer on top. Overlap
is accepted by the Head of QC's ruling of 18.09.2026: anything under it is a footer line
or a page number, and the stamp says the document is checked, accredited and approved.

The signature rotates through all 19 of the Head of QC's iterations, and the impression is
turned and offset like a stamp pressed by hand — both DERIVED from the certificate code,
the document and the page number, so every page differs and every rebuild is identical.
"""
import argparse, glob, io, os, sys
import pymupdf
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
DPI = 300; MM = DPI / 25.4; PT = 72 / 25.4
DEJA  = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
DEJAB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def F(pt, b=False): return ImageFont.truetype(DEJAB if b else DEJA, max(1, int(pt*DPI/72)))
INK=(27,58,107,255); INK_M=(27,58,107,180); GOLD=(160,124,48,150)

W_MM, H_MM = 40.0, 14.5
SIG_H, SIG_A, SIG_DX = 8.6, 0.55, 2.0
TILT_DEG, JIT_MM, PAD_MM = 5.5, 3.0, 5.0
SIGS = sorted(glob.glob(os.path.join(HERE, '_signatures', 'qc_*.png')))


def _hash(key):
    h = 0
    for ch in key:
        h = (h * 131 + ord(ch)) & 0xFFFFFFFF
    return h


def _wobble(key):
    h = _hash(key)
    f = lambda n: ((h >> n) & 0xFFFF) / 0xFFFF * 2 - 1
    return f(0)*TILT_DEG, f(11)*JIT_MM, f(21)*JIT_MM, SIGS[(h >> 7) % len(SIGS)]


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


def mark(page, coq, issued, key):
    """Lay the stamp over this page, bottom-right of what the reader actually sees."""
    tilt, dx, dy, sig = _wobble(key)
    img = make_stamp(coq, issued, sig).rotate(tilt, resample=Image.BICUBIC, expand=True)
    buf = io.BytesIO(); img.save(buf, 'PNG'); png = buf.getvalue()
    w_pt = img.width/MM*PT; h_pt = img.height/MM*PT
    R = page.rect                                  # the VISIBLE box, rotation applied
    pad = PAD_MM*PT
    x1, y1 = R.x1 - pad + dx*PT, R.y1 - pad + dy*PT
    box = pymupdf.Rect(x1-w_pt, y1-h_pt, x1, y1)
    # insert_image works in UNROTATED space, so the box is derotated and the picture is
    # pre-turned by the page's own rotation — not against it. Turning it the other way
    # put the stamp upside down on the landscape microbiology certificate; this was
    # settled by rendering all four compensations and looking at them.
    page.insert_image(box * page.derotation_matrix, stream=png,
                      rotate=page.rotation % 360, overlay=True)


def build(coq_pdf, icoa_pdf, externals, coq, issued, dest, spec_pdf=None, spec_code=""):
    """externals: [(path, code, date)] in chronological order.

    spec_pdf is the intermediate bulk product specification for the strain and grade the
    certificate names — the last page of the bundle (Head of QC, 18.09.2026). Like the
    certificate of quality and the internal certificate it is OURS, so it carries no
    true-copy stamp: the stamp says a laboratory's document has been checked against its
    original, and there is no original elsewhere for a document we issue.
    """
    book = pymupdf.open()
    for p in (coq_pdf, icoa_pdf):
        d = pymupdf.open(p); book.insert_pdf(d); d.close()
    toc = [[1, '%s — certificate of quality' % coq, 1],
           [1, 'internal certificate of analysis', book.page_count]]
    for path, code, date in externals:
        first = book.page_count + 1
        d = pymupdf.open(path); book.insert_pdf(d); n = d.page_count; d.close()
        for i in range(n):
            mark(book[first-1+i], coq, issued, '%s|%s|%d' % (coq, code, i))
        toc.append([1, '%s · %s' % (code, date), first])
    if spec_pdf:
        first = book.page_count + 1
        d = pymupdf.open(spec_pdf); book.insert_pdf(d); d.close()
        toc.append([1, '%s — product specification' % (spec_code or 'QCSP 001'), first])
    book.set_toc(toc)
    book.save(dest, deflate=True, garbage=3)
    n = book.page_count; book.close()
    return n, toc


if __name__ == '__main__':
    G = os.path.dirname(HERE); B = '/tmp/claude-0/bundle'
    coq, issued = 'CoQ-PP_26-111', '25.08.2026'
    ext = [(B+'/8-0011-26.pdf',  '8/0011/26',  '20.01.2026'),
           (B+'/81-2026.pdf',    '81/2026',    '02.02.2026'),
           (B+'/220-4-K-26.pdf', '220-4-К/26', '25.08.2026'),
           (B+'/220-4-M-26.pdf', '220-4-М/26', '11.09.2026')]
    dest = HERE + '/CJ082501-1_P060022_T2_retest_batch_documentation.pdf'
    n, toc = build(G+'/design_handoff/pdf/pages/CoQ-PP_26-111_P060022_CJ_Cap_Junky_Grade_I.pdf',
                   G+'/icoa_handoff/v3/pdf/pages/iCoA-PP_26-127_P060022_CJ_Cap_Junky_Retest_1.pdf',
                   ext, coq, issued, dest)
    print('%s\n  %d pages, %.1f MiB, %d signature iterations in rotation'
          % (os.path.basename(dest), n, os.path.getsize(dest)/1048576, len(SIGS)))
    for _, t, p in toc: print('   p%-3d %s' % (p, t))
