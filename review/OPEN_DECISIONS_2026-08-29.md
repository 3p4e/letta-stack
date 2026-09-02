# Open decisions — what needs an owner ruling (2026-08-29)

Companion to `APP_SECURITY_REVIEW_2026-08-29.md`, which records the findings, and to
`docs/ENGINE_CONSOLIDATION_2026-08-29.md`, which records the engine evidence. This one
records only what is **still open**, and who has to decide it.

## Why this exists

Six commits of security and CI remediation landed on `claude/google-drive-links-d932ku`.
Eleven of sixteen findings closed in the repository; the rest could not, because they are
live-stack decisions, QC rulings, or changes that would break working callers if rushed.

Separately, the QC coverage analysis, the independent cross-check, the RAGFlow health
audit, the Letta topology audit and the potency grade design each left decisions parked
in their own document. Nobody had a single list, so an item needing a QC Manager's ruling
sat next to one needing an SSH session, and neither got picked up.

Twenty-four items. Each carries what the thing actually does, why it is open, the
options, a recommendation, and what changes if it is taken. Where the recommendation is
"I cannot make this call", it says so and why.

## How to read it

| Mark | Meaning |
|---|---|
| 🔴 | Live risk or data integrity — decide now |
| 🟠 | Needs your ruling; nothing is bleeding while it waits |
| 🟢 | Low-risk and reversible — **proceeding by default**, listed so the default is visible |

| Owner | Meaning |
|---|---|
| **Host** | Needs SSH / dockge on KVM4. I cannot reach it from here. |
| **QC** | A QC Manager's ruling. Not a technical question. |
| **Repo** | I can do it on the branch. |

---

# A. Live exposure — nothing here is closed by merging the PR

### A1 🔴 **Host** — kvm4-runner is internet-facing with root-equivalent access

**What it is.** A deliberate SSH substitute. Outbound port 22 is blocked from cloud
Claude Code sessions, so the same surface SSH would give — run a shell, exec in a
container, move files — is exposed as JSON over HTTPS at
`runner.srv1231216.hstgr.cloud`, behind one bearer token. Its own README says it:
"anyone holding the token has root-on-host equivalent."

**Why it is open.** I hardened the code (`4c86726`): constant-time token compare,
audit logging on the file endpoints, a timeout on `/exec/stream`, writes confined to a
root, API docs disabled. **None of that is running.** Editing `runner.py` here changes
nothing on the live service. Worse, `deploy.py` inlines the source as a heredoc, so the
deployed copy may not even match the repo copy and nothing verifies it.

**Options.** (a) Rotate `RUNNER_TOKEN` and redeploy with the hardened build.
(b) Put a Traefik IP-allowlist middleware in front of the router now, redeploy later.
(c) Take the route down until you need it.

**Recommendation: (b) then (a).** The allowlist is minutes and closes the exposure to
the internet immediately; the redeploy can follow at your convenience. Do **not**
decommission — no session here can reach the host, so this is the intended path for
exactly this kind of work.

**What changes.** After (b), only your allowlisted IPs reach the runner; everyone else
gets a 403 at Traefik. After (a), the old token stops working — anything holding it
breaks, which as far as the repo shows is only `deploy.py` itself. Diff the deployed
source against the repo copy before and after, because of the heredoc drift.

---

### A2 🔴 **Host** — RAGFlow MCP authenticates no client and is publicly routed

**What it is.** The Model Context Protocol server in front of RAGFlow, so an AI client
can query your certificate corpus as a tool. Running in `--mcp-mode=self-host`.

**Why it is open.** Your own enablement doc records it plainly: in self-host mode the
server *"authenticates no client. Anyone who reaches
`ragflow-mcp.srv1231216.hstgr.cloud/mcp` is served as the tenant"* — read access to
every dataset, i.e. the whole eCoA corpus. Wildcard DNS is live, so the hostname is
guessable. **You accepted this risk on 25.08.2026.** It is listed here for
reconsideration, not to overturn your call.

**Options.** (a) Leave it — the accepted risk stands. (b) Switch to
`--mcp-mode=host`; every client then presents its own RAGFlow key. (c) Traefik
middleware in front of the router (IP allowlist or basic auth), keeping self-host mode.

**Recommendation: (c).** It closes public reachability without touching client
configuration, and it is the same mechanism as A1(b), so it is one piece of work.
(b) is the more correct fix but every client — including your desktop Claude — needs a
key issued and configured.

