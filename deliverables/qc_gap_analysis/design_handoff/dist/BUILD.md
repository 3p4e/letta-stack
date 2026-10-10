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
python3 design_handoff/toolchain/package_v40.py                                 # the four archives below
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

## The archives

Four whole archives, each under GitHub's 100 MB limit, nothing split: one per tranche — the
merged tranche document and the retest-only document, then every certificate of the tranche
as HTML, vector PDF and Word by round — and `PP_CoQ_Package_2026-09-17.zip` with everything
shared: the merged documents of all three tranches and the by-round documents
(`01_Merged_PDF/`), the six certificates outside the tranches (`02_Certificates/`), the two
certificate lists (`03_Lists/`), the 154 internal certificates (`04_Internal_CoA/`), the master
workbook (`05_Master_Workbook/`), the potency specification (`06_Specifications/`) and the
desk's records (`07_Records/`). `package_v40.py` refuses a stale build: every page must be
newer than its HTML and every Word file newer than its page.

## The Word documents

Each .docx carries the certificate as the page exactly as it prints — the vector PDF page
rendered at 300 dpi, edge to edge on A4 with zero margins. It opens and prints in Word like
any Word file and cannot drift from the PDF. The text inside is not editable in Word: the
editable source is the certificate's HTML beside it, and the controlled record is the PDF.
