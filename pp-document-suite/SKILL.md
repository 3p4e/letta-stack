---
name: pp-document-suite
description: Unified Purely Plant GmbH document engine — generates AND formats SOPs, Annexes, AND reports/computational records in the bilingual Macedonian|English Purely Plant house style, and can also format any already-drafted text/document into that style. Replaces the four legacy skills (pp-content-developer, pp-template-formatter, pp-annex-content-creator, pp-annex-formatter) and absorbs the method-validation report engine. Use for: writing an SOP/annex from scratch, formatting approved content into a controlled .docx, producing reports & records with native Word equations / worked calculations / data-entry & execution forms / statistical charts, or restyling existing drafted text into Purely Plant format.
when_to_use: "Use when the user wants to (1) develop SOP or Annex CONTENT (questionnaire-driven, GMP-compliant), (2) FORMAT approved content into the Purely Plant bilingual .docx (SOP two-column or Annex inline), (3) build a REPORT or computational RECORD with formulas/worked-calcs/forms/charts (validation/verification reports & protocols, stability/trending reports, OOS records, CoA/calculation sheets, logbooks), or (4) reformat ANY drafted document/text into the Purely Plant house style. Triggers: 'write/create/draft an SOP', 'what should this SOP/annex include', 'format this SOP/annex', 'make this a Purely Plant document', 'create a form/log/template/checklist', 'write a report with these formulas/calculations', 'add equations/charts/forms', 'turn this into our house style'."
version: 1.6.2
dependencies: "python3 + python-docx (build); latex2mathml + lxml + Microsoft Office MML2OMML.XSL (native Word equations); matplotlib (charts); Microsoft Word COM (Windows) or LibreOffice/soffice (PDF render)"
---

# PURELY PLANT DOCUMENT SUITE (UNIFIED)

One skill for the whole Purely Plant document lifecycle. It merges four legacy skills into a single matrix:

|  | **Content development** (what goes in) | **Formatting / build** (how it looks) |
|---|---|---|
| **SOP** | mandatory 9-section structure | two-column MK \| EN, vertical divider, native TOC |
| **Annex** | forms / logs / templates / checklists | full-page bilingual inline (MK 11pt \| EN 7pt) |
| **Report / record** | reports, protocols, computational records | bilingual sections + **native Word equations**, worked calculations, data-entry/execution forms, **statistical charts** |

Plus a third capability: **format any already-drafted text/document** into the Purely Plant house style (auto-detecting SOP vs Annex).

> **Engine note.** The legacy skills generated .docx with Node `docx-js`. This unified skill standardizes on **python-docx** + Microsoft Word COM (or `soffice`) for rendering — the toolchain already proven in this environment. Scripts: `scripts/pp_format.py` (SOP/annex shells), `scripts/pp_report.py` (reports/records: native equations, worked calcs, forms — §3.7), `scripts/pp_charts.py` (figures — §3.6), `scripts/pp_theme.py` (canonical colour/type tokens — one house navy `#2B547E`), `scripts/pp_assets.py` (brand asset registry + glyph guard — logos, bundled verified fonts, `chart_style()`, `missing_glyphs()`/`audit_docx()`/`check_environment()`; see §6D), `scripts/pp_verify.py` (pre-delivery QC gate — §6, now glyph-audited via `pp_assets`), `scripts/render_pdf.ps1` (Word-COM PDF). Brand assets live in `assets/brand/` (wordmark) and `assets/fonts/` (bundled Carlito + Montserrat, full Cyrillic coverage — see §6D for why these are bundled rather than trusting the OS font cache).

---

## 0. MASTER ROUTER — decide before doing anything

> **First time in a fresh container/session:** run `bash scripts/pp_setup_fonts.sh` once
> before building anything. It installs the full Carlito/Montserrat font packages and
> quarantines any subset webfont copies that would otherwise silently scramble Macedonian
> text (see §6D). `pp_verify.py` re-checks this on every build regardless, so a stale
> environment fails the gate instead of reaching the reader — but running the setup script
> up front avoids the failure entirely.

Resolve two axes, then act:

```
            ┌──────────────────────────────────────────────┐
            │ AXIS 1 — Document TYPE                        │
            │   SOP   → 9-section, two-column format        │
            │   Annex → form/log/template/checklist, inline│
            │   (Annex if code contains "_A" e.g. QASOP031_A07,│
            │    or it is a form/log/template/checklist)   │
            └──────────────────────────────────────────────┘
            ┌──────────────────────────────────────────────┐
            │ AXIS 2 — MODE                                 │
            │   A. Develop CONTENT (no finalized text yet) │
            │   B. FORMAT approved content                  │
            │   C. FORMAT arbitrary drafted text/doc        │
            └──────────────────────────────────────────────┘
```