**What changes.** With (c), the corpus stops being reachable from any address you have
not allowed. Your desktop Claude keeps working if its IP is on the list; if you work
from changing networks, (b) is the better shape.

---

### A3 🔴 **Host** — the Letta API is unauthenticated, and the cause is a typo

**What it is.** Letta's own password middleware. It reads the environment variable
`LETTA_SERVER_PASSWORD` and installs only when the container is started with
`SECURE=true`.

**Why it is open.** The deployment sets **`LETTA_SERVER_PASS`** — a different name. So
`LETTA_SERVER_PASSWORD` is unset, Letta generates a random password nobody holds, and
with no `SECURE` flag the middleware never installs at all. An unauthenticated
`GET /v1/agents` succeeded against the live server during the 12.08 audit. This is what
made the ppdocwiz chat proxy a credential-exfiltration chain rather than a nuisance.

**Options.** (a) Rename the variable, set `SECURE=true`, set a strong secret.
(b) Leave it and rely on network isolation.

**Recommendation: (a).** It is a one-word rename plus a flag. (b) depends on the Traefik
topology question in E5, which the repo cannot currently answer — so it is trusting
something unverified.

**What changes.** Every Letta API caller needs the password. That includes
`letta-mcp-rust`, `wwf-scheduler`, `weekly_weed_flow-backend-1` and any script using
`LETTA_TOKEN`. **Do this in a maintenance window** and update those callers together, or
they fail closed. This is the item most likely to break something, and that is precisely
because nothing is authenticating today.

---

### A4 🔴 **Host** — the RAGFlow API key is still in git history

**What it is.** A live RAGFlow key committed at `83ae904` in `.claude/settings.json`
before it was moved to a gitignored local file.

**Why it is open.** Moving the file does not remove it from history. It is allowlisted
in `.gitleaks.toml` by commit with a note, so the secret scan still passes and *new*
leaks still fail — but the key itself is exposed to anyone who can read the repository.

**Options.** (a) Rotate the key in RAGFlow, then delete the allowlist entry.
(b) Rewrite history to purge the blob. (c) Leave it.

**Recommendation: (a).** Rotation is the actual fix; history rewriting on a shared
branch causes more damage than it prevents, and the key is worthless once rotated.

**What changes.** The old key stops working, so anything using it needs the new value —
`ingest_coa_database_2026.py`, `reclassify_watcher.py`, and your desktop MCP client.
Once rotated, the `83ae904` allowlist entry comes out of `.gitleaks.toml` so a future
leak of that same shape fails CI again.

---

# B. Data integrity — batches already released

### B1 🔴 **QC** — roughly thirteen certificates released against failing results

**What it is.** The independent cross-check compared certificate *values* against
certificate *limits* — a question the coverage analysis never asked, because it only
asked whether a panel had been tested.

**Why it is open.** **Five IPH microbiology certificates report a count above the
acceptance criterion while still concluding ОДГОВАРА** (conforms): `320/0587/25`
(GG1024-01, 42 000), `1032/1851/25` (CJ062501/2, 49 000), `946/1684/25` (GP052501, 36 000),
`904/1589/25` (OPM052501, 33 000) and `948/1686/25` (HPA052501, 26 000) — all TYMC, all
against a criterion of `10⁴ CFU/g` whose maximum acceptable count is 20 000.

> **Amended 31.08.2026.** This item read *"at least ten"* and additionally named
> `472/0863/25`, `587/1066/25`, `949/1687/25`, `628/1129/25` and `1220/2171/25`. The first
> four (19 000, 15 000, 17 000, 12 000) clear the pharmacopoeial ceiling: Ph. Eur. 5.1.4 /
> 2.6.12 and USP <1111> read an enumeration criterion of `10ⁿ CFU` as a maximum acceptable
> count of 2 × 10ⁿ, not 10ⁿ. They do **not** clear Purely Plant's own `QCSP 001 v.03`, which
> prints `≤ 10⁴ CFU/g` and states no maximum, so they are **undetermined** pending a QA
> reading of that specification — neither cleared nor failed. `1220/2171/25` (200 against `10²`) turns on a manufacturer's own tighter
> specification and is item 1.4 of `review/QC_DECISIONS_2026-08-31.md`, not this one. The
> **two CNP CBN results** (ППК26033 on P050022, ППК26058 on P050202) are accelerated
> 40 °C / 75 % RH **stability** timepoints and not failed releases — see §6 of
> `ECOA_REGISTER_VERIFICATION_2026-08-29.md`. Full record:
> `review/OOS_RECTIFICATION_2026-08-31.md`.

