#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A certificate's HTML as a real Word document — text, tables, pictures, all editable.

    python3 html_to_docx.py IN.html OUT.docx

The Head of QC, 18.09.2026: a Word document is for pinpoint edits and formatting in a
word processor; a page image pasted into one is a PDF wearing the wrong extension. So this
walks the certificate's own HTML — the same file the PDF is printed from — and writes each
part as the Word construct it is:

    header bar          a three-cell table: logo, titles, document code and date
    section labels      shaded heading paragraphs
    identity grids      borderless tables, one cell per label/value pair
    results, lab table  Word tables with header rows, merged group rows, sub-rows indented
    methods, checklist  the internal certificate's method cards and observation record
    approval block      one column per signatory, the signature as an inline picture
    footer              the page footer, and the company line

Both fleets share it: the certificate of quality (design_handoff/out) and the internal
certificate of analysis (icoa_handoff/v3/ISSUE_iCOA) are built from the same house layout
and the same class names. The fonts are named as the design names them — Montserrat,
Orbitron, Roboto Mono — and fall back on a machine that does not have them; the text is
the same either way, which is the point.

The subordinate Macedonian (`.mk`) is kept beside the English in a smaller grey run, as
the page shows it. `☒` and `☐` are text, and an editor can flip them.
"""
import base64
import io
import os
import re
import sys

from bs4 import BeautifulSoup, NavigableString, Tag
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm, Pt, RGBColor

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(os.path.dirname(HERE))
LOGO_SVG = os.path.join(GAP, "icoa_handoff", "v3", "ISSUE_iCOA", "_logo.svg")

NAVY = "1B3A5C"; GOLD = "C9A24A"; GREY = "5A7391"; PALE = "EEF3F8"; SUB = "F7F9FB"; INK = "1F2A37"
BASE = "Montserrat"; DISPLAY = "Orbitron"; MONO = "Roboto Mono"
PT = {"base": 7.5, "mk": 6.3, "small": 6.5, "title": 15, "code": 10, "name": 13, "sec": 8.5,
      "th": 7, "td": 7.3, "ap": 7}


# --------------------------------------------------------------------------- low-level
# Word tolerates a property element out of schema order; LibreOffice does not, and a file
# it will not open is not a deliverable. So every property is placed where the schema
# puts it, not appended.
PPR_ORDER = ("pStyle", "keepNext", "keepLines", "pageBreakBefore", "framePr", "widowControl", "numPr",
             "suppressLineNumbers", "pBdr", "shd", "tabs", "suppressAutoHyphens", "kinsoku", "wordWrap",
             "overflowPunct", "topLinePunct", "autoSpaceDE", "autoSpaceDN", "bidi", "adjustRightInd",
             "snapToGrid", "spacing", "ind", "contextualSpacing", "mirrorIndents", "suppressOverlap", "jc",
             "textDirection", "textAlignment", "textboxTightWrap", "outlineLvl", "divId", "cnfStyle", "rPr")
TCPR_ORDER = ("cnfStyle", "tcW", "gridSpan", "hMerge", "vMerge", "tcBorders", "shd", "noWrap", "tcMar",
              "textDirection", "tcFitText", "vAlign", "hideMark")
TBLPR_ORDER = ("tblStyle", "tblpPr", "tblOverlap", "bidiVisual", "tblStyleRowBandSize", "tblStyleColBandSize",
               "tblW", "jc", "tblCellSpacing", "tblInd", "tblBorders", "shd", "tblLayout", "tblCellMar", "tblLook")


def place(pr, el, order):
    """Insert el into pr at its schema position."""
    tag = el.tag.split("}")[1]
    idx = order.index(tag)
    for child in list(pr):
        ctag = child.tag.split("}")[1]
        if ctag in order and order.index(ctag) > idx:
            child.addprevious(el); return
    pr.append(el)


def shade(cell_or_par, hexfill):
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), hexfill)
    if hasattr(cell_or_par, "_tc"):
        place(cell_or_par._tc.get_or_add_tcPr(), shd, TCPR_ORDER)
    else:
        place(cell_or_par._p.get_or_add_pPr(), shd, PPR_ORDER)


def borders(table, sz=4, color="C6D4E2", inside=True):
    b = OxmlElement("w:tblBorders")
    for side in ("top", "left", "bottom", "right") + (("insideH", "insideV") if inside else ()):
        e = OxmlElement("w:" + side)
        e.set(qn("w:val"), "single"); e.set(qn("w:sz"), str(sz)); e.set(qn("w:space"), "0"); e.set(qn("w:color"), color)
        b.append(e)
    place(table._tbl.tblPr, b, TBLPR_ORDER)


def no_borders(table):
    b = OxmlElement("w:tblBorders")
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement("w:" + side); e.set(qn("w:val"), "nil"); b.append(e)
    place(table._tbl.tblPr, b, TBLPR_ORDER)


def cell_margins(table, mm=1.2):
    m = OxmlElement("w:tblCellMar")
    for side in ("top", "left", "bottom", "right"):
        e = OxmlElement("w:" + side); e.set(qn("w:w"), str(int(mm * 56.7))); e.set(qn("w:type"), "dxa"); m.append(e)
    place(table._tbl.tblPr, m, TBLPR_ORDER)


def bottom_rule(par, color=GOLD, sz=8):
    bdr = OxmlElement("w:pBdr")
    e = OxmlElement("w:bottom")
    e.set(qn("w:val"), "single"); e.set(qn("w:sz"), str(sz)); e.set(qn("w:space"), "1"); e.set(qn("w:color"), color)
    bdr.append(e)
    place(par._p.get_or_add_pPr(), bdr, PPR_ORDER)


def tight(par, before=0, after=0, line=1.05):
    f = par.paragraph_format
    f.space_before = Pt(before); f.space_after = Pt(after); f.line_spacing = line


def run(par, text, size=None, bold=None, italic=None, color=None, font=None, sup=False, sub=False, caps=False):
    r = par.add_run(text)
    r.font.size = Pt(size or PT["base"])
    r.font.name = font or BASE
    r._element.rPr.rFonts.set(qn("w:eastAsia"), font or BASE)
    if bold is not None: r.font.bold = bold
    if italic is not None: r.font.italic = italic
    if color: r.font.color.rgb = RGBColor.from_string(color)
    if sup: r.font.superscript = True
    if sub: r.font.subscript = True
    if caps: r.font.all_caps = True
    return r


def text_of(node):
    return re.sub(r"\s+", " ", node.get_text(" ", strip=True)) if node else ""


# --------------------------------------------------------------------------- inline
class Inline:
    """Write a node's inline content into a paragraph, keeping the runs the page draws."""

    def __init__(self, size=None, color=None, bold=None, mono_names=True):
        self.size = size or PT["base"]; self.color = color; self.bold = bold

    @staticmethod
    def space(par):
        """A space between two runs the page separates by layout rather than by text."""
        if par.runs and par.runs[-1].text and not par.runs[-1].text[-1].isspace():
            par.runs[-1].text = par.runs[-1].text + " "

    def write(self, par, node, size=None, color=None, bold=None, italic=None, font=None):
        size = size or self.size; color = color or self.color
        bold = self.bold if bold is None else bold
        if isinstance(node, NavigableString):
            t = str(node)
            t = re.sub(r"\s+", " ", t)
            if t:
                run(par, t, size=size, bold=bold, italic=italic, color=color, font=font)
            return
        if not isinstance(node, Tag):
            return
        cls = node.get("class") or []
        name = node.name
        if name == "br":
            par.add_run().add_break(WD_BREAK.LINE); return
        if name == "img":
            return
        if "mk" in cls:
            self.space(par)
            for ch in node.children:
                self.write(par, ch, size=PT["mk"], color=GREY, bold=False, italic=italic, font=font)
            return
        if "cert" in cls and par.runs and par.runs[-1].text.strip():
            par.add_run().add_break(WD_BREAK.LINE)         # one cited document per line
        if "pp-no" in cls:
            run(par, text_of(node) + "  ", size=size, bold=True, color=GOLD, font=DISPLAY); return
        if {"pot-tol", "pot-win", "lr-ac", "cd", "grp-ref", "ratio", "pp-name", "fa-ref", "pp-ref-m"} & set(cls):
            self.space(par)
        if "bisep" in cls:
            run(par, " | ", size=size, color="9EACBA"); return
        if name in ("b", "strong"):
            for ch in node.children: self.write(par, ch, size=size, color=color, bold=True, italic=italic, font=font)
            return
        if name in ("i", "em"):
            for ch in node.children: self.write(par, ch, size=size, color=color, bold=bold, italic=True, font=font)
            return
        if name == "sup":
            run(par, text_of(node), size=size, bold=bold, color=color, sup=True); return
        if name == "sub":
            run(par, text_of(node), size=size, bold=bold, color=color, sub=True); return
        if name == "small":
            par.add_run().add_break(WD_BREAK.LINE)
            for ch in node.children: self.write(par, ch, size=PT["small"], color=GREY, bold=False, font=font)
            return
        style = node.get("style") or ""
        if "Roboto Mono" in style:
            font = MONO
        if "uppercase" in style:
            for ch in node.children: self.write(par, ch, size=size, color=color, bold=True, italic=italic, font=font)
            return
        if "disp-batch" in cls:
            self.space(par); run(par, text_of(node) + "   ", size=size + 1, bold=True, color=NAVY, font=MONO); return
        if "bx" in cls:
            run(par, text_of(node) + " ", size=size, bold=True, color=color); return
        if "chip-sel" in cls or "chip-un" in cls:
            self.space(par)
            on = "chip-sel" in cls
            for ch in node.children:
                self.write(par, ch, size=size, color=(NAVY if on else "8C9BB0"), bold=on, font=font)
            run(par, "   ", size=size); return
        if "stack" in cls or "grp" in cls:
            for ch in node.children: self.write(par, ch, size=size, color=color, bold=bold, italic=italic, font=font)
            return
        for ch in node.children:
            self.write(par, ch, size=size, color=color, bold=bold, italic=italic, font=font)


