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
FONT_FLOOR_PT = 6                # NEVER render below 6 pt (w:sz >= 12 half-points)

def floor_ok(half_points):
    """True if a w:sz value (half-points) respects the 6 pt house floor."""
    return half_points is None or half_points >= FONT_FLOOR_PT * 2
