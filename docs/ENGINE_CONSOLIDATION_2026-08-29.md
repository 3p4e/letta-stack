# PP document engine — two diverged lines, and how to pick one (2026-08-29)

Decision record and bake-off design. **No engine wiring changes in this batch.**
Repointing the engine changes rendered output for *controlled documents*, which needs
its own regression pass against previously issued documents; mixing that into a
security batch risks neither landing cleanly.

The purpose here is to replace assertion with evidence. Both trees carry documentation
calling themselves canonical, and both are wrong about the other.

## The two lines

| | `pp-document-suite/` (root) | `apps/wwf-docengine/engine/` (vendored) |
|---|---|---|
| Consumers | the Letta tool `build_pp_document`, ~7 deliverables builders, ppdocwiz | the GrowFlow DocEngine service |
| Calls itself | "MASTER (post-cutover 2026-08-08)" — `README.md`, `engine_sync.md` | "vendored **canonical** pp-document-suite" — `engine/PROVENANCE.md` |
| Maintained since consolidation | yes — `593e7f7`, 2026-08-14 | no — untouched since import |

Both entered this repository at the same commit (`da12dbe`), so the divergence is
inherited from the two upstream sources, not created here.

## Which one does the Letta stack actually run

Root. This was the first draft's error — it called root "superseded", which is
backwards — so the evidence is set out rather than asserted.

The registered tool `build_pp_document` runs from `/root/.letta/pp-document-suite`.
`server/runbooks/engine_sync.md` records the hashes installed on that volume. Comparing
them to both trees as they stand today:

| File | Volume (per `engine_sync.md`) | Root | Vendored |
|---|---|---|---|
| `build_from_md.py` | `a8a35700` | **`a8a35700`** ✅ | `dfdd5271` |
| `pp_format.py` | `1d54edab` | **`1d54edab`** ✅ | `7aa1d076` |
| `pp_report.py` | `1be84f35` | `64ac6704` | `86feab6a` |
| `pp_verify.py` | `a2060978` | `d045d6b4` | `99d9a57b` |

Root matches the volume exactly on **two of four**; the vendored copy matches on
**none**. Root is the Letta-stack engine. ppdocwiz already points at it correctly.

## The capability split — it runs both ways

This is the part that makes the decision a real one. Only `pp_theme.py` (`4fad64b1`)
is byte-identical between the trees; every other file differs.

> **Superseded 29.08.2026 for the two capabilities below.** Root has since had the
> overflow compression and the word-boundary matching restored (see the `593e7f7`
> resolution). The description is kept because it is what the vendored line's
> `PROVENANCE.md` documents and what the graft actually does — but it is no longer a
> capability root lacks.

**Only the vendored line had** content-aware table handling. Its `pp_format.fixed()`
carries the graft `PROVENANCE.md` documents, with the marker comment at the graft site:

- **Overflow compression.** Each column is floored to its widest *data* cell (data must
  never wrap) and to its header's longest single token (headers may wrap, but not below
  a word). If even those floors overflow the page, width is shared proportionally;
  otherwise the slack goes to the longest headers, so headers wrap least where they are
  longest.
- **Word-boundary entry matching.** `re.search(r'\b' + k, h)` rather than `k in h`, so
  that — per its own comment — `'име'` inside `'примерок'` is **not** a hit. The
  substring form mis-sizes any column whose header happens to contain a keyword.

It also carries `pp_format_layout_addons.py`, a re-export shim, and its `pp_format.py`
is 612 lines against root's 331.

**Only the root line has** the delivery-gate glyph guard. `pp_assets.py` (203 lines,
added 2026-08-14) provides `missing_glyphs()`, `audit_docx()` and `check_environment()`,
and `pp_verify.py` calls them, so a run whose declared font cannot render its own text
**fails verification** instead of shipping. That is the fix for the real incident where
subset Carlito webfonts with no Cyrillic shadowed the system font and scrambled
Macedonian into tofu. Root also holds the brand assets, the verified
Carlito/Montserrat fonts and `pp_setup_fonts.sh`.

Neither line had both capabilities — that was the whole decision in one sentence, until
the restore put both on root. **What remains genuinely open is everything else**: root's
`pp_format.py` is 331 lines against the vendored 612, the vendored tree carries
`pp_format_layout_addons.py` that root does not, and `pp_charts.py` and `pp_data.py`
differ between the two by a line or two each with nobody having read the diffs. Those
have not been examined and are what the bake-off is now for.

## Two documentation claims that are no longer true

**1. `PROVENANCE.md` says four files are "identical in both lines".** Today only one is.

| File | Root | Vendored | Claim |
|---|---|---|---|
| `pp_theme.py` | `4fad64b1` | `4fad64b1` | holds ✅ |
| `pp_charts.py` | `7251e1d0` (128 ln) | `6fe89440` (137 ln) | stale |
| `pp_data.py` | `4aed5f77` (133 ln) | `36e0b4af` (134 ln) | stale |
| `pp_verify.py` | `d045d6b4` (101 ln) | `99d9a57b` (84 ln) | stale |

The claim was presumably true when the vendoring was done; root has moved since. It is
a snapshot presented as a standing fact, which is how it misleads.

