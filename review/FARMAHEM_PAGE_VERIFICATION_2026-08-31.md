# The Farmahem certificates, read off their own pages

**Scope:** all 63 Farmahem reports behind 63 register rows — cannabinoids, mycotoxins and
loss on drying. None had ever been checked against a document.

| Suffix | Reports | Register columns | Values | Agreement |
|---|---|---|---|---|
| `К` / `K` | 31 | THC %, CBD %, CBN % | 93 | 89 — **4 defects** |
| `М` | 22 | Aflatoxins Σ, Aflatoxin B1, Ochratoxin A | 65 | 65 |
| `GS` / `ГС` | 10 | Loss on drying % | 10 | 10 |
| **total** | **63** | | **168** | **164 — 97.6%** |

(The register's `THC spec` column holds `≥ 5.00 %`, a specification rather than a result,
and is excluded from the comparison.)

## Every defect is the same mistake wearing a different hat

All four sit in the cannabinoid reports. Each prints one table —
`Име на компонента | Кратенка | Резултат [%w/w] | U [%w/w]` — with three rows: CBD, CBN,
Δ9-THC. Beside every result sits its own uncertainty, and directly above or below sits
another component's result. **Three of the four ways to pick the wrong cell have
happened.**

| Row | Certificate | Register held | Page prints | What went wrong |
|---|---|---|---|---|
| 9 | `197-1-К/26` BG1024 | CBN `0.02` | CBN **`0.28`**, U `0.02` | took the **U column** |
| 276 | `197-7-К/26` P060352 | CBD `<LOQ`, CBN `0.22` | CBD **`0.22`**, CBN **`< LOQ`** | the **two rows swapped** |
| 286 | `197-13-К/26` HPA1024 | CBN `N.D.` | CBN **`0.36`** | a result recorded as **not detected** |

Each confirmed at 2.6× magnification before being called. All applied by
`apply_farmahem_corrections.py` — four cells, nothing else touched.

**Δ9-THC is correct on all 31 reports**, every mycotoxin value on all 22 is correct, and
every loss-on-drying value on all 10 is correct. The defects are confined to the CBD/CBN
pair: the two minor cannabinoids, adjacent to each other and to the uncertainty column,
where any number looks plausible whatever cell it came from.

**No range check can see any of this.** Every wrong value is inside the plausible range
for the parameter it was entered against. Only reading the column header catches it —
the concrete argument for a typed extraction record carrying value, unit, limit *and
source column* in one object, rather than a chunk of prose.

**Row 286 is the one a reviewer should care about.** `N.D.` is not a small number; it is
a statement that the laboratory looked and found nothing. It reported 0.36 %.

---

## What the certificates themselves get wrong

### Two loss-on-drying reports carry the wrong batch

`100-2-ГС/26` (CF-152/26) and `100-3-ГС/26` (CF-154/26) both print **`J31112501`**. Their
own cannabinoid twins — the same samples, consecutive internal numbers — print
**`J31122501`**:

| Internal no. | Report | Sample | Batch printed |
|---|---|---|---|
| CF-151/26 | `100-2-К/26` | Jokerz 31, рачно тримиран цвет | `J31122501` |
| CF-152/26 | `100-2-ГС/26` | Jokerz 31, рачно тримиран цвет | **`J31112501`** |
| CF-153/26 | `100-3-К/26` | Jokerz 31, тримиран цвет | `J31122501` |
| CF-154/26 | `100-3-ГС/26` | Jokerz 31, тримиран цвет | **`J31112501`** |

Both are real batches — `J31112501` is rows 193–196, `J31122501` is rows 211–220 — so
this is not a typo that fails a format check. The register places all four under
`J31122501`, agreeing with the cannabinoid reports. The likeliest reading is that the
laboratory carried the previous sample's batch number down into the two LoD reports; the
register is right and the certificates are not.

**This revises the earlier reading of the IJZ serial.** The IPH pass found `1628/2026`
printing `J311122501` against its sibling's `J31122501` and called it an isolated typo.
It is not isolated: the same batch family is written three different ways across three
laboratories' documents. Anything keying on the batch string needs
`ingestion/common/batch_id.py`, and even that cannot repair a document that names a
different real batch.

### One report is bound backwards

`100-3-ГС/26` has its results on page 1 and its cover on page 2 — the only document in
the family with reversed pages. A reader who opens it expecting the cover finds the
result table, and any pipeline that assumes "page 1 is the cover" reads the wrong page.

### Sample names drift

`Cap Junkie` / `Cap Junky`, `Kush Crasher` / `Kush Krasher` — the same sample written two
ways on reports issued the same day by the same laboratory.

---

## Three things that look like defects and are not

**`<LOQ` versus `< LOQ (<0.20)`.** The 051 and 100 series print `<LOQ**` with their own
footnote `<LOQ** - под лимит на квантификација (<0.20%)`. The register expands that
footnote inline — *more* informative than the page.

**`2.06` versus `2.06 — DETECTED, >LOQ`.** Row 40's ochratoxin A carries the register's own
detection flag. Reading that as a difference produced a false finding once, which is why
`compare_farmahem_reads.py` normalises all three of these explicitly rather than silently.

**`ND` versus `<LOQ` in the mycotoxin table.** These are not the same and the laboratory
does not treat them as such: `ND` is `< 0.5 µg/kg`, `<LOQ` is `< 1 µg/kg`. Three reports
use `<LOQ` for ochratoxin A — `276-31-М/25`, `197-13-М/26` — and the register preserves
the distinction correctly.

---

## Method

The Drive download lands on disk and never enters context. Pages render at 200 DPI. Page
1 is normally the cover and page 2 carries both the sample table — client name, batch, and
the laboratory's own internal number `CF-nnn/26` — and the result table, so the page read
names its own certificate. The one reversed document was caught because its page 2 was a
cover with no results on it.

**These are scans.** `pdftotext` returns zero characters on every one of the 63, so the
render is the only admissible source. Worth stating plainly, because this series was
extracted "verbatim" in an earlier task — from the RAG corpus, not from the paper.

Classical OCR is not used and is forbidden by `scripts/policy_check.py` rule 1.

Raw readings: `review/farmahem_page_reads_2026-08-31.json`. Renderer:
`deliverables/qc_gap_analysis/render_farmahem_certificates.py`. Comparison:
`deliverables/qc_gap_analysis/compare_farmahem_reads.py`.
