#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A certificate's page as a Word document laid out where the PDF lays it — and editable.

    python3 html_to_docx.py IN.html OUT.docx

The Head of QC, 18.09.2026: the Word document must be the same page as the HTML and the
PDF — not a picture of it, and not a re-flowed approximation of it either. So nothing here
is taken from class names or from the style sheets. The page is opened in the browser that
prints the PDF (measure_page.py: same Chromium, same subset house fonts, Google blocked),
and every element's rectangle and computed typography are read back. The Word document is
then built from those measurements:

    the page        A4, zero margins; 1 CSS px = 0.2646 mm
    every block     a table whose row height is the block's measured height and whose
                    column widths are its children's measured rectangles
    every text      a run in the measured family, size (px x 0.75 pt), weight, style,
                    colour, letter-spacing and transform, on a line at the measured height
    backgrounds     the measured colours on the cells that carry them
    rules           the measured bottom borders
    tables          the HTML table's own rows and cells, with measured widths and heights,
                    merged where the page merges them
    pictures        the logo and the signatures as inline pictures at their measured size

A Word table cell is editable text, so every figure on the page can be corrected in Word.
The page prints like the PDF because it is laid out from the PDF's own geometry.
"""
import base64
import io
import os
import re
import sys

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm, Pt, RGBColor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import measure_page as MP                                                # noqa: E402
import embed_fonts as EF                                                 # noqa: E402

CYR = re.compile(r"[\u0400-\u04FF\u0500-\u052F]+")

PX = 0.264583                      # mm per CSS pixel at 96 dpi
PT_PER_PX = 0.75
TW = lambda px: str(int(round(px * PX * 56.6929)))     # twentieths of a point


# --------------------------------------------------------------------------- OOXML helpers
PPR_ORDER = ("pStyle", "keepNext", "keepLines", "pageBreakBefore", "framePr", "widowControl", "numPr",
             "suppressLineNumbers", "pBdr", "shd", "tabs", "suppressAutoHyphens", "kinsoku", "wordWrap",
             "overflowPunct", "topLinePunct", "autoSpaceDE", "autoSpaceDN", "bidi", "adjustRightInd",
             "snapToGrid", "spacing", "ind", "contextualSpacing", "mirrorIndents", "suppressOverlap", "jc",
             "textDirection", "textAlignment", "textboxTightWrap", "outlineLvl", "divId", "cnfStyle", "rPr")
TCPR_ORDER = ("cnfStyle", "tcW", "gridSpan", "hMerge", "vMerge", "tcBorders", "shd", "noWrap", "tcMar",
              "textDirection", "tcFitText", "vAlign", "hideMark")
TBLPR_ORDER = ("tblStyle", "tblpPr", "tblOverlap", "bidiVisual", "tblStyleRowBandSize", "tblStyleColBandSize",
               "tblW", "jc", "tblCellSpacing", "tblInd", "tblBorders", "shd", "tblLayout", "tblCellMar", "tblLook")
TRPR_ORDER = ("cnfStyle", "divId", "gridBefore", "gridAfter", "wBefore", "wAfter", "cantSplit", "trHeight",
              "tblHeader", "tblCellSpacing", "jc", "hidden")


def place(pr, el, order):
    tag = el.tag.split("}")[1]
    idx = order.index(tag)
    for child in list(pr):
        if child.tag.split("}")[1] == tag:
            pr.remove(child)
    for child in list(pr):
        ctag = child.tag.split("}")[1]
        if ctag in order and order.index(ctag) > idx:
            child.addprevious(el); return
    pr.append(el)


def hexcolor(css):
    m = re.match(r"rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)", css or "")
    if not m:
        return None
    if m.group(4) is not None and float(m.group(4)) == 0:
        return None
    return "%02X%02X%02X" % (int(m.group(1)), int(m.group(2)), int(m.group(3)))


def fill_of(st):
    """The colour a box shows: its background-color, else the first non-white stop of its gradient."""
    c = hexcolor(st.get("background-color"))
    if c:
        return c
    for m in re.finditer(r"rgba?\([^)]*\)", st.get("background-image") or ""):
        h = hexcolor(m.group(0))
        if h and h not in ("FFFFFF", "FEFEFE", "FDFEFF", "FCFDFE"):
            return h
    return None


def px(v):
    try:
        return float(str(v or "0").replace("px", "") or 0)
    except ValueError:
        return 0.0


def shade(cell, hexfill):
    if not hexfill:
        return
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), hexfill)
    place(cell._tc.get_or_add_tcPr(), shd, TCPR_ORDER)


def cell_borders(cell, sides):
    b = OxmlElement("w:tcBorders")
    for side in ("top", "left", "bottom", "right"):
        e = OxmlElement("w:" + side)
        if side in sides:
            e.set(qn("w:val"), "single"); e.set(qn("w:sz"), str(sides[side][0]))
            e.set(qn("w:space"), "0"); e.set(qn("w:color"), sides[side][1])
        else:
            e.set(qn("w:val"), "nil")
        b.append(e)
    place(cell._tc.get_or_add_tcPr(), b, TCPR_ORDER)


def cell_margins(cell, top, left, bottom, right):
    m = OxmlElement("w:tcMar")
    for side, v in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        e = OxmlElement("w:" + side); e.set(qn("w:w"), TW(max(v, 0))); e.set(qn("w:type"), "dxa"); m.append(e)
    place(cell._tc.get_or_add_tcPr(), m, TCPR_ORDER)


def valign(cell, v):
    e = OxmlElement("w:vAlign"); e.set(qn("w:val"), v)
    place(cell._tc.get_or_add_tcPr(), e, TCPR_ORDER)


def table_setup(table, widths_px):
    pr = table._tbl.tblPr
    b = OxmlElement("w:tblBorders")
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement("w:" + side); e.set(qn("w:val"), "nil"); b.append(e)
    place(pr, b, TBLPR_ORDER)
    lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); place(pr, lay, TBLPR_ORDER)
    m = OxmlElement("w:tblCellMar")
    for side in ("top", "left", "bottom", "right"):
        e = OxmlElement("w:" + side); e.set(qn("w:w"), "0"); e.set(qn("w:type"), "dxa"); m.append(e)
    place(pr, m, TBLPR_ORDER)
    tw = OxmlElement("w:tblW"); tw.set(qn("w:w"), TW(sum(widths_px))); tw.set(qn("w:type"), "dxa"); place(pr, tw, TBLPR_ORDER)
    table.autofit = False
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    for i, gc in enumerate(table._tbl.tblGrid.findall(qn("w:gridCol"))):
        if i < len(widths_px):
            gc.set(qn("w:w"), TW(widths_px[i]))
    for r in table.rows:
        for i, c in enumerate(r.cells):
            if i < len(widths_px):
                c.width = Mm(widths_px[i] * PX)


def row_height(row, pxh):
    trPr = row._tr.get_or_add_trPr()
    h = OxmlElement("w:trHeight")
    h.set(qn("w:val"), TW(max(pxh, 0.5))); h.set(qn("w:hRule"), "exact")
    place(trPr, h, TRPR_ORDER)


def tight(par, line_px=None, align=None, before_px=0.0):
    sp = OxmlElement("w:spacing")
    sp.set(qn("w:before"), TW(before_px)); sp.set(qn("w:after"), "0")
    if line_px:
        sp.set(qn("w:line"), TW(line_px)); sp.set(qn("w:lineRule"), "exact")
    place(par._p.get_or_add_pPr(), sp, PPR_ORDER)
    if align:
        par.alignment = {"left": WD_ALIGN_PARAGRAPH.LEFT, "center": WD_ALIGN_PARAGRAPH.CENTER,
                         "right": WD_ALIGN_PARAGRAPH.RIGHT, "start": WD_ALIGN_PARAGRAPH.LEFT,
                         "end": WD_ALIGN_PARAGRAPH.RIGHT, "justify": WD_ALIGN_PARAGRAPH.JUSTIFY}.get(align, WD_ALIGN_PARAGRAPH.LEFT)
    return par


def family_of(css):
    fam = (css or "").split(",")[0].strip().strip("'\"")
    return fam or "Montserrat"


def add_run(par, text, st, shade_hex=None):
    """One run in the measured face. Orbitron has no Cyrillic, and the browser falls
    through to Montserrat glyph by glyph; so does this, run by run."""
    fam0 = family_of(st.get("font-family"))
    if fam0 == "Orbitron" and CYR.search(text):
        last = None
        for piece in re.split(r"([\u0400-\u04FF\u0500-\u052F]+)", text):
            if not piece:
                continue
            st2 = dict(st, **{"font-family": "Montserrat"}) if CYR.search(piece) else st
            last = add_run(par, piece, st2, shade_hex)
        return last
    r = par.add_run(text)
    w = st.get("font-weight", "400")
    ital = st.get("font-style", "normal") == "italic"
    fam, bold, ital = EF.face_name(fam0, w, ital)
    rpr = r._element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts"); rpr.insert(0, rf)
    for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rf.set(qn(a), fam)
    r.font.size = Pt(round(px(st.get("font-size", "10px")) * PT_PER_PX * 2) / 2)
    r.font.bold = bold
    r.font.italic = ital
    c = hexcolor(st.get("color"))
    if c:
        r.font.color.rgb = RGBColor.from_string(c)
    ls = st.get("letter-spacing", "normal")
    if ls.endswith("px") and abs(px(ls)) > 0.01:
        sp = OxmlElement("w:spacing"); sp.set(qn("w:val"), str(int(round(px(ls) * PT_PER_PX * 20)))); rpr.append(sp)
    if st.get("text-transform") == "uppercase":
        r.font.all_caps = True
    if shade_hex:
        sh = OxmlElement("w:shd"); sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), shade_hex)
        rpr.append(sh)
    return r


# --------------------------------------------------------------------------- the emitter
class Emitter:
    def __init__(self, html_path, doc=None, measured=None):
        self.html_path = html_path
        self.m = measured or MP.measure(html_path)
        self.doc = doc or Document()
        s = self.doc.sections[0]
        s.page_width, s.page_height = Mm(210), Mm(297)
        s.left_margin = s.right_margin = s.top_margin = s.bottom_margin = Mm(0)
        s.header_distance = s.footer_distance = Mm(0)
        st = self.doc.styles["Normal"]
        st.font.name = "Montserrat"; st.font.size = Pt(7)
        st.paragraph_format.space_after = Pt(0); st.paragraph_format.space_before = Pt(0)
        self.W = self.m["page"]["w"]
        self.cursor_y = 0.0

    # ---- pictures
    def picture(self, node):
        src = node.get("src") or ""
        mm = re.match(r"data:image/(\w+(?:\+xml)?);base64,(.*)", src, flags=re.S)
        if mm:
            raw = base64.b64decode(mm.group(2))
            return self.svg_png(raw) if mm.group(1).startswith("svg") else raw
        p = os.path.join(os.path.dirname(self.html_path), src)
        if os.path.exists(p):
            raw = open(p, "rb").read()
            return self.svg_png(raw) if p.lower().endswith(".svg") else raw
        return None

    @staticmethod
    def svg_png(raw):
        import pymupdf
        d = pymupdf.open(stream=raw, filetype="svg")
        return d[0].get_pixmap(dpi=300, alpha=True).tobytes("png")

    # ---- text lines under a node, grouped by baseline
    def lines(self, node):
        items = []

        def walk(n, pill=None):
            if n["tag"] == "img":
                items.append(("img", n)); return
            # a chip is a coloured pill: its fill travels with its text as run shading
            here = pill
            if any(c in ("chip-sel", "chip-un", "disp-batch") for c in n["cls"].split()):
                here = fill_of(n["st"]) or pill
            for t in n["texts"]:
                for (x, y, w, h) in t["rects"]:
                    items.append(("txt", (t["t"], dict(n["st"], _pill=here), x, y, w, h)))
            for k in n["kids"]:
                walk(k, here)
        walk(node)
        txt = sorted((i[1] for i in items if i[0] == "txt"), key=lambda t: (t[3], t[2]))
        imgs = [i[1] for i in items if i[0] == "img"]
        lines = []
        for t in txt:
            if lines and abs(lines[-1][0] - t[3]) < max(2.5, t[5] * 0.5):
                lines[-1][1].append(t)
            else:
                lines.append([t[3], [t]])
        for ln in lines:
            ln[1].sort(key=lambda t: t[2])
        return lines, imgs

    def fill_cell(self, cell, node, top_px, left_px, align=None):
        """Write node's text lines into the cell at their measured sizes and positions."""
        lines, imgs = self.lines(node)
        first = not cell.paragraphs[0].runs
        st_align = align or node["st"].get("text-align", "left")
        prev_bottom = top_px
        for im in imgs:
            data = self.picture(im)
            if not data:
                continue
            p = cell.paragraphs[0] if first else cell.add_paragraph()
            first = False
            gap = max(0.0, im["y"] - prev_bottom)
            tight(p, line_px=im["h"], align=st_align, before_px=gap)
            pic = p.add_run().add_picture(io.BytesIO(data), width=Mm(im["w"] * PX), height=Mm(im["h"] * PX))
            m = re.search(r"rotate\((-?[\d.]+)deg\)", im.get("style") or "")
            if m:
                xfrm = pic._inline.graphic.graphicData.pic.spPr.find(qn("a:xfrm"))
                if xfrm is not None:
                    xfrm.set("rot", str(int(round(float(m.group(1)) * 60000))))
            prev_bottom = im["y"] + im["h"]
        for y, parts in lines:
            p = cell.paragraphs[0] if first else cell.add_paragraph()
            first = False
            hmax = max(t[5] for t in parts)
            gap = y - prev_bottom
            gap = gap if gap > 2.0 else 0.0
            tight(p, line_px=hmax, align=st_align, before_px=gap)
            x0 = parts[0][2]
            if st_align in ("left", "start") and x0 - left_px > 1.0:
                p.paragraph_format.left_indent = Mm((x0 - left_px) * PX)
            # parts the page separates horizontally sit at tab stops set to their measured x
            last_x1 = None
            tabs = []
            for (text, st, x, yy, w, h) in parts:
                pill = st.get("_pill")
                if last_x1 is not None and x - last_x1 > 2.0:
                    # a tab stop only where there is room for it: Word's advance widths
                    # differ from the browser's by a percent or two, and a stop the text
                    # has already passed throws the rest of the line onto the next one
                    if st_align in ("left", "start") and x - last_x1 > 7.0:
                        tabs.append(x - left_px)
                        add_run(p, "\t", st)
                    else:
                        add_run(p, " ", st)
                add_run(p, re.sub(r"\s+", " ", text), st, shade_hex=pill)
                last_x1 = x + w
            if tabs:
                tb = OxmlElement("w:tabs")
                for tx in tabs:
                    e = OxmlElement("w:tab"); e.set(qn("w:val"), "left"); e.set(qn("w:pos"), TW(tx)); tb.append(e)
                place(p._p.get_or_add_pPr(), tb, PPR_ORDER)
            prev_bottom = y + hmax

    # ---- blocks
    @staticmethod
    def extent(node):
        """(x0, x1) of everything drawn under node: its box and every text and picture."""
        x0, x1 = node["x"], node["x"] + node["w"]

        def walk(n):
            nonlocal x0, x1
            for t in n["texts"]:
                for (x, y, w, h) in t["rects"]:
                    x0 = min(x0, x); x1 = max(x1, x + w)
            if n["tag"] == "img":
                x0 = min(x0, n["x"]); x1 = max(x1, n["x"] + n["w"])
            for k in n["kids"]:
                walk(k)
        walk(node)
        return x0, x1

    def columns(self, kids):
        """Children side by side become columns; a column is as wide as the ink it holds,
        because the page lets a value overflow its grid box and Word would wrap it."""
        ks = sorted(kids, key=lambda k: k["x"])
        cols = []
        for k in ks:
            kx0, kx1 = self.extent(k)
            kx1 += 2.5 + (kx1 - kx0) * 0.02                # slack: Word's advance widths round differently
            if cols and kx0 < cols[-1][0] + cols[-1][1] - 0.5:
                cx, cw, mem = cols[-1]
                nx = min(cx, kx0); nw = max(cx + cw, kx1) - nx
                cols[-1] = (nx, nw, mem + [k])
            else:
                cols.append((kx0, kx1 - kx0, [k]))
        # the last column may reach past the block's right edge; clamp it
        return cols

    # ---- the recursive layout: rows for what stacks, columns for what sits side by side
    @staticmethod
    def visible(node):
        return [k for k in node["kids"] if k["w"] > 0.5 and k["h"] > 0.5]

    @staticmethod
    def stacked(kids):
        """True when the children follow one another down the page."""
        ks = sorted(kids, key=lambda k: k["y"])
        for a, b in zip(ks, ks[1:]):
            if b["y"] < a["y"] + a["h"] - 1.5:
                return False
        return len(ks) > 1

    def one_cell_table(self, container, width_px, height_px):
        t = container.add_table(rows=1, cols=1)
        table_setup(t, [width_px])
        row_height(t.rows[0], height_px)
        return t

    def block(self, node, container=None, width_px=None):
        """node into container (the document or a cell) as tables of its measured shape."""
        container = container or self.doc
        width_px = width_px or node["w"]
        kids = self.visible(node)
        bg = fill_of(node["st"])
        # a leaf: text (and pictures) laid on lines at their measured heights
        if not kids or node["texts"]:
            t = self.one_cell_table(container, width_px, node["h"])
            c = t.rows[0].cells[0]
            shade(c, bg)
            pl = px(node["st"].get("padding-left"))
            cell_margins(c, 0, pl, 0, 0)
            sides = {}
            for side in ("top", "left", "right", "bottom"):
                b = self.border_px(node, side)
                if b:
                    sides[side] = b
            if sides:
                cell_borders(c, sides)
            if node["texts"] or kids or node["tag"] == "img":
                self.fill_cell(c, node, node["y"], self.extent(node)[0] + pl)
            else:
                tight(c.paragraphs[0], line_px=1)
            return
        # children down the page: one row each, with the gaps between them kept
        if self.stacked(kids):
            t = container.add_table(rows=1, cols=1)
            table_setup(t, [width_px]); row_height(t.rows[0], node["h"])
            c = t.rows[0].cells[0]
            shade(c, bg)
            sides = {}
            for side in ("top", "left", "right", "bottom"):
                b = self.border_px(node, side)
                if b:
                    sides[side] = b
            if sides:
                cell_borders(c, sides)
            tight(c.paragraphs[0], line_px=1)
            y = node["y"]
            for k in sorted(kids, key=lambda k: k["y"]):
                if k["y"] - y > 1.0:
                    sp = self.one_cell_table(c, width_px, k["y"] - y); tight(sp.rows[0].cells[0].paragraphs[0], line_px=1)
                self.block(k, c, width_px)
                y = k["y"] + k["h"]
            return
        # children side by side: columns as wide as their ink
        cols = self.columns(kids)
        widths, cells, x = [], [], node["x"]
        # a value the page lets overflow its grid box may reach past the block's edge;
        # the column follows it, as far as the page allows
        right = min(max(node["x"] + node["w"], max(c[0] + c[1] for c in cols)), self.W)
        for (cx, cw, members) in cols:
            cx = max(cx, x); cw = min(cw, right - cx)
            if cw <= 0.5:
                continue
            if cx - x > 0.5:
                widths.append(cx - x); cells.append(None)
            widths.append(cw); cells.append(members)
            x = cx + cw
        if right - x > 0.5:
            widths.append(right - x); cells.append(None)
        t = container.add_table(rows=1, cols=len(widths))
        table_setup(t, widths)
        row_height(t.rows[0], node["h"])
        node_bottom = self.border_px(node, "bottom")
        if node["st"].get("white-space") == "nowrap":
            pass
        for i, members in enumerate(cells):
            c = t.rows[0].cells[i]
            shade(c, bg)
            sides = {"bottom": node_bottom} if node_bottom else {}
            if members is None:
                tight(c.paragraphs[0], line_px=1)
                if sides:
                    cell_borders(c, sides)
                continue
            if sides:
                cell_borders(c, sides)
            tight(c.paragraphs[0], line_px=1)
            if len(members) == 1:
                m0 = members[0]
                if m0["y"] - node["y"] > 1.0:
                    sp = self.one_cell_table(c, widths[i], m0["y"] - node["y"]); tight(sp.rows[0].cells[0].paragraphs[0], line_px=1)
                self.block(m0, c, widths[i])
            else:
                y = node["y"]
                for k in sorted(members, key=lambda k: k["y"]):
                    if k["y"] - y > 1.0:
                        sp = self.one_cell_table(c, widths[i], k["y"] - y); tight(sp.rows[0].cells[0].paragraphs[0], line_px=1)
                    self.block(k, c, widths[i])
                    y = k["y"] + k["h"]

    def border_px(self, node, side):
        st = node["st"]
        w = px(st.get("border-%s-width" % side))
        col = hexcolor(st.get("border-%s-color" % side))
        if w > 0.3 and col:
            return (max(2, int(round(w * 6))), col)
        return None

    def html_table(self, tnode):
        rows = []

        def find_rows(n):
            if n["tag"] == "tr":
                rows.append(n); return
            for k in n["kids"]:
                find_rows(k)
        find_rows(tnode)
        if not rows:
            return
        edges = set()
        for r in rows:
            for c in r["kids"]:
                if c["tag"] in ("td", "th"):
                    edges.add(round(c["x"], 1)); edges.add(round(c["x"] + c["w"], 1))
        edges = sorted(edges)
        widths = [edges[i + 1] - edges[i] for i in range(len(edges) - 1)]
        t = self.doc.add_table(rows=len(rows), cols=len(widths))
        table_setup(t, widths)
        for ri, r in enumerate(rows):
            row_height(t.rows[ri], r["h"])
            rbg = fill_of(r["st"])
            for c in r["kids"]:
                if c["tag"] not in ("td", "th"):
                    continue
                i0 = min(range(len(edges)), key=lambda i: abs(edges[i] - c["x"]))
                i1 = min(range(len(edges)), key=lambda i: abs(edges[i] - (c["x"] + c["w"])))
                cell = t.rows[ri].cells[i0]
                if i1 - 1 > i0:
                    cell = cell.merge(t.rows[ri].cells[i1 - 1])
                shade(cell, fill_of(c["st"]) or rbg)
                pt = px(c["st"].get("padding-top")); pl = px(c["st"].get("padding-left")); pr_ = px(c["st"].get("padding-right"))
                cell_margins(cell, pt, pl, 0, pr_)
                va = c["st"].get("vertical-align", "middle")
                valign(cell, {"top": "top", "bottom": "bottom"}.get(va, "center"))
                sides = {}
                for side in ("top", "left", "right", "bottom"):
                    b = self.border_px(c, side)
                    if b:
                        sides[side] = b
                if sides:
                    cell_borders(cell, sides)
                self.fill_cell(cell, c, c["y"] + pt, c["x"] + pl, align=c["st"].get("text-align"))

    def emit(self):
        page = self.m["tree"]
        for node in page["kids"]:
            if node["h"] < 0.5:
                continue
            gap = node["y"] - self.cursor_y
            if gap > 1.0:
                sp = self.doc.add_table(rows=1, cols=1); table_setup(sp, [self.W]); row_height(sp.rows[0], gap)
                tight(sp.rows[0].cells[0].paragraphs[0], line_px=1)
            tables = []

            def find_tables(n):
                if n["tag"] == "table":
                    tables.append(n); return
                for k in n["kids"]:
                    find_tables(k)
            find_tables(node)
            if tables:
                # the wrapper's own top edge to the table's
                for tb in tables:
                    g = tb["y"] - max(self.cursor_y, node["y"])
                    if g > 1.0:
                        sp = self.doc.add_table(rows=1, cols=1); table_setup(sp, [self.W]); row_height(sp.rows[0], g)
                        tight(sp.rows[0].cells[0].paragraphs[0], line_px=1)
                    self.html_table(tb)
                    self.cursor_y = tb["y"] + tb["h"]
                self.cursor_y = max(self.cursor_y, node["y"] + node["h"])
            else:
                if node is page["kids"][-1]:
                    # the page's last block gives up the height of the paragraph Word
                    # requires after a table, so the page stays one page
                    node = dict(node, h=max(node["h"] - 6.0, 1.0))
                self.block(node)
                self.cursor_y = node["y"] + node["h"]
        last = self.doc.add_paragraph()
        tight(last, line_px=1)
        rpr = last._p.get_or_add_pPr()
        r = OxmlElement("w:rPr"); sz = OxmlElement("w:sz"); sz.set(qn("w:val"), "2"); r.append(sz); rpr.append(r)
        self.compact_cells()
        return self.doc

    def compact_cells(self):
        """A cell must end in a paragraph and python-docx also starts it with one. Inside a
        row of exact height those empty paragraphs take the room the content needs, so
        every empty paragraph that is not a cell's last child goes, and the last one
        becomes a hairline."""
        W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
        body = self.doc.element.body
        for tc in body.iter(W + "tc"):
            kids = list(tc)
            blocks = [k for k in kids if k.tag in (W + "p", W + "tbl")]
            if len(blocks) < 2:
                continue
            for k in blocks[:-1]:
                if k.tag == W + "p" and not k.findall(".//" + W + "t") and not k.findall(".//" + W + "drawing") and not k.findall(".//" + W + "tab"):
                    tc.remove(k)
            lastp = [k for k in list(tc) if k.tag == W + "p"]
            if lastp and lastp[-1] is list(tc)[-1] and not lastp[-1].findall(".//" + W + "t"):
                pp = lastp[-1]
                pPr = pp.find(W + "pPr")
                if pPr is None:
                    pPr = OxmlElement("w:pPr"); pp.insert(0, pPr)
                sp = OxmlElement("w:spacing"); sp.set(qn("w:before"), "0"); sp.set(qn("w:after"), "0"); sp.set(qn("w:line"), "10"); sp.set(qn("w:lineRule"), "exact")
                place(pPr, sp, PPR_ORDER)
                r = OxmlElement("w:rPr"); sz = OxmlElement("w:sz"); sz.set(qn("w:val"), "2"); r.append(sz); place(pPr, r, PPR_ORDER)


def convert(html_path, out_path, measured=None):
    doc = Emitter(html_path, measured=measured).emit()
    code = re.search(r'class="hb-code">([^<]+)<', open(html_path, encoding="utf-8").read())
    doc.core_properties.title = code.group(1) if code else os.path.basename(out_path)
    doc.core_properties.comments = "Laid out from the printed page's own measured geometry; editable text and tables; house fonts embedded."
    doc.save(out_path)
    EF.embed(out_path)


def convert_many(html_paths, out_path, title=None, measured=None):
    """Several pages in one document, one per page; measured: {path: measurement}."""
    doc = None
    for h in html_paths:
        if doc is not None:
            doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
        doc = Emitter(h, doc, measured=(measured or {}).get(h)).emit()
    doc.core_properties.title = title or os.path.splitext(os.path.basename(out_path))[0]
    doc.save(out_path)
    EF.embed(out_path)
    return len(html_paths)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    convert(sys.argv[1], sys.argv[2])
    print("wrote", sys.argv[2])
