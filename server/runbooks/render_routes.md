# DOCX → PDF render routes (verified 2026-08-08)

Ordered by preference. LibreOffice inside the cloud Claude containers is broken for .docx import
(both the ACME_SOP and CoA_TRACK threads reproduced it) — do not rely on it there.

## 1. In-stack Gotenberg (server-side) — the reliable route

From **inside the Letta stack** (agents, `run_from_source` sandbox), Gotenberg answers at
**`http://gotenberg:3000`** (Docker DNS). Verified: this is the ONLY address that works from the
sandbox — external `:3000` is firewalled (correctly), and `172.17.0.1` / `host.docker.internal`
do not resolve.

```
curl -sS -o out.pdf --form files=@in.docx http://gotenberg:3000/forms/libreoffice/convert
```

Server-side build+render recipe (used to produce the AM02.1 A1/A2 PDFs): POST to Letta
`/v1/tools/run` a function that (1) hash-gates a gz+b64 markdown payload, (2) builds with the
volume engine `/root/.letta/pp-document-suite/scripts/build_from_md.py`
(`PYTHONPATH=/root/.letta/pp-libs`), (3) runs `pp_verify.py` (must PASS), (4) curls Gotenberg,
(5) leaves both files in `/root/.letta/pp-out/`. Fetch results back in base64 slices of
≤ 40,000 chars — `/v1/tools/run` responses are capped at 50,000 chars — and re-hash after
reassembly. Never install or accept a transfer without an end-to-end SHA-256 gate.

## 2. qms-api front

`POST /api/v1/document/convert-to-pdf` on qms-api (`:8500`) fronts the same Gotenberg.

## 3. Chromium HTML→PDF (cloud containers)

For documents that also exist as HTML:
`/opt/pw-browsers/chromium-*/chrome-linux/chrome --headless --disable-gpu --no-sandbox
--no-pdf-header-footer --print-to-pdf=out.pdf file:///abs/path/in.html`
(`chromium` is not on PATH; use the absolute binary.) This renders the HTML rendition, not the
DOCX — fine when HTML is a first-class rendition (CoA_TRACK QC docs), wrong when the DOCX layout
itself must be proofed.

## 4. Word on a user machine

Last resort; also the only renderer that updates TOC/Page-X-of-Y fields interactively (Ctrl+A, F9).

================================================================================
# FILE: runbooks/verification_2026-08-08.md — see the full copy in the repo
(runbooks/verification_2026-08-08.md) or in CoA_TRACK docs/ops/. Verdict in one line:
the ACME_SOP handover v2.0 verified accurate on every testable hard fact; staleness only by
growth (54→66 agents, DB3 25→278 files); PQ1 source embedding is text-embedding-3-large;
port-8787 sidecar absent; pp_house_rules path + qms_docx_formatter Gotenberg address fixed live.
================================================================================
