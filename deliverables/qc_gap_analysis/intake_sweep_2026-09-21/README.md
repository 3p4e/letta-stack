# The sweep intake of 21.09.2026 — in progress

Owner, 21.09.2026: *"There will be no empty space in the certificate of quality nor the
certificate of analysis — all parameter results must be filled in."*

After the closed token set was restored, 485 cells on the face of the 172 certificates
carried a marker rather than a result. **176 of those are the owner's declared exception**
— #10.1 aflatoxin B1 and #10.3 ochratoxin A on the *initial* certificates, which the
release round never ran and the re-analysis campaign carries. That leaves **309 to hunt**.

## What this intake is

The audit of 20.09.2026 enumerated the owner's `eCoA_DATABASE` and held it against every
desk record. **Twenty-four laboratory scans are in no record at all** — not the ingested
corpus, not the release register, not the 09.09 resolution pass. Fifteen of them stand
behind a cell that prints a marker today:

| document | lot | fills |
|---|---|---|
| `75/0118/26` IJZ-MB | P060102 WED102501 | #9.1–9.5 |
| `76/0119/26` IJZ-MB | P060182 GRC102501 | #9.1–9.5 |
| `131/0228/26` IJZ-MB | P060202 J31112501 | #9.1–9.5 |
| `132/0229/26` IJZ-MB | P060162 SJ102501 | #9.1–9.5 |
| `137/0234/26` IJZ-MB | P060222 OPM112501 | #9.1–9.5 |
| `362/0692/26` IJZ-MB | P060342 SCR012601＊ | #9.1–9.5 |
| `403/0786/26` IJZ-MB | P060442 SCR022601 | #9.1–9.5 |
| `407/0790/26` IJZ-MB | P060392 FB012603V | #9.1–9.5 |
| `408/0791/26` IJZ-MB | P060432 FB012603 | #9.1–9.5 |
| `434/0848/26` IJZ-MB | P060452 FB032601 | #9.1–9.5 (second panel) |
| `475/0927/26` IJZ-MB | P050022 GP0824-02 | #9.1–9.5 |
| `031-1-К/26` Farmahem | P060182 GRC102501 | #3, #4, #5, #6 |
| `031-1-ГС/26` Farmahem | P060182 GRC102501 | #8 |
| `328/2026` IJZ | P060182 GRC102501 | #10.2, #11.1–11.4, #12 |
| `227-18-М/26` Farmahem | P050202 GP062501 | #10.1, #10.3 |

The four GRC102501 documents together close a lot that prints 22 markers today — the
cannabinoids, loss on drying, microbiology and the whole contaminant panel, all on file
and none of it read.

## The gate

The same one, unchanged: two vendors' models read each rendered page without seeing the
other's answer (`two_reads.py` → `reads_A.json` / `reads_B.json`), a value is taken only
where both wrote it, and anything they differ on is held until a third read of the page
settles it and records the region it was cut from.

**State: the two reads are running. Nothing is applied until the gate reports, and a
document is applied only for the determinations it actually reports.**

## Files

    drive_ids.json   the fifteen documents, their Drive ids, lot and laboratory
    two_reads.py     the two vendor reads
    read.log         their running record
