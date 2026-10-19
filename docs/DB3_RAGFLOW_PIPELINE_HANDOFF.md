# DB3_PP_CURRENT — the approved-documents pipeline (handoff, 18.10.2026)

The rules for the RAGflow dataset that holds Purely Plant's **approved, in-use** controlled documents, and for loading
them and the ACME_SOP work in progress into the DocEngine. Rulings are the Head of QC's, 18.10.2026 unless dated.

## 1. What DB3 is, and is not

- **DB3_PP_CURRENT** holds the text of the approved, in-use documents, and only those. The authors read it for house
  structure and wording; they never copy a value, batch, name, date or result from it into a new document
  (`ragflow.EXAMPLES_NOTE`).
- **No draft goes into DB3.** A draft retrieved as "approved and in use" is the failure the dataset exists to prevent.
  The ACME_SOP work in progress is stored in the engine (`kind: wip`) and is never indexed.
- **Not a QMS record** (CLAUDE.md §10). The approved originals, their signatures and QALI 001 stay the authority;
  DB3 is a working copy for drafting. No deviation, OOS or other QMS procedure is raised from this work.

## 2. The dataset

| setting | value |
|---|---|
| name / id | `DB3_PP_CURRENT` / `880312c6cb1411f18ed047989fb7f345` |
| embedding | voyage-3-large |
| parser | naive (text) |
| chunk size | 1024 tokens |
| delimiter | `\n\n` |
| GraphRAG / RAPTOR | off / off |
| engine setting | `RAGFLOW_EXAMPLE_DATASETS` (default this id since 18.10.2026); the first id is where approved text is indexed |

Change a setting only by `PUT /api/v1/datasets/{id}` with the four fields above; RAGflow refuses extra parser fields.

## 3. One entry per code + version

Most approved documents exist twice: the Word file and the signed scanned PDF of the same document.

1. **Pair** them by house code + version (house form: `QCSOP011`, `QCSOP011A01`, `QCT017`; CLAUDE.md §10 and
   `app/house_codes.py`).
2. **The Word file is the text** that is embedded.
3. **The scan is the legal record.** It is referenced (Drive id) and never embedded or re-OCR'd in bulk.
4. **A scan is read only to settle a named disagreement**, one document at a time: its first page, for code,
   version, effective date and signatures. A disagreement with the Word file or the register goes to the Head of
   QC; nothing is decided for him. What the read establishes is written back in the same change.
5. **A scan-only document** (no Word file) is listed in the manifest as `scan_only` and is not ingested until its text
   is obtained (OCR on request, tagged `source: scan`, its text checked before use).
6. **Two Word files for one code + version that differ** are `ambiguous`: both listed, neither ingested, the Head of
   QC chooses.

## 4. How a document gets in

```
Drive (approved folder 1oPEIlNTWMutZIineO6Pb_DC3HZ9ue1WM)
  └─ read the Word text (Drive connector read_file_content — never a binary download)
     └─ <CODE>_v<VER>.md   YAML front matter + text          (one file per code + version)
        └─ tools/ingest_reference.py approved <dir>         (inside pp-docengine)
           └─ PUT /reference   → docengine.reference_docs   (kind approved, sha256 of the text)
                               → RAGflow DB3: "<CODE>_v<VER>.md", titled "<CODE> v<VER> — <title>", parsed
```

- **Front matter:** `code, version, title_mk, title_en, effective_date, department, source_name, drive_docx_id,
  drive_scan_ids` (`wip` adds `parent, package, drive_id, drive_folder`).
- **Idempotent:** the engine keeps the sha256 of the text. The same text sent again changes nothing; a changed text
  replaces the entry and deletes the old RAGflow document.
- **Manifest:** every run writes `MANIFEST.tsv` with `paired | docx_only | scan_only | ambiguous` per document; only
  `paired` and `docx_only` are ingested.
- **Never opened:** `secrets*`, `cookies*`, `*.env`, `credentials*` in any Drive folder.

## 5. Where it shows

- `GET /library` puts every code on one shelf: **approved**, **revision** (in use, a new version being written),
  **drafts**, **numbers** (reserved, unconfirmed or known only), **retired**. It never decides a disagreement: an
  approved copy whose register row says otherwise is shown with a note.
- `GET /reference`, `/reference/{id}` list the held documents and give one with its text.

## 6. Running it on KVM4

- Ingest in batches under the memory guard: RAGflow parsing and the RAGflow server share 16 GB with Agent Zero
  (7 GB on 18.10.2026), and KVM4 has no swap. Stop if available memory falls under 1.2 GB.
- `docker cp` the `.md` folder and `tools/ingest_reference.py` into `pp-docengine`, then
  `docker exec pp-docengine python /tmp/ingest_reference.py approved /tmp/db3` (`DOCENGINE_API_KEY` is in the
  container's environment; never print it).
- Check afterwards: `GET /reference?kind=approved` count = `paired + docx_only` in the manifest; DB3 `document_count`
  the same; every RAGflow document `run: DONE`.

## 7. Open

- The 12 register conflicts (`register/QALI001_QC.yaml`) and every manifest `ambiguous` / `scan_only` row wait for
  the Head of QC.
- QCSOP009: QALI 001 says awaiting signature, the AM index says v01 signed 04.05.2026 — settle from its scan, once.