Also open, and unrelated to the arithmetic above: **one in-house CoA with an
out-of-specification total Δ⁹-THC** (P050202).

**This is the most urgent item in the register.** A batch with no test can still be
tested. A batch released against a failing result has already left the building.

**Options.** (a) Open a deviation record per certificate, assess product impact, decide
on recall or justification. (b) Re-verify each certificate against the source PDF first,
then open deviations only for confirmed cases. (c) Query the laboratories — a limit may
be misprinted, or the conclusion may rest on a criterion not on the page.

**Recommendation: (b) then (a), in parallel with (c).** The cross-check's *free-text
descriptions are reliable*, but its `Finding category` column is over-assigned — of 48
rows tagged out-of-specification, the descriptions support roughly 15. So verify before
raising deviations, but start the laboratory queries immediately since they have the
longest lead time.

**(b) has since been done.** All ten certificates were read from the rendered page on
31.08.2026 and every value confirmed; the count of deviations owed then fell from ten to
five on the arithmetic, not on the reading. That is the order this recommendation asked
for, and it changed the answer by half.

**What changes.** Confirmed cases become deviation records under your QMS, each with a
product-impact assessment. Some may resolve as laboratory transcription errors. Any that
do not may reach batches already delivered — which is a commercial and regulatory
decision, not a documentation one.

---

### B2 🟠 **Host** — thirty agents answer from a knowledge base that does not exist

**What it is.** Letta agents whose system prompts tell them to retrieve from sources
attached to them.

**Why it is open.** All nine Letta sources were deleted 19.08.2026 on your instruction,
with no backup. Thirty of sixty-six agents still reference them, or reference archival
memory with no backing store. The topology audit puts it exactly: *"They will answer,
but from nothing."*

For a QC fleet this is a data-integrity hazard, not a broken feature. An agent that
answers a question about a certificate **without retrieving one** is worse than an agent
that fails, because the failure is invisible.

**Options.** (a) Rewrite the thirty system prompts to point retrieval at RAGFlow and
state plainly that Letta holds no corpus (Phase 1 of the topology audit — reversible).
(b) Mark them deprecated in their description and leave them. (c) Retire them.

**Recommendation: (a), and (b) for any that cannot be given a real retrieval path.**
Nothing should be left silently answering from nothing.

**What changes.** The thirty agents start citing RAGFlow datasets. Answers will change —
some will start saying "I have no source for that", which is the point. Reversible: the
prompts are the only thing edited.

---

### B3 🟠 **QC** — Identification C: 69 internal CoAs, or 81?

**What it is.** Identification C is the thin-layer chromatography identity test in the
QCSP 001 specification panel.

**Why it is open.** **No laboratory has ever performed it, on any of the 81 batches.**
It is discharged in-house by risk analysis citing the qualitative HPLC determination.
The question is documentary: if a single risk-analysis annex covers it, only the **69**
batches lacking a CNP Ph. Eur. certificate need an internal CoA. If it must be stated
per batch, all **81** do.

**Options.** (a) One risk-analysis annex, 69 internal CoAs. (b) Per-batch statement,
81 internal CoAs.

**Recommendation: (a), if your regulatory position supports a panel-level justification.**
It is twelve fewer controlled documents to issue, review and store, and the underlying
justification is identical in both. But this is your call against your marketing
authorisation and inspectorate expectations — I can tell you the counts, not the
regulatory sufficiency.

**What changes.** The internal CoA issuance run is either 69 or 81 documents. The
`iCoA_scope` column in `batch_gap_analysis.csv` and the CI reconciliation both key off
this, so the choice propagates to the deliverables automatically.

---

### B4 🟠 **QC** — do the 41 in-house `QCCoA 001v02` CoAs discharge Identification A?

**What it is.** Forty-one already-issued in-house release CoAs that carry Appearance
(Visual) and Foreign matter (2.8.2) — but no microscopy.

**Why it is open.** Identification A is macroscopic/microscopic identity. If Appearance
(Visual) discharges it, those batches need less than a full panel. If microscopy is
required, they do not.

