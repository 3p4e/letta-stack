# Formatting Specs (Mode B/C) — SOP two-column & Annex inline

Engine: `scripts/pp_format.py` (python-docx). Render: Word COM (`scripts/render_pdf.ps1`) or `soffice --headless --convert-to pdf`.
**Font floor:** never below 6 pt (`w:sz` ≥ 12 half-points). **Calibri** body throughout; **Arial Narrow** only for the annex header doc-name.

## SOP — two-column (MK left | EN right)
| Element | Spec |
|---|---|
| Page | A4 portrait, margins 0.5" (1.27 cm) all sides |
| Body | MK 11 pt (left col) · EN 11 pt (right col), **separate columns, no pipe**, justified |
| Vertical divider | 0.5 pt black line between columns (left cell right-border + right cell left-border) |
| Section headers (1.0…) | 12 pt bold, light-gray `#E8E8E8` fill, both columns |
| Sub-headers (1.1…) | 11 pt bold |
| Tables | nested in a **full-width merged row** (no divider); table text MK 11 pt \| EN 7 pt (pipe) |
| Page 1 | title (24 pt) + code (18 pt) + bilingual subtitle (12 pt) + approval table (blue `#D9E2F3` header) |
| Page 2 | **Word native TOC** field `TOC \o "1-3" \h \z \u` (levels 1–3, page numbers right) — user updates field on open |
| Structure | mandatory 9 sections (SKILL §2.1) |

## Annex — full-page bilingual inline
| Element | Spec |
|---|---|
| Page | A4; portrait margins 1" (2.54 cm); landscape margins 0.5" (1.27 cm) for wide registers (A08/A09) |
| Layout | **full-page width, NO columns**; every text run is inline "МК 11pt \| EN 7pt" |
| Section header rows | navy `#2B547E` fill + **white** text (inject `w:color=FFFFFF`), bold |
| Label cells | `#EDF2F7` (bold MK) · Data cells white · Alternating rows `#F7FAFC` |
| Accents | caution `#FEF9E7` · critical `#FDEDEC` · approval/pass `#EAFAF1` |
| **Shading type** | **ALWAYS `clear`, NEVER `solid`** (solid renders black in LibreOffice/PDF) |
| Cell margins | top/bottom 29 DXA, left/right 58 DXA (not zero) |
| Borders | 1 pt blue-gray `#B0BEC5` |
| Alignment | cell text centered (h+v); tables full width |
| Title block (body) | code 12 pt bold · bilingual title 14 pt bold · parent-SOP ref 10 pt |
| Header/footer | from `SOP_Blanc_Template.docx`: PP leaf logo + wordmark, doc name in **Arial Narrow** (MK 13 pt bold ALL-CAPS, EN 9 pt ALL-CAPS), doc code + version (Calibri bold), footer "Page X of Y" right |

### Header/footer application (existing .docx → Workflow B, XML-level)
For an existing annex, prefer unpack → edit `word/header1.xml`/`footer1.xml`/`document.xml` → repack, copying the template header rels + media (`image1.jpg` leaf, `image2.png` wordmark). This preserves validated content byte-for-byte. Replace doc-name paragraph, doc-code, and version for the specific annex (registry of MK/EN names + codes lives with the template).

## Content preservation (Mode C / any existing doc)
100 % of input text appears in output. Verify: extract all `<w:t>` from input vs output, sort, compare — must be identical. Never summarize/omit/paraphrase; formatting changes appearance only.

## Mandatory header / footer (base template — ALL documents)
Loaded from `assets/PP_BASE_TEMPLATE.docx` by `new_sop()/new_annex()`; never re-drawn in code.

| Element | Spec |
|---|---|
| Header table | 2 rows × 3 cols, full width, centred; top/bottom rules `#7F7F7F` 8pt |
| Col 1 (logo) | PP leaf `image1.jpg` (cropped) + wordmark `image2.png`; vMerged |
| Col 2 (name) | `Име на документ \| Document name:` + bilingual doc name; Calibri; MK then EN |
| Col 3 (code/ver) | `Код на документ \| Code of document:` + **code** (Calibri bold); row 2 `Верзија \| Ver: <v>` |
| Footer | `Page X of Y` via PAGE/NUMPAGES fields; Calibri 12pt |
| Page | A4 11906×16838 twips; margins T540 B630 L720 R720; header 567 / footer 144 twips |

