# Internal certificates of analysis — the iCoAs the CoQs cite

*Purely Plant GmbH · Quality Desk · 17.09.2026 · work in progress*

Every certificate of quality names its in-house iCoA in Section 03 and credits
determinations to it. This builds those documents, straight from the certificates that
cite them, on the owner's own `iCoA_Template_v02_VariationF.html` (vendored under `base/`).

```
python3 icoa_handoff/build_icoa_v1.py            # every cited in-house iCoA
python3 icoa_handoff/build_icoa_v1.py --only retest
```

## What is here

`out/INITIAL/` (77) and `out/RETEST/` (38) — **115 documents**, one per in-house iCoA code
the certificates actually cite. `out/_build_report.tsv` lists each with its round, lot,
scope and the certificates it serves.

* **95** cover Identification A + B + Foreign matter (`#1 #2 #7`), **13** cover
  Identification B alone, the rest are the legacy full/part-panel in-house records.
* **INITIAL** holds the identity iCoAs issued once at packaging (26 cited only at release,
  51 also carried to the reissue). **RETEST** holds the 38 records a retest certificate is
  the first to cite.

## Why the certificate is the source, not a register

The master workbook's **iCoA Register** sheet has two rows inserted (serials 212-213) that
shift 192 of its codes by +1/+2 against the certificates' own numbering; the 09.09 CSV
parts company on 46 lots through spelling variants. Building off either register would
print the wrong code and lot. The certificate that cites an iCoA is internally consistent,
so the builder reads code, scope, results, dates and laboratory from it.

## Still to do before these are final

1. **The Head of QC's review** — these have not been signed off; the CoQ visual pass is
   still settling and the same house style should carry here.
2. **Print to PDF** — no print/flatten pipeline is wired for the iCoAs yet.
3. **`227-18-М/26`** — the one Tranche 3 mycotoxin scan still unread (OI-48) does not affect
   the identity iCoAs but is the one open external gap in the set.

Nothing here is a controlled record until the Head of QC signs it: every signature block
prints its roles and titles with no name and no date, for wet signature.