**Options.** (a) Appearance discharges Identification A — the 69 full-panel batches
split **37 + 32**, and 32 need a reduced document. (b) It does not — all 69 stay full.

**Recommendation: hold the headline figures on the current basis (69) until you rule.**
That is what the analysis does today, deliberately. I am not able to make this call —
it depends on how your specification defines Identification A, which is a document I
should not reinterpret.

**What changes.** Potentially 32 batches move to a reduced internal CoA scope, which
changes the issuance workload and the register's `iCoA_scope` values.

---

### B5–B8 🟠 **QC** — four batch-identity rulings

These come out of the batch-identity rule (`ingestion/common/batch_id.py`), which
encodes two of your rules: the separator before a sub-lot index carries no meaning
(`GG1024/01` = `GG1024_01`), but the index itself does and it nests. Reading the batches
as families exposed a convention change that settles most of them: **all four 2024
families register the parent bulk lot as well as its sub-lots; all nine 2025-onward
families register sub-lots and no parent.**

| | Item | Finding | Recommendation |
|---|---|---|---|
| **B5** | `FB012601` | Certificate ППК26067 prints `/1` on two independent readings. FB012601 is a 2026 batch, a vintage that never registers a parent. The bare register row is the anomaly. | **Ruled 01.09.2026 — the digit is part of the batch number.** Applied as chain step 19 (`apply_fb012601_sublot.py` → `SUBLOT_2026-09-01`); the phantom second CoQ pair for this batch is gone. Its two IPH certificates (2362/2026, 308/0552/26) still await entry — `review/TRACKER_TRUTH_CHECK_2026-09-01.md`. |
| **B6** | `GG1024` | A 2024 parent with sub-lots at register #4 and #8, holding a parent-level release CoA on disk but **no register row**. The only such case. | **Add the register row.** Clerical omission, not ambiguity. It is already carried as batch #81 with `in_register=N`, and CI fails if that stops being explained. |
| **B7** | `MB0824_01` | Certificate ППК25118 is filed as `MB0824_04` and the page reads `MB0824_01`. I first called it an OCR artifact; the independent transcription read `_01`. It is a **well-formed sub-lot code**, and the register jumps straight to `_04` and `_05`. | **Look at the page.** Not safely dismissable as a misread. Either the file is misnamed or an unregistered sub-lot exists. |
| **B8** | `GRC102501` | Registered at sub-lot 2 with no `/1`. | **Look at the page.** Same shape as B7. |

**What changes.** Each ruling either corrects a register row or registers a sub-lot.
`batch_spellings.csv` is regenerated and CI diffs it, so the corrections propagate and
cannot drift. Of 121 batch keys observed, **35 are already recorded more than one way**
and `GP0824/2` is written four ways — these four are the ones where the spelling
difference might mean a different batch rather than a different spelling.

---

# C. Potency grade design

### C1 🟠 **QC** — the T2 anchors are unofficial, and 29 batches' grades rest on them

**What it is.** The grade design assigns each batch a THC grade (nominal ± tolerance)
from its CoQ-forming assay value. Where a batch was retested, the retest supersedes for
release purposes — that is rule R5.

**Why it is open.** The Farmahem re-analysis of **26.08.2026** covers 29 batches and is
**unofficial pending the formal eCoAs**. The design is anchored on those values because
that is the correct rule, and every grade anchored on them is marked provisional and
carries its basis and date. But provisional grades are on documents you may be issuing.

**Options.** (a) Hold issuance of the affected CoQs until the eCoAs arrive. (b) Issue
now with the provisional marking, reissue if a certified value differs. (c) Chase
Farmahem for the certificates.

**Recommendation: (c) now, and (a) for anything not commercially urgent.** The design
re-runs in one command against certified values, so the cost of waiting is low and the
cost of reissuing a controlled document is not.

**What changes.** When the eCoAs arrive, the solver re-runs; any value that moves shifts
its batch's grade and the register, Atlas and spec documents rebuild from it. If the
certified values match the unofficial ones — the likely case — nothing moves and the
provisional marking simply comes off.

---

### C2 🟠 **QC** — `PM112501` misses its mandated grade by 0.01

**What it is.** Six of the 48 mandatory product codes you set are **arithmetically
impossible** against the batches' actual values, and were resolved with the smallest
possible deviation, each flagged. Forty-two of 48 are honoured exactly.

