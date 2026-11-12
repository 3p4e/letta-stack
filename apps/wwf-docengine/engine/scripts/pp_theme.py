# -*- coding: utf-8 -*-
"""
Purely Plant — house DESIGN TOKENS (single source of truth).

Colour and typography constants shared by the whole document suite:
  pp_format.py  (SOP two-column / Annex inline)
  pp_report.py  (reports, computational records, forms)
  pp_charts.py  (matplotlib figures)

Canonical house navy = #2B547E. All three engines render this same navy so a
document's section headers, table headers and embedded charts match exactly.
Import these (engines on the scripts/ path can `import pp_theme`), or mirror the
values — but never introduce a second navy.
"""
import re as _re
from docx.shared import RGBColor, Pt

# ---- canonical palette (hex strings = python-docx shading; RGBColor = runs) ----
NAVY_HEX    = "2B547E"   # house navy — section-header fills, accents, chart series
GREY_HEX    = "595959"   # secondary text (EN gloss, notes)
WHITE_HEX   = "FFFFFF"
LABEL_HEX   = "EDF2F7"   # label / lead-in cells
ROWALT_HEX  = "F7FAFC"   # zebra striping
# semantic accent fills (status / caution boxes) — shared annex + report
PASS_HEX    = "E2EFDA"   # mint  (approval / pass)
FAIL_HEX    = "FCE4D6"   # rose  (fail / critical)
CAUTION_HEX = "FFF2CC"   # cream (caution / provisional)
BORDER_HEX  = "B0BEC5"   # blue-gray gridlines
# light structure (Head of QC, 04.11.2026: "lighten up the colours … instead of that dark navy blue strip"):
# section bars and table headers are pale blue with navy text; navy stays the accent (text, rules), never a fill.
BAR_HEX     = "DCE6F2"   # level-1 section bar
SUBBAR_HEX  = "F1F5FA"   # level-2+ section bar
HEAD_HEX    = "E6EDF6"   # table header row
GRID_HEX    = "9DB2C7"   # table gridlines
EX_HEX      = "C00000"   # example (simulated) value, printed [in brackets]
FILL_HEX    = "7F7F7F"   # write-in hint
# approval tiers (analyst -> peer review -> approver), as on the HPLC method validation draft
TIER_HEX    = {"analyst": "EAF1FB", "peer": "FFF4E0", "approver": "E8F4EA"}

NAVY  = RGBColor(0x2B, 0x54, 0x7E)
GREY  = RGBColor(0x59, 0x59, 0x59)
BLACK = RGBColor(0x00, 0x00, 0x00)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
GREEN = RGBColor(0x37, 0x56, 0x23)
RED   = RGBColor(0xC0, 0x00, 0x00)
AMBER = RGBColor(0xC5, 0x5A, 0x11)

# ---- matplotlib (hex with '#') ----
MPL_NAVY = "#2B547E"; MPL_RED = "#C0392B"; MPL_GREEN = "#1E8449"; MPL_GREY = "#595959"

# ---- typography ----
FONT_BODY     = "Calibri"        # body throughout
FONT_HEADER   = "Arial Narrow"   # annex header doc-name only
FONT_FLOOR_PT = 6                # template floor: the fixed header carries one 6 pt line
BODY_FLOOR_PT = 7                # body floor (04.11.2026): 6 pt English did not survive print and scan

def floor_ok(half_points):
    """True if a w:sz value (half-points) respects the 6 pt house floor."""
    return half_points is None or half_points >= FONT_FLOOR_PT * 2


# ---- values that are the same in both languages print once (Head of QC, 04.11.2026) ----
# "1,097 | 1.097", "0,691 × 0,877 | 0.691 × 0.877", "HPLC | HPLC": a number, a formula, a unit, a code or an English-only
# term reads the same in both languages, so it is ONE entry, never two. The two halves are "the same" when they are equal
# or differ only by the decimal separator (comma in Macedonian, point in English); the Macedonian form is the one printed.
_DEC_COMMA = _re.compile(r"(?<=\d),(?=\d)")

def same_in_both(mk, en):
    """True when the Macedonian and English halves of an entry say the same thing (nothing to translate)."""
    a, b = (mk or "").strip(), (en or "").strip()
    if not a or not b:
        return False
    return a == b or _DEC_COMMA.sub(".", a) == b

def collapse(mk, en):
    """(mk, en) with the English half dropped when it only repeats the Macedonian."""
    return (mk, "") if same_in_both(mk, en) else (mk, en)

# ---- inline value markup (04.11.2026) ----
# [[EX:12.45]]  an example (simulated) value: printed red in brackets, "[12.45]", in a simulation build;
#               an empty write-in in an execution build (HEADERDATA "build: execution").
# [[FILL:dd/mm/yyyy]]  a write-in for the person executing the record: grey hint on a dotted line, never red.
import re as _re
TOKEN = _re.compile(r"\[\[(EX|FILL):([^\]]*)\]\]")
MODE = {"build": "simulation"}

def split_tokens(text):
    """[(kind, text)] with kind 'plain' | 'ex' | 'fill' (an EX in an execution build becomes a blank 'fill')."""
    out, pos = [], 0
    for m in TOKEN.finditer(text or ""):
        if m.start() > pos:
            out.append(("plain", text[pos:m.start()]))
        kind, val = m.group(1).lower(), m.group(2).strip()
        if kind == "ex" and MODE["build"] == "execution":
            kind, val = "fill", ""
        out.append((kind, val))
        pos = m.end()
    if pos < len(text or ""):
        out.append(("plain", text[pos:]))
    return out

def has_tokens(text):
    return bool(TOKEN.search(text or ""))

def plain(text):
    """The text as printed: an example value in brackets, a write-in as its hint (used for verdicts and the gate)."""
    return "".join(v if k == "plain" else ("[" + v + "]" if k == "ex" else v) for k, v in split_tokens(text))

def style_run(r, kind, sz):
    """Colour and underline a run written for an 'ex' or 'fill' token."""
    from docx.enum.text import WD_UNDERLINE
    if kind == "ex":
        r.font.color.rgb = RGBColor.from_string(EX_HEX); r.bold = True
    elif kind == "fill":
        r.font.color.rgb = RGBColor.from_string(FILL_HEX); r.italic = True
        r.font.underline = WD_UNDERLINE.DOTTED

def token_text(kind, val):
    if kind == "ex":
        return "[" + val + "]"
    if kind == "fill":
        return val if val else "\u00a0" * 14          # an empty write-in keeps a line to write on
    return val
