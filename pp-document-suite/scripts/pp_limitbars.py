"""Limit bars — a value shown against its acceptance limit inside its own table cell (native Word, no image).

Each cell carries the value as text and, under it, a horizontal bar drawn as a one-row nested table whose
filled part is proportional to the value. The full cell width is the limit (100 %). Colour:
green ≤ amber threshold, amber up to the limit, red above the limit / detected. First used on the LabCore
microbiology OOS report of 12.11.2026.

Markdown block (build_from_md.py):

    [[LIMITS]]
    @col TAMC, CFU/g ~~ ≤ 10⁵ (max 500 000) | 500000 | log
    @col E. coli ~~ absent /1 g | absent | qual
    @group P050182 · HPA052501 · 26-HD-035 ~~ E. coli detected (LabCore)
    17.09.2025 ~~ IPH 948/1686/25 ||| 2.7 × 10⁴ = 27000 ||| Absent
    @ext 12.11.2026 ~~ LabCore (Versa) ||| - ||| Detected in 1 g
    [[/LIMITS]]

  @col   label ~~ criterion text | limit (number, or 'absent' for qualitative) | scale (log|linear|qual)
  @group a batch / block header; text after ~~ is printed in red as the finding
  row    first cell = row label (~~ second line); then one cell per @col
  @ext   same as a row, tinted (results from another laboratory)
  value  'label = number' (the number drives the bar), or a plain number, or '- ' (not reported),
         '< 10' (drawn at 10), '10³–10⁴' (drawn at its upper bound); qualitative: Absent / Detected…
"""
import math, re
from docx.shared import Cm, Pt, RGBColor
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.enum.text import WD_ALIGN_PARAGRAPH
import pp_report as pr

GREEN, AMBER, RED, TRACK = "2E9E5B", "E0A100", "D0342C", "EEF1F3"
SUP = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻", "0123456789-")

def parse_value(raw):
    """-> (label, number|None, kind) kind: 'num' | 'nr' (not reported) | 'abs' | 'det'"""
    s = raw.strip()
    if s in ("", "-", "—", "n/r", "not reported"): return ("not reported", None, "nr")
    if re.match(r"(?i)^(absent|отсутна|одговара|conforms|not detected|nd)\b", s): return (s, None, "abs")
    if re.match(r"(?i)^(detected|present|најден)", s): return (s, None, "det")
    if "=" in s:
        lab, num = s.rsplit("=", 1)
        try: return (lab.strip(), float(num.strip().replace(" ", "").replace(",", ".")), "num")
        except ValueError: pass
    t = s.replace(" ", "").replace(",", ".")
    m = re.search(r"(\d+(?:\.\d+)?)?(?:[×x]10([⁰¹²³⁴⁵⁶⁷⁸⁹⁻]+|\^-?\d+))?", t)
    nums = []
    for mm in re.finditer(r"(\d+(?:\.\d+)?)?[×x]?10([⁰¹²³⁴⁵⁶⁷⁸⁹⁻]+|\^-?\d+)|(\d+(?:\.\d+)?)", t):
        if mm.group(2):
            e = int(mm.group(2).lstrip("^").translate(SUP)); a = float(mm.group(1) or 1)
            nums.append(a * 10 ** e)
        elif mm.group(3): nums.append(float(mm.group(3)))
    if nums: return (s, max(nums), "num")
    return (s, None, "txt")

def fraction(x, limit, scale):
    if scale == "linear": return x / limit
    return math.log10(max(x, 1)) / math.log10(limit)          # log: 100 % = limit, 1 → 0 %

def colour(frac, over, amber_at):
    return RED if over else (AMBER if frac > amber_at else GREEN)

def _shade(cell, hexf): pr.shade(cell, hexf)

def _no_borders(tbl):
    tblPr = tbl._tbl.tblPr
    b = OxmlElement("w:tblBorders")
    for e in ("top", "left", "bottom", "right", "insideH", "insideV"):
        x = OxmlElement("w:" + e); x.set(qn("w:val"), "nil"); b.append(x)
    tblPr.append(b)
    mar = OxmlElement("w:tblCellMar")
    for e in ("top", "left", "bottom", "right"):
        x = OxmlElement("w:" + e); x.set(qn("w:w"), "0"); x.set(qn("w:type"), "dxa"); mar.append(x)
    tblPr.append(mar)

def _bar(cell, frac, fill, width_cm, height_pt=5):
    """Nested 1×2 table: filled part + track. frac in 0..1."""
    frac = min(max(frac, 0.04), 1.0)
    t = cell.add_table(rows=1, cols=2 if frac < 0.999 else 1)
    _no_borders(t); t.autofit = False
    w1 = width_cm * frac
    tblPr = t._tbl.tblPr
    lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); tblPr.append(lay)
    tw = tblPr.find(qn("w:tblW"))
    if tw is None: tw = OxmlElement("w:tblW"); tblPr.append(tw)
    tw.set(qn("w:w"), str(int(width_cm * 567))); tw.set(qn("w:type"), "dxa")
    grid = t._tbl.tblGrid
    for gc, w in zip(grid.findall(qn("w:gridCol")), [w1, width_cm - w1]): gc.set(qn("w:w"), str(int(w * 567)))
    cells = t.rows[0].cells
    cells[0].width = Cm(w1); _shade(cells[0], fill)
    if len(cells) > 1: cells[1].width = Cm(width_cm - w1); _shade(cells[1], TRACK)
    tr = t.rows[0]._tr; trPr = tr.get_or_add_trPr()
    h = OxmlElement("w:trHeight"); h.set(qn("w:val"), str(int(height_pt * 20))); h.set(qn("w:hRule"), "exact"); trPr.append(h)
    for c in cells:
        p = c.paragraphs[0]; p.paragraph_format.space_before = p.paragraph_format.space_after = Pt(0)
    # a nested table must be followed by a paragraph inside the cell
    tail = cell.add_paragraph(); tail.paragraph_format.space_before = tail.paragraph_format.space_after = Pt(0)
    tail.paragraph_format.line_spacing = Pt(2)

