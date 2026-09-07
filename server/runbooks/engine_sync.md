# pp-document-suite engine sync — repo master → Letta volume (Mode A)

**Master (post-cutover 2026-08-08):** the `3p4e/letta-stack` repo → `pp-document-suite/scripts/`.
(Previously `3p4e/ACME_SOP`, now a frozen mirror pending its deprecation pointer.)
**Deployment target:** `/root/.letta/pp-document-suite/` inside the `letta` container
(persistent volume; survives container recreation; an image REBUILD clears `/root/.letta/pp-libs`
→ reinstall with `pip install --target=/root/.letta/pp-libs python-docx lxml`).

Canonical hashes as of the 2026-07-30 sync (verified again live 2026-08-08):

| file | sha256[:8] | bytes |
|---|---|---|
| build_from_md.py | `a8a35700` | 14 055 |
| pp_report.py | `1be84f35` | 32 842 |
| pp_format.py | `1d54edab` | 16 538 |
| pp_verify.py | `a2060978` | 3 357 |

> **Hold lifted 29.08.2026 — but re-hash before you sync.** The hold existed because
> the drift ran both ways: the volume's `pp_report 1be84f35` carried the table
> overflow-compression logic that `593e7f7` had removed from the master, so a sync
> would have installed the glyph guard **and** taken working table sizing off the
> engine that builds controlled documents. That logic has since been restored to the
> master and is covered by `pp-document-suite/tests/test_layout.py`, so the master now
> carries both capabilities and a sync installs both.
>
> The hashes in the table below therefore no longer describe either side. **Re-run
> step 1 and record the new pair before transferring anything** — do not sync against
> the stale figures. Background: `docs/ENGINE_CONSOLIDATION_2026-08-29.md`.

Procedure (as executed and proven):
1. **Diff first** — `run_from_source` probe hashes the volume files; compare to repo hashes.
2. **Transfer** — gzip+base64 through `run_from_source`, with a SHA-256 gate at the destination:
   decode → hash → compare to the expected repo hash → only then back up the old file
   (`<name>.bak.<timestamp>`) and overwrite → re-hash the installed file. Chunk ≤ ~5 KB per
   call if a one-shot payload exceeds ~14 KB. Never bypass the gate.
3. **Smoke test on the volume** — build a doc through the volume engine; `pp_verify` must PASS.
   `build_pp_document` reloads modules per call → no Letta restart needed.
4. **Rollback** — restore the `.bak.*` files via the same mechanism.
5. Re-run `scripts/export_manifests.py` and commit, so the stack state is versioned.
