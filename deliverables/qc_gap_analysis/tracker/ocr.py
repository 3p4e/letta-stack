#!/usr/bin/env python3
"""OCR a scanned certificate: pages rendered at 300 DPI, tesseract with Macedonian + English."""
import os, subprocess, sys, tempfile
import pymupdf


def ocr_pdf(path, dpi=300, lang='mkd+eng'):
    doc = pymupdf.open(path)
    out = []
    with tempfile.TemporaryDirectory() as td:
        for i, page in enumerate(doc):
            png = os.path.join(td, f'p{i}.png')
            page.get_pixmap(dpi=dpi).save(png)
            r = subprocess.run(['tesseract', png, 'stdout', '-l', lang, '--psm', '6'],
                               capture_output=True, text=True, timeout=300)
            out.append(r.stdout)
    doc.close()
    return '\n'.join(out)


if __name__ == '__main__':
    print(ocr_pdf(sys.argv[1])[:2500])
