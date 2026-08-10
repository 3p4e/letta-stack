# ImB_QC_COAs — Ingestion & Ph.Eur. 3028 Coverage Status

_Last updated: 2026-08-10 by cloud Claude session._

## Source of truth
- **Drive folder:** `1. PP/DATA_B/QC_eCoA/ImB_QC_COAs` (Drive ID `16oMK_j0FUusjveV61B5rxWi6Sl5kQsn5`)
- **Letta source:** `source-271bc3be-10d1-4541-8a5b-be3f6fab7c97` (ImB_QC_COAs)
- **Agent attached:** `imb_qc_coa_agent` (`agent-edf27c5c-1f88-495b-b6fb-506105bd717c`)
- **Embedding:** OpenAI `text-embedding-3-small`, 1536 dim, chunk 300.
  (An older README claiming `voyage-3-large` is **wrong** — the server holds no Voyage key.)

## Current state — CLEAN

| Metric | Value |
|--------|-------|
| Total files in source | **263** |
| `completed` | **263** |
| `error` | **0** |

_263 = 261 CoA/QC records + 2 governance records added 2026-08-10:_
_`SOP_RAG_INGESTION_per_batch_folder_rule_v1.1.txt` and `DRIVE_INDEX_001_COAs_batch_folders_v1.txt`_
_(filename retained for history; the folder it indexes has since been merged into the_
_Drive source-of-truth folder itself — see Standing rule below)._

The 2026-06-01 embedding blocker is **resolved**. Root cause was an OpenAI
`429 credit_balance_exhausted` on the server key — Letta accepted each upload and
wrote the row, then the embedding call flipped it to `error`. After the account
balance was refreshed, every errored row was purged and re-uploaded cleanly.

## 2026-08-10 ingestion run

**12 UKIM ППК certificates** (`ППК26110`–`26119`, `26127`, `26128`) — full
six-parameter Ph.Eur. records (identification macro + micro, foreign matter,
loss on drying, total CBN / CBD / Δ9-THC), each with acceptance criteria and results.

**42 Farmahem 197-series certificates** (`197-1` … `197-21`, each K + M) — every
record carries `Parameter | Acceptance criterion | Result | Expanded uncertainty U`:
- **K panel** — cannabinoids by HPLC/DAD, method `ИР 7.2.1-47К (в.1)`, Ph.Eur.
  Cannabis flos (3028). Reports print results only (no limit column), so the PP
  release-spec limits are added and **labelled as added-for-review**.
- **M panel** — aflatoxins B1/B2/G1/G2 + ochratoxin A, methods `ИР 7.2.1-43М` /
  `ИР 7.2.1-44М`.

**8 legacy error-state files re-driven** (5 `Bundle_*`, 2 `QC_ERRATA`, 1
`UKIM_PPK26037`) — stored content was re-read server-side, deleted, re-uploaded.

### QC findings raised by this run
- **197-14-M** (High Pro Amnesia, `HPA1024_01`): **Ochratoxin A 2.06 µg/kg**
  (U 11.80 %) — the only mycotoxin above LOQ in the series. Flagged
  *verify against the PP registered mycotoxin limit before release*.
- **197-13-M** (`HPA1024`): Ochratoxin A `<LOQ`. All other mycotoxin results across
  all 21 samples are `ND`.
- **197-19-K** (`P060242`): Δ9-THC 7.91 % — lowest in the series, still ≥ 5.00 % minimum.
- **ППК26127** (Fat Bastard `FB032601`): foreign-matter discrepancy — see below.

## Open QC item — ППК26127 foreign matter

Logged in the source as `QC_QUERY_PPK26127_FatBastard_FB032601_foreign_matter_seed_v1.txt`.

The certificate records foreign matter as `0.08% (Не одговара)` against the limit
`макс. 2.00 % (без присуство на семе и листови подолги од 1 cm)`. The recorded
result is **within** the 2.00 % mass limit and the results section records **no seed
observation**; seed presence is asserted only in the free-text conclusion. Since the
`Одговара / Не одговара` verdict is the standard per-parameter tag on this form, the
fail flag is inconsistent with the recorded result.

A neutral query to CNP asks them to either **(A) substantiate** — supply the recorded
Ph.Eur. 2.8.2 observation evidencing seed, or **(B) correct** — reissue with foreign
matter 0.08 % conforming. Batch disposition is held pending their written reply.

## Standing rule — one Drive folder per tested batch (v1.1)

Stored in the RAG as `SOP_RAG_INGESTION_per_batch_folder_rule_v1.1.txt`. Supersedes
v1.0, which prescribed a zero-padded `NN. <batch>` numeric prefix; **that prefix is
retired** (a human corrected this call — inserting a batch out of order would have
forced a full renumber, and the Drive tools cannot rename).

