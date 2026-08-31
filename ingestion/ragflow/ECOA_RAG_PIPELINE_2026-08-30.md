# A RAG pipeline for the eCoAs that cannot hide a failed result

Written after the register verification of 29–30.08.2026, which found **five**
certificates carrying a mould count over the Ph. Eur. acceptance criterion —
four of them recorded in the register an exponent too low, so they read as
passing.

> **Amended 31.08.2026.** This document originally said ten. Every certificate
> named in it is real and every value page-verified, but the ceiling they were
> compared against was the literal `10⁴` rather than the maximum acceptable count
> of `2 × 10⁴` that Ph. Eur. 5.1.4 / 2.6.12 and USP <1111> prescribe. Five of the
> ten conform. That correction strengthens the argument below rather than
> weakening it: the pipeline's whole point is that a value only means something
> next to the limit it is judged against, and **a limit is two numbers, not one**
> — what the certificate prints, and the largest result that still conforms. The
> typed record now carries both. Record:
> `review/OOS_RECTIFICATION_2026-08-31.md`.

The point of this document is not that an OCR made a mistake. It is that
**a single superscript decides pass or fail, and nothing in the pipeline was
built to notice.** That is a design problem, not a model problem, and a better
prompt does not fix it.

## What the current pipeline actually produces

Measured against 17 certificates whose values were read off the rendered page:

| RAGFlow's parse of the TYMC result | Count |
|---|---|
| Correct | 6 |
| **Wrong** | **2** |
| **Not extractable at all** — parameter label present, result absent | **9** |

So for these certificates the corpus is reliable for about a third of the
values, wrong on one in eight, and silent on half. An agent querying it gets a
confident answer built on that.

Both errors are the same failure and point the same way: **10⁴ read as 10³**,
never the reverse. `320/0587/25` parses as `4,2 х 10³` where the page says
`4,2 x 10⁴`. `1032/1851/25` parses as `4,9 х 10³` where the page says
`4,9 x 10⁴`.

## Four root causes

**1. The exponent is a superscript, and no text path survives it.**
Drive's text extraction drops it entirely — the same certificate extracts as
`- 10 CFU/g … 5,1 х 10 CFU/g 4,2 x 10 CFU/g`, with every exponent gone. The
RAGFlow vision parse renders exponents but misreads ⁴ as ³. There is no text
route to a trustworthy number here; only the rendered page is authoritative.

**2. Table structure is lost, so values detach from their labels.**
In 9 of 17 the chunk contains `Вкупен број габи и мувли-ТYMC` and, somewhere
else, a list of numbers — but nothing binds the parameter to its result and its
limit. Retrieval then returns a plausible sentence with the wrong number in it,
which is worse than returning nothing.

**3. Cyrillic and Latin homoglyphs are unstable across the corpus.**
`ТАМС`/`TAMC`, `ТУМС`/`ТYMC`/`TUMC` for the same parameter; `131112501` parsed
for batch `J31112501`; certificate codes appear as `197-1-К/26` (Cyrillic К) and
`197-1-K-26` (Latin K) for the same document. Any exact-match lookup fails
silently on these.

**4. Nothing ever compared a result to its own limit.**
Every certificate prints the limit next to the result. Five of them printed a
result above the acceptance criterion and concluded ОДГОВАРА. One subtraction
would have caught all five, at ingest, years before a person did — provided the
subtraction is done against the right number, which is the fifth cause below.

**5. And when something finally did compare them, it compared against the wrong
number.** The first version of `validate_ecoa_limits.py` parsed the criterion
with the same function that parses the result. `magnitude()` answers *what number
is this measurement*; `10⁴ CFU/g` as a criterion is not the number 10 000. Nine
results were reported out of specification where five are. **The typed record is
the fix for this too**: `limit` and `max_acceptable` are separate fields, and R1
compares against the second.

## The pipeline

The governing idea: **numbers stop being retrieved from prose.** Chunk text is
for narrative questions; every value a QC decision touches comes from a typed
record extracted once, validated, and stored.

### 1. Render, never read the text layer

Every page goes to an image at ≥300 DPI and is read by the vision chain in
`AGENT_MODEL_POLICY.md`. `pdftotext` and the Drive text layer are excluded from
the numeric path entirely — proven above to drop exponents. This is also why
`scripts/policy_check.py` rule 1 forbids classical OCR: Macedonian Cyrillic
mixed with Latin chemical symbols is the case it handles worst.

### 2. Extract to a typed record, not a chunk

Per result, capture the value and its criterion together, because their meaning
is only in their relationship — and capture the criterion as **two** numbers,
what the page prints and the largest result that still conforms:

