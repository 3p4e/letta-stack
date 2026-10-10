# Application security review — apps, CI and ingestion tooling (2026-08-29)

Third in the series after `LETTA_TECH_REVIEW_2026-08-09.md` (static analysis of the
repos) and `LETTA_HOST_AUDIT_2026-08-12.md` (live probe of the Letta host). This one
covers what those two did not: the two applications in `apps/`, the CI configuration,
and the ingestion tooling in `ingestion/coa_track/`.

Everything below was read from the repository at `10a0bbb`. Where a claim is
empirically confirmed the confirmation is named; where it is reasoned from framework
semantics it says so. **No live host was reachable from this session**, which is why
several findings close only in the repository and are marked accordingly.

## The shape of it

The defects cluster in two places, and the reason matters more than the count.

**`apps/ppdocwiz` was built to a laxer standard than `apps/wwf-docengine` sitting
next to it.** The docengine is careful code — constant-time key comparison,
parameterised SQL, UUID-gated file access, atomic publish, incident-annotated fixes.
ppdocwiz had no authentication at all, on a port published to every interface. The
house pattern existed; it simply was not applied.

**`ingestion/coa_track/kvm4-runner` is a deliberately maximal remote shell that is
live on the internet.** That is not an accident: outbound :22 is blocked from cloud
Claude Code sessions, so the same surface SSH would give (run shell, exec in a
container, move files) was exposed as JSON over HTTPS. Its own README says it
plainly — "anyone holding the token has root-on-host equivalent." The finding is not
that it exists, but that its one credential was compared with `!=` and its file
endpoints logged nothing.

The most consequential ppdocwiz finding is a **chain**, not a lone bug. Its open
`POST /api/chat` proxied to the Letta API, which `LETTA_HOST_AUDIT_2026-08-12.md`
finding #1 records as unauthenticated, and whose custom tools finding #3 records as
running in a local sandbox with access to host secrets. Three separately-tolerable
weaknesses compose into credential exfiltration by anyone who can reach port 8770.

## Findings

### 1. 🔴 ppdocwiz served every route unauthenticated, on all interfaces

`docker-compose.yml` published `8770:8770` — every interface, not loopback — in front
of an application with no credential check anywhere. Six routes were open, including
`/api/wizard/build` (arbitrary Markdown into `soffice`) and `/api/chat`.

**Root cause:** the app was written as an internal tool and never revisited when the
compose gained a published port. The sibling service's `app/security.py` has had the
correct pattern since it was written.

**Fixed** (`01bf3d6`): loopback pin, plus new `backend/security.py` and
`backend/config.py` mirroring `wwf-docengine/app/security.py` — `hmac.compare_digest`,
fail-closed **503** when `PPDOCWIZ_API_KEY` is unset. Six routes gated. `/api/health`
stays open deliberately: the compose healthcheck sends no headers, and gating it would
leave the container permanently `unhealthy`. That is now pinned by a test, so nobody
"fixes" it later.

**Design note — why a cookie and not just a header.** The download links are plain
`<a href>` anchors. A browser cannot attach a header to a navigation, so a
header-only scheme would have meant rewriting them into fetch-and-blob. Instead
`POST /api/session` sets an `HttpOnly; Secure; SameSite=Strict` cookie whose value is
**HMAC-derived from the key, never the key itself** — so an XSS of the F3 class cannot
read a usable credential. Cookies ride both `fetch` and navigations, so this required
**zero changes to the six existing fetch sites and zero changes to the anchors**.
CSRF is covered by `SameSite=Strict` plus JSON-body-only mutating routes; no token.

### 2. 🔴 Arbitrary agent selection in `/api/chat`

`ChatReq.agent` was client-supplied and took precedence over the server's default, and
the lookup ran over `limit=200`. A caller named **any** agent on the Letta server and
talked to it — including agents whose tools reach host secrets.

**Fixed** (`01bf3d6`): the target resolves against a server-side allowlist derived from
`LETTA_AGENT`; anything else is rejected with 400.

### 3. 🟠 Unsanitised filename into `os.path.join` and the `soffice` argv