def _text(cell, text, colour_hex=None, bold=True, size=8.5, italic=False, align=WD_ALIGN_PARAGRAPH.LEFT):
    p = cell.paragraphs[0]; p.text = ""; p.alignment = align
    p.paragraph_format.space_before = Pt(1); p.paragraph_format.space_after = Pt(1)
    r = p.add_run(text); r.font.size = Pt(size); r.bold = bold; r.italic = italic
    if colour_hex: r.font.color.rgb = RGBColor.from_string(colour_hex)
    return p

def parse_block(rows_raw):
    cols, items = [], []
    for line in rows_raw:
        s = line.strip()
        if not s: continue
        if s.startswith("@col"):
            parts = [x.strip() for x in s[4:].split("|")]
            lab = parts[0]; lim = parts[1] if len(parts) > 1 else ""; sc = parts[2] if len(parts) > 2 else "log"
            cols.append(dict(label=lab, limit=None if lim.lower() == "absent" else float(lim), scale=sc))
        elif s.startswith("@group"):
            items.append(("group", s[6:].strip()))
        else:
            ext = s.startswith("@ext")
            cells = [c.strip() for c in (s[4:] if ext else s).split("|||")]
            items.append(("row", cells, ext))
    return cols, items

def emit(d, rows_raw, page_w_cm, feat):
    cols, items = parse_block(rows_raw)
    if not cols: return
    amber_at = float(feat.get("limit_bars_amber_at", 0.75))
    show_bars = feat.get("limit_bars", True)
    first_w = 3.4; cw = (page_w_cm - first_w) / len(cols); barw = cw - 0.35
    n = 1 + len(items)
    t = d.add_table(rows=n, cols=1 + len(cols)); t.alignment = pr.WD_TABLE_ALIGNMENT.CENTER; t.autofit = False
    widths = [first_w] + [cw] * len(cols)
    for row in t.rows:
        for i, c in enumerate(row.cells): c.width = Cm(widths[i])
    # header
    mk, en = (x.strip() for x in ("Тест / лабораторија ~~ Test / laboratory".split("~~")))
    pr.cellfmt(t.cell(0, 0), mk, en, sz=8, col=pr.WHITE, bold=True, fill=pr.NAVYF)
    for j, c in enumerate(cols, 1):
        a, b = (c["label"].split("~~", 1) + [""])[:2]
        pr.cellfmt(t.cell(0, j), a.strip(), b.strip(), sz=8, col=pr.WHITE, bold=True, fill=pr.NAVYF)
    ri = 1
    for it in items:
        if it[0] == "group":
            a, b = (it[1].split("~~", 1) + [""])[:2]
            m = t.cell(ri, 0).merge(t.cell(ri, len(cols)))
            _shade(m, "EEF4F0")
            p = _text(m, a.strip(), bold=True, size=9)
            if b.strip():
                r = p.add_run("   " + b.strip()); r.font.size = Pt(8.5); r.font.color.rgb = RGBColor.from_string("A33A3A")
            ri += 1; continue
        cells, ext = it[1], it[2]
        a, b = (cells[0].split("~~", 1) + [""])[:2]
        c0 = t.cell(ri, 0)
        p = _text(c0, a.strip(), size=8.5)
        if b.strip():
            q = c0.add_paragraph(); q.paragraph_format.space_after = Pt(1)
            r = q.add_run(b.strip()); r.font.size = Pt(7); r.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
        if ext: _shade(c0, "FFF4F2")
        for j, c in enumerate(cols, 1):
            cell = t.cell(ri, j)
            if ext: _shade(cell, "FFF4F2")
            raw = cells[j] if j < len(cells) else "-"
            lab, x, kind = parse_value(raw)
            if kind == "nr":
                _text(cell, "not reported", "999999", bold=False, size=7, italic=True, align=WD_ALIGN_PARAGRAPH.CENTER); continue
            if c["limit"] is None or kind in ("abs", "det"):
                det = kind == "det"
                _text(cell, lab, RED if det else None, size=8.5)
                if show_bars: _bar(cell, 1.0 if det else 0.04, RED if det else GREEN, barw)
                continue
            if x is None:
                _text(cell, lab, size=8.5); continue
            frac = fraction(x, c["limit"], c["scale"]); over = x > c["limit"]
            col = colour(frac, over, amber_at)
            _text(cell, lab, None if col == GREEN else col, size=8.5)
            if show_bars: _bar(cell, frac, col, barw)
        ri += 1
    pr.borders(t)
    if feat.get("limit_bars_legend", True):
        pr.note(d, "Лента: целата ќелија е границата (100 %%); зелено ≤ %d %%, жолто до границата, црвено над границата / детектирано." % (amber_at * 100),
                "Bar: the full cell is the limit (100 %%); green ≤ %d %%, amber up to the limit, red above the limit / detected." % (amber_at * 100))
