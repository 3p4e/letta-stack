# Purely Plant `.docx` — Use the `pp-document-suite` Skill (AUTHORITATIVE)

> **The house format is produced by ONE thing: the `pp-document-suite` skill engine.**
> Do not hand-roll formatting, do not invent colours, do not guess. Build with the engine,
> verify with the engine, render to PDF, and eyeball the result. That is the whole job.

The skill lives in this repo at **`pp-document-suite/`** (installed from `pp-document-suite.skill`,
Google Drive). Its `SKILL.md` is the master spec. The engine is `pp-document-suite/scripts/pp_format.py`
(SOP/annex), `pp_report.py` (reports/records with native equations & charts), `pp_theme.py`
(the one canonical palette), `pp_verify.py` (QC gate). The base template
`pp-document-suite/assets/PP_BASE_TEMPLATE.docx` carries the mandatory running header (PP leaf
logo + wordmark, bilingual Document name, Code, Version) and the "Page X of Y" footer.

## The one command loop

```
1. Content lives as bilingual Markdown in TRANS_DIST/md/<code>.md   (convention below)
2. Build via the engine:   python3 scripts/build_from_md.py TRANS_DIST/md/<code>.md TRANS_DIST/docx/<code>.docx
3. Verify (skill gate):    python3 pp-document-suite/scripts/pp_verify.py TRANS_DIST/docx/<code>.docx   → RESULT: PASS
4. Render + eyeball:       soffice --headless --convert-to pdf <docx> ; pdftoppm -png <pdf>  → look at it
```

`scripts/build_from_md.py` is a thin adapter: it maps the Markdown blocks onto the engine's
house-style helpers. It does **no** styling of its own — all appearance comes from `pp_format.py`.

## Canonical house style (from `pp_theme.py` / `SKILL.md` — do not deviate)

- **One house navy = `#2B547E`.** Never introduce a second navy. Label cells `#EDF2F7`,
  zebra rows `#F7FAFC`, accents mint `#E2EFDA` / rose `#FCE4D6` / cream `#FFF2CC`, gray text `#595959`.
- Font **Calibri** (header doc-name Arial Narrow). **Font floor 6 pt** — never below `w:sz` 12.
- Bilingual **Macedonian first**, English second; decimal **commas** in MK; **never translate**
  abbreviations (QA, QC, QP, GMP, CoA, SOP, HPLC, pH, …); never duplicate symbols/numbering.
- **SOP → two-column**: MK 11pt left | EN 11pt gray right, 0.5pt vertical divider; gray `#E8E8E8`
  section headers (12pt bold); title+approval page; native Word TOC (levels 1–3, `sop_toc`);
  §7/§8/§9 as full-width `sop_block_table`.
- **Annex → inline full page**: **navy `#2B547E` section-banner rows with white text**
  (`annex_section_header`); label cells `#EDF2F7` (`bold_first`); zebra data rows; bilingual
  inline MK 11 | EN 7; `annex_signoff` (Изготвил КК / Проверил QA / Одобрил QP).
- **Every page** carries the base-template header (logo + doc name + code + version) and
  "Page X of Y" footer — these come from `PP_BASE_TEMPLATE.docx`, never re-drawn.
- Shading is always `w:val="clear"` (never `solid`). Tables fit the page width.

## Engine API you build with (`import pp_format as pf`)

- SOP: `pf.new_sop(code, version, mk_title, en_title)` → `pf.sop_titlepage(...)` → `pf.sop_toc(d)` →
  `t=pf.sop_table(d)` → `pf.sop_section_row(t,num,mk,en,level)` / `pf.sop_body_row(t,mk,en)` →
  `pf.sop_finalize(t)` ; full-width tables `pf.sop_block_table(d,headers,rows,widths)` → `pf.save(d,path)`.
- Annex: `pf.new_annex(code, version, mk_title, en_title, orient)` → `pf.annex_title_block(...)` →
  `t=pf.annex_table(d,widths)` → `pf.annex_section_header(t,mk,en)` (navy) / `pf.annex_row(t,values,bold_first,alt)`
  → `pf.annex_finalize(t)` ; `pf.annex_signoff(d)` → `pf.save(d,path)`.
- Reports/records with formulas/charts/forms: `pp_report.py` (`cover_page`, `chapter`, `calc_step`,
  `eqn`, `entry_table`, `execution_signoff`, `figure`) — see `SKILL.md` §3.7.

## Markdown source convention (input to `build_from_md.py`)

```
<!--HEADERDATA
mk_title / en_title / code / version / doctype (SOP|ANNEX|FORM|LOG|CHECKLIST) / supersedes / parent / orient
-->
# 1. ЦЕЛ | PURPOSE            -> SOP: two-col section row · Annex: navy banner
## 1.1 Наслов | Subtitle      -> SOP: subsection row · Annex: label sub-bar
Реченица. ||| Sentence.        -> bilingual body (SOP two-col · Annex justified paragraph)
- Точка ||| Bullet
[[TABLE]]  Заглавје ~~ Header ||| ...   [[/TABLE]]   -> row 1 = navy header, rest = zebra data
[[FORM]]   Поле ||| Field ||| _         [[/FORM]]    -> label cell (#EDF2F7) + empty entry cell
```
`|||` = MK|EN separator; `~~` = MK~~EN inside a table cell; `_` = blank entry (never underscores).

## MANDATORY workflow & gates

1. Read `pp-document-suite/SKILL.md` (master router: SOP vs Annex; Mode A content / B format / C restyle).
2. Content per SKILL §2 (SOP 9-section; annex mandatory fields; quantify; cite the clause).
3. Build via `scripts/build_from_md.py` (engine). **Never** style by hand.
4. `pp_verify.py` must print **RESULT: PASS** (font floor ≥ 6 pt, bilingual, fidelity).
5. Render to PDF and **look at it** — header/logo, navy banners, tables, footer must match the
   reference docs `PP_SOP_SS/QCSOP_018_A08/A10` and the engine smoke output.
6. Native TOC (SOP) shows blank until fields are updated in Word (Ctrl+A → F9) — that is expected.

## DO-NOT

- ❌ Do not write a parallel/hand-rolled formatter. Use `pp_format.py` / `pp_report.py`.
- ❌ Do not invent colours. The only navy is `#2B547E` (`pp_theme.NAVY`).
- ❌ Do not drop the base-template header/footer/logo, or render below 6 pt, or use `_` placeholders.
- ❌ Do not guess the look — render and compare, every time.