**Fill API:** `apply_pp_header(d, mk_name, code, en_name, version)` overwrites only the value runs;
`wipe_body(d)` clears the body keeping `<w:sectPr>`; `save()` re-seats `<w:sectPr>` last.

## Type scale & table density (reports/records — QC Head 2026-06-22)
| Element | MK | EN | Notes |
|---|---|---|---|
| Body prose (`body` / `bullet`) | 11 pt | 8 pt | inline "МК \| EN"; EN grey italic |
| Notes (`note`) | 10 pt | 8 pt | grey italic |
| Table cells (`cellfmt`) | sz (8–10) | sz − 2 (≥ 7) | EN auto-rendered smaller; a combined "МК \| EN" string in one cell is **auto-split** so EN drops to sz−2 |
| Chapter / sub titles | 20 / 16 · 16 / 12 | — | unchanged; **space BEFORE and AFTER** (chapter 12/7, subsec 8/4 pt) |

- **Intelligent, use-aware column distribution — AUTOMATIC (`fixed(tbl)` is the single table-layout brain):** it measures each column's real bilingual content (the longer of the MK / EN halves) and decides the table's *fit*:
  - **Narrow "label | value" SUMMARY tables** (≤ 3 columns whose content fits comfortably) → **COMPACT & CENTERED** at their natural width — the label column is wide enough that labels do not stack vertically, and the value sits beside it instead of floating in a vast empty column. (This is the correct shape for regression/agreement/criteria summaries; do NOT stretch them to full width.)
  - **Wide DATA tables** → fill the page width (never overflow the margins). **Uniform grids** (≥ 4 columns whose content all fits) are distributed **EVENLY** so no cell wraps to a second row; mixed tables (one long text column) stay content-proportional.
  - **Summary "Mean / Σ" rows** show each column's COMPUTED value (label only in column 0) — never a label repeated across every cell; emphasise the key result cell (bold, +1 pt, accent fill).
  - **Concluding calc results** (`calc_step` result line) are emphasised automatically: navy left-rule + light fill, and the result itself is a **native LaTeX equation** (navy bold) — `result` is LaTeX, `tag` is optional trailing text (e.g. a ✓/verdict). Column widths are measured on the TRUE inline bilingual width (MK + separator + smaller EN), so headers/labels never wrap; labeled grids size column 0 to its labels and split the data columns evenly.
  - Ordinal/number columns (№, n, i, Det.) collapse to just-enough; **hand-written ENTRY columns are purpose-sized even when blank** — Name/Позиција ≈ 5.2 cm (fits a MK + EN name & surname), Date ≈ 2.6 cm, Signature ≈ 3.8 cm; Role/Action take the remainder.
  - Override only when needed: `weights=[…]` forces ratios; `mode='compact'|'full'` forces the fit.
