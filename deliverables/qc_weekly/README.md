# QC Weekly Plan/Report — Issue 01 (10–14 Aug 2026)

First issue of the owner's weekly QC plan/report cycle, built with the
pp-document-suite engine (bilingual MK|EN, house header, cover + TOC-less
compact layout, issues-first per the owner's highlight rule).

- `QC_Weekly_Plan_Report_Issue01_10-14Aug2026.docx` / `.pdf` — the document.
- `build_qc_weekly.py` — the builder (persisted; the first build was run
  ad hoc and not committed — this is the reproducible version).
- `weekly_dataset.json` — §6B bound dataset: every report figure computed
  from the verified letta-stack QC artifacts (spec matrix / listing /
  iCoA-CoQ plans), never hand-typed.
- `merge_timelines.py`, `consolidated_ruler.png`, `merged_sources.json` —
  the annex band: four parallel sessions on one Skopje hour-ruler, **filtered
  to Purely Plant content only** (see Scope below). No source figure
  altered; totals not summable across lanes.
- Sources: QC_Activity_Timeline (this repo), a task-family time ledger
  (Drive 1gByKejrs…), a work timeline (Drive 1-tGe57q…), a work-time
  overview (Drive 1VB9m90H…).
- Issue resolution dates are printed as "pending" — to be dictated by the
  QC Manager and dropped in on the next rebuild (`build_qc_weekly.py`
  keeps `PEND` centralized so this is a one-line change).

## Not a QMS-controlled document

Per the owner's instruction, this is an **informal working document** — it
carries no document code and no version, and says so in both the header
(`pr.informal_header`) and the cover footer (`cover_page(..., controlled=False)`).
The authoritative QC records continue to be kept under the quality system;
this submission is for management information only.

## Scope: Purely Plant content only

Only work on Purely Plant content counts toward the time band. Infrastructure
work — container/stack configuration and repair, test-suite runs, production
deploys — is excluded, even where the underlying session touched the same
tools. Work on the **Letta host** (its knowledgebase, its memory/agent
databases, and the QC data held in them) **does** count, because that data
*is* Purely Plant content, not infrastructure.

`merge_timelines.py` documents each source's own itemised rows and which
were kept vs. excluded (`SOURCES` / `EXCLUSIONS` in that file); the excluded
items and their hours are also printed on the annex figure and in a table in
the document itself, so nothing is silently dropped.

| Source | PP-content hours | Source's own total | Excluded |
|---|---|---|---|
| QC data session | 4.9 h | 4.9 h | — |
| Letta host, witnessed | 5.3 h | 5.3 h | — |
| Letta host, checkpoint span | 52.8 h | 52.8 h | 13.8 h background monitoring of non-PP repos |
| WWF platform | 1.7 h | 2.25 h | 0.9 h test suites + production deploy |
| ImB spec design | 35.0 h | 35.0 h | — |

## Font-rendering fix

The first build of this document (and of `deliverables/timeline/…`) rendered
with Macedonian text scrambled — caused by subset webfont copies of Carlito
in `~/.fonts` shadowing the full system font. Root-caused and fixed at the
render-environment level; see `pp-document-suite/scripts/pp_assets.py`
(glyph guard) and `pp-document-suite/scripts/pp_setup_fonts.sh` (environment
setup), and SKILL.md §6D. `pp_verify.py` now fails the delivery gate on any
recurrence instead of shipping it.