*Reported first as 🔴 Critical and "verified" — that was wrong, and the correction is
the substance of this entry.* The original repro proved the **Python path arithmetic**
(`/data/../../../etc/… → /etc/…`), not **HTTP reachability**.

**Now confirmed empirically**, on the pinned `starlette 1.3.1`, against the real app:

| Request | Result | Meaning |
|---|---|---|
| `/api/download/real.docx` | **200** | the route matches and serves |
| `/api/download/real.exe` | **400** | the new extension guard fires |
| `/api/download/..` | 404 | normalised away before dispatch |
| `/api/download/%2e%2e%2f%2e%2e%2fetc%2fpasswd.docx` | 404 | percent-decoded **before** routing, so it is multi-segment |
| `/api/download/....//....//etc/passwd.docx` | 404 | multi-segment |

Starlette compiles `{name}` to `[^/]+`, and uvicorn decodes before routing, so no
traversal escapes a single path segment. The finding was **latent, not remotely
exploitable** — corrected to 🟠.

It was worth fixing anyway, and the reason is the interesting part: ppdocwiz pinned
**no** dependency versions (finding 7), so that routing behaviour was free to float,
and a future `{name}` → `{name:path}` would have made it live instantly. A latent bug
behind an unpinned dependency is not a safe bug.

**Fixed** (`01bf3d6`): one `_safe_name()` helper applied at both ends, plus an
extension allowlist and a `realpath` + `commonpath` containment assert on the read
side. `subprocess.run` was already list-form, so with the path proven contained there
is no injection surface left.

**Accepted risk, recorded rather than argued:** this is now the *third* near-copy of
the safe-name rule in the repository (`integrations/service.py`,
`wwf-docengine/app/builder.py`, and this one). `integrations/` is not importable from
ppdocwiz — `app.py` only adds `SUITE/scripts` to the path. Reshaping a container's
import graph inside a security batch is the larger risk; the duplication is the
smaller one.

### 4. 🟠 Attribute-injection chain: `code` → `doc_id` → `download_docx` → `href`

Findings 3 and 5 are the same bug seen from two ends. The document `code` became
`doc_id` through a sanitiser that stripped only `/` and space — so `"` survived —
which became `download_docx`, which was interpolated raw into `href="…"`. A code of
`x" onmouseover="alert(1)` broke out of the attribute.

**Fixed** (`01bf3d6`) at **both** ends: `_safe_name` on the write side kills it at
source, escaping on the read side catches anything else. The regression guard is a test
asserting `download_docx` always matches `^/api/download/[A-Za-z0-9._-]+\.docx$`.

### 5. 🟡 Unescaped `innerHTML` sinks throughout the frontend

Twenty interpolations of build output, agent replies and tool returns went straight
into `innerHTML`, including one partial escape that handled `<` but missed `&`, `>`,
`"` and `'`.

**Fixed** (`01bf3d6`): an `esc()` helper (the pattern already in
`qc_register_artifact.html`) at every sink, and a `textContent` path for the echoed
user message. `bubble()` keeps a one-line contract comment: callers pass
already-escaped HTML.

**CSP was deliberately not added.** The page uses inline `<style>`, inline `<script>`
and about ten inline `onclick=` handlers, so any workable policy needs
`script-src 'unsafe-inline'` — which forfeits exactly the protection being sought.
Escaping the sinks is the fix; a CSP here would have been decoration.

### 6. 🟡 An 890-line test suite that never ran

`apps/wwf-docengine/tests/` was comprehensive and entirely ungated — no CI job
executed it. Worse, `tests/conftest.py` **skips** the persistence tests when no DSN is
set, and `test_api.py` was written assuming CI would supply one, so `app/db.py`
(`job_create`, `document_create`, `reap_stale_jobs`) had no executed coverage at all.

**Fixed** (`f914f10`), and the Postgres service container is justified empirically
rather than assumed: run locally against a throwaway `initdb` on port 55432, the suite
goes from **45 passed / 6 skipped** to **51 passed / 0 skipped**. Those six were a
committed intent nobody had completed.

### 7. 🟡 Dependencies installed with no pins, in two images

