# PQ1 Water Testing — Generator Pipeline

Scripts that produce the deliverables in `/QC_eCoA/WATER_TESTING/PQ1_DELIVERABLES/` from the raw CPH PDF reports.

## Pipeline overview

```
Drive folder 18KPrhRys1RaBhMEwVznZp39jTGNROeN2 (91 CPH PDFs)
      │
      │  Google Drive API (Service Account)
      ▼
/tmp/pq1_pdfs/<NNNN> П.pdf                       # 91 files
      │
      │  pdftotext + regex extraction
      ▼
parsed samples (date, SL_CPH, doc_code, 19 params)
      │
      ├──► build_forms.py            → 97 DOCX forms (zipped)
      └──► build_pq1_deliverables.py → PQ1 Plan/Report + Quali Rezults XLSX
                                        │
                                        └──► extend_defs.py (post-processor)
```

## Scripts

| Script | Purpose |
|---|---|
| `build_forms.py` | For each sample: fills A03/A05/A06 spec form with results + OOS checkboxes. For each sampling day: fills A02 results log with all sampled SLs. Outputs 97 DOCX in `/tmp/forms/` then zips. |
| `build_pq1_deliverables.py` | Builds the populated PQ1 Plan/Report DOCX (based on Annex 07 template, with narrative analysis sections modeled on the GMP example) + the Quali Rezults XLSX (16 SLs × 9 dates × 19 parameters with OOS highlights). |
| `build_xlsx.py` | Earlier raw long-format xlsx (one row per parameter per sample). Superseded by Quali Rezults format but retained for audit. |
| `extend_defs.py` | Post-processor: adds 20 water/sampling-specific abbreviations to Table 1 (Definitions) of the PQ1 DOCX. |
| `fix_c71.py` | One-shot fix: renamed 6 files in the Letta source (`...RO_C71_...` → `...RO_C171_...`) after CPH confirmed the C71 typo. |

## Inputs

- **Source PDFs**: 91 from Drive folder `18KPrhRys1RaBhMEwVznZp39jTGNROeN2` (PQ1_WQC). Some are also git-tracked in `/QC_eCoA/WATER_TESTING/PQ1_WQC/`.
- **DOCX templates**: in `/docs/PQ1_source_docs/`:
  - `EQP-PPS002_PQ-V01_Annex_07_TEMPLATE.docx`
  - `A02_Water_Testing_Results_Log_TEMPLATE.docx`
  - `A03_TW_Specification_TEMPLATE.docx`
  - `A05_TR_Specification_TEMPLATE.docx`
  - `A06_RO_Specification_TEMPLATE.docx`
- **Reference example** (for content style): `GMP_Reference_PQ1_PlanReport_Reverse_Osmosis.docx` + `GMP_Reference_Quali_Rezults.xlsx`.

## Runtime requirements

```bash
python -m venv /tmp/wv
/tmp/wv/bin/pip install google-api-python-client google-auth requests \
                       pandas openpyxl python-docx pymupdf pypdf 'mcp[cli]'
sudo apt-get install -y poppler-utils  # for pdftotext
```

Plus a Google Drive Service Account JSON with `drive.readonly` scope and access to the PQ1 folder.

## Letta source target

```
Source: source-dd320361-43a1-42c1-939a-66530dfab85e
Name:   "PQ1 Water Testing Results Report"
Server: https://mcp-letta.srv1231216.hstgr.cloud/mcp
```

⚠ **Security note**: the Letta MCP endpoint is currently exposed publicly without authentication. Put it behind Cloudflare Access or a bearer-token requirement before further use.