**Location history:** the batch folders were first built under a staging folder
named `001 COAs`; a human then cleared the ImB_QC_COAs Drive folder itself of its old
loose files/folders and moved all 80 batch folders directly into it. `001 COAs` no
longer exists. **The batch folders now live directly under the Drive source-of-truth
folder**, `16oMK_j0FUusjveV61B5rxWi6Sl5kQsn5`.

On **every** future ingestion of outsourced certificates:
1. Determine the tested batch; name the folder by **batch number, P-number preferred**
   with the cultivation code in parentheses (e.g. `P060402 (GorillaGlue)`), else the
   strain/lot code alone (e.g. `FB032601`, `BG1024`). **No numeric prefix** — the
   folder title is the batch name only.
2. **Reuse** an existing folder for that batch; **create** one only for a batch that
   has none yet — directly under the ImB_QC_COAs Drive folder.
3. Place every outsourced certificate for that batch (matched by P-number and/or
   cultivation code) into its folder; de-duplicate exact byte-duplicates.
4. Chronological order is **not** encoded in the folder name (Drive sorts un-prefixed
   names alphabetically). It is recorded separately by the `seq` + issue-date columns
   of the Drive index / master table kept in the RAG.

> **Tooling constraint:** the Drive MCP tools can create folders and copy files but
> **cannot move, rename, or delete**. Copying a certificate into its batch folder
> leaves the original in the parent folder, which a human must delete. Always report
> the parent-level duplicates that need manual deletion.

## Ph.Eur. 11.5 Cannabis Flower Monograph (3028) — parameter coverage

| Ph.Eur. parameter | Method | Lab | Coverage |
|-------------------|--------|-----|----------|
| Identification (macro + micro) | 2.8.23 | UKIM | ✅ explicit per-sub-result on UKIM records |
| Assay Total THC / CBD / CBN | 2.2.29 HPLC/DAD | Farmahem / UKIM | ✅ broad, with U |
| Loss on drying | 2.2.32 | Farmahem / UKIM | ✅ broad |
| Foreign matter | 2.8.2 | UKIM | ✅ on UKIM records (full compound criterion preserved) |
| Mycotoxins (aflatoxins + OTA) | 2.8.18 | Farmahem / IPH | ✅ 197-series M panel + Bundle summaries |
| Pesticides | 2.8.13 | IPH + State Phytosanitary | ⚠ raw OCR + Bundle summaries |
| Heavy metals Cd/Pb/As/Hg | 2.4.27 | IPH | ⚠ raw OCR + Bundle summaries |
| Microbial enumeration | 2.6.12 / 5.1.8 | IPH | ⚠ raw OCR + Bundle summaries |

Where an external certificate prints results but no limit column, the applicable
acceptance criterion is added from PP-QC-SPEC-IB-001 / Ph.Eur. 3028 and **labelled as
added-for-review**, never presented as printed on the certificate.

## Pipeline gotchas (hard-won — read before scripting against Letta)

- **`run_from_source` schema derivation is recursive.** Letta derives a JSON schema
  from submitted code and requires docstrings + type annotations on **nested**
  functions too. Write **one top-level function with no nested `def`s**, or the call
  is rejected before it runs. For repeat use, register the uploader once as a real
  Letta tool (`operation=create`) and call it by name.
- **Long multi-upload calls can return a transport error while still executing
  server-side.** Always re-query file state before retrying, or you create duplicates.
- **`error` state usually means the embedding key/quota, not the file.** Check the
  OpenAI key first; a 429 flips every file to `error`.
- **Redrive** = `DELETE {BASE}/v1/sources/{SID}/{file_id}` then re-upload.
- Reading Drive PDFs: `get_file_metadata` returns the extracted text in
  `contentSnippet` — cheaper than `read_file_content`, and far cheaper than
  `download_file_content` (base64 blows up context).

## Data integrity — absolute

Transcribe only values actually printed. Never invent, infer, round or back-calculate
a pharmaceutical result. Preserve `ND`, `<LOQ` and any printed `<value` verbatim. Leave
absent fields blank. Where OCR is ambiguous, transcribe the best reading and attach a
`Data-integrity note (OCR)` line — never silently normalise. Where a certificate is
internally inconsistent, do not quietly "fix" it and do not assert an error without
evidence: raise a QC discrepancy note and query the issuing laboratory.

## File naming convention in this source
```
UKIM_PPK<no>_<Strain>_<batch>.txt
Farmahem_<series>-<n>-<K|M|GS>_<Strain>_<batch>_<panel>.txt
Bundle_<batchcode>_<Strain>_<Pnumber>_full_panel.txt
```