```json
{"parameter": "TYMC", "value": 42000.0, "value_printed": "4,2 x 10⁴ CFU/g",
 "limit": 10000.0, "limit_printed": "10⁴ CFU/g",
 "max_acceptable": 20000.0, "limit_basis": "pharmacopoeial_enumeration",
 "unit": "CFU/g", "verdict_printed": "ОДГОВАРА",
 "certificate": "320/0587/25", "batch": "GG1024-01", "page": 1}
```

`value` and `limit` are floats. The exponent becomes an integer power at
extraction, so no downstream consumer ever has to read a superscript again.
`value_printed` is retained verbatim so a human can always check the machine
against the paper.

**Capture the limit per result, not per column.** The register's column header
says TYMC ≤ 10⁴, but `1220/2171/25` prints ≤ 10² on its own face — its result of
200 fails on the paper and passes against the column. Only a per-result limit
gets that right.

### 3. Two independent reads, and require agreement

Extract each numeric field twice — different model in the chain, or two passes —
and compare. Agreement stores the value; disagreement stores neither and raises
the page for a human. A second read is far cheaper than a missed out-of-spec
batch, and the failure here was a single unchecked read.

### 4. Validate arithmetically at ingest, and refuse to store silently

`validate_ecoa_limits.py` implements the two rules that matter:

- **R1** — a result above its limit is reported regardless of the laboratory's
  verdict. A conclusion of ОДГОВАРА is a claim, not a fact.
- **R2** — a result exactly one decade below its limit is flagged SUSPECT,
  because that is the precise shape a misread ⁴→³ leaves behind, and the only
  shape that converts a fail into a pass.

Run against the register before and after this batch's corrections: **5 R1
findings before, 9 after**. The check works, and the gap between those numbers
is exactly the set of failures the pipeline had been hiding.

### 5. Normalise identity at ingest

One canonical form for certificate codes and batches, computed once:
fold Cyrillic homoglyphs onto Latin, strip separators, map Farmahem's `-LoD-` to
`ГС`/`GS`, and map in-house `QCCoA 001v02` to the register's `PP CoA #NNN`.
Reuse `ingestion/common/batch_id.py::batch_key` for batches — it is the single
definition in this repository and `policy_check.py` already imports it. Without
these four normalisations a naive reconciliation reports hundreds of false
failures; with them, 236 of 284 register rows resolve on the first pass.

### 6. Retrieval returns the record and a link to the page

A QC answer cites the typed record and the certificate page it came from, so
the paper is always one click away. Free-text chunks stay available for
narrative questions — who signed, what method, what the remarks say — but never
supply a number that a release decision rests on.

## The files

| File | What it is |
|---|---|
| `config/ecoa_dataset_config.json` | PATCH body for `/api/v1/datasets/f29f8f58…`, generated from the live config so only the intended fields differ. Strip `_`-prefixed keys before sending. |
| `config/ecoa_extraction_schema.json` | JSON Schema for the typed record. Draft 2020-12, and its conditional rules are enforced, not decorative — a class B record with `confidence: high`, or `reads_agree: false` with a non-null value, are both rejected. |
| `config/ecoa_extraction_agent.json` | Model chain, the extraction prompt, routing by document class, and the acceptance tests. |
| `validate_ecoa_limits.py` | R1/R2 at ingest. |

The agent config carries an `acceptance_tests` block naming the 17 certificates
whose values were read off the page during the verification, with the six
expected flags and the eleven that must stay clean. **An extractor that cannot
reproduce those has not fixed the thing it exists to fix**, and that is a
runnable claim rather than a hope.

## Fixing what is already in the corpus

1. **Re-ingest under the new extraction.** The current `eCoA_DATABASE` parse is
   wrong on at least two documents and silent on many more; it should not be the
   basis of any QC answer until re-read.
2. **Run R1/R2 over the re-ingest** and clear every finding against a page
   before the dataset is trusted.
3. **The chunk counter drifts** — the dataset header advertises 1272 chunks
   where the documents sum to 1261. Refresh it, or consumers keep reading a
   number that is not true.
4. **Keep the corpus and the register in one direction.** The register agreeing
   with the parse and disagreeing with the paper is what let this run; whichever
   becomes the system of record, the other should be derived from it and
   diffed, never maintained in parallel.

## What this does not solve

The five certificates still concluded ОДГОВАРА over their own failing numbers.
No pipeline fixes that — it is a question for the issuing laboratories and for
the deviation records. What the pipeline changes is that the next one is caught
at ingest instead of a year later.
