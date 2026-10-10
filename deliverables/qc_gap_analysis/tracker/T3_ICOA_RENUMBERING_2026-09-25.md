# The Tranche 3 internal-certificate renumbering — Head of QC, 25.09.2026

## The ruling

> *"For those Tranche 3 certificates of quality and the internal certificates of analysis that are
> cited in the CoQs — if their document number is already cited to another document that is from
> Tranche 2 or 1, that means you will take the first available number, for the first chronological
> batch that needs one; and the same will go for the internal certificates of analysis. Simple as
> that."*

## The certificate-of-quality side: the rule applies and finds nothing

`CoQ-PP_26-001` … `-172` has **no gap, no duplicate, and no Tranche 3 number held by a Tranche 1 or 2
document**. There is nothing to move and no free certificate-of-quality number to move it to — nor is
one needed. **No `CoQ` code was touched.** This is worth stating rather than passing over: the rule was
applied to both fleets, and on one of them the answer is that the numbering is already sound.

## The internal-certificate side: eleven moves

| | |
| --- | ---: |
| Tranche 3 retest records | **31** |
| whose number a delivered Tranche 1/2 page already held | **11** |
| free numbers in the series | **16** |
| used by this ruling | **11**, the lowest eleven |
| left for the five Tranche 2 duplicates | 5 — `103 108 119 120 127` |

**Chronology** comes from the cultivation batch code, which carries the month and year: `BSS1024` is
10/2024, `CJ052501` is 05/2025, `J31112501` is 11/2025. The strain prefix may itself contain digits
(`J31`), so the **trailing** digit run is read, not the leading one — a first attempt that read the
leading digits turned `FB012603` into the year 2060 and failed on `J31112501` altogether.

**Within one month** the packaging lot orders the batches, and a batch with no packaging lot yet sorts
after those that have one. Four batches share 10/2024, so this tiebreak decides their order and is
recorded here as a choice rather than a fact.

| # | batch | cultivation batch | P lot | certificate of quality | internal certificate was | now |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | 10/2024 | `GG1024_02` | P050012 | `CoQ-PP_26-147` | `iCoA-PP_26-147` | **`-085`** |
| 2 | 10/2024 | `BSS1024_01` | P050122 | `CoQ-PP_26-137` | `iCoA-PP_26-137` | **`-086`** |
| 3 | 10/2024 | `BSS1024_01/2` | P050142 | `CoQ-PP_26-138` | `iCoA-PP_26-138` | **`-088`** |
| 4 | 10/2024 | `CJ1024` | — | `CoQ-PP_26-142` | `iCoA-PP_26-142` | **`-089`** |
| 5 | 05/2025 | `CJ052501-2` | P050172 | `CoQ-PP_26-140` | `iCoA-PP_26-140` | **`-090`** |
| 6 | 06/2025 | `GP062501` | P050202 | `CoQ-PP_26-149` | `iCoA-PP_26-149` | **`-093`** |
| 7 | 07/2025 | `GP072501-1` | P050292 | `CoQ-PP_26-150` | `iCoA-PP_26-150` | **`-094`** |
| 8 | 10/2025 | `GRC102501/1` | P060142 | `CoQ-PP_26-152` | `iCoA-PP_26-152` | **`-095`** |
| 9 | 11/2025 | `CC112501` | — | `CoQ-PP_26-139` | `iCoA-PP_26-139` | **`-096`** |
| 10 | 11/2025 | `GG112501` | — | `CoQ-PP_26-148` | `iCoA-PP_26-148` | **`-097`** |
| 11 | 01/2026 | `FB012603` | — | `CoQ-PP_26-143` | `iCoA-PP_26-143` | **`-101`** |

## What the run did, and what it refused to do

`tracker/apply_t3_icoa_moves_2026-09-25.py` — `--check` writes nothing, `--apply` commits the change.
It wrote **11 `icoa_code` fields and 33 citing rows**.

The citing rows needed care. Sixty-six rows in the register name one of the eleven numbers, and every
one of them cites **its own record's number** — none cites another lot's. So the 33 belonging to the
moved Tranche 3 records follow the move, and the 33 belonging to the Tranche 1/2 records that
legitimately own those numbers are left exactly as they are. The script rewrites only inside the record
it is moving and **reports** any row elsewhere rather than touching it; that was checked before applying,
not assumed.

Guards that abort the run: a number held by one of the 44 delivered pages may never move; exactly the
colliding records move; every number taken must have been free and no two moves may take the same one;
and the batch order must be readable for every record.

## Read back off the register afterwards

| | |
| --- | ---: |
| Tranche 3 retests still colliding with a delivered page | **0** |
| delivered numbers still pointing at their own page | **44 / 44** |
| distinct certificate-of-quality codes over 172 records | **172** |
| citing rows naming a number no document holds | **0** |
| numbers still held by two lots | **5** — `113 123 125 129 134` |

Those five are Tranche 2 records colliding with other Tranche 1/2 documents. They are **outside this
ruling's scope**, which was Tranche 3, and the five free numbers they need are reserved and unused. The
numbering is not yet single-valued across the whole series, and saying so is part of the record.

## Still not issued

All 31 remain `issued = false`, and 30 carry `Issuable = allocated`. Moving allocated → issued is the
Head of QC's GMP authorisation, and this change does not approach it. No certificate was built or
reprinted — the 31 Tranche 3 documents do not yet exist in the approved format, and that build needs
disk this container does not have.
