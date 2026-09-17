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

One per tranche, each carrying **every certificate as HTML, vector PDF and Word (.docx)**,
plus the merged tranche documents; and one by testing round.

| archive | contents |
| --- | --- |
| `PP_CoQ_Tranche_1_2026-09-17.zip` | `HTML/`, `PDF/` and `DOCX/` for the 21 release + 21 retest certificates · `CoQ_Tranche_1.pdf` (42 pp) · `CoQ_Tranche_1_Retest.pdf` (21 pp) |
| `PP_CoQ_Tranche_2_2026-09-17.zip` | the 32 + 32 · `CoQ_Tranche_2.pdf` (64 pp) · `CoQ_Tranche_2_Retest.pdf` (32 pp) |
| `PP_CoQ_Tranche_3_2026-09-17.zip` | the 30 + 30 · `CoQ_Tranche_3.pdf` (60 pp) · `CoQ_Tranche_3_Retest.pdf` (30 pp) |
| `PP_CoQ_By_testing_round_2026-09-17.zip` | `CoQ_ISSUE_COQ.pdf` (89 pp) · `CoQ_REISSUE_T1/T2/T3.pdf` (21 / 32 / 30 pp) · `Not_in_a_tranche/` — HTML, PDF and DOCX of the six release certificates that belong to no tranche (FB032601, GG032601, JD022601, P160012, P160022, P160032), so every one of the 172 documents is delivered individually in exactly one archive |

An HTML certificate is self-contained — brand mark, stylesheet, fonts by link — and opens
in any browser; printing it from the browser at A4, margins 0,
background graphics on, gives the same page as its PDF.

## The Word documents

Each .docx carries the certificate as the page exactly as it prints — the vector PDF page
rendered at 300 dpi, edge to edge on A4 with zero margins. It opens and prints in Word like
any Word file and cannot drift from the PDF. The text inside is not editable in Word: the
editable source is the certificate's HTML beside it, and the controlled record is the PDF.
