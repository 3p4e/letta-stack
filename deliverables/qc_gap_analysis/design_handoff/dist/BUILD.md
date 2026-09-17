# How this folder is rebuilt

Everything here is built from the repository and can be thrown away and remade:

```
node    design_handoff/toolchain/build_v40.js                                   # 172 documents (HTML)
python3 design_handoff/toolchain/print_v40.py --no-flatten                      # one vector PDF per document + four folder documents
python3 design_handoff/toolchain/merge_tranches_v40.py --no-print --no-flatten  # tranche 1 and 2, both rounds
python3 design_handoff/toolchain/merge_tranches_v40.py --no-print --no-flatten --series reissue
python3 design_handoff/toolchain/merge_tranches_v40.py --no-print --no-flatten --tranche 3
python3 design_handoff/toolchain/merge_tranches_v40.py --no-print --no-flatten --tranche 3 --series reissue
```

python3 design_handoff/toolchain/export_docx_v40.py                             # one .docx per certificate
python3 design_handoff/toolchain/package_v40.py --single                        # ONE archive of the whole folder tree, in parts under 95 MB
```

`package_v40.py` refuses a stale build: every page must be newer than its HTML and every
Word file newer than its page.

## Vector, not flattened

The deliverable is the **vector PDF**. A laser printer renders vector text and fills crisply
at its native resolution; a flattened 300 dpi raster only softens it. The documents are
prepared for print rather than rasterised: fonts subset and embedded, every gradient opaque
(no alpha veil for the RIP to composite), the heading bars one smooth two-stop fill with no
inset stripes. No image is placed on the page: the signature boxes carry their line and
the space above it, and the certificate is signed by hand once printed (Head of QC,
17.09.2026).

## The archive

One archive, `PP_CoQ_Package_2026-09-17.zip`, written in parts of at most 95 MB (`.z01`, `.z02` …)
because GitHub refuses any file over 100 MB. Inside it, the whole folder tree: `01_Merged_PDF/`
(the tranche documents, release round then retest, and the retest rounds alone, then the
by-round documents), `02_Certificates/` (every certificate as HTML, vector PDF and Word by
tranche and round, the six outside the tranches under `Not_in_a_tranche/`), `03_Lists/`,
`04_Internal_CoA/`, `05_Master_Workbook/`, `06_Specifications/`, `07_Records/`, and this
README. `package_v40.py --single` refuses a stale build: every page must be newer than its HTML
and every Word file newer than its page. Without `--single` it still writes the four
per-tranche archives of before.

## The Word documents

Each .docx carries the certificate as the page exactly as it prints — the vector PDF page
rendered at 300 dpi, edge to edge on A4 with zero margins. It opens and prints in Word like
any Word file and cannot drift from the PDF. The text inside is not editable in Word: the
editable source is the certificate's HTML beside it, and the controlled record is the PDF.
