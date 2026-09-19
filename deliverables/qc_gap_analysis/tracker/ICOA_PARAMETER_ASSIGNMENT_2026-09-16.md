# #1, #2 and #7 now cite the internal certificate the master already assigned them

The Head of QC: *"in the latest version of the CoQ Analysis Master you should actually
continue and assign the certificate of analysis from Purely Plant — basically the internal
certificate of analysis — covering parameters one, two and seven, with dates and every
other information already present there."*

It was already there. `CoQ_Analysis_Master_v41.xlsx` (the script resolves the newest on disk), sheet **iCoA Register**, carries one
row per internal certificate of analysis with its code, its issue date, its basis date,
the batch it belongs to and its own verdict in the columns `#1 Ident. A`, `#2 Ident. B`
and `#7 Foreign matter`. 211 codes, and every certificate that was short on those three
determinations had its code among them.

122 certificates already printed the three from their iCoA. The other 74 printed a red
`[ — ]` under *"to be performed — see route"* — not because the desk had no result, but
because nothing carried the sheet's assignment across into the certificate rows.
`apply_icoa_parameters.py` is that step.

## What it wrote

**165 of 174 cells.** The verdict is the sheet's, never the script's:

* a row whose `#1 Ident. A` reads `Conforms` prints Conforms, cites the iCoA code, takes
  the date the record already carries for that iCoA (03.06.2026 for this series) and
  credits **Purely Plant GmbH (in-house)**;
* a row that names an external certificate instead — `CNP ППК26111` — cites that
  certificate, its own issue date and the laboratory that issued it, which is the
  treatment OI-27 already describes;
* a row the sheet leaves blank stays blank.

| | before | after |
| --- | ---: | ---: |
| Tranche 1 retest — cells with no result | 31 | **30** |
| Tranche 2 retest — cells with no result | 108 | **80** |
| all 172 certificates | 1,330 | **1,165** |

**#1, #2 and #7 are now complete on every Tranche 1 and Tranche 2 certificate.** Assertion
findings are unchanged at 42, hard 2.

## What it held, and why

Three cells: `CoQ-PP_26-071` (P060362, Jelly Donutz, the initial release of 06.06.2026)
#1, #2 and #7. The sheet assigns them `CNP ППК26111`, which CNP issued on **30.06.2026** —
after the certificate. The ruling of v35 stands: a release certificate may not rest on a
document that did not exist when it issued. The same lot's twelve-month reissue takes it
without difficulty, because that certificate is dated later.

## One thing the sheet asserts that the register does not corroborate

`ППК26111` is filed in the release register under the cultivation batch `JD012603-02V`
alone. The iCoA Register assigns it to **three** packaged lots of that cultivation batch —
P060362, P060412 and P060422. A certificate has one issue date and one laboratory wherever
it is filed, so the date and the laboratory are not in doubt; which lots it covers is the
master's assignment, and carrying that across is what this script was asked to do. It is
recorded here rather than resolved, because it is the Head of QC's to confirm.