**Why this one is different.** `PM112501` measures **10.79**. THC12's floor is
`0.90 × 12 = 10.80`. It misses by **exactly 0.01**, so it was moved to THC10.

**Options.** (a) Accept THC10. (b) Re-read the source certificate — if the paper value
is 10.80, THC12 becomes feasible. (c) Widen THC12's tolerance, which breaks the
symmetric ±10 % rule.

**Recommendation: (b).** A 0.01 difference is within rounding and transcription range,
and this is the one deviation of the six that a single certificate reading could
eliminate. If the paper says 10.80, the design re-runs in one command.

**What changes.** `PM112501` returns to its mandated THC12, and the deviation count
drops from six to five. If the paper confirms 10.79, THC10 stands and the deviation is
simply documented — which it already is.

---

### C3 🟠 **QC** — accept the five remaining forced deviations, or revise the codes

**What it is.** The other five impossible mandatory codes, resolved minimally:

- **`FB012601/1`** 17.99 exceeds THC16's ceiling 17.60 → **THC18**.
- **`GRC102501/2`** 9.80 is below THC12's floor 10.80 → **THC10**.
- **`JD012603/02`** 14.43 is far below THC20's floor 18.00 → **THC14**.
- **`GP092501` (25.24) and `GP082501/1` (25.13)**, both coded THC26 → **both THC24**.
  The THC26 floor they force needs 0.87 of tolerance budget while the mandatory THC24
  holding GP0824_02 (22.61) needs 1.39; 0.87 + 1.39 = 2.26 against a 1.99 budget, so the
  windows must collide whatever the split. No smaller move set exists, including any
  single-batch move.

**Options.** (a) Accept the deviations as flagged. (b) Revise the mandatory codes for
these batches to match. (c) Change the tolerance rule (symmetric, ±10 % cap, gapless
ladders) — which re-opens the whole design.

**Recommendation: (b) for the record, (a) in effect.** The assignments are already the
minimum-deviation solution; formally revising the codes to match makes the register
self-consistent rather than permanently carrying six flagged exceptions. Do **not** take
(c) — the rules are what guarantee no batch falls between two grades.

**What changes.** Either the deviation flags stay and are explained (a), or the tranche
code list is updated and the flags disappear (b). No batch's grade moves under either.

---

# D. The document engine

### D1 🟠 **Repo** — was commit `593e7f7` a deliberate simplification or an accidental revert?

**What it is.** `pp_report.fixed()` sizes table columns. The sophisticated version floors
each column to its widest *data* cell (data must never wrap) and to its header's longest
*word*, then distributes slack to the longest headers so they wrap least — plus
word-boundary keyword matching, so `'име'` inside `'примерок'` is not a false hit.

**Why it is open.** Root's `pp_report.py` **used to have this**. Commit `593e7f7` —
whose message is entirely about Macedonian glyph rendering, the weekly report and brand
assets — replaced it with the simple form: substring matching, and the overflow
machinery deleted. Nothing in the commit explains it. Most likely `pp_report.py` was
imported wholesale from an older source while the font work was being done.

**Options.** (a) Investigate and, if accidental, restore the logic. (b) Accept the
simpler version. (c) Leave it until the bake-off.

**~~Recommendation: (a)~~ — RESOLVED 29.08.2026.** It was an accidental revert, and the
first guess about the mechanism was wrong: not a wholesale import, but a genuine edit
(adding `informal_header()`, which the message does describe) that took collateral damage
in `fixed()`. None of the 60 changed lines mention a font, a glyph or an asset.

Restored surgically — `fixed()` is byte-identical to its pre-`593e7f7` state and the
informal-header work is untouched — and covered by `pp-document-suite/tests/test_layout.py`,
whose two key cases fail against the regressed version. **This changes D2 and D3.**

**What changes.** If restored, wide bilingual tables in root-built documents size the way
they did before 14.08.2026 — headers wrap less, data cells stop wrapping. Documents built
in the interim used the simpler sizing.

---

### D2 🟠 **QC/you** — pick an engine line

**What it is.** Two copies of the PP document engine, serving different consumers.
`pp-document-suite/` (root) feeds the Letta tool `build_pp_document`, about seven
deliverables builders and ppdocwiz. `apps/wwf-docengine/engine/` feeds the GrowFlow
DocEngine service.

