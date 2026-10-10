# docengine/engine — vendored pp-document-suite

**Since 09.10.2026 this directory is an exact copy of the repository's `pp-document-suite/`**
(`scripts/` — the `.py`, `.sh` and `.ps1` files — `assets/` and `references/`). The Head of QC
ruled that the DocEngine runs the current suite (canon revision noted at the top of
`docs/wwf_DOCENGINE-CANON-2026-07.md`).

- **Do not edit files here.** Change `pp-document-suite/`, then run `engine/sync_from_suite.sh`.
- `tests/test_engine_sync.py` fails CI if this copy and the suite differ in any file.
- The copy exists only because the DocEngine image is built from `apps/wwf-docengine/`.

What the previous line (canon-2026-07: ZIP v1.7.0 + ACME_SOP grafts) had that the suite lacked
was ported into the suite before the switch, so nothing was dropped: `kv_block`, `cell08`,
`value_span`, `_merge` and `sop_nested_table` (`pp_format.py`), the `pp_format_layout_addons.py`
re-export shim, `pp_verify.py --require-bilingual`, and the line-anchored HEADERDATA parser in
`build_from_md.py`. The previous line's provenance is in git history before this commit.