`apps/ppdocwiz/Dockerfile` and `pp-document-suite/Dockerfile` both `pip install`ed
bare package names. An unpinned image is not reproducible, and — per finding 3 — it
silently changes the framework behaviour the app's own path handling rests on.

**Fixed** (`01bf3d6`), but the first attempt did not close it and the reason is worth
recording. The obvious fix, pointing `pp-document-suite/Dockerfile` at its existing
`requirements.txt`, would have (a) still floated, because that manifest carries
**ranges** (`python-docx>=1.1`, `lxml>=4.9`, …), and (b) **dropped** `fastapi` and
`uvicorn[standard]`, which the inline list installed and that manifest never listed —
breaking the service. Closure needed a separate, fully pinned
`requirements-service.txt` alongside the ranged dev manifest. Every pin was verified to
resolve with `pip download`.

*Non-root user deferred:* LibreOffice needs a writable `$HOME`, and the existing
`ppdocwiz_out` named volume would not be re-chowned on upgrade.

### 8. 🔴 kvm4-runner — live, internet-exposed, root-on-host equivalent

Deployed behind Traefik with Let's Encrypt on `runner.srv1231216.hstgr.cloud` and
exercised as recently as 22.08.2026. `/exec`, `/shell`, `/file/read`, `/file/write`
behind a single bearer token compared with `!=`.

Specifics: the token compare was not constant-time and the 401/403 split confirmed
header shape to an attacker; `/file/read` and `/file/write` logged **nothing**;
`/exec/stream` enforced no timeout while `/exec` and `/shell` did; and `/file/write`
took an arbitrary absolute path with `mkdir=True` and caller-supplied chmod — with
`/opt` mounted read-write, it could **rewrite the runner's own source**.

**Fixed in the repository** (`4c86726`): `hmac.compare_digest` with a uniform 401,
request logging on every privileged endpoint, a deadline on `/exec/stream`, writes
confined to `RUNNER_WRITE_ROOT`, and `docs_url`/`redoc_url`/`openapi_url` set to
`None` with the `/` banner trimmed to a bare liveness string. `deploy.py` no longer
prints the token except when it generates one.

> ⚠️ **This does not close the live exposure, and must not be read as if it did.**
> Editing `runner.py` in this repository changes nothing on the running service. The
> exposure closes only when someone with host access rotates `RUNNER_TOKEN` and
> redeploys. Until then the internet-facing root-equivalent surface is exactly as it
> was. If the redeploy will be delayed, the immediate mitigation is host-side and
> independent of this branch: put a Traefik IP-allowlist middleware on the router, or
> take the route down.

**Drift risk, pre-existing and still open:** `deploy.py` inlines `runner.py` as a
heredoc, so the deployed code may not be byte-identical to the repository copy and
nothing verifies it. Editing the file here changes nothing until a redeploy. Confirm
the deployed source before and after.

**What it is for** — asked during review, and the answer is *not* CoA ingestion.
`gdrive_pull.py` and `ocr_batch.py` were orphans with no caller anywhere (both
retired in `10a0bbb`); CoA ingestion runs through `ingestion/ragflow/**`; and
`reclassify_watcher.py` explicitly rejected the runner as unfit. `deploy.py` is its
only client. It is an SSH substitute, and its endpoints were chosen to be maximally
general on purpose rather than derived from any needed operation. **Do not
decommission** — no session here can reach the host, so it is the intended path for
exactly this kind of work. The right narrowing is named allowlisted operations with
`/shell` kept as explicit break-glass behind an IP allowlist and audit logging.

### 9. 🟠 RAGFlow MCP authenticates no client and is publicly routed

`RAGFLOW_MCP_ENABLE.md` records it directly: in self-host mode the server
"authenticates no client. Anyone who reaches `ragflow-mcp.srv1231216.hstgr.cloud/mcp`
is served as the tenant" — with read access to every dataset, i.e. the whole eCoA
corpus. Wildcard DNS is live, so the hostname is guessable.

**Owner-accepted risk, recorded 25.08.2026 — surfaced here for reconsideration, not
overridden.** Not fixable from this repository. The recorded one-word fix is
`--mcp-mode=self-host` → `--mcp-mode=host` (every client then needs its own RAGFlow
key), or a Traefik middleware in front of the router.

