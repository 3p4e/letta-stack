# docengine/engine — vendored canonical pp-document-suite

Assembled per **docs/DOCENGINE-CANON-2026-07.md** (the binding per-component
version decision). Do not edit these files ad hoc — changes go through a canon
revision.

| File | Source | Note |
|---|---|---|
| `scripts/pp_theme.py`, `pp_charts.py`, `pp_data.py`, `pp_verify.py` | ZIP v1.7.0 (≡ repo) | identical in both lines |
| `scripts/pp_format.py` | ZIP v1.7.0 **+ graft** | `fixed()` replaced with the ACME_SOP repo version @ 2026-07-14 (data-driven overflow compression + word-boundary entry matching); marker comment at the graft site |
| `scripts/pp_report.py` | ZIP v1.7.0 | imports `fixed`/`PAGE_W` from `pp_format` (one layout brain) |
| `scripts/pp_format_layout_addons.py` | ZIP v1.7.0 | re-export shim (§6D filename reference) |
| `scripts/build_from_md.py` | ACME_SOP repo @ 2026-07-14 | Markdown adapter incl. `[[FORM:grid]]` content-aware packing |
| `scripts/render_pdf.ps1` | ZIP v1.7.0 | Windows-only; service uses Gotenberg instead |
| `assets/PP_BASE_TEMPLATE.docx` | ZIP v1.7.0 | house header/footer/logo |
| `references/formatting_specs.md`, `questionnaire_library.md`, `regulatory_and_context.md` | ZIP v1.7.0 | |
| `references/GUIDE_bilingual_markdown.md` | ACME_SOP repo | Markdown grammar |

Origins: ZIP = `pp-document-suite_v1.7.0.zip` (owner's Drive,
`1Kzw0aLcHGczPU4_T9yFNXGrxgy-UFbk3`); repo = `3p4e/ACME_SOP` branch
`claude/cannabis-import-sop-docs-uju5fb` @ `2ad7be8`.
