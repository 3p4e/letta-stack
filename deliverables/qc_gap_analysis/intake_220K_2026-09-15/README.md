# Tranche 2 potency certificates — intake of 15.09.2026

Thirty-two Farmahem reports of analysis, `220-1-К/26` … `220-32-К/26`, from the owner's
eCoA database (Drive folder `eCoA_DATABASE`, `1SmOicCRa8KEqoB-YlCojdap161YMQ-Di`, files
`250826_220-n-K-26_FHM_…` and `260826_220-n-K-26_FHM_…`; the Drive id and the SHA-256 of
every PDF are in `reads_220K.json`). Each is 2 pages with no text layer. Received by the
laboratory **17.08.2026**, analysed 24.08.2026 (220-1 … -16) or 25.08.2026 (220-17 … -32),
issued **25.08.2026** (220-1 … -16) and **26.08.2026** (220-17 … -32). Each prints Total CBD,
Total CBN and Total Δ9-THC by HPLC/DAD, ИР 7.2.1-47К (в.1), accredited to MKC EN ISO
17025:2018; no specification column and no conclusion — a report of results. Total CBD and
Total CBN read `< LOQ` (< 0.20 %) on every certificate; Total Δ9-THC as printed with its
expanded uncertainty (k = 2).

## Why they are an intake of 15.09.2026

The files have been in the owner's database since 09.09.2026 — the reconciliation of that
day listed them as documents on file and even read five of them for lots that had no other
potency certificate — but the desk never took them in as the Tranche 2 retest assays. So on
the v29 `CoQ Register` every Tranche 2 reissue stood *not yet issuable — mycotoxins on file,
retest assay pending*, and the owner asked (15.09.2026): "they are all contained in the
database … here are all retest results that I have on file and correct yourself." This
folder is the correction.

## How they were read

`reads_220K.json` is the page read of 15.09.2026: Claude's transcription of every certificate
from the rendered page crops at 100 DPI (the report number and issue date from page 1; the
receipt date, the sample line, the laboratory sample number, the mass, the analysis date, the
method and the results table from page 2) — no text layer, no classical OCR. `readB2_220K.json`
is the second read: an independent transcription of the same pages by a separate reader
session that was given only the PDFs and saw no other transcription, at 130 DPI with 300 DPI
re-checks of every digit. The runner's Gemini reader (`extract_ecoa_records.read_gemini`) was
refused on 15.09.2026 — every key answered 503 or 403 — so the second read is not Gemini's,
and this README says so.

`apply_220K.load_reads()` compares the two on the batch printed, the date of issue, the date
of analysis, the receipt date, the laboratory sample number, the three results and the
uncertainty beside each, and refuses to write on any disagreement: **32 of 32 agree**. The
second reader's notes: 220-18-К/26 prints `Jelly Donutz / P060422` without the `V` the file
name carries; `Clemosa a Bud` and `Pure Michigen` are spelled as printed.

## Where each certificate goes

`apply_220K.py` writes the 32 into the owner's release register, idempotently, in the shape
of the 197-n-К/26 rows: THC % as printed, `≥ 5.00 %` in THC spec, `<LOQ` for CBD and CBN,
`/` in every column the certificate does not report, the code with the register's Cyrillic К,
the date of issue, Farmahem, Open. Every one of the 32 lands in an existing block — 28 by the
P lot printed, `GG1024`, `JD042601`, `FB042601` and `CC042601` by the cultivation batch printed
— and seven of the 28 through the Head of QC's batch list (`tracker/batch_dates.csv`) because
their label row carries no P lot: P060322 = FB012601/1, P060182 = GRC102501-2, P060412 =
JD012603-02, P060422 = JD012603-02V, P060172 = KC102501, P060232 = PM112501, P060282 =
SCR112501. The script opens no block and stops if one is missing.

`instances_220K.py` writes the 32 as #3–#6 testing instances into `tracker/new_instances.json`
(identification C `Conforms` on the HPLC cannabinoid profile, the owner's ruling of
02.09.2026; Total THC, CBD, CBN as printed), keyed on the code, so the tracker cites them —
the register alone never reaches a tracker cell (the v27 lesson). `receipt_dates.py` reads
`date_received` from `reads_220K.json` as its fifth source, so the references table carries
17.08.2026 beside every 220-n-К/26 it cites.

## What changes on the registers

With these 32, every Tranche 2 lot has all three parts of its 12-month reissue — the retest
assay (220-n-К/26, 25/26.08.2026), the mycotoxins (220-n-М/26, 11.09.2026) and the campaign's
internal certificate (sampled 12–14.08, issued 17.08.2026) — so the `CoQ Register` numbers the
Tranche 2 reissues after the Tranche 1 series, each planned for the first working day 7 days
after the last certificate it cites. Tranche 3 still waits for its mycotoxin certificates
(227-n-М/26): the owner's database and the three Farmahem tranche folders shared on
15.09.2026 hold 197 K + M, 220 K + M and 227 K — no 227 M.

    python3 deliverables/qc_gap_analysis/intake_220K_2026-09-15/apply_220K.py
    python3 deliverables/qc_gap_analysis/intake_220K_2026-09-15/instances_220K.py
    python3 deliverables/qc_gap_analysis/receipt_dates.py