**2. Both trees call themselves canonical.** `README.md` and `engine_sync.md` name root
MASTER as of the 2026-08-08 cutover; `PROVENANCE.md` names the vendored copy canonical
per `DOCENGINE-CANON-2026-07.md`. Both are internally consistent and mutually
exclusive. **Whichever line wins the bake-off, the loser's canon document must be
amended in the same change** — otherwise this recurs.

## ⚠️ Two things to settle before any sync

**A regression in root that no commit message mentions.** Root's `pp_report.fixed()`
*used to have* the same overflow-compression and word-boundary logic the vendored line
carries. Commit `593e7f7` — whose message is entirely about Macedonian glyph rendering,
the weekly report and brand assets — replaced it with the simpler form: substring
matching, and `ideal[j] = max(ideal[j], min(L,cap)*CHCM+PAD)` with the
`data_cm`/`hdr_cm`/`word_cm` machinery deleted.

**Resolved 29.08.2026 — and the guess above was wrong.** It was not a wholesale import
from an older source. The same commit also added `informal_header()` and
`cover_page(controlled=False)`, which are exactly what its message describes and are
correct; it was a genuine edit to the file that took collateral damage in `fixed()`.
None of the 60 changed lines in `pp_report.py` mention a font, a glyph or an asset.

The logic has been restored surgically — `fixed()` is byte-identical to its
pre-`593e7f7` state, the informal-header work is untouched — and is now covered by
`pp-document-suite/tests/test_layout.py`, whose two key cases were run against the
regressed version and fail there. **Root therefore now carries both contested
capabilities**, which changes what the bake-off is comparing.

**A naive sync would push that regression onto the live volume.** The volume runs
`pp_report 1be84f35` — the *pre-*`593e7f7` version, which **has** the overflow
compression — and `pp_verify a2060978`, which **lacks** the glyph guard. So today:

| | Overflow compression | Glyph guard |
|---|---|---|
| Live Letta volume | ✅ | ❌ |
| Root (repo master) | ❌ | ✅ |

The live tool and its own master each have exactly one of the two. Syncing root → volume
under the current runbook would install the glyph guard **and** remove working table
sizing from the engine that builds controlled documents. **Do not run the
`engine_sync.md` procedure until the `pp_report` question above is answered.**

That the gap exists at all is the second finding: sync is manual and hash-gated, and
nothing detects drift between the master and the volume. Whatever engine wins, a drift
check belongs in CI or in the runbook's step 1 as an automated probe rather than an
instruction to remember.

## Consumer inventory — every one is a migration site

**Root engine:**

- `apps/ppdocwiz/` — `Dockerfile`, `docker-compose.yml`, `backend/app.py`,
  `backend/wizard.py`, `tests/conftest.py`
- `deliverables/potency_study/` — `build_potency_report.py`,
  `build_potency_atlas_docx.py`, `render_figures.py`
- `deliverables/batch_thc_summary/build_summary.py`
- `deliverables/qc_weekly/build_qc_weekly.py`
- `ingestion/coa_track/letta-imb-coas/reports/` — `build_qc_activity_report.py`,
  `build_qc_consolidated_report.py`
- the Letta volume `/root/.letta/pp-document-suite`, via `engine_sync.md`

**Vendored engine:** the GrowFlow DocEngine service in `apps/wwf-docengine/`, through
its own `app/builder.py`.

Root has by far the larger consumer surface, which is an argument about **migration
cost**, not about which engine is better. Keep the two separate when deciding.

## The bake-off

Per the owner: give both engines the same prompt to produce a one-page document, and
judge from the output. Provenance claims are what got us here; rendered pages are
what settle it.

1. **Settle the `593e7f7` question first.** Comparing against an accidental revert
   measures the wrong thing.
2. **Pick three sources already in the repository**, chosen so each exercises a
   contested capability rather than agreeing trivially:
   - an SOP — the ordinary case;
   - an annex with `[[FORM:grid]]` — the content-aware packing the vendored
     `build_from_md` claims to improve;
   - a report with a **wide bilingual table** — the case the `fixed()` graft exists for,
     and where the two lines should differ most visibly.
   Include Cyrillic body text in all three, so the glyph guard is exercised too.
3. **Build each through both** — root `pp-document-suite/scripts/build_from_md.py` and
   `apps/wwf-docengine/engine/scripts/build_from_md.py` — into separate output
   directories. The docengine tree is used **read-only**; nothing there is edited.
4. **Run each engine's own `pp_verify` on its own output.** Both must PASS. A failure is
   a defect to fix, not a preference to weigh — and note that only root's verify checks
   glyphs, so a vendored PASS is a weaker statement than a root PASS.
5. **Render to PDF and compare page by page**, with images: overflow handling, form-grid
   packing, table fitting, and Cyrillic rendering.
6. **Owner picks.** Only then does any wiring change — as its own commit, with a
   regression pass against previously issued documents, and with the losing line's canon
   document amended in the same change.

**Do not assume the vendored copy wins.** Its grafts are documented intentions; step 5
is what turns them into evidence. The likely outcome is that neither line wins outright
and the answer is a merge — the vendored `fixed()` into root, which already has the
glyph guard, the assets and the consumers. That is a hypothesis to test, not a
conclusion to adopt.

## Rollback

The volume keeps timestamped `.bak.*` copies of every file the sync procedure
overwrites, restored through the same hash-gated mechanism. In the repository both
trees remain intact until a decision lands, so a wiring change is a one-line revert of
whichever `Dockerfile`/`PP_SUITE_DIR` was repointed. Nothing here is destructive.