**Why it is open.** Both call themselves canonical, and only `pp_theme.py` is
byte-identical between them. Root **is** the Letta-stack engine — the volume hashes match
root on two of four files and the vendored copy on none. But the capability gap runs both
ways:

| | Table overflow compression | Glyph guard (fails delivery on tofu) |
|---|---|---|
| Root | ✅ *(restored 29.08.2026 — see D1)* | ✅ |
| Vendored | ✅ | ❌ |

**Options.** (a) Run the bake-off: same prompt through both, both verified, rendered and
compared page by page — you pick. (b) Merge the vendored `fixed()` into root, which
already has the glyph guard, the assets and the consumers. (c) Leave both.

**Recommendation: (a), and it is now a narrower question than it was.** With the restore,
root carries both *known* contested capabilities, so the case for merging the vendored
`fixed()` into root has largely been served by another route. What has **not** been
examined is everything else: root's `pp_format.py` is 331 lines against the vendored 612,
the vendored tree carries a `pp_format_layout_addons.py` that root does not, and
`pp_charts.py` and `pp_data.py` differ by a line or two each with nobody having read the
diffs. Run the bake-off on those, rather than on a gap that is now closed.

**What changes.** Whatever wins, the loser's canon document is amended in the same change
so this cannot recur. Any wiring change is its own commit with a regression pass against
previously issued documents.

---

### D3 🟠 **Host** — sync the engine to the volume (hold lifted 29.08.2026)

**What it is.** `server/runbooks/engine_sync.md` copies the repo master onto the Letta
volume at `/root/.letta/pp-document-suite`, hash-gated at every step.

**Why it was open.** The drift ran both ways. The volume runs `pp_report 1be84f35` —
the pre-`593e7f7` version, which **has** the overflow compression — and `pp_verify
a2060978`, which **lacks** the glyph guard. So:

| | Overflow compression | Glyph guard |
|---|---|---|
| Live volume | ✅ | ❌ |
| Repo master | ✅ *(restored 29.08.2026)* | ✅ |

Running the sync *before 29.08.2026* would have installed the guard **and removed working
table sizing from the engine that builds controlled documents**. The restore in D1 put both
capabilities on the master, so **the hold is lifted** — but the hashes recorded in
`engine_sync.md` now describe neither side, so step 1's diff must be re-run and the new
pair recorded before anything is transferred.

**Recommendation: sync, after re-hashing.** D1 is resolved, so this is now the ordinary
hash-gated procedure — with one caveat written into the runbook: the canonical hashes
recorded there predate the restore and describe neither side, so step 1's diff must be
re-run and the new pair recorded first. Do not sync against the stale figures.

**What changes.** One sync installs both capabilities instead of trading one for the
other. Documents built through the Letta tool start getting the glyph guard, which fails
delivery rather than shipping scrambled Cyrillic. Worth adding at the same time: a drift
check, so the next gap is detected rather than discovered — sync is manual and nothing
currently notices.

---

# E. Infrastructure and estate

### E1 🔴 **Host** — RAGFlow has no swap and loses documents under memory pressure

**What it is.** RAGFlow's ingestion worker on a host with no swapfile.

**Why it is open.** A bulk ingestion coinciding with a memory spike kills the worker and
**loses whichever document is in flight.** A 4 GB swapfile with `vm.swappiness=10` is the
correct remedy; the attempt was refused by a session permission policy and not worked
around. Elasticsearch also sits at 74 % of a 2 GiB cap.

**Options.** (a) Add the swapfile and raise the ES cap. (b) Free ~2 GB by stopping
services. (c) Keep the current workaround — queue heavy documents one at a time.

**Recommendation: (a).** The workaround recovered all eight failures last time, but it
depends on someone remembering to use it. The corpus is about to grow.

**What changes.** Bulk ingestion stops being fragile; you can queue documents in
parallel again. Raising the ES cap needs a container restart.

---

### E2 🟠 **QC** — do RAPTOR and GraphRAG both need to be on?

**What it is.** Two RAGFlow retrieval enhancements. RAPTOR builds a hierarchical summary
tree over chunks; GraphRAG extracts entities and relations (the 2,351 knowledge-graph
entities carrying no `doc_id`).

**Why it is open.** They are the reason ingestion is expensive enough to be fragile, and
the reason a reparse cannot restore a document to its previous chunk count on its own.
Turning either off **changes retrieval behaviour**, so it is a QC decision about answer
quality, not a maintenance one.

