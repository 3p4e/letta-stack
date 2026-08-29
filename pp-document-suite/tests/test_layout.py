"""Column-sizing contract for pp_report.fixed().

Every case here pins behaviour that was silently removed once. Commit 593e7f7
(14.08.2026) rewrote `fixed()` while adding the brand assets and the glyph guard;
its message describes fonts, the weekly report and brand assets, and says nothing
about layout. The overflow compression and the word-boundary entry matching went
with it and nothing noticed for two weeks, because no test covered them.

These run without LibreOffice, Letta or a network — python-docx builds the table
in memory and the assertions read the resulting column widths back off the XML.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

docx = pytest.importorskip("docx", reason="python-docx is the engine's own dependency")
from docx import Document                                          # noqa: E402
import pp_report as R                                              # noqa: E402


def widths(rows, **kw):
    """Build a table from `rows` (first row = header), size it, return column cm."""
    d = Document()
    t = d.add_table(rows=len(rows), cols=len(rows[0]))
    for i, r in enumerate(rows):
        for j, v in enumerate(r):
            t.cell(i, j).text = v
    R.fixed(t, **kw)
    return [c.width.cm for c in t.columns]


WIDE = [
    ["Серија | Batch", "Параметар | Parameter",
     "Критериум за прифаќање | Acceptance criteria",
     "Добиена вредност | Obtained value", "Лабораторија | Laboratory"],
    ["GG1024_01", "Вкупен Δ9-THC | Total Δ9-THC", "18.0 – 22.0 %", "19.84 %",
     "Фармахем | Farmahem"],
    ["CJ062501/2", "TYMC", "≤ 10⁴ CFU/g", "4.2 × 10⁴ CFU/g", "ИЈЗ | IPH"],
]


# ------------------------------------------------------------------ the page
@pytest.mark.parametrize("rows", [WIDE, WIDE[:2], [["A", "B"], ["1", "2"]]])
def test_no_table_exceeds_the_page(rows):
    """The house rule at the top of pp_report.py: every table FITS the page.
    Fits, not fills — a narrow two-column table is left compact rather than
    stretched across the text block, which is why this is `<=` and not `==`."""
    assert sum(widths(rows)) <= R.PAGE_W + 0.05


def test_an_overflowing_table_is_widened_to_exactly_the_page():
    """Where the content genuinely does not fit, the sized table must occupy the
    full text block — anything less means content was discarded rather than
    compressed."""
    assert sum(widths(WIDE)) == pytest.approx(R.PAGE_W, abs=0.05)


def test_no_column_collapses():
    """Proportional sizing on an overflowing table can drive a narrow column to
    nothing. The compression path floors each column instead."""
    assert all(x > 0.5 for x in widths(WIDE))


# ------------------------------------------------- overflow compression path
def test_wide_table_is_compressed_not_scaled_proportionally():
    """The regression guard for 593e7f7.

    Plain proportional scaling shrinks every column by the same ratio, so the
    widest column keeps the largest share. Compression floors each column to its
    own data and header-word demand first, then gives the *slack* to the longest
    headers — so a column carrying short data but a long header ends up wider
    than its proportional share, and a column of long data keeps its floor.
    The two strategies therefore cannot produce the same widths."""
    w = widths(WIDE)
    ideal_sum_scaling = None  # what plain proportional sizing would have produced
    # Reproduce the proportional branch directly from the same measurements.
    CHCM, PAD, cap = 0.176, 0.42, 34
    ideal = [0.8] * len(WIDE[0])
    for row in WIDE:
        for j, cell in enumerate(row):
            parts = cell.split(" | ")
            L = (len(parts[0]) + 3 + 0.8 * len(parts[1])) if len(parts) == 2 else len(cell)
            ideal[j] = max(ideal[j], min(L, cap) * CHCM + PAD)
    total = sum(ideal)
    assert total > R.PAGE_W, "fixture must overflow, or this test proves nothing"
    ideal_sum_scaling = [x / total * R.PAGE_W for x in ideal]

    assert w != pytest.approx(ideal_sum_scaling, abs=0.01), (
        "widths match plain proportional scaling — the overflow compression "
        "branch is gone (this is exactly what 593e7f7 removed)")


def test_explicit_weights_bypass_compression():
    """A caller that passes weights has already decided; compression must not
    second-guess it. Several builders rely on this — cover_page() sizes its
    approval table with fixed(t, [5.0, 5.46, 3.5, 4.5])."""
    w = widths([["A", "B", "C", "D"], ["1", "2", "3", "4"]], weights=[5.0, 5.46, 3.5, 4.5])
    assert sum(w) == pytest.approx(R.PAGE_W, abs=0.05)
    assert w[1] > w[0] > w[3] > w[2], "the caller's proportions were not preserved"


# ------------------------------------------------ word-boundary entry sizing
def test_entry_column_matching_respects_word_boundaries():
    """`_ENTRY_TARGETS` purpose-sizes hand-written columns — signature, date,
    name. Matching on a bare substring makes 'име' hit inside 'примерок', so a
    sample-description column gets sized as a name field. The comment in the
    source calls this out by name; the substring form is what 593e7f7 restored
    by accident."""
    sample = widths([["Опис на примерок | Sample description", "Вредност | Value"],
                     ["x", "1"]])
    name = widths([["Име | Name", "Вредност | Value"], ["x", "1"]])
    assert sample[0] != pytest.approx(name[0], abs=0.01), (
        "'примерок' was sized as a name column — substring matching regressed")


@pytest.mark.parametrize("header,other", [
    ("Потпис | Signature", "Забелешка | Note"),
    ("Датум | Date", "Забелешка | Note"),
])
def test_real_entry_columns_still_match(header, other):
    """The counterpart: tightening to word boundaries must not stop the genuine
    signature and date columns from being purpose-sized."""
    tight = widths([[header, other], ["", ""]])
    loose = widths([["Опис | Description", other], ["", ""]])
    assert tight[0] != pytest.approx(loose[0], abs=0.01), f"{header} lost its entry sizing"
