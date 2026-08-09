# GrowFlow DocEngine — Canonical Instruction Set (2026-07)

**Status:** BINDING. This is the single source of truth for how the GrowFlow
DocEngine generates and formats Purely Plant documents. It was produced by an
in-depth, cross-source comparison of **every** instruction source the owner
provided — the v1.7.0 skill ZIP, the `3p4e/ACME_SOP` repository (full git
history), both Google Drive `pp-document-suite` mirrors, the legacy root
skills, and the **live deployed engine** read read-only from the Letta server.
Where sources conflict, the "winner" column below is authoritative and the
reason (date / content) is given. Stage 1 vendors exactly the merged engine
described here.

> **GxP guardrail (overrides everything):** never fabricate pharmaceutical
> data. If a value is not in the source, the field stays **blank** for a human
> to fill — never guessed. A document is shipped **only** when `pp_verify.py`
> prints `RESULT: PASS`.

---

## 1. Sources compared (provenance)

| # | Source | How read | Effective date |
|---|--------|----------|----------------|
| A | **pp-document-suite v1.7.0 ZIP** (Drive `1Kzw0aLcHGczPU4_T9yFNXGrxgy-UFbk3`) | unpacked, 13 files | SKILL 1.7.0; `pp_format.py` 2026-07-01, `pp_report.py` 2026-07-01 |
| B | **`3p4e/ACME_SOP`** branch `claude/cannabis-import-sop-docs-uju5fb` | cloned, 600 files + history | engine SKILL 1.6.2; commits through **2026-07-14** |
| C | **Drive `pp-document-suite` mirror #1** (`1Q9Ba_…`) & **#2** (`10_eICI7V0y…`) | listed + dated | Jun-22 / Jul-11 — both older than A/B |
| D | **Legacy root skills** (`SKILL pp-content-developer-v3`, `pp-template-formatter-v3`, `pp-annex-content-creator-v1`, `SKILL-05_PP-mVAL_Formatter_v1_4`) + ADDENDUM | in repo B | superseded by content (folded into 1.6.x/1.7.0) |
| E | **LIVE deployed engine** — Letta REST `build_pp_document` / `fetch_pp_document` `source_code` | GET (read-only) via `$LETTA_API_KEY` | deployed ≈ 2026-07-10 = repo lineage, **pre-Jul-14** |
| F | **`qms-creator/`** CONTENT_CREATOR_FRAMEWORK (in this repo) | read | oldest; workflow-shape source only |

Confirmed live (read-only): **9 Letta sources** — `DB1_REGULATORY`,
`DB2_GMP_PRO`, `DB3_PP_CURRENT_unified`, `PQ1 Water Testing…` (3072-dim
outlier), `ImB_QC_COAs`, `CoA_Individual_Split`, `Equipment_Manuals_PP`,
`Superior_Primary_Packaging`, `GrowFlow_Weekly_Snapshots`. The handover's
Rust-MCP decode bug reproduced (`missing field 'package'`); **direct REST is
the working path** and is what the DocEngine uses.

