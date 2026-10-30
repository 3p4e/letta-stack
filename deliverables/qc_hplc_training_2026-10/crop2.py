"""Cluster the raster images on a manual page into separate figures and crop each one."""
import os, sys, warnings
warnings.filterwarnings('ignore')
import pymupdf as m
PDF = os.environ.get('PP_SHIMADZU_PDF', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pdf')) + '/'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fig') + '/'
OFF = {'GS': 0, 'OPG': 14, 'SUG': 10, 'IM': 8, 'TH': 10}
docs = {k: m.open(PDF + k + '.pdf') for k in OFF}

def clusters(man, page):
    p = docs[man][page + OFF[man] - 1]
    bs = [m.Rect(i['bbox']) & p.rect for i in p.get_image_info()]
    bs = [b for b in bs if b.width > 40 and b.height > 30 and b.width * b.height > 4000]
    bs.sort(key=lambda b: b.y0)
    out = []
    for b in bs:
        for c in out:
            if b.y0 < c.y1 + 22 and b.y1 > c.y0 - 22:
                c |= b; break
        else:
            out.append(m.Rect(b))
    # second pass: merge clusters that now overlap
    merged = True
    while merged:
        merged = False
        for i in range(len(out)):
            for j in range(i + 1, len(out)):
                if out[i].y0 < out[j].y1 + 22 and out[i].y1 > out[j].y0 - 22:
                    out[i] |= out[j]; out.pop(j); merged = True; break
            if merged: break
    out = [c for c in out if c.height > 45]          # drop thin rules and chapter tabs
    return p, sorted(out, key=lambda c: c.y0)

def run(man, page):
    p, cs = clusters(man, page)
    names = []
    for i, c in enumerate(cs):
        r = m.Rect(c.x0 - 14, c.y0 - 8, c.x1 + 14, c.y1 + 8) & p.rect
        n = f'{man}_{page}_{i}'
        p.get_pixmap(matrix=m.Matrix(2.2, 2.2), clip=r).save(OUT + n + '.png')
        names.append(n)
    return names

if __name__ == '__main__':
    for tok in sys.argv[1:]:
        man, pages = tok.split(':')
        for pg in pages.split(','):
            print(man, pg, run(man, int(pg)))
