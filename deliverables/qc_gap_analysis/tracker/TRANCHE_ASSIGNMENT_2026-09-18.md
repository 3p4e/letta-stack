# The tranches, as the Head of QC has now grouped them

**18.09.2026.** The Head of QC:

> "Inside the folders named T1, T2 and T3 you will find individual folders named after each
> batch number that is contained in tranche one, two or three. This is the new decision.
> Some batches are removed or pushed to tranche three. Observe this for future reference
> and use, because the list of tranche one, two and three batches has changed since the
> last time you had the information."

Read on 18.09.2026 from Drive, `BY_P_FOLDERS/T1`, `/T2` and `/T3`. Seventy-seven batch
folders, named `<cultivation batch>_<P batch>` where the lot has a P number and by the
cultivation batch alone where it has none. The full table is
`tranche_assignment_2026-09-18.csv`; the folder listing exactly as read is
`intake_tranches_2026-09-18/drive_folders_2026-09-18.tsv`.

## What changed

|  | Tranche 1 | Tranche 2 | Tranche 3 | Total |
| --- | ---: | ---: | ---: | ---: |
| Held before (15.09.2026) | 21 | 32 | 30 | 83 |
| **New decision (18.09.2026)** | **20** | **26** | **31** | **77** |

Seventy-six of the seventy-seven are where they were. Two things moved.

### One batch pushed to Tranche 3

| Batch | P lot | Was | Now |
| --- | --- | --- | --- |
| CC012601_1 | P060332 | Tranche 1 | **Tranche 3** |

### Six batches removed from the tranches

All six were in Tranche 2, and none appears in any tranche folder now.

| Batch | P lot | Was |
| --- | --- | --- |
| CLE072501 | P050282 | Tranche 2 |
| OPM092501 | P060042 | Tranche 2 |
| SJ092501 | P060082 | Tranche 2 |
| JD042601 | P060492 | Tranche 2 |
| FB042601 | no P number | Tranche 2 |
| CC042601 | no P number | Tranche 2 |

## The thing this does not decide, and must not be taken to decide

The desk carries **two** groupings, and only one of them is in these folders.

1. **The delivery tranche** — how the certificates are grouped when they are packed and
   handed over. That is what these folders state, and the desk now follows them.
2. **The laboratory campaign** — which of Farmahem's three re-analysis rounds tested the
   batch. That is not a grouping anyone assigns: it is printed on the certificate, as the
   running number of the 197-, 220- or 227-series, and it is what fixes the retest
   sampling day and the reissue's issue date (`sampling_dates.py`, the owner's ruling of
   15.09.2026 — Tranche 1 sampled 21–24.07 and issued 27.07, Tranche 2 sampled 12–14.08
   and issued 17.08, Tranche 3 sampled 19–21.08 and issued 24.08).

`sampling_dates.py` already says this in so many words: *"A campaign is identified by its
certificate series, never by a delivery list: the tranche lists are delivery groupings and
the laboratory tested batches that are on none of them."* So the desk has **not** re-dated
anything on the strength of a folder move. Seventy-three of the seventy-seven agree with
their campaign anyway; three carry no campaign certificate at all
(GRC102501/P060182, JD012603/P060412, JD012603/P060422); and one does not agree:

| Batch | Now in | Campaign certificates | Campaign says |
| --- | --- | --- | --- |
| CC012601_1 · P060332 | Tranche 3 | 197-6-К/26, 197-6-М/26 | Tranche 1 |

`197-6` is the sixth certificate of the first campaign, which the ruling of 15.09.2026
puts on the first sampling day, **21.07.2026**, issuing **27.07.2026**. Its reissue
`CoQ-PP_26-087` is dated on that basis. If the move to Tranche 3 is meant to re-date the
work as well, that certificate moves to sampled 19–21.08.2026 and issued 24.08.2026 — but
the page Farmahem signed would still say 197-6. The desk will not overwrite a date derived
from a laboratory's own certificate on the strength of a folder, so this is **OI-56** and
waits for the Head of QC.

The six removed batches are the same question in a different shape. Each carries a 220-series
certificate — 220-7, 220-22, 220-27, 220-30, 220-31, 220-32 — so each was tested in the
second campaign whatever folder it now sits in. Removing them from the delivery tranche does
not unmake the analysis. What it plainly does mean is that their certificates are **not
delivered in the tranche packages**; whether they are withdrawn from the issue set entirely,
or delivered separately, is the second half of OI-56.

## What follows from this record

* `tranche_assignment_2026-09-18.csv` is the delivery grouping from today. Anything that
  packs or merges by tranche reads it.
* Nothing has been re-dated, re-numbered or re-issued. The 172 certificates on the branch
  are unchanged by this record.
* The campaign grouping in `sampling_dates.py` is untouched, and stays keyed on the
  certificate series.