- **Repeat header row on page breaks — AUTOMATIC:** `fixed()` marks row 0 as a `w:tblHeader`, so when a table spans pages the column headings reprint at the top of each page.
- **Paragraph spacing — space only at boundaries:** body/bullet paragraphs of the SAME style carry **no** inter-paragraph space (tight within a logical chunk). Space is added ONLY before/after chapter & sub-chapter titles, around tables/figures, and between logical chunks (use `gap(d)` for a deliberate chunk break). Never add space after every line of the same paragraph.
- **Math in headers & emphasised results (native OMML, not plain text):** a header cell that *is* a mathematical expression (xᵢ, xᵢ−x̄, (xᵢ−x̄)², u_c, RSD, U …) uses `mathcell(cell, latex)` → white native equation on the navy header (legible). The conclusion of a logical calculation block uses `eqn_result(d, latex, mk, en)` → navy left-rule + light fill + NAVY bold equation, to mark its importance. Inline math inside prose stays `eqn_in`; pure-formula light cells use `eqn_cell`.
- **Table design follows information ROLE (decide BEFORE building):** classify what the table carries, then choose the construct so prominence matches role —
  - *Conclusion / outcome* (status, verdict, overall result) → **emphasis**: a `databox()` or a compact highlighted grid, never a sprawling table. The six method-status tiers use `status_grid(d, options, selected, ncols=2)` — a compact 3×2 checkbox grid (narrow checkbox columns, wide label columns, a thin borderless gap between the two blocks, label font bumped up) instead of a tall 6-row list.
  - *Major / headline data* (the dataset the document exists to present, e.g. raw results, statistics) → a prominent, well-spaced table.
  - *Supporting data* (uncertainty budgets, per-level detail) → compact tables, smaller font (within the 6 pt floor).
  - *Transitory / local* (single values, inline checks) → minimal or inline; do not over-build.
  Every datum is relevant, but its visual PROMINENCE must match its role — pick databox vs table vs grid vs inline accordingly.
- **`status_grid(d, options, selected, ncols=2)`** — compact checkbox/option grid for any short mutually-exclusive list (status tiers, yes/no selections); column-major fill, checkbox columns minimal, label columns wide, borderless gap between blocks, selected = ☒ green bold.
- **Reported figures are DERIVED, never typed (single source of truth):** for any document that reports calculated results, bind the study's dataset, compute every statistic with `pp_data.py`, inject it into both prose and tables, then `assert` the document matches the recompute (§6B / §6A). Do not paste an aggregate (bias, LoA, CI, RSD, U, r, Q …) as a literal into a sentence or a summary cell — that is how numbers drift from the data.
- **Summary / footer rows:** a "Mean …" / total row must use ONE spanning label, not a label repeated across columns — use `hmerge(tbl, row, c0, c1, "МК | EN")` to merge the label cells and keep a single value cell (fixes flattened/duplicated legacy table dumps).
- **Formulas in cells:** a cell that is a *pure formula* uses `eqn_cell(cell, latex)` → native OMML equation (light/white cells only; never on a navy fill — OMML runs are black and would be invisible). Inline variable mentions inside prose cells stay as text.
- **Font floor:** never below 6 pt; in practice EN table text floors at 7 pt and body EN at 8 pt.

## Document opening, justification & sign-off (reports/protocols — QC Head 2026-06-22)
- **Cover page (page 1, UNNUMBERED):** `cover_page()` — keeps the **standard running header** (logo + doc name + code + version) like every page; below it: big bilingual title (centered, not justified) + **Document-information block** + **Approval block** + "Controlled document". Only the page number is suppressed on page 1; numbering resumes bottom-right from page 2.
- **Table of contents (page 2) — when applicable:** `toc_page()` — native Word TOC field `TOC \o "1-3" \h \z \u`; `chapter()`/`subsec()` carry outline levels. Footer shows **2**. **TOC rule:** SOPs ALWAYS; reports/protocols (AMVR/AMVP) and long annexes YES; **short forms, status forms (AMSF) and 1–3-page checklists (e.g. QCSOP009_A04) OMIT the TOC** (content then begins on page 2).
- **Content:** Executive Summary first (page 3 with a TOC, page 2 without). Render MUST update fields (Word COM `doc.Fields.Update()` before SaveAs, or Ctrl+A → F9) for the TOC and "Page X of Y".
- **Justification:** body / notes / bullets **justified to the margins**; chapter & sub-titles and the cover title are NOT justified.
- **Tables:** cells **centered** (horizontal + vertical); `fixed()` scales widths to the 18.46 cm text width so **every table fits the page**; ordinal/number columns minimal width.
- **Per-step two-role sign-off:** `step_signoff()` (or `entry_table(…, signoff=True)`) after EACH record step — **Operator/Analyst** (executed + entered raw data) and **QC Department Manager** (checked + approved that record), because steps occur at different dates/times. A final `execution_signoff()` closes the protocol.