### 10. 🟠 Thirty agents retrieve from nothing

All nine Letta sources were deleted 19.08.2026 with no backup, but 30 of 66 agents
still reference them, or reference archival memory with no backing store.
`LETTA_TOPOLOGY_AUDIT_2026-08-21.md` puts it exactly: "They will answer, but from
nothing."

For a QC fleet this is a **data-integrity** item, not a broken feature. An agent that
answers a question about a certificate without retrieving one is worse than an agent
that fails. Not fixable from this repository — either repoint them at RAGFlow (Phase 1
of that audit, no completion recorded) or retire them.

### 11. 🟡 Dead code for infrastructure that no longer exists

Four scripts still ingested into the deleted Letta sources, and `policy_check.py`
rule 2 forbids creating a Letta source at all — so they could not work and would have
broken the policy if they had. Two further kvm4-runner scripts had no caller anywhere.
About a dozen builders carried stale `ImB_QC_COAs` provenance labels.

**Fixed** (`10a0bbb`). The retirement, what was kept, and why is recorded in
`server/runbooks/ingestion_policy.md`, which is already the record of the deletion.

Two things there are worth repeating here. First, **rule 2 only ever scanned `.py`**,
and both retired `deploy.sh` files created their sources over
`curl -X POST .../v1/sources/` — so the guard had never covered the way this
repository actually did it. Widened to shell, and negative-tested. Second, the
provenance labels were **corrected, not repointed**: the present-tense claims were
false and are fixed, but the dated verification records ("4,134 passages scanned
live", "263 files verified 13.08.2026") describe checks that really happened against a
store that really existed then. Repointing those at RAGFlow would assert a
verification that was never run there — a worse defect than a stale name.

### 12. ℹ️ `pp-document-suite/integrations/service.py` — four unauthenticated routes

Lower risk than finding 1 because `docker-compose.letta.yml` declares **no `ports:`**,
so it is unreachable from the host. Not *no* risk: `/build*` accept arbitrary Markdown
and shell out to `soffice` from any container on the `letta` network — which is where
the Letta local-sandbox tool code runs.

**Partly fixed** (`10a0bbb`): `traefik.enable=false`, matching the guard
`network-shared/after/gotenberg.yml` and `after/qdrant.yml` use, so a future Traefik
reconfiguration cannot pick it up by accident.

**Auth deliberately deferred.** This is a shared engine with **registered Letta REST
tools** (`integrations/letta_register.py`, `pp_tool.py`). Adding a key breaks every
registered caller until each is updated — a coordinated rollout, not a surgical diff,
and not something to bundle into a security batch.

### 13. ℹ️ `/api/health` disclosed the container filesystem path

The endpoint returned `suite` — the resolved engine path inside the container — and
must stay ungated for the compose healthcheck. **Fixed** (`01bf3d6`): the field is
dropped; the frontend never read it. Pinned by a test.

### 14. ℹ️ kvm4-runner's `/` banner enumerated every privileged endpoint

Ungated, and FastAPI's `/docs`, `/redoc` and `/openapi.json` were left enabled — a
complete API map for anyone who found the hostname. **Fixed** (`4c86726`), subject to
the same redeploy dependency as finding 8.

### 15. 🟠 Two diverged engine lines, serving different consumers

*Corrected before writing: the first draft called the root `pp-document-suite`
"superseded", which is backwards.* Verified — the registered Letta tool
`build_pp_document` runs from `/root/.letta/pp-document-suite`, and the volume hashes
in `engine_sync.md` match **root** exactly on two of four files while the
`wwf-docengine/engine/` copy matches **none**. Root **is** the Letta-stack engine.

All four core scripts differ between the two trees. This is "two lines diverged, pick
one", not "migrate off the old one". Recorded and deferred by owner decision — see
`docs/ENGINE_CONSOLIDATION_2026-08-29.md`. Repointing the engine changes rendered
output for *controlled documents*, which needs its own regression pass and must not
ride along in a security batch.

### 16. 🟠 The repository master has drifted ahead of the live Letta volume

`engine_sync.md` records the volume at `pp_report 1be84f35` / `pp_verify a2060978`;
root now holds `64ac6704` / `d045d6b4`. Two of four engine files on the volume are
therefore **older** than the master that `build_pp_document` is supposed to run. Sync
is manual and hash-gated, and nothing detects the gap. Also recorded in the engine
consolidation document.

## What is now enforced rather than remembered

Individual fixes close today's instances; these stop tomorrow's from landing. Each was
negative-tested — made to fail on purpose — so none is decorative.

| Guard | Stops |
|---|---|
| `policy_check` #2, widened to `.sh` | a shell script creating a Letta source over `curl` (finding 11) |
| `policy_check` #6 | a compose we author publishing on `0.0.0.0` (finding 1) |
| `policy_check` #7 | an unpinned `pip install` in a tracked Dockerfile (finding 7) |
| `policy_check` #8 | an interpolation into `innerHTML` without `esc()` (finding 5) |
| CI `ppdocwiz-tests` | 23 cases: auth, fail-closed 503, cookie ≠ key, traversal, extension, `_safe_name`, the `download_docx` shape (findings 1–5, 13) |
| CI `docengine-tests` + Postgres | the 6 persistence tests that had never run (finding 6) |
| CI `deps` | `pip-audit --strict` on all three pinned manifests (finding 7) |

## Honest closure

Eleven of sixteen findings close fully in this repository. The rest do not, and are
listed as open rather than absorbed:

| Open | Why it is not closed here |
|---|---|
| **8, 14** | Fixed in the repository; the live exposure closes only on host redeploy |
| **9, 10** | Not fixable by any code change here — live-stack decisions needing host access |
| **12** | Auth deferred by design; would break registered Letta tool callers if rushed |
| **15, 16** | Deferred by owner decision; a rendering change needs its own regression pass |

Also carried, pre-existing and not introduced by this work:

- RAGFlow API key rotation — historical leak at `83ae904`, allowlisted in
  `.gitleaks.toml` by commit with a note, so new leaks still fail the scan.
- Letta API auth (`LETTA_HOST_AUDIT_2026-08-12.md` #1): the server reads
  `LETTA_SERVER_PASSWORD`, the deployment sets `LETTA_SERVER_PASS`, and no `SECURE`
  flag is set, so the middleware never installs. A one-word rename — and it underpins
  the severity of finding 1.
- `scripts/export_manifests.py` has not been re-run since 2026-08-09, ten days before
  the source deletion and sixteen before MCP enablement. 51 of 66 agents have no
  exported tool/source record and 31 of 33 tools are unenumerated. Those are **gaps,
  not clean bills**.

## Behaviour changes to announce

1. **`http://<host>:8770` no longer works from anywhere but the host.** Replacement:
   an SSH tunnel, or a Traefik route once the topology question below is settled.
2. **Every `/api/*` caller now needs a credential.** No in-repo caller besides the
   frontend, but the live host could not be inspected from here — check for scripts or
   agents calling `:8770` before deploying.
3. **`_safe_name` changes generated filenames.** `WHSOP/002` and `WHSOP 002` both
   previously became `WHSOP_002_<hex>`; anything reconstructing a URL by the old
   two-`replace` rule will mismatch. No such consumer found in-repo.
4. **`docker compose up` hard-fails** until `PPDOCWIZ_API_KEY` is in the stack's
   `.env` — `${VAR:?}` not `${VAR:-}`, deliberately, so a misconfigured deploy fails
   with a readable message instead of 503-ing every request. It belongs in the deploy
   runbook.

## Uncertainty flagged rather than guessed

**Traefik's network topology is ambiguous in the repository.**
`network-shared/README.md` records `network_mode: host` (2026-05-22);
`RAGFLOW_MCP_ENABLE.md` asserts Traefik reaches containers over the Docker network;
`ragflow/docker-compose.override.yml` joins `ai-net`. These cannot all describe
current state. Loopback-pinning is safe under every reading — which is why it was done
unconditionally — but **do not enable the ppdocwiz Traefik route until this is settled
on the host.** The commented label block in `docker-compose.yml` names both
prerequisites: the stack must join the Traefik network, *and* the labels need the
`entrypoints`/`certresolver` pair that the current block omits.
