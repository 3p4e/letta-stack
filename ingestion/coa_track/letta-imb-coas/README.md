# ImB QC CoAs — ingestion driver and QC deliverable builders

Everything here works from the **In-process / Bulk / Finished-product Certificates
of Analysis** issued by the outsourced laboratories (Farmahem, UKIM Center for
Natural Products) for Purely Plant GmbH. Two kinds of code live in this
directory: the RAGFlow ingestion path, and the builders that turn the ingested
certificates into QC deliverables.

## Retired 29.08.2026 — the Letta ingestion bundle

This directory began as a **Letta** deployment bundle: `deploy.sh` created the
`ImB_QC_COAs` Letta source plus the `imb_qc_coa_agent`, and `ingest_imb_coas.py`
/ `ingest_imb_coas_v2.py` walked Drive (or a local mount) and uploaded into it.

**That source no longer exists.** All nine Letta sources were deleted 19.08.2026
on the owner's instruction, `ImB_QC_COAs` among them (263 records), and
`server/runbooks/ingestion_policy.md` now states the standing rule: *never create
a Letta source, and never upload a document to one.* The three scripts ingested
into infrastructure that is gone and did the one thing the policy forbids, so
they have been removed rather than left as a trap for someone who greps for an
ingester and finds a working-looking one. Git history retains them.

The **replacement is RAGFlow**, and it is in this directory:
`ingest_coa_database_2026.py`. The OCR fallback chain that
`ingest_imb_coas_v2.py` pioneered was not lost with it — it is declared as
policy in `agent_model_policy.py` and implemented in
`ingestion/ragflow/doc_identity.py`.

## Ingestion path (current)

| Script | Purpose |
|---|---|
| `ingest_coa_database_2026.py` | Drive eCoA folder → the **RAGFlow** `CoA_DATABASE_2026` dataset (id `f29f8f58…`, voyage-3-large). The only ingester in this directory. |
| `classify_ecoa.py` | Per-certificate classification + metadata from the certificate's own text — batch-release result vs stability-programme timepoint. |
| `reclassify_watcher.py` | Trails RAGFlow's parse queue and repairs `test_type` on documents uploaded before the field-detection fix landed. |
| `agent_model_policy.py`, `AGENT_MODEL_POLICY.md` | The vision/OCR model chain and the per-agent model policy. |
| `rewire_agents.py`, `rewire_via_rest.py` | Apply `agent_model_policy` to the live Letta agents' `llm_config`. Agent models only — these touch no sources. |

> The same RAGFlow dataset id `f29f8f58…` is called **`CoA_DATABASE_2026`** here and
> **`eCoA_DATABASE`** in the deliverables. One dataset, two names in the repo.

## Deliverable builders

They read the certificate data and emit QC artifacts; none of them ingest
anything.

| Script | Emits |
|---|---|
| `build_master_workbook.py`, `build_master_register_html.py`, `coa_pivot.py` | The master eCoA workbook and the published HTML register. `coa_pivot.py` is the shared classification layer both import, so a fix lands in both and they cannot disagree. |
| `build_ecoa_register.py`, `build_qc_register.py` | eCoA and QC batch-release registers. |
| `build_coqs.py` | Per-batch Certificates of Quality (Markdown → the PP document engine). |
| `build_house_specs.py`, `build_spec_matrix.py`, `build_spec_param_listing.py` | QCSP 001 product specifications, the wide-format spec matrix, and the parameter listing. |
| `build_tranche.py`, `build_tranche1_potency_pdf.py`, `build_thc_by_strain.py`, `build_pp_qc_result_table.py` | Tranche and potency summaries. |
| `build_open_items.py`, `coverage_audit.py`, `crosscheck_sources.py`, `reconcile_master_table.py` | Integrity and coverage checks across the sources of truth. |
| `add_*.py`, `fix_*.py`, `normalise_strain_names.py`, `restore_verbatim_cert_codes.py` | One-shot data corrections, kept for audit. |
| `house_fonts.py` | Font resolution for the rendered artifacts. |

Supporting data lives in `sources_of_truth/`, `exports/` and `reports/`;
`INGESTION_STATUS.md` records what has been ingested and what has not.

## Before ingesting anything

Follow `server/runbooks/ingestion_policy.md` — confirm the target RAGFlow
dataset and its embedding model, diff against what it already holds, and verify
parse status and chunk counts afterwards.