Routing rules:
- "write / draft / develop / what should it include" → **Mode A (content)**.
- "format / build / make .docx / apply house style" + content provided → **Mode B**.
- "reformat this / turn this draft into our style" + a finished draft or file → **Mode C** (content-preservation, see §4).
- If unsure of TYPE: ask one question — "SOP or Annex?" Do not guess.

---

## 1. Company & regulatory context (shared)

Full detail in `references/regulatory_and_context.md`. In brief:

- **Purely Plant GmbH (DOOEL Skopje)**, Petrovec, North Macedonia — GACP indoor cultivation + GMP dry-flower production (Grade D), EU medical market.
- **Author voice / QP:** Blagoj Nikolov, M.Pharm. (batch-disposition authority).
- **Regulatory frame:** EudraLex Vol. 4 (EU GMP + Annexes 1, 7, 8, 11, 16) → ICH (Q7, Q9, Q10, Q2(R2)) → EMA/HMPC → Ph. Eur. (incl. Monograph 3028 *Cannabis flos*) → MALMED → ISO. Cite the clause for every requirement.
- **House language rule:** author technical content in English; deliver **bilingual Macedonian | English** (Macedonian first; decimal **commas** in Macedonian). **Never translate abbreviations** (QA, QC, QP, LOD, HPLC, GMP, CoA, IPQC, SOP, SST, CFU, pH). Never duplicate symbols/numbering.

---

## 2. MODE A — Content development (SOP or Annex)

Shared **intelligent questionnaire** methodology (full question banks in `references/questionnaire_library.md`):

