# Why a retest certificate still prints nothing — 16.09.2026

The rule, as the Head of QC states it: a batch was made a year ago and tested in full
then. At twelve months the qualified person retests **cannabinoids and mycotoxins** only,
and on that basis a new certificate issues carrying **every** parameter of the
specification — the retested ones from the retest laboratory, every other one **from the
initial testing of the same batch**. That is legitimate: heavy metals, mycotoxins and
pesticides cannot rise on a stored lot and microbiology only improves. One certificate may
be cited for one parameter and not another — where the Centre for Natural Products tested
loss on drying on the same page as the cannabinoids, that page is cited for loss on drying
while the retest laboratory's page is cited for the assay.

That is what the desk does. Where a retest certificate prints nothing it is **not** the
carry failing.

## Measured

| | certificates | cells | filled |
| --- | ---: | ---: | ---: |
| Tranche 1 retest | 20 | 420 | **90 %** |
| Tranche 2 retest | 30 | 630 | **78 %** |

Eighteen of the fifty are short of a whole panel, always the same way — the initial
round's microbiology, heavy metals or in-house identity.

| tranche | certificate | lot | missing |
| --- | --- | --- | --- |
| 1 | CoQ-PP_26-091 | P060352 | microbiology, heavy metals, loss on drying, pesticides |
| 1 | CoQ-PP_26-092 | P060402 | microbiology, heavy metals |
| 1 | CoQ-PP_26-097 | HPA1024 | loss on drying |
| 1 | CoQ-PP_26-099 | P060152 | microbiology, heavy metals |
| 1 | CoQ-PP_26-101 | OPM1024 | loss on drying |
| 1 | CoQ-PP_26-105 | P060382 | microbiology, heavy metals, loss on drying, pesticides |
| 2 | CoQ-PP_26-106 | P060122 | microbiology, heavy metals, identity |
| 2 | CoQ-PP_26-108 | P060372 | microbiology, heavy metals, identity, loss on drying, pesticides |
| 2 | CoQ-PP_26-109 | P060132 | microbiology, heavy metals, identity |
| 2 | CoQ-PP_26-115 | GG1024 | microbiology, heavy metals |
| 2 | CoQ-PP_26-120 | P060182 | microbiology, heavy metals, identity |
| 2 | CoQ-PP_26-122 | P060362 | microbiology, heavy metals, identity, loss on drying, pesticides |
| 2 | CoQ-PP_26-123 | P060412 | microbiology, heavy metals |
| 2 | CoQ-PP_26-124 | P060422 | microbiology, heavy metals |
| 2 | CoQ-PP_26-125 | P060492 | microbiology, heavy metals, identity, loss on drying, pesticides |
| 2 | CoQ-PP_26-126 | P060172 | microbiology, heavy metals |
| 2 | CoQ-PP_26-131 | P060232 | microbiology, heavy metals |
| 2 | CoQ-PP_26-132 | P060112 | microbiology, heavy metals |

## The Head of QC is right: the results are on the desk, and not in the register

`ingestion/coa_track/letta-imb-coas/exports/master_coa_table.tsv` — the export of the
eCoA database, 2,479 rows, one per certificate and parameter, with the certificate code,
the issue date, the issuing institution and the Drive file link — holds results that the
**release register** does not, and the release register is the one source a certificate
of quality compiles from.

**GG1024** is the clearest case. The database holds **103 rows** for it, among them
**15 microbiology** and **12 heavy-metal** results on `1766/2025`, `2472/2025` and
`320/0587/25`. `CoQ-PP_26-115` prints nothing for either panel. The same holds for
`HPA1024` (78 rows, 10 microbiology, 10 metals) and `OPM1024` (140 rows, 20 and 18).

Across all 172 certificates, **116 cells that print the withheld token have a result, a
certificate code and a date in that table**. Fifty-one lots are affected; `GG1024` alone
accounts for eighteen cells.

For the 2026-packaged lots the database agrees with the register: `P060402` and `P060152`
carry an explicit `[COVERAGE GAP] — No record found` row where microbiology and metals
would be, and `P060122`, `P060132`, `P060362`, `P060372`, `P060492`, `P060112` have no
rows at all. Those are genuine gaps in the testing, not in the desk.

## What taking them in requires

The table names a parameter in prose — *"Total Δ9-THC, as Δ9-THC (Ph.Eur. 2.2.29)"*,
*"На жолчка толерантни грам-негативни бактерии"* — and a certificate of quality needs
each mapped to its determination number with certainty. A pattern written in one pass
matched 28 cells to arsenic on the letters `As`, which is exactly how a mercury result
lands in the arsenic row. **The mapping has to be read and confirmed per distinct
parameter name before a single value is written**, the way every earlier intake was: the
IJZ-MB campaign, the April-2026 panel, the Farmahem 227-К series.

That is the next job, and it is bounded — the table holds a few dozen distinct parameter
spellings, not thousands.