**Options.** (a) Both on — accept the cost, and rebuild the dataset-level RAPTOR tree
after any bulk reparse. (b) GraphRAG off. (c) RAPTOR off.

**Recommendation: (a) unless retrieval quality is measured and shows they are not
earning it.** I have no evidence either way — nobody has A/B'd retrieval with them off,
and guessing on retrieval quality for a certificate corpus is not something to do
casually.

**What changes.** Under (a), add "rebuild the RAPTOR tree" to the post-reparse
procedure. Under (b) or (c), ingestion gets faster and cheaper and answers change in a
way nobody has measured.

---

### E3 🟠 **Host** — the Letta estate: four stacks, 58 stranded agents

**What it is.** There are **four** Letta stacks on KVM4, not one. `letta` on :8283 is the
old deployment; `letta-6ou3` on :32770 is the new letta-code one; `wwf-letta` is the
GrowFlow line; and `letta-scy7` appeared during the RAGFlow health check, after the
topology audit was written.

**Why it is open.** The cut-over was started and left half-finished. `wwf-docengine`
points at the new stack, while `letta-mcp-rust`, `wwf-scheduler` and
`weekly_weed_flow-backend-1` still point at the old one, and **58 of 66 agents exist only
on the old stack.** Backups are taken and gzip-verified; migration is confirmed feasible
(all stacks run Letta 0.16.8).

**Four sub-decisions:**

1. **The 58 old-stack-only agents** — migrate from `old_letta-agents.json`, or retire?
2. **`GrowFlow_Weekly_Snapshots`** — stay Letta sources, or move to RAGFlow like
   everything else? (`wwf-letta` still holds four live sources, so Letta is still acting
   as a RAG engine despite the rule excluding it.)
3. **CVAT and ZoneMinder** — genuinely finished, or paused and expected back? Twenty-one
   stopped containers wait on this.
4. **Letta Cloud** (`Letta Code`, `RAG`, `Memo`) — in scope for consolidation or left
   alone?

**Recommendation.** Migrate the 58 (reversible, and the backup exists). Move GrowFlow to
RAGFlow for consistency with your own standing rule — unless GrowFlow is a genuinely
separate system, which is the judgment I cannot make. Retire CVAT/ZoneMinder only on your
word. **And find out what `letta-scy7` is** before touching anything — the audit's
consolidation plan was written against an estate that has since changed.

**What changes.** Phase 2 repoints the three stale callers and unpublishes :8283.
Phase 3 removes 21 stopped containers and their images — irreversible, and volumes are
handled individually by name, never by `prune`.

---

### E4 🟠 **Host** — no scheduled backup of letta-postgres

**What it is.** The PostgreSQL database holding every Letta agent, its memory and its
configuration.

**Why it is open.** `START_HERE.md` calls a scheduled `pg_dump` with rotation *"the
single highest-value resilience item"* and it is still not done. One ad-hoc backup exists
from 21.08.2026.

**Recommendation: schedule it.** Nothing in this register is cheaper relative to what it
protects. The nine deleted sources are gone with no backup — that already happened once.

**What changes.** A cron job and disk for the dumps. No behaviour change.

---

### E5 🟠 **you** — deploy ppdocwiz, and settle the Traefik topology first

**What it is.** The wizard/chat front-end for the document engine. Hardened this batch:
authenticated, path-contained, output-escaped, dependencies pinned, 23 tests in CI.
It is **not deployed** — it sits under "§10 remainder" in `START_HERE.md`.

**Why it is open.** Two blockers. (1) `PPDOCWIZ_API_KEY` must be in
`/opt/stacks/ppdocwiz/.env` or `docker compose up` **hard-fails** — deliberately, so a
misconfigured deploy fails with a readable message instead of 503-ing every request.
(2) The port is now pinned to loopback, so `http://<host>:8770` will not work from
anywhere but the host. Reaching it needs an SSH tunnel or a Traefik route — and **the
Traefik topology is ambiguous in the repository**: one document records
`network_mode: host`, another says Traefik reaches containers over the Docker network, a
third joins `ai-net`. These cannot all be true.

**Recommendation.** Generate a key, deploy behind an SSH tunnel first, confirm it works,
then settle the topology on the host before enabling the Traefik route. The commented
label block in `docker-compose.yml` names both prerequisites — the stack must join the
Traefik network, *and* the labels need the `entrypoints`/`certresolver` pair the current
block omits.