**Live tool truth:** `build_pp_document(markdown, out_name)` writes to
`/root/.letta/pp-out`, runs `build_from_md.main()` then in-process
`pp_verify`, returns `{ok, verify, path, bytes}`. `fetch_pp_document(path)`
returns the .docx as base64. This is the exact contract the DocEngine
reproduces natively (no dependency on the shared Letta container's filesystem).

---

## 2. The central finding — the two lines DIVERGED (~Jul 1)

There is **no single most-advanced source**. After the ZIP (A) was cut on
Jul 1, the repo (B) kept advancing *different* components through Jul 14. The
ZIP advanced others that never went back to the repo. "Most advanced" is
therefore a **per-component merge**, not a pick.

| Component | WINNER | Why (date / content evidence) |
|-----------|--------|-------------------------------|
| **SKILL instruction text** | **A (ZIP v1.7.0)** | strict superset of B's 1.6.2: adds §6D **D1–D8** layout/revision canon (dated 2026-06-30) + 2 new checklist gates (§6 layout & engine-route). |
| **`pp_format.py`** | **A (ZIP, 604 vs 331 lines — strict superset)** | adds `kv_block`/`cell08`/`value_span`/`_merge` (compact metadata, §6D), `sop_nested_table`, **parameterized approval roles** (removes hardcoded personnel names — GxP win), header double-code fix, bilingual empty-EN fix, auto annex layout (`annex_table(ncol=…)`), and hosts `fixed()` as the shared brain. |
| **`fixed()` layout algorithm** | **B (repo, 2026-07-14, inline in `pp_report.py`)** | B's `fixed()` has data-driven overflow **compression** (`data_cm`/`hdr_cm`/`word_cm` floors → longest headers get slack) and **word-boundary** entry matching (`\b`-anchored, so "име" in "примерок" is not a false hit). A's copy of `fixed()` lacks both. → **graft B's `fixed()` into A's `pp_format.py`**. |
| **`build_from_md.py`** (Markdown→docx adapter) | **B (repo — A has NONE)** | B's `[[FORM:grid]]` content-aware **per-field packing** (each label sized to its own longest word, each value to its own write-in, greedy first-fit) is the most advanced realization of §6D D4/D7. The ZIP ships no Markdown adapter at all. |
| **`pp_report.py`** | **A (ZIP)** — imports `fixed` from `pp_format` | A already dedupes the brain (`from pp_format import fixed, PAGE_W, …`), eliminating drift. Rest of file equivalent to B. |
| `pp_charts.py` · `pp_data.py` · `pp_theme.py` · `pp_verify.py` | identical in A & B | `diff -rq` clean. |
| **references** | **UNION** | A's 3 (`formatting_specs.md`, `questionnaire_library.md`, one more) **+** B's `GUIDE_bilingual_markdown.md` **+** B's `PP_UNIFIED_DOCX_GUIDE.md` (the `build_from_md` grammar spec). |
| Deployment artifacts (`Dockerfile`, `LETTA_INTEGRATION.md`, `integrations/`, `openapi_letta.json`) | B only | reference material for the FastAPI service. |
| **Deployed Docker engine (E)** | **SUPERSEDED** | repo@≈Jul-10: no `kv_block`, pre-grid-packing. The DocEngine is strictly ahead of what's live. |
| **Agent workflow SHAPE** (questionnaire → section authors → regulatory check → assemble) | **F (`qms-creator/`)** — shape kept, texts superseded | its pipeline topology is sound; its instruction *texts* are older and yield to A/B where they conflict. |

### Canonical engine (what Stage 1 vendors)

```
docengine/engine/            ← vendored, provenance-stamped
  pp_theme.py                = A (≡ B)
  pp_format.py               = A (ZIP v1.7.0)  ── with B's Jul-14 fixed() grafted in
  pp_report.py               = A (imports fixed/PAGE_W from pp_format)
  pp_format_layout_addons.py = A (re-export shim; §6D filename ref must resolve)
  pp_charts.py               = A (≡ B)
  pp_data.py                 = A (≡ B)
  pp_verify.py               = A (≡ B)  ── the hard PASS gate
  build_from_md.py           = B (repo Jul-14, grid mode)  ── the Markdown adapter
  assets/PP_BASE_TEMPLATE.docx = A (header/footer/logo template)
  references/                = UNION (A's 3 + B's GUIDE_bilingual_markdown.md + PP_UNIFIED_DOCX_GUIDE.md)
```

**Import reconciliation (proven empirically in Stage 1):** `build_from_md.py`
(B) calls `pr.fixed`, `pr.PAGE_W`, `pr._apply_widths`, `pr.cellfmt`, `pr.rin`,
`pr.borders`, `pr.status_grid`. A's `pp_report.py` re-exports `fixed`/`PAGE_W`
from `pp_format`, so `pr.fixed` resolves to the **grafted** (upgraded)
algorithm automatically. Any helper B's adapter needs that A's `pp_report`
lacks is reconciled in Stage 1 and covered by an offline build+verify test —
a mismatch fails CI, never a shipped document.

---

## 3. Canonical house style (verbatim, from A — do not drift)

- **One house navy `#2B547E`** (`pp_theme.NAVY`). Never a second navy.
- Palette: label `#EDF2F7`, zebra `#F7FAFC`, pass/mint `#E2EFDA`, fail/rose
  `#FCE4D6`, caution/cream `#FFF2CC`, gridline `#B0BEC5`.
- Body font **Calibri**; annex header doc-name **Arial Narrow**.
- **Font floor ≥ 6 pt** — `pp_verify` FAILS any `w:sz` < 12 half-points.
- Shading type always `clear`, **never `solid`**.
- **Bilingual Macedonian-first**; decimal commas in MK; abbreviations
  untranslated. Inline `MK | EN`; separator omitted when EN is empty.

### Document types & routes (§0 master router — resolve BEFORE generating)
- **SOP** → mandatory **9-section** structure, **two-column** MK|EN with a
  0.5 pt vertical divider, native Word TOC (levels 1–3), gray `#E8E8E8`
  section headers (**never green**), §7/§8/§9 as nested full-width tables.
  9 sections: 1 ЦЕЛ/PURPOSE · 2 ПОДРАЧЈЕ/SCOPE (2.1 Applicability, 2.2
  Exclusions, 2.3 Future Extension) · 3 ОДГОВОРНОСТИ/RESPONSIBILITIES · 4
  РЕФЕРЕНТНИ ДОКУМЕНТИ/REFERENCES · 5 ДЕФИНИЦИИ/DEFINITIONS (5.1/5.2) · 6
  ПОСТАПКА/PROCEDURE (all procedural; training & deviation as final 6.x) · 7
  ЗАПИСИ/RECORDS · 8 ПОВРЗАНИ/RELATED · 9 РЕВИЗИЈА/REVISION.
- **Annex / Form / Checklist / Log** → **inline full-page** bilingual
  "МК 11pt | EN 7pt"; navy `#2B547E` section-header rows with **white** text;
  built via the **annex** path (`new_annex` + annex helpers + `kv_block`),
  **never** via `pp_report` report helpers.
- **Report / computational record** → `pp_report.py`: native OMML equations,
  worked calculations, execution forms, charts, cover + TOC + per-step
  two-role sign-off. Statistics **derived** via `pp_data` — never typed.
- **MODE A** content-develop (questionnaire) → **MODE B** format → **MODE C**
  restyle existing draft.

### §6D layout & revision canon (2026-06-30; verified in the §6A review)
- **D3** use-aware column widths (ordinal ~0.8 cm; value cells sized to
  hand-entry via `value_span`, **not** maximised).
- **D4/D8** pack "label|value" summaries multi-pair-per-row on the 6-col grid
  (`kv_block`); merge related sections into ONE table; every cell line-spacing
  0.8 / no space before-after.
- **D2** annexes/forms via `new_annex` + annex helpers, never `pp_report`.
- **D5** SOP revisions **regenerated** through `new_sop` with the full prior
  version as context (≥100 % content — §5A), never row-patched into a legacy
  .docx.
- **D6** from a sample, take **structure not style**.

### Verify gate (`pp_verify.py`, hard PASS/FAIL)
Checks structure (paras/tables/oMath/figures), typography (min font ≥ 6 pt),
bilingual presence (Cyrillic + Latin), and — with `--source` — **content
fidelity §5A** (output words & chars ≥ Σ source; no impoverishment). Exit 0 =
PASS. **The DocEngine never returns a document on FAIL.**

---

## 4. Bilingual Markdown grammar (from B `PP_UNIFIED_DOCX_GUIDE.md`)

`build_from_md.py` consumes:
- `<!--HEADERDATA … -->` front-block: `mk_title`, `en_title`, `code`,
  `version`, `doctype` (SOP/ANNEX/FORM/CHECKLIST/LOG), `parent`, `orient`.
- Headings `# …` with `|` splitting MK|EN; auto-numbered.
- `[[TABLE:mode]]` / `[[FORM:mode]]` … `[[/…]]` blocks; rows use `|||` between
  columns; `~~` splits MK~~EN inside a cell.
- `[[FORM:grid]]` → content-aware per-field packing (the Jul-14 win).
- Single-select option lists → `status_grid()` compact checkbox grid.

This grammar is the DocEngine's internal assembly target: the agent fleet
produces bilingual Markdown in exactly this grammar; the formatting core turns
it into the controlled .docx.

---

## 5. Agent fleet mapping (SHAPE from F, TEXTS from A/B canon)

The `qms-creator/` pipeline topology is retained and namespaced `gf_*`
(ADDITIVE — the ~54 existing live agents are never modified, per the handover
caution). Each agent's instructions are (re)written from **this canon**, not
from F's older texts:

- **Orchestrator** — runs the §0 router (TYPE + MODE), sequences the pipeline.
- **Section authors** (9-section SOP) — one per section responsibility.
- **MK⇄EN translator** — bilingual parity, Macedonian-first, decimal commas.
- **Regulatory checker** — bound to the **real** sources `DB1_REGULATORY` +
  `DB3_PP_CURRENT_unified` (PQ1 **excluded** — 3072-dim outlier); cites real
  passages; never fabricates a clause.
- **RACI / responsibilities specialist**, **annex/table specialist**,
  **QA auditor** (runs the §6A review + `pp_verify` interpretation), plus
  general assistant agents for the app's other AI features.

Provider config follows what the live server actually accepts (the handover's
`model_endpoint_type:"other"` write-rejection makes this a **create-new**
path, never an edit of existing agents). `fleet.py` ensure-loop: create-by-
name if missing, attach sources, set the shared `pp_house_rules`-equivalent
memory block **from §3 of this canon**.

---

## 6. What this canon explicitly rejects

- The **legacy Node `docx-js`** engine (D) — replaced by python-docx.
- Hardcoded personnel names in approval blocks (present in B's `pp_format`) —
  the ZIP's parameterized-roles version wins (GxP: identity belongs to the
  document, not the generator).
- The **older `fixed()`** in A's `pp_format` and in the deployed engine (E) —
  replaced by B's Jul-14 algorithm.
- Any second navy, any `solid` shading, any sub-6pt font, any typed statistic,
  any guessed pharmaceutical value.
- The imported `qms-creator/` **empty** `db1_regulatory`/`db2_entity_qms`
  archives — the real knowledge base is the live Letta sources, not those.