1. **Pre-question analysis** — parse the request + any uploaded examples; map to the regulatory hierarchy; pick the category (SOP: QC/PROD/CULT/QA · Annex: form/log/template/checklist); decide how many rounds.
2. **Questionnaire** — multi-round, **all answers pre-populated** (user selects, doesn't type); options must be truthful, regulation-verified, GMP-valid; multi-select where logical. Use the `AskUserQuestion` tool to present rounds.
3. **Auto-completion** — for anything unanswered, choose the **most compliant** option per the regulatory hierarchy (defaults table in the reference).
4. **Generate content** —
   - **SOP** → the mandatory **9-section** structure (see §2.1). All procedural content goes in §6; regulatory framework in §4; training & deviation as §6.x.
   - **Annex** → the structure for its category (ID/header fields, body table, approval/signatures, pagination).
5. **Precision standards** — never vague: quantify everything ("NMT 12.0 %", "within 24 h", "2–8 °C"), cite the regulatory basis inline, label risk-control/rationale for complex steps.
6. **Approval gate** — present the drafted content; once the user approves, proceed to Mode B (formatting).

### 2.1 Mandatory SOP 9-section structure
1.0 ЦЕЛ / PURPOSE · 2.0 ПОДРАЧЈЕ НА ПРИМЕНА / SCOPE (2.1 Applicability, 2.2 Exclusions, 2.3 Future Extension) · 3.0 ОДГОВОРНОСТИ / RESPONSIBILITIES · 4.0 РЕФЕРЕНТНИ ДОКУМЕНТИ / REFERENCE DOCUMENTS (regulatory framework as subsections) · 5.0 ДЕФИНИЦИИ / DEFINITIONS (5.1 Definitions, 5.2 Abbreviations) · 6.0 ПОСТАПКА / PROCEDURE (ALL procedural content; training & deviation as final 6.x) · 7.0 ЗАПИСИ / RECORDS · 8.0 ПОВРЗАНИ ДОКУМЕНТИ / RELATED DOCUMENTS · 9.0 РЕВИЗИЈА / REVISION.

---

## 3. MODE B — Formatting / build (approved content → .docx)

Full specs in `references/formatting_specs.md`; engine in `scripts/pp_format.py`. Ask **only** formatting questions (bilingual vs MK-only; department code; document number). Then build:

- **SOP → two-column.** A4, Calibri; body MK 11pt (left) | EN 11pt (right) in separate columns with a 0.5 pt vertical divider; section headers 12 pt bold on light-gray; title+approval page; **Word native TOC** (levels 1–3); tables nested in merged full-width rows (no divider) with table text MK 11pt | EN 7pt.
- **Annex → inline full-page.** A4 (portrait 1" / landscape 0.5"), Calibri; **all** text bilingual inline "МК 11pt | EN 7pt"; navy `#2B547E` section-header rows with **white** text; label cells `#EDF2F7`; alternating rows `#F7FAFC`; accents cream/rose/mint; **shading type always `clear`, never `solid`**; cell margins 29/58 DXA; template header (PP logo + bilingual doc name in Arial Narrow) + "Page X of Y" footer.

Render to PDF with Word COM (Windows: `scripts/render_pdf.ps1`) or `soffice --headless --convert-to pdf`.

---

## 3.5 Mandatory page furniture — header, footer, logo (REQUIRED on EVERY document)

Every Purely Plant controlled document — SOP, annex, form, log, report, **without exception** — MUST carry the standard running header and footer. These are NOT generated run-by-run; they live in the base template **`assets/PP_BASE_TEMPLATE.docx`** and are loaded by the engine.

**Header** (2×3 table, full page width, gray `#7F7F7F` top/bottom rules):
- **Left cell:** Purely Plant leaf logo + wordmark (`image1.jpg` cropped leaf + `image2.png` wordmark) — preserved from the template, never re-drawn.
- **Centre cell:** `Име на документ | Document name:` then the **actual document title** — `mk_title` (Macedonian) and `en_title` (English), passed to `new_sop`/`new_annex`. Calibri. The generic "Standard Operating Procedure / ANNEX" phrase is only a fallback when no title is supplied — the header must carry the real SOP/annex title.
- **Right cell:** `Документ бр. | Code of document:` + the document **code** (Calibri bold), and below `Верзија | Ver: <version>`.

**Footer:** `Page X of Y` (Word PAGE/NUMPAGES fields, Calibri 12pt).

**Page geometry (from the template):** A4 (11906×16838 twips); margins top 540 / bottom 630 / left 720 / right 720 twips; header 567 / footer 144 twips.

### How the engine applies it (automatic)
`new_sop()` and `new_annex()` default to `from_template=True`. They (1) open `PP_BASE_TEMPLATE.docx` (header + logo + footer + geometry come with it); (2) `apply_pp_header(d, mk_name, code, en_name, version)` stamps the centre/right values; (3) `wipe_body(d)` clears the old body but keeps `<w:sectPr>`; (4) you build the body; (5) `save(d, path)` re-seats `<w:sectPr>` last so the header/footer/geometry apply document-wide.

```python
import pp_format as pf
d = pf.new_sop(code="QCSOP 009", version="1.0",
               mk_title="Аналитички методи: употреба, валидационен статус и опфат",
               en_title="Analytical Methods: Use, Validation Status and Scope")  # header carries the ACTUAL title
pf.sop_titlepage(d, "QCSOP 009 · v1.0", mk_title, en_title)
pf.sop_toc(d)
# ... build sections ...
pf.save(d, "QCSOP 009 ....docx")                    # header on every page
```
Annex: `d = pf.new_annex(code="QCSOP009_A02", mk_name="...", en_name="...", version="1.0")`. Pass `from_template=False` only for a throwaway draft with no controlled header. (`sop_section_row` now auto-applies Heading 1–3 styles, so the inserted TOC field populates on update; use `sop_block_table` for the §7/§8/§9 tables.)


## 3.6 Data visualizations (figures) — statistical / justification charts

Statistics-bearing documents (validation/verification reports, comparison/correlation studies) **should include charts** that clarify and justify the results — they are part of the deliverable, not optional. Charts are matplotlib **PNGs embedded as images** (house palette); this is distinct from formula notation, which stays as **native Word equations**. Protocols (blank execution forms) get no charts.

- Engine: `scripts/pp_charts.py` (navy `#2B547E`; red for fails/limits). Embed with `figure(d, png, mk_caption, en_caption)` — centered image + bilingual MK | EN caption. Reports carry a "Визуелни претстави | Visual representations" subsection inside the calculations appendix.
- Pick charts that match the statistics present:
  - precision / acceptance → `horrat_bar` (vs limit), `horwitz_plot` (observed vs Horwitz model)
  - measurement uncertainty / decision rule → `guardband` (spec ± U zones)
  - method comparison / correlation → `regression_scatter` (OLS + identity line), `bland_altman` (bias + 95% LoA)
  - per-group comparison → `bias_bar`, `qratio_bar` (pass/fail coloured)

```python
import pp_charts as pc, pp_format as pf
png = pc.horrat_bar(["R1","R2","R3","R4","R5"], horrat, passmask, "fig.png")
pf.figure(d, png, "HorRat_r по ниво наспроти 2,0", "HorRat_r per level vs 2.0")
```

---

## 3.7 Reports, computational records & forms (ALL QMS teams) — `scripts/pp_report.py`

Beyond SOPs and annexes, the suite builds **reports and computational records** in the same house style — **general-purpose, not limited to method validation**: validation/verification reports & protocols, stability and trending reports, OOS/OOE investigation records, CoA calculation sheets, method calculation worksheets, micro CFU records, equipment logbooks — anything with **formulas, step-by-step calculations, data-entry forms, or charts**.

Engine `scripts/pp_report.py` (`exec(open('pp_report.py').read())` or `import pp_report`). Key helpers:

- **Native Word equations (editable, NOT images)** — `eqn(d, latex)` for a display equation, `eqn_in(p, latex)` inline. LaTeX → MathML (`latex2mathml`) → OMML (Office `MML2OMML.XSL`); falls back to monospace text if the engine is unavailable. Use for EVERY formula in any QMS document instead of typing `√`, `x̄`, fractions or superscripts as plain text.
- **Worked-calculation cascade** — `calc_step(d, mk, en, formula, substituted, result)`: bilingual label → general formula (OMML) → the same formula with the actual numbers substituted (OMML) → bold result. Use for transparent, audit-ready calculations (ALCOA+ — show the working).
- **Data-entry & execution forms** — `entry_table(d, headers, rows, widths, label_mk, label_en)` (blank or row-labelled grid for execution) and `execution_signoff(d)` (Executed → Reviewed (QA) → Approved cascade, distinct from authorship approval). Use for logbooks, sampling/cleaning records, training records, any GMP form/record.
- **Bilingual prose & blocks** — `chapter / subsec / minilabel / body / bullet / note` (MK | EN), `databox(d, lines, fill, tcol)` (status/caution box), `cellfmt` (table cell). Macedonian first, decimal commas, abbreviations untranslated.
- **Figures** — `figure(d, png, mk, en)` embeds a `pp_charts.py` chart with a bilingual caption (§3.6).
- **Formulas inside table cells** — `eqn_cell(cell, latex)` renders a *pure-formula* cell as a native equation (light/white cells only — never on a navy fill). Inline variable mentions in prose cells stay as text.

> **Type scale (QC Head 2026-06-22).** Body **MK 11 / EN 8**; notes MK 10 / EN 8; table cells **MK (8–10) / EN (sz−2, ≥ 7)** — a combined "МК | EN" string in one cell is **auto-split** so EN renders smaller; **space before AND after** chapter/sub titles; ordinal/number columns get minimal width. Full table in `references/formatting_specs.md`.

```python
exec(open('pp_report.py',encoding='utf-8').read())            # or: import pp_report
d = Document('assets/PP_BASE_TEMPLATE.docx')                   # mandatory header/footer come with it
swap_header(d,"ИЗВЕШТАЈ — ","CODE","Report — ...","PP-QC-XXX-","001/202","6")  # ACTUAL title in header
wipe_body(d)
chapter(d,"6","НЕОДРЕДЕНОСТ","Uncertainty")
calc_step(d,"Комбинирана неодреденост","Combined uncertainty",
          r"u_c=\sqrt{u_{Rw}^2+u_{cal}^2}", r"u_c=\sqrt{1.92^2+0.06^2}", "u_c = 1,92 %")
```

> **Design tokens (one source of truth).** All three engines (`pp_format`, `pp_report`, `pp_charts`) render the **single** house navy `#2B547E` and respect the **6 pt font floor** — canonical values in `scripts/pp_theme.py`. Never introduce a second navy. (Reference worked examples: the a02.2 oven AMVR/AMVP/AMSF/A04 package and the SAM_a02.1 HMA package.)

---

## 3.8 Document opening, justification & per-step sign-off (reports/protocols)

Every report/protocol from this skill opens the same way (engine `pp_report.py`):

- **Cover page (page 1, UNNUMBERED)** — `cover_page(d, title_mk, title_en, info_rows, kind_mk, kind_en, study_mk, study_en, approval_rows=…)`. The cover keeps the **standard running header** (PP logo + doc name + code + version) exactly like every other page — it is NOT dropped. Below the header: big bilingual method title (centered, NOT justified) + **Document-information block** + **Approval block** + "Controlled document". Only the **page number is suppressed on page 1** (no first-page footer); numbering resumes bottom-right from page 2 (`_cover_header_footer()` points the first-page header at the real header part and removes the first-page footer ref).
- **Table of contents (page 2) — WHEN APPLICABLE** — `toc_page(d)` inserts a native Word TOC field (`TOC \o "1-3" \h \z \u`); `chapter()`/`subsec()` carry outline levels so it populates. Footer shows **2**.
- **Content** — `chapter(d,"1","РЕЗИМЕ","Executive Summary")`; begins on page 3 when a TOC is present, or page 2 when the TOC is omitted.

**When to include a TOC (QC Head 2026-06-22):**
- **SOPs — ALWAYS** (mandatory, levels 1–3).
- **Reports & protocols (AMVR, AMVP) and LONG annexes** (many chapters/sub-chapters, extensive content) — **yes**.
- **Short forms & checklists — OMIT the TOC**: status forms (AMSF), one-page forms, and checklists of ~1–3 pages (e.g. `QCSOP009_A04`) do NOT get a TOC — call `cover_page()` then go straight to the content (which then begins on page 2). A TOC adds no navigational value to a short structured form, so it is left out of generation for these document types.

Build order: `wipe_body(d)` → `cover_page(…)` → `toc_page(d)` → chapters. The render step MUST update fields (Word COM `doc.Fields.Update()` before SaveAs, or user presses Ctrl+A → F9) so the TOC and "Page X of Y" populate.

**Justification & tables (house rule):** body / notes / bullets are **justified to the margins**; table cells are **centered (horizontal + vertical)**; chapter & sub-titles and the cover title are NOT justified. Every table is **fitted to the page** — `fixed()` scales column widths to the 18.46 cm text width so nothing overflows.

**Per-step two-role sign-off (validation & verification protocols):** because record-making steps are executed at different dates/times, place a `step_signoff(d)` after EVERY logical record step — or simply pass `entry_table(…, signoff=True)`. Each sign-off records two roles: **Operator/Analyst** (executed & entered the raw data) and **QC Department Manager** (checked & approved that record). A final overall `execution_signoff(d)` closes the protocol. This mechanism is general — use it for any method validation/verification protocol (§6.5 full validation, §6.6 verification, §6.7 correlation) and any table-based record document.

---

## 4. MODE C — Format any drafted text into PP style

Use when the user hands over a finished draft (text or .docx) and wants it in house style.
1. Detect TYPE (SOP vs Annex) from structure/code; confirm if ambiguous.
2. **Content-preservation rule (NON-NEGOTIABLE):** 100 % of input text must appear in the output — never summarize, omit, paraphrase, reorder meaning, or edit. Apply formatting only (fonts, bilingual structure, tables, layout, header/footer). Verify by extracting and sorting all text runs from input vs output — they must match.
3. If the draft lacks the mandatory structure, you may *map* it into the 9-section / annex structure **without changing wording**; flag any section with no source content rather than inventing it.
4. Build via Mode B; render; verify.

---

## 5. Content-preservation rule (applies to all formatting)

Content in = content out. The formatter changes **appearance only**. Zero tolerance for content loss; this is a GMP data-integrity requirement (ALCOA+). When editing an existing .docx, prefer additive/append operations or XML-level edits over regeneration so nothing validated is disturbed.

## 5A. Content-fidelity / no-impoverishment (NON-NEGOTIABLE — Modes A, B, C)

**A merge, restyle, or reformat MUST NOT reduce the descriptive or explanatory depth of the source(s).** (QC Head, 2026-06-22.)

- Treat every transformation as **ADDITIVE / UNION, never lossy**. Every requirement, rationale, worked example, numeric criterion, citation and explanatory sentence in the source(s) survives in the output, in **at least** its original level of detail.
- The ONLY permissible reduction is **de-duplication of genuinely identical content** when consolidating two+ sources — and even then keep the **longer / more complete** wording.
- **Never** summarize, paraphrase-to-shorten, or "tidy" prose in a way that drops detail. When two sources state the same requirement with different depth, keep the **MORE descriptive** version.
- Prefer **verbatim retention** of source sentences; rewrite only to splice sections together, never to compress.

**Fidelity verification (run before delivery — page count is NOT a fidelity metric):**
1. Extract body text (paragraphs + all table cells), source(s) vs output.
2. Compare **WORD and CHARACTER counts**. Output ≥ Σ(unique source content).
3. Section-level check: for every retained section, output words ≥ source words; LIST any section that shrank and justify (allowed only for true duplication) or restore.
4. Page-count differences are expected (margins/header/layout) and must NOT be used as evidence of completeness either way.

> **Known debt to repair:** the QCSOP 009 v1.0 merge tightened the 009-origin §6 procedure prose by ~6 % (≈283 words) while adding 013 material. A zero-compression rebuild of §6 (restore full 009 wording + keep 013 additions) is pending the QC Head's go-ahead.

---

## 6. Verification checklist (before delivery)
- [ ] **Content:** all source text present (sorted run comparison = identical); nothing summarized/omitted.
- [ ] **Content fidelity (§5A):** output word & character counts ≥ Σ unique source; every retained section ≥ source words (list/justify any shrink — dedup only); page count NOT used as a fidelity metric.
- [ ] **Type/format:** SOP=two-column with divider; Annex=inline full-page; correct structure.
- [ ] **Bilingual:** Macedonian first; abbreviations untranslated; decimal commas in MK.
- [ ] **Typography:** Calibri; SOP body MK 11 | EN 11; Annex/table MK 11 | EN 7; **font floor ≥ 6 pt** (grep `w:sz` < 12 half-points).
- [ ] **Annex colour:** section headers `#2B547E` + white text; shading `clear` (no `solid`); no legacy colours.
- [ ] **Page furniture:** title/approval page (SOP) or template header+footer (Annex); native TOC (SOP); "Page X of Y".
- [ ] **Figures:** statistics documents carry the matching charts (`figure()` + `pp_charts.py`); protocols none.
- [ ] **Equations:** every formula is a **native Word equation** (`eqn`/`calc_step`), not typed text or an image (reports/records).
- [ ] **Render:** PDF generated and visually checked.
- [ ] **References chapter** present with full citations (DOI / clause / page where applicable).
- [ ] **Automated gate:** `python scripts/pp_verify.py <doc.docx> [--source <src.docx>]` → PASS (font floor ≥ 6 pt, glyph coverage — every run's declared font can render its own text, render environment free of subset-font shadowing, bilingual MK+EN, and — with `--source` — fidelity word/char counts ≥ source per §5A).

---

## 6D. Brand assets, the glyph guard, and informal (non-QMS) documents — `scripts/pp_assets.py`

**What broke once.** A delivered report rendered with Macedonian text scrambled into
tofu boxes and wrong characters. Root cause: `~/.fonts` held *subset* webfont copies of
Carlito (as few as 106 glyphs, no Cyrillic) alongside the full 2 117-glyph system Carlito,
and fontconfig's substitution picked the subset for `Calibri`/`Carlito` runs — every
Macedonian character in the document was asked of a font that did not have it. The
document was correct; the render environment was not, and nothing checked for it.

**The fix, structurally.** `pp_assets.py` is now the single place that knows which font
file backs each house typeface, and it can prove — before delivery, not after — that a
font covers the text it's asked to render:

- `missing_glyphs(face, text)` — resolves `face` to the actual file the renderer will use
  and returns the characters it cannot render (`""` = clean).
- `audit_docx(path)` — walks every run in a built `.docx` (body + header + footer) and
  checks its declared font against its own text.
- `check_environment()` — detects the subset-webfont trap directly: any font under
  `~/.fonts` or `~/.local/share/fonts` with a suspiciously small glyph count that could
  shadow a full system face.
- `logo()`, `font_file()`, `chart_style()` — the asset registry half: wordmark path,
  bundled font file path, and matplotlib rcParams matching the house style, so a builder
  never hard-codes a path.

`pp_verify.py` calls all three glyph checks on every run — a font/script mismatch is now
a **FAIL** on the pre-delivery gate, not something a reader discovers in the PDF. If you
add a new bundled face to `assets/fonts/`, register it in `pp_assets.FACES` with its
`aliases` (the names that appear in `.docx` runs) so the guard resolves it correctly.

**Informal / non-QMS documents.** Not everything this engine builds is a controlled QMS
record — working exports, informal management submissions (e.g. a weekly plan/report),
and drafts-for-review carry no document code and no version, and must say so rather than
borrow SOP/Annex document-control furniture they don't have:

- `informal_header(d, title_mk, title_en, tag_mk=…, tag_en=…)` — header variant that
  replaces the doc-code/version box with a plain bilingual tag (e.g. "Неформален работен
  документ | Informal working document"). Use instead of `swap_header()` whenever the
  document has no `QCxxx`/`PP-xxx` code.
- `cover_page(..., controlled=False)` — swaps the "Контролиран документ | Controlled
  document" footer line for an explicit "Informal working document — not a controlled
  record" line. Pair with `informal_header()`, not `swap_header()`.

---

## 6A. Post-generation comprehensive review (MANDATORY before final delivery)

After generating/completing any document, run a ruthless, instructional, correctional review and FIX issues before delivering. Do not present a document as final until it passes. Review across:

1. **Skill adherence** — cover (running header present, page 1 unnumbered, numbering bottom-right from p.2); TOC only where applicable; body justified; table cells centered; **every table AutoFit-to-Window (no margin overflow)** with sensible column distribution (ordinal minimal; Name/Date/Signature sized; Role/Action remainder); fonts (body MK 11 / EN 8, tables MK ≤10 / EN ≤7-8, floor ≥ 6 pt); formulas are native OMML; per-step two-role sign-off present in protocols; references chapter with DOIs/clauses.
2. **Regulatory & GxP** — EU GMP Part I Ch. 6 (§6.15/§6.17), Annex 15, Annex 11 (ALCOA+); ICH Q2(R2)/Q14, Q9, Q10; Ph. Eur. (2.2.32, 2.5.32, 2.1.7, Monograph 3028), USP <1225>/<1226>; ISO/IEC 17025; correct method route (§6.5 validation / §6.6 verification / §6.7 correlation) and status tier.
3. **Scientific basis** — method/measurand correctness, acceptance criteria appropriate to the method, limitations documented.
4. **Mathematical correctness** — independently recompute the key statistics (e.g. RSD, HorRat, pooled iP, U, Q-ratio, r, regression, bias, LoA) and confirm they match the tables/figures.
5. **Content fidelity** — output ≥ source (no impoverishment); bilingual MK | EN; decimal commas in MK; abbreviations untranslated; document codes reconciled.
6. **Tools** — run `python scripts/pp_verify.py <doc> [--source <src>]`; visually check the rendered PDF (cover, TOC, tables, equations, sign-offs).

Record the findings; correct; only then deliver. This review is itself part of the skill's standard workflow.

## 6B. Data-driven documents — dataset binding & single source of truth (MANDATORY)

Any document that REPORTS calculated results (validation / verification / correlation reports, stability & trending, OOS/OOT, capability studies, CAPA effectiveness …) must be built from a **bound experimental dataset** — never from numbers typed into prose.

1. **Bind a dataset first.** Before generating, obtain that study's own data: ask the user for the file path, or to paste/attach it in chat, or to point to a connected source. Do NOT invent, assume, or carry over figures from a different study. Every study has its OWN ranges/levels, material matrix, and (for cannabis) strain — the binding accepts arbitrary levels and matrices; nothing is hardcoded to a prior dataset, strain, or range set.
2. **Single source of truth.** Every reported statistic (mean, SD, RSD, pooled iP, bias, LoA, CI, r, slope, Q, u_c, U, HorRat …) is COMPUTED from the bound dataset at build time (via `pp_data.py`) and INJECTED into BOTH the prose and the summary tables. Never hand-type an aggregate into a narrative sentence or a summary cell — that is precisely how figures drift from the data (the root cause of the 2026-06-22 HMA mean-bias defect, where a frozen +1.76 contradicted the live +1.74).
3. **Self-verify before delivery.** Re-derive every reported figure from the dataset and `assert` it equals what the document prints (fail the build on mismatch); cross-check tables against each other (e.g. per range, U = 2·√(bias² + s²)). Record dataset provenance — `pp_data.provenance()` → file, SHA-256, size, date — in a data-provenance note for ALCOA+ traceability. This is enforced inside the §6A review.

Engine: `scripts/pp_data.py` — `load_dataset` (.json/.csv/.tsv, arbitrary shape), descriptive stats, `t975` (SciPy-free Student-t), `bland_altman` / `pearson` / `ols` / `q_ratio` / `expanded_U`, `provenance`, `assert_consistent`. Build pattern for any data-driven document: **bind → compute → inject → assert**.

4. **Per-method datasets — extend the skill per method (no forced universal schema).** Each analytical method binds its OWN method-specific dataset, shaped to that method's nature (oven LoD per-level replicates; HMA paired ranges; a future HPLC validation will carry system-suitability, linearity, accuracy/recovery, precision, range; a microbiological purity package will carry its own structure). Do NOT force one schema across methods. When a new method documentation need arises, EXTEND this skill with that method's dataset shape + builder; the engine (`pp_report`, `pp_data`, charts) is reused unchanged.
5. **No reported number is hard-typed in a bilingual string (enforced).** Where a literal must remain in prose, the builder recomputes the value from the dataset and `assert`s the literal matches (a build-time guardrail), then prints `SELF-CHECK OK …`. Both current builders do this (HMA: bias/LoA/CI/r/U; oven: pooled iP/U/HorRat). A drift between any printed number and the data fails the build. This is how "the principle holds everywhere," even where injection is impractical.
6. **Engine API (importable).** The engine's public functions ARE its API — `chapter, subsec, body, bullet, note, gap, cover_page, toc_page, table helpers (fixed, render_dump, cellfmt, mathcell, hmerge, status_grid), eqn/eqn_in/eqn_cell/eqn_result/calc_step, entry_table/step_signoff/execution_signoff, figure, databox`, plus `pp_data` and `pp_charts`. Builders may `import pp_report` (preferred) instead of `exec()`-ing it; nothing external is required from the user.
7. **Verify-before-deliver gate.** The §6A review script (independent recompute of every key statistic + structure/skill-adherence) is the headless self-test; run it on every build and only deliver on a clean pass. `pp_data.assert_consistent(reported, recomputed)` is the reusable golden-check primitive.

## 6C. QCSOP 009 lifecycle record set (the full prescribed document family)

The skill produces EVERY record type prescribed by QCSOP 009 for the analytical-method lifecycle — not just the report. Build them with the same engine (cover_page → chapters → `fixed` tables / `status_grid` / sign-off):

1. **AMRRF** — Analytical Method Registration Request Form (per method, §6.2): identification table (AM code, title, type, source, linked STP, spec ref, intended scope, initial status, equipment, reference standards, training) + PROVISIONAL status grid + QC Head/QA approval. Opens the lifecycle.
2. **PP AMVP** — Validation/Verification/Comparison Protocol (per study, §6.5/6.6/6.7): pre-defined criteria + execution forms + per-step two-role sign-off.
3. **PP AMVR** — Validation/Verification/Comparison Report (per study): worked calcs, native equations, statistics, MU (§6.8), status recommendation.
4. **QCSOP009_A04** — Compendial Method Verification Checklist (compendial verifications only, §6.6).
5. **AMSF** — Analytical Method Status Form (per method): compact `status_grid` (the six tiers), basis, scope/limitations, history, periodic review.
6. **QCSOP009_A02** — Master AM/STP Register (facility, §6.2; **landscape**): one row per method (code, title, type, source, status, scope, dates, AMSF ref, remarks); outsourced detail points to A03.
7. **QCSOP009_A03** — Outsourced-Laboratory Method Correlation Matrix (facility, §6.9; **landscape**): per outsourced parameter → accredited method reference (ISO/MKC EN / Ph. Eur.), pharmacopoeia name, PP STP code, contract lab + accreditation No./scope/expiry + technical-agreement ref + report/station No. Record the Ministry-recognized release labs (e.g. Faculty of Pharmacy — Center for Natural Products = primary for cannabinoid potency; Institute for Public Health = microbiology / heavy metals / pesticides / mycotoxins) and the valid technical quality agreements.

**Orientation:** forms and reports are portrait; wide registers (A02, A03) are built **landscape** (section orientation + raise the table text-width so `fixed()` fills the page).
8. **QCSOP009_A05** — Revalidation Trigger Assessment (event, §6.10): trigger event + category grid + ICH Q9 impact/risk + scope grid (partial/full/SST-only) + approval.

Status routing by method type (§6.4): compendial → §6.6 → VERIFIED (AMVP+AMVR+A04+AMSF); in-house → §6.5 → VALIDATED; alternative/SAM → §6.7 → CHARACTERIZED, IPQC-only (AMVP+AMVR+AMSF); outsourced → §6.9 → A03 entry.

**Chronological lifecycle — generate documents in this order, per method:** (1) **AMRRF** registration request → status PROVISIONAL; (2) **AMSF v1.0** initial status form (PROVISIONAL, at registration); (3) **AMVP** protocol, approved, criteria pre-defined before execution; (4) **execution & raw data** (ALCOA+, second-person verified); (5) **AMVR** report (+ **A04** for compendial) → status recommendation; (6) **AMSF v2.0** status updated to VERIFIED / CHARACTERIZED / VALIDATED; (7) **QCSOP009_A02** Master Register updated (and **A03** if outsourced). **A05** only on a later revalidation trigger. The AMSF is one living record versioned through the lifecycle (PROVISIONAL → final).

**Release vs internal-QC roles (site policy):** batch release and any legally-binding result are ALWAYS issued by an accredited outsourced laboratory (recorded in A03) — now and after the site's own accreditation; in-house methods, even when VERIFIED/VALIDATED, serve the internal QC / IPQC / in-process / trending function ONLY and are not used for release. In A02 give the in-house method the primary internal-QC role with accredited labs as fallback, and record the release route as the accredited outsourced lab.

## 7. Activation triggers
Develop: "write/draft an SOP", "create an annex/form/log/checklist", "what should this SOP/annex include". Format: "format this SOP/annex", "make .docx", "apply Purely Plant template/house style". Report/record: "write a validation/verification report or protocol", "build a calculation/stability/trending report", "add native equations / worked calculations / execution forms / charts" → §3.7 `pp_report.py`. Restyle: "turn this draft into our format", "reformat into PP style". Not for: label population (use pp-bag-label-populator / pp-storage-release-labels). (AM validation/verification reports are now handled HERE via `pp_report.py`, replacing the legacy external `skill_helpers.py`.)

---
**Purely Plant Document Suite v1.6.2** — covers the FULL QCSOP 009 record family (AMRRF · AMVP · AMVR · QCSOP009_A04 · AMSF · QCSOP009_A02 register · QCSOP009_A03 outsourced matrix · QCSOP009_A05 trigger form; §6C). Unifies pp-content-developer + pp-template-formatter + pp-annex-content-creator + pp-annex-formatter, and absorbs the method-validation report engine (`pp_report.py`: native equations, worked calculations, execution forms, charts, `eqn_cell` in-cell formulas, **cover page + TOC + per-step two-role sign-off**) for use by all QMS teams. House rules: cover (unnumbered, keeps the running header; number suppressed only on p.1) → TOC (p.2, **only where applicable** — SOPs/reports/protocols/long annexes; omitted on status forms & short checklists) → content; body justified, **no inter-paragraph space within a logical chunk** (space only at boundaries — titles, tables, chunk breaks via `gap()`), table cells centered; body MK 11 / EN 8, tables MK ≤10 / EN ≤8 (auto-split); **intelligent, use-aware column distribution** via `fixed()` (compact-centered for "label | value" summaries, full-width for data tables; ordinals minimal; Name/Date/Signature entry columns purpose-sized; **first row repeats on page breaks**); merged single-label summary rows via `hmerge()`; per-step two-role sign-off in protocols; **table design by information role** (conclusions→`databox`/`status_grid`; headline→prominent; supporting→compact; transitory→inline) with `status_grid()` compact checkbox grids; **native math in headers/results** (`mathcell` white-on-navy header equations, `eqn_result` emphasised conclusion equations); and a MANDATORY post-generation review (§6A) before delivery; **data-driven documents are built from a bound dataset as the single source of truth** — compute → inject → assert via `pp_data` (§6B), so reported figures can never drift from the data. Engines: `pp_format` · `pp_report` · `pp_data` · `pp_charts` · `pp_theme` · `pp_verify` (python-docx). Output: bilingual MK|EN controlled .docx + PDF.
