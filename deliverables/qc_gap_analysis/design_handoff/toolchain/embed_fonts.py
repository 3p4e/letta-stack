#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The house fonts, embedded in a Word document so the page keeps its widths anywhere.

    python3 embed_fonts.py IN.docx            # rewrites in place

A Word file names its fonts; a machine without Montserrat, Orbitron and Roboto Mono
substitutes something wider or narrower, the lines re-wrap, and the page is no longer the
page the PDF shows. Embedding the faces closes that: Word (and LibreOffice) read them out
of the file and lay the text out in the face it was measured in.

Word matches an embedded face by NAME and knows only four styles per name — regular,
bold, italic, bold italic — so each weight the design uses is embedded under its own
family name: "Montserrat" (400/700 and the italics), "Montserrat Medium" (500),
"Montserrat SemiBold" (600), "Montserrat ExtraBold" (800), "Montserrat Black" (900), and
the same for Orbitron and Roboto Mono. html_to_docx.py names runs accordingly.

The faces are static instances cut from Google's variable fonts (fontTools instancer),
cut to the Latin and Cyrillic alphabets plus the document's own characters, obfuscated as OOXML requires (the first 32 bytes XORed with the font key), and written as
word/fonts/*.odttf with the fontTable, its relationships, the content types and the
embedTrueTypeFonts setting.
"""
import glob
import io
import os
import re
import shutil
import sys
import tempfile
import uuid
import zipfile

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.environ.get("PP_FONT_SRC", "/tmp/claude-0/fonts")
CACHE = os.path.join(HERE, ".fontcache_ttf")

# (family, weight, italic) -> the embedded family name and the style slot
STYLE = {400: ("", "regular"), 700: ("", "bold")}
WEIGHT_NAME = {300: "Light", 500: "Medium", 600: "SemiBold", 800: "ExtraBold", 900: "Black"}
VARIABLE = {("Montserrat", False): "Montserrat[wght].ttf", ("Montserrat", True): "Montserrat-Italic[wght].ttf",
            ("Roboto Mono", False): "RobotoMono[wght].ttf", ("Roboto Mono", True): "RobotoMono-Italic[wght].ttf",
            ("Orbitron", False): "Orbitron[wght].ttf"}
WEIGHTS = {"Montserrat": (300, 400, 500, 600, 700, 800, 900), "Roboto Mono": (400, 500, 600, 700),
           "Orbitron": (500, 600, 700, 800, 900)}


def face_name(family, weight, italic):
    """(embedded family name, bold?, italic?) for a measured family/weight/style."""
    w = int(weight) if str(weight).isdigit() else (700 if weight == "bold" else 400)
    ws = WEIGHTS.get(family)
    if ws:
        w = min(ws, key=lambda x: abs(x - w))
    if w in (400, 700):
        return family, w == 700, bool(italic)
    return "%s %s" % (family, WEIGHT_NAME.get(w, str(w))), False, bool(italic)


def instance(family, weight, italic):
    """A static TTF for one face, cut from the variable font and renamed for Word."""
    os.makedirs(CACHE, exist_ok=True)
    out = os.path.join(CACHE, "%s-%d%s.ttf" % (family.replace(" ", ""), weight, "-Italic" if italic else ""))
    if os.path.exists(out):
        return out
    # A family with no variable source mapped — Orbitron has no italic, for one — used to
    # join an EMPTY name onto SRC, which is the cache DIRECTORY. os.path.exists() says yes
    # to a directory, so the miss sailed past this guard and fontTools was handed a folder
    # to open. Ask for the name first, and require a file.
    name = VARIABLE.get((family, italic))
    src = os.path.join(SRC, name) if name else ""
    if not name or not os.path.isfile(src):
        if italic:
            return instance(family, weight, False)
        return None
    f = TTFont(src)
    if "fvar" in f:
        f = instancer.instantiateVariableFont(f, {"wght": weight}, inplace=False, overlap=True)
    fam, bold, ital = face_name(family, weight, italic)
    sub = ("Bold Italic" if bold and ital else "Bold" if bold else "Italic" if ital else "Regular")
    name = f["name"]
    for rec in list(name.names):
        if rec.nameID in (1, 2, 3, 4, 6, 16, 17):
            name.removeNames(nameID=rec.nameID)
    name.setName(fam, 1, 3, 1, 0x409); name.setName(sub, 2, 3, 1, 0x409)
    name.setName("%s %s" % (fam, sub), 4, 3, 1, 0x409)
    name.setName("%s-%s" % (fam.replace(" ", ""), sub.replace(" ", "")), 6, 3, 1, 0x409)
    name.setName("%s;%s" % (fam, sub), 3, 3, 1, 0x409)
    os2 = f["OS/2"]
    os2.usWeightClass = weight
    os2.fsSelection = (os2.fsSelection & ~0x261) | (0x20 if bold else 0) | (0x01 if ital else 0) | (0x40 if not (bold or ital) else 0)
    f["head"].macStyle = (0x01 if bold else 0) | (0x02 if ital else 0)
    f.save(out)
    return out


# What an embedded face carries. A whole Montserrat weight is 375 KB and a certificate
# names some twenty faces, which made each Word file 1.8 MB and pushed the Tranche 1
# archive over the 95 MiB it may be. The page itself uses a few hundred glyphs, so each
# face is cut down to the alphabets the desk writes in — Latin with its accented letters,
# Cyrillic, the punctuation and symbols a certificate prints — plus whatever else the
# document actually contains. Editing in either alphabet stays possible; a glyph outside
# this set would fall back to a substitute face, which is why the document's own
# characters are always added to it.
KEEP = (set(range(0x20, 0x7F)) | set(range(0xA0, 0x180)) | set(range(0x400, 0x460))
        | {0x2013, 0x2014, 0x2018, 0x2019, 0x201C, 0x201D, 0x2022, 0x2026, 0x2030, 0x20AC,
           0x2122, 0x2190, 0x2192, 0x2212, 0x2260, 0x2264, 0x2265, 0x25CF, 0x2713, 0x2717,
           # Greek Delta, superscripts and subscripts, the numero sign, the sum, the check boxes
           # and the fullwidth star the batch list uses
           0x0394, 0x2116, 0x2211, 0x2610, 0x2611, 0x2612, 0xFF0A}
        | set(range(0x2070, 0x2090)))
SUBSET_CACHE = os.path.join(CACHE, "subset")


def subset_face(path, extra=frozenset()):
    """The face at `path` cut to KEEP plus `extra`; cached when `extra` adds nothing."""
    need = set(extra) - KEEP
    if not need:
        os.makedirs(SUBSET_CACHE, exist_ok=True)
        out = os.path.join(SUBSET_CACHE, os.path.basename(path))
        if os.path.exists(out):
            return open(out, "rb").read()
    font = TTFont(path)
    opt = subset.Options()
    opt.layout_features = ["*"]
    opt.notdef_outline = True
    opt.name_IDs = ["*"]
    opt.name_legacy = True
    opt.hinting = False
    opt.desubroutinize = True
    sub = subset.Subsetter(opt)
    sub.populate(unicodes=sorted(KEEP | need))
    sub.subset(font)
    buf = io.BytesIO()
    font.save(buf)
    data = buf.getvalue()
    if not need:
        open(out, "wb").write(data)
    return data


def obfuscate(data, guid):
    """OOXML font obfuscation: XOR the first 32 bytes with the GUID's bytes, reversed."""
    key = bytes.fromhex(guid.replace("{", "").replace("}", "").replace("-", ""))[::-1]
    out = bytearray(data)
    for i in range(32):
        out[i] ^= key[i % 16]
    return bytes(out)


def faces_used(document_xml):
    """Every (family, bold, italic) a run in the document names."""
    used = set()
    for m in re.finditer(r"<w:r>(.*?)</w:r>", document_xml, flags=re.S):
        rpr = m.group(1)
        fm = re.search(r'w:rFonts [^>]*w:ascii="([^"]+)"', rpr)
        if not fm:
            continue
        bold = bool(re.search(r"<w:b/>|<w:b w:val=\"(?:1|true|on)\"", rpr))
        ital = bool(re.search(r"<w:i/>|<w:i w:val=\"(?:1|true|on)\"", rpr))
        used.add((fm.group(1), bold, ital))
    return used


def embed(docx_path):
    tmp = tempfile.mkdtemp(prefix="embed_")
    with zipfile.ZipFile(docx_path) as z:
        z.extractall(tmp)
    doc_xml = open(os.path.join(tmp, "word", "document.xml"), encoding="utf-8").read()
    used = faces_used(doc_xml)
    # every character the document sets, so no glyph is left out of its face
    chars = frozenset(ord(c) for t in re.findall(r"<w:t[^>]*>(.*?)</w:t>", doc_xml, flags=re.S)
                      for c in re.sub(r"&[a-z#0-9]+;", "&", t))
    by_name = {}
    for fam, bold, ital in used:
        by_name.setdefault(fam, set()).add((bold, ital))
    fonts_dir = os.path.join(tmp, "word", "fonts"); os.makedirs(fonts_dir, exist_ok=True)
    rels, table, ctypes_add = [], [], []
    n = 0
    for fam, styles in sorted(by_name.items()):
        base = fam
        weight = 400
        for w, nm in WEIGHT_NAME.items():
            if fam.endswith(" " + nm):
                base = fam[: -len(nm) - 1]; weight = w
        if base not in WEIGHTS:
            continue
        slots = []
        for bold, ital in sorted(styles):
            wv = 700 if bold else weight
            path = instance(base, wv, ital)
            if not path:
                continue
            n += 1
            guid = "{%s}" % str(uuid.uuid4()).upper()
            rid = "rIdFont%d" % n
            fn = "font%d.odttf" % n
            open(os.path.join(fonts_dir, fn), "wb").write(obfuscate(subset_face(path, chars), guid))
            rels.append('<Relationship Id="%s" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/font" Target="fonts/%s"/>' % (rid, fn))
            slot = "embedBoldItalic" if bold and ital else "embedBold" if bold else "embedItalic" if ital else "embedRegular"
            slots.append('<w:%s r:id="%s" w:fontKey="%s"/>' % (slot, rid, guid))
        if slots:
            table.append('<w:font w:name="%s"><w:charset w:val="00"/><w:family w:val="auto"/><w:pitch w:val="variable"/>%s</w:font>' % (fam, "".join(slots)))
    if not table:
        shutil.rmtree(tmp, ignore_errors=True)
        return 0
    ft = os.path.join(tmp, "word", "fontTable.xml")
    xml = open(ft, encoding="utf-8").read() if os.path.exists(ft) else \
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:fonts xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"></w:fonts>'
    if 'xmlns:r=' not in xml.split(">", 2)[1]:
        xml = xml.replace("<w:fonts ", '<w:fonts xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" ', 1)
    # drop any prior declaration of these names, then add ours
    for fam in by_name:
        xml = re.sub(r'<w:font w:name="%s">.*?</w:font>' % re.escape(fam), "", xml, flags=re.S)
    xml = xml.replace("</w:fonts>", "".join(table) + "</w:fonts>")
    open(ft, "w", encoding="utf-8").write(xml)
    relp = os.path.join(tmp, "word", "_rels", "fontTable.xml.rels")
    os.makedirs(os.path.dirname(relp), exist_ok=True)
    rx = open(relp, encoding="utf-8").read() if os.path.exists(relp) else \
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"></Relationships>'
    rx = rx.replace("</Relationships>", "".join(rels) + "</Relationships>")
    open(relp, "w", encoding="utf-8").write(rx)
    ct = os.path.join(tmp, "[Content_Types].xml")
    cx = open(ct, encoding="utf-8").read()
    if 'Extension="odttf"' not in cx:
        cx = cx.replace("</Types>", '<Default Extension="odttf" ContentType="application/vnd.openxmlformats-officedocument.obfuscatedFont"/></Types>')
    if "fontTable.xml" not in cx:
        cx = cx.replace("</Types>", '<Override PartName="/word/fontTable.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.fontTable+xml"/></Types>')
    open(ct, "w", encoding="utf-8").write(cx)
    drel = os.path.join(tmp, "word", "_rels", "document.xml.rels")
    dx = open(drel, encoding="utf-8").read()
    if "fontTable.xml" not in dx:
        dx = dx.replace("</Relationships>", '<Relationship Id="rIdFontTable" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/fontTable" Target="fontTable.xml"/></Relationships>')
        open(drel, "w", encoding="utf-8").write(dx)
    sp = os.path.join(tmp, "word", "settings.xml")
    sx = open(sp, encoding="utf-8").read()
    if "embedTrueTypeFonts" not in sx:
        sx = re.sub(r"(<w:settings[^>]*>)", r"\1<w:embedTrueTypeFonts/><w:embedSystemFonts/>", sx, count=1)
        open(sp, "w", encoding="utf-8").write(sx)
    out = docx_path + ".tmp"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        ct_path = os.path.join(tmp, "[Content_Types].xml")
        z.write(ct_path, "[Content_Types].xml")
        for root, _d, files in os.walk(tmp):
            for f in files:
                p = os.path.join(root, f)
                if p == ct_path:
                    continue
                z.write(p, os.path.relpath(p, tmp))
    os.replace(out, docx_path)
    shutil.rmtree(tmp, ignore_errors=True)
    return n


if __name__ == "__main__":
    print("faces embedded:", embed(sys.argv[1]))