**What changes.** Loopback-pinning is safe under every reading of the topology, which is
why it was done unconditionally. Nothing else in the stack is affected.

---

### E6 🟠 **Repo** — `pp-document-suite/integrations/service.py` has four unauthenticated routes

**What it is.** The REST service that lets Letta agents build documents —
`/build`, `/build.docx`, `/build.pdf`, `/health`.

**Why it is open.** It declares no `ports:`, so it is unreachable from the host — but
`/build*` accept arbitrary Markdown and shell out to `soffice` from **any container on
the `letta` network**, which is where the Letta local-sandbox tool code runs. It now
carries `traefik.enable=false` so it can never be routed by accident, but it has no
authentication.

**Why the auth is deferred.** It is a shared engine with **registered Letta REST tools**
(`integrations/letta_register.py`, `pp_tool.py`). Adding a key breaks every registered
caller until each is updated — a coordinated rollout, not a surgical diff.

**Recommendation: do it as its own PR**, gating the three build routes with
`PPSUITE_API_KEY` and leaving `/health` open, with the tool registrations updated in the
same change.

**What changes.** Every registered Letta tool needs the key. Done in one change, nothing
breaks; done piecemeal, document building stops working for whichever caller lags.

---

# F. 🟢 Low-risk items, proceeding by default

Reversible, and none of them needs a ruling to be correct. They are listed so the
default is visible and can be countermanded, not to ask permission.

| | Item | What changes |
|---|---|---|
| F1 | **Investigate `593e7f7`** (= D1) and restore the overflow logic if the revert was accidental | Wide bilingual tables size correctly again in root-built documents |
| F2 | **Re-run `scripts/export_manifests.py`** and commit the dated output | Closes the evidence gap — the current snapshot is 20 days stale, predates the source deletion and MCP enablement, and leaves 51 of 66 agents and 31 of 33 tools unenumerated. Needs live server reach; if unavailable it becomes a host item |
| F3 | **Add an engine drift check** so the master/volume gap is detected rather than discovered | One check; fails loudly when repo and volume diverge |
| F4 | **Refresh the RAGFlow dataset counters** so the API stops advertising 9,148 chunks against 8,923 | Cosmetic but the header is what the API returns, so it misleads every consumer. Needs host reach |
| F5 | **Delete the ten orphaned MinIO buckets** belonging to knowledge bases that no longer exist (22 objects) | Pure residue removal, by name after confirming each is unreferenced. Needs host reach |
| F6 | **Re-cut scene 07 of the two films** — they quote "1,038 verified parameters across 49 batches", which predates the coverage analysis; 49 counts only the P-numbered subset and the register holds 81 | The films stop understating the work before they are shown externally |

---

---

## Where each item comes from

Nothing here is new analysis. Every item is carried forward from a document already in
the repository, so the evidence is checkable rather than asserted:

| Section | Source |
|---|---|
| A1, A4, D1–D3, E5, E6 | `review/APP_SECURITY_REVIEW_2026-08-29.md`, `docs/ENGINE_CONSOLIDATION_2026-08-29.md` |
| A2 | `server/RAGFLOW_MCP_ENABLE.md` |
| A3, B2 | `review/LETTA_HOST_AUDIT_2026-08-12.md`, `server/LETTA_TOPOLOGY_AUDIT_2026-08-21.md` |
| B1, B5–B8 | `deliverables/qc_gap_analysis/CROSS_CHECK_2026-08-22.md`, `README.md` |
| B3, B4 | `deliverables/qc_gap_analysis/README.md` |
| C1–C3 | `deliverables/potency_study/METHODOLOGY_Potency_Grades.md` §4.4, `design_check.json` |
| E1, E2, F4, F5 | `server/RAGFLOW_HEALTH_2026-08-22.md` |
| E3, E4 | `server/LETTA_TOPOLOGY_AUDIT_2026-08-21.md`, `START_HERE.md` |

## Maintaining it

Close an item by recording the decision **in the source document** — that is where the
evidence lives and where the next reader will look — then strike it here. A decision
recorded only in this register would be a second copy that drifts from the first, which
is the failure mode this whole batch has been correcting.

Do not renumber. A struck item keeps its identifier so a reference to B3 in a meeting
note still resolves a year from now.