# --------------------------------------------------------------------------- blocks
class Converter:
    def __init__(self, html_path, doc=None):
        self.html_path = html_path
        html = open(html_path, encoding="utf-8").read()
        self.soup = BeautifulSoup(html, "lxml")
        self.doc = doc or Document()
        s = self.doc.sections[0]
        s.page_width, s.page_height = Mm(210), Mm(297)
        s.left_margin = s.right_margin = Mm(12); s.top_margin = Mm(10); s.bottom_margin = Mm(12)
        st = self.doc.styles["Normal"]
        st.font.name = BASE; st.font.size = Pt(PT["base"]); st.font.color.rgb = RGBColor.from_string(INK)
        st.element.rPr.rFonts.set(qn("w:eastAsia"), BASE)
        st.paragraph_format.space_after = Pt(0); st.paragraph_format.space_before = Pt(0)
        self.inline = Inline()
        self.width = 186  # mm of text width

    # ---- pictures
    def picture_bytes(self, img):
        src = img.get("src") or ""
        m = re.match(r"data:image/(\w+(?:\+xml)?);base64,(.*)", src, flags=re.S)
        if m:
            raw = base64.b64decode(m.group(2))
            if m.group(1).startswith("svg"):
                return self.svg_png(raw)
            return raw
        p = os.path.join(os.path.dirname(self.html_path), src)
        if os.path.exists(p):
            raw = open(p, "rb").read()
            return self.svg_png(raw) if p.lower().endswith(".svg") else raw
        return None

    @staticmethod
    def svg_png(raw):
        import pymupdf
        d = pymupdf.open(stream=raw, filetype="svg")
        pix = d[0].get_pixmap(dpi=300, alpha=True)
        return pix.tobytes("png")

    # ---- helpers
    def par(self, before=0, after=0, align=None):
        p = self.doc.add_paragraph(); tight(p, before, after)
        if align: p.alignment = align
        return p

    def table(self, rows, cols, widths_mm=None, bordered=False):
        t = self.doc.add_table(rows=rows, cols=cols)
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        t.autofit = False
        (borders if bordered else no_borders)(t)
        cell_margins(t)
        if widths_mm:
            for i, w in enumerate(widths_mm):
                for r in t.rows:
                    r.cells[i].width = Mm(w)
        return t

    def cell_par(self, cell, first=True):
        p = cell.paragraphs[0] if first and cell.paragraphs and not cell.paragraphs[0].text else cell.add_paragraph()
        tight(p); return p

    # ---- header
    def header_bar(self, node):
        t = self.table(1, 3, [40, 106, 40])
        for c in t.rows[0].cells: shade(c, NAVY)
        img = node.find("img")
        if img is not None:
            data = self.picture_bytes(img)
            if data:
                p = self.cell_par(t.rows[0].cells[0]); p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                p.add_run().add_picture(io.BytesIO(data), width=Mm(34))
        c = t.rows[0].cells[1]
        for cls, size, bold, color, font in (("hb-title", PT["title"], True, "FFFFFF", DISPLAY), ("hb-mk-title", 8, False, "D7E3F0", BASE),
                                             ("hb-sub", 7.5, True, "FFFFFF", BASE), ("hb-mk-sub", PT["mk"], False, "D7E3F0", BASE)):
            e = node.find(class_=cls)
            if e is not None:
                p = self.cell_par(c, first=(cls == "hb-title")); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run(p, text_of(e), size=size, bold=bold, color=color, font=font)
        c = t.rows[0].cells[2]
        for cls, size, bold, color, font in (("hb-code-lbl", PT["mk"], False, "D7E3F0", BASE), ("hb-code", PT["code"], True, "FFFFFF", MONO),
                                             ("hb-issue", 7, False, "FFFFFF", BASE)):
            e = node.find(class_=cls)
            if e is not None:
                p = self.cell_par(c, first=(cls == "hb-code-lbl")); p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                self.inline.write(p, e, size=size, color=color, bold=bold, font=font)
        self.par(after=2)

    def sec_label(self, node):
        p = self.par(before=6, after=2); shade(p, NAVY)
        no = node.find(class_="sec-no")
        if no is not None:
            run(p, " " + text_of(no) + "   ", size=PT["sec"], bold=True, color=GOLD, font=DISPLAY); no.extract()
        self.inline.write(p, node, size=PT["sec"], color="FFFFFF", bold=True)

    def goldrule(self):
        p = self.par(after=2); bottom_rule(p)

    def pb_main(self, node):
        p = self.par(before=4, after=2)
        name = node.find(class_="pb-name")
        if name is not None:
            self.inline.write(p, name, size=PT["name"], color=NAVY, bold=True)
        pot = node.find(class_="pb-potency")
        if pot is not None:
            run(p, "     ", size=PT["name"])
            run(p, text_of(pot), size=PT["name"], bold=True, color=GOLD, font=DISPLAY)

    def label_grid(self, node):
        """selrow / gridrow / disp-row: one cell per label-value group."""
        items = [c for c in node.children if isinstance(c, Tag) and ({"lk", "grp"} & set(c.get("class") or []))]
        if len(items) < 2:
            p = self.par(before=3, after=2)
            for it in (items or [node]):
                lbl = it.find(class_="lk-lbl")
                if lbl is not None:
                    self.inline.write(p, lbl, size=PT["mk"], color=GREY, bold=True); lbl.extract()
                    run(p, "    ", size=PT["base"])
                self.inline.write(p, it, size=PT["base"] + 1, color=NAVY, bold=True)
            return
        n = len(items)
        t = self.table(1, n, [self.width / n] * n)
        for cell, it in zip(t.rows[0].cells, items):
            lbl = it.find(class_="lk-lbl")
            p = self.cell_par(cell)
            if lbl is not None:
                self.inline.write(p, lbl, size=PT["mk"], color=GREY, bold=True); lbl.extract()
                p = cell.add_paragraph(); tight(p)
            self.inline.write(p, it, size=PT["base"], color=INK, bold=True)

    def note(self, node, size=None, italic=False):
        p = self.par(before=2, after=2)
        self.inline.write(p, node, size=size or PT["small"], color=GREY, italic=italic)

    # ---- tables
    def html_table(self, node):
        rows = node.find_all("tr")
        ncols = max(sum(int(td.get("colspan", 1)) for td in tr.find_all(["td", "th"])) for tr in rows)
        cols = node.find("colgroup")
        widths = None
        if cols is not None:
            px = []
            for col in cols.find_all("col"):
                m = re.search(r"width:\s*(\d+)px", col.get("style") or "")
                px.append(int(m.group(1)) if m else None)
            if len(px) == ncols:
                known = sum(w for w in px if w); free = [i for i, w in enumerate(px) if not w]
                total_px = 700
                rest = max(total_px - known, 60)
                widths = [(w if w else rest / max(len(free), 1)) * self.width / total_px for w in px]
        t = self.table(len(rows), ncols, widths, bordered=True)
        for ri, tr in enumerate(rows):
            ci = 0
            head = tr.find("th") is not None
            rcls = tr.get("class") or []
            for td in tr.find_all(["td", "th"]):
                span = int(td.get("colspan", 1))
                cell = t.rows[ri].cells[ci]
                if span > 1:
                    cell = cell.merge(t.rows[ri].cells[ci + span - 1])
                p = self.cell_par(cell)
                if head:
                    shade(cell, NAVY)
                    self.inline.write(p, td, size=PT["th"], color="FFFFFF", bold=True)
                elif "row-group" in rcls:
                    shade(cell, PALE)
                    self.inline.write(p, td, size=PT["td"], color=NAVY, bold=True)
                else:
                    if "sub-row" in rcls and ci == 1:
                        p.paragraph_format.left_indent = Mm(3)
                    if "sub-row" in rcls: shade(cell, SUB)
                    res = "r-cell" in (td.get("class") or []) or "lr-mono" in (td.get("class") or [])
                    self.inline.write(p, td, size=PT["td"], color=INK, bold=res, font=(MONO if res else None))
                    if res: p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                ci += span
        self.par(after=1)

    # ---- internal certificate blocks
    def pp_cols(self, node):
        cards = node.find_all(class_="pp", recursive=False)
        for card in cards:
            head = card.find(class_="pp-head"); ref = card.find(class_="pp-ref")
            p = self.par(before=3, after=1)
            self.inline.write(p, head, size=PT["base"], color=NAVY, bold=True)
            if ref is not None:
                run(p, "   ", size=PT["base"]); run(p, text_of(ref), size=PT["mk"], color=GREY, italic=True)
            grid = card.find(class_="pp-grid")
            if grid is None: continue
            kids = [c for c in grid.children if isinstance(c, Tag)]
            pairs = [(kids[i], kids[i + 1]) for i in range(0, len(kids) - 1, 2)]
            t = self.table(len(pairs), 2, [28, self.width - 28])
            for (l, v), row in zip(pairs, t.rows):
                p = self.cell_par(row.cells[0]); self.inline.write(p, l, size=PT["mk"], color=GREY, bold=True)
                p = self.cell_par(row.cells[1]); self.inline.write(p, v, size=PT["small"], color=INK)

    def findings(self, node):
        for block in node.children:
            if not isinstance(block, Tag): continue
            cls = block.get("class") or []
            if "fa-head" in cls:
                p = self.par(before=4, after=1); shade(p, PALE)
                idx = block.find(class_="fa-idx"); t_ = block.find(class_="fa-t"); mk = block.find(class_="mk")
                ref = block.find(class_="fa-ref"); disp = block.find(class_="fa-disp")
                if idx is not None: run(p, " " + text_of(idx) + "   ", size=PT["sec"], bold=True, color=GOLD, font=DISPLAY)
                if t_ is not None: run(p, text_of(t_), size=PT["base"], bold=True, color=NAVY)
                if mk is not None: run(p, "  " + text_of(mk), size=PT["mk"], color=GREY)
                if ref is not None: run(p, "   " + text_of(ref), size=PT["mk"], color=GREY, italic=True)
                if disp is not None:
                    run(p, "      Result · Резултат:  ", size=PT["mk"], color=GREY, bold=True)
                    run(p, text_of(disp), size=PT["base"], bold=True, color=NAVY)
            elif "fa-grid" in cls:
                fcs = block.find_all(class_="fc", recursive=False)
                if not fcs: continue
                t = self.table(len(fcs), 2, [34, self.width - 34])
                for fc, row in zip(fcs, t.rows):
                    attr = fc.find(class_="fc-attr"); opts = fc.find(class_="fc-opts")
                    p = self.cell_par(row.cells[0]); self.inline.write(p, attr, size=PT["small"], color=NAVY, bold=True)
                    p = self.cell_par(row.cells[1])
                    for ck in (opts.find_all(class_="ck", recursive=False) if opts else []):
                        on = "ck-on" in (ck.get("class") or [])
                        self.inline.write(p, ck, size=PT["small"], color=(NAVY if on else "8C9BB0"), bold=on)
                        run(p, "    ", size=PT["small"])
            elif "fc-mass" in cls:
                p = self.par(before=2, after=1); self.inline.write(p, block, size=PT["small"], color=INK)
            else:
                p = self.par(); self.inline.write(p, block, size=PT["small"])

    # ---- approval
    def approval(self, node):
        cols = [c for c in node.children if isinstance(c, Tag) and c.name == "div"]
        n = len(cols) or 1
        t = self.table(1, n, [self.width / n] * n)
        for cell, col in zip(t.rows[0].cells, cols):
            role = col.find(class_="ap-role"); img = col.find("img"); title = col.find(class_="ap-title")
            name = col.find(class_="ap-name"); cred = col.find(class_="ap-cred"); date = col.find(class_="ap-date-row")
            p = self.cell_par(cell); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            if role is not None: self.inline.write(p, role, size=PT["ap"], color=GREY, bold=True)
            p = cell.add_paragraph(); tight(p, before=2); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            if img is not None:
                data = self.picture_bytes(img)
                if data:
                    m = re.search(r"height:\s*([\d.]+)px", img.get("style") or "")
                    h = float(m.group(1)) if m else 50.0
                    p.add_run().add_picture(io.BytesIO(data), height=Mm(h * 0.2646 * 1.15))
            p = cell.add_paragraph(); tight(p); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; bottom_rule(p, color=NAVY, sz=6)
            if title is not None:
                p = cell.add_paragraph(); tight(p, before=2); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                self.inline.write(p, title, size=PT["ap"], color=GREY, bold=True)
            if name is not None:
                p = cell.add_paragraph(); tight(p); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run(p, text_of(name), size=PT["base"] + 1.5, bold=True, color=NAVY)
            if cred is not None:
                p = cell.add_paragraph(); tight(p); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run(p, text_of(cred), size=PT["mk"], color=GREY, italic=True)
            if date is not None:
                p = cell.add_paragraph(); tight(p, before=2); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                lbl = date.find(class_="ap-date-label"); val = date.find(class_="ap-date-val")
                run(p, (text_of(lbl) + "  ") if lbl is not None else "", size=PT["mk"], color=GREY)
                run(p, text_of(val) if val is not None else "", size=PT["ap"], bold=True, color=INK, font=MONO)

    def footer(self, node):
        sec0 = self.doc.sections[0]
        if sec0.footer.paragraphs and sec0.footer.paragraphs[0].text.strip():
            return                             # a merged set shares one footer
        left = node.find(class_="foot-left")
        text = ""
        if left is not None:
            text = " ".join(str(x) if isinstance(x, NavigableString) else (" " if x.name == "br" else text_of(x)) for x in left.children)
            text = re.sub(r"\s+", " ", text).strip()
        sec = self.doc.sections[0]
        p = sec.footer.paragraphs[0]; tight(p); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run(p, text, size=PT["mk"], color=GREY)
        p = sec.footer.add_paragraph(); tight(p); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run(p, "Page ", size=PT["mk"], color=GREY)
        for tag, txt in (("begin", None), (None, "PAGE"), ("end", None)):
            r = p.add_run(); r.font.size = Pt(PT["mk"]); r.font.color.rgb = RGBColor.from_string(GREY)
            if tag:
                fc = OxmlElement("w:fldChar"); fc.set(qn("w:fldCharType"), tag); r._r.append(fc)
            else:
                it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = txt; r._r.append(it)
        run(p, " of ", size=PT["mk"], color=GREY)
        for tag, txt in (("begin", None), (None, "NUMPAGES"), ("end", None)):
            r = p.add_run(); r.font.size = Pt(PT["mk"]); r.font.color.rgb = RGBColor.from_string(GREY)
            if tag:
                fc = OxmlElement("w:fldChar"); fc.set(qn("w:fldCharType"), tag); r._r.append(fc)
            else:
                it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = txt; r._r.append(it)

    # ---- walk
    def convert(self, out_path=None):
        page = self.soup.find(class_="page") or self.soup.body
        for node in page.children:
            if not isinstance(node, Tag):
                continue
            cls = node.get("class") or []
            if "header-bar" in cls: self.header_bar(node)
            elif "sec-label" in cls: self.sec_label(node)
            elif "goldrule" in cls: self.goldrule()
            elif "pb-main" in cls: self.pb_main(node)
            elif {"selrow", "gridrow", "disp-row"} & set(cls): self.label_grid(node)
            elif "tbl-wrap" in cls:
                for tb in node.find_all("table", recursive=False): self.html_table(tb)
            elif node.name == "table": self.html_table(node)
            elif "pp-cols" in cls: self.pp_cols(node)
            elif "fnd" in cls: self.findings(node)
            elif "approval-grid" in cls: self.approval(node)
            elif "footer" in cls: self.footer(node)
            elif {"pot-note", "disp-note"} & set(cls): self.note(node)
            elif "goldrule" in cls: self.goldrule()
            else:
                if text_of(node):
                    p = self.par(); self.inline.write(p, node)
        core = self.doc.core_properties
        code = self.soup.find(class_="hb-code")
        core.title = text_of(code) if code is not None else os.path.basename(out_path)
        core.subject = text_of(self.soup.find(class_="hb-title")) + " — Purely Plant"
        core.comments = "Built from the certificate's own HTML, the same file the PDF is printed from; editable text and tables."
        if out_path:
            self.doc.save(out_path)
        return self.doc


def convert(html_path, out_path):
    Converter(html_path).convert(out_path)


def convert_many(html_paths, out_path, title=None):
    """Several certificates in one Word document, one per page, in the order given."""
    doc = None
    for i, h in enumerate(html_paths):
        if doc is not None:
            doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
        doc = Converter(h, doc).convert()
    if doc is None:
        raise SystemExit("nothing to convert")
    core = doc.core_properties
    core.title = title or os.path.splitext(os.path.basename(out_path))[0]
    core.comments = "%d certificates, each built from its own HTML; editable text and tables." % len(html_paths)
    doc.save(out_path)
    return len(html_paths)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    convert(sys.argv[1], sys.argv[2])
    print("wrote", sys.argv[2])
