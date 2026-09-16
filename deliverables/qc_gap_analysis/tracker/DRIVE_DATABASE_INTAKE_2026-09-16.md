# The certificate database held what the desk did not — intake of 16.09.2026

The Head of QC said, of the parameters printing an empty cell: *"that's impossible, I
personally ingested every certificate and cross-checked and double-checked every
certificate in the database folder — there is definitely saved somewhere something."*

He was right, and the desk was wrong about where to look.

## 1 · What was checked, and what it said

Before going to Drive, every local source the desk holds was asked for the missing
microbiology and metals of the short lots:

| source | answer |
| --- | --- |
| the release register (`coq_artifact_data.json`, `reg`) | no microbiology, no metals for these lots |
| `exports/master_coa_table.tsv` (2,479 rows) | prints `[COVERAGE GAP] — No record found in RAG for … Heavy metals (Cd/Pb/Hg/As), Pesticides` against these very P numbers |
| `exports/PP_Spec_Parameter_Listing.xlsx` | `Missing / not tested` |
| `exports/PP_eCoA_Master_Database.xlsx` (QC Exceptions) | the same coverage gap, as an exception row |
| `ingestion/ragflow/cache/all_cert_texts_2026-08-30.json` (291 texts) | none of the codes below is in it |
| the RAGFlow container on the KVM server (14.09) | `total_chunks: 3` — holds nothing the desk does not |

So the absence was real in every file the desk holds. It was **not** real in the owner's
Drive folder `1SmOicCRa8KEqoB-YlCojdap161YMQ-Di`, which carries all twenty-three of the
documents below. The ingestion never picked them up; that is the defect, and it is in the
pipeline, not in the record-keeping.

## 2 · What was taken in

Twenty-three certificates of the Institute of Public Health, against nineteen packaged
lots, written into the release register in the register's own shape by
`apply_ijz_intake.py`:

**Microbiology (#9.1 – #9.5)** — thirteen reports of the Оддел за микробиологија

| P lot | batch on the page | report | issued |
| --- | --- | --- | --- |
| P060152 | J31102501 | 133/0230/26 | 06.03.2026 |
| P060232 | PM112501 | 135/0232/26 | 06.03.2026 |
| P060172 | KC102501 | 129/0226/26 | 06.03.2026 |
| P060112 | PUM102501 | 74/0117/26 | 09.02.2026 |
| P060122 | ACC102501 | 77/0120/26 | 09.02.2026 |
| P060132 | CF102501 | 73/0116/26 | 09.02.2026 |
| P060182 | GRC102501 | 76/0119/26 | 09.02.2026 |
| P060362 | JD012603/1 | 365/0695/26 | 01.06.2026 |
| P060372 | CC012603 | 363/0693/26 | 01.06.2026 |
| P060382 | SCR012603 | 364/0694/26 | 01.06.2026 |
| P060402 | GG012603 | 404/0787/26 | 24.06.2026 |
| P060412 | JD012603/02 | 405/0788/26 | 24.06.2026 |
| P060422 | JD012603/02V | 406/0789/26 | 24.06.2026 |

**Metals, pesticides and total aflatoxins (#11.1 – #11.4, #12, #10.2)** — ten full IJZ
panels: `1056/2026`, `1058/2026`, `1059/2026`, `1060/2026` (09.03.2026), `326/2026`,
`327/2026`, `330/2026` (11.02.2026), `3659/2026`, `3660/2026`, `3662/2026` (22.06.2026).

The metals block does **not** print its four analytes in the same order on every page —
09.03 pages read олово / жива / арсен / кадмиум, 11.02 `330/2026` reads олово / арсен /
кадмиум / жива, and the June pages read олово / кадмиум / арсен / жива. Each value was
taken by its position under that page's own header, and the header is recorded with the
value in `intake_ijz_2026-09-16/reads_panel.json`.

## 3 · What it filled

`apply_campaign_result.py` then placed the results by the rules already in force — the
carry of 15.09 and the date rule of v35, unchanged. **145 cells** that printed a red
`[ — ]` now print a result and cite the document that certifies it.

| | before | after |
| --- | ---: | ---: |
| Tranche 1 retest — cells with no result | 53 | **31** |
| Tranche 2 retest — cells with no result | 155 | **108** |
| all 172 certificates | 1,477 | **1,332** |

(The counts exclude #9.6 and #9.7, which are upon-request determinations and are absent
from every certificate by design.) Assertion findings are unchanged at 40, hard 2.

## 4 · What was read once, and what is therefore NOT printed

The desk's intake gate is two independent reads. This intake is **one** read — of the
Drive text layer — because the owner asked for the fastest route that still tells the
truth. The discipline that replaces the second read is this: **where the page did not
render a figure unambiguously, the figure is not written.** Eight cells are held for a
second read and are listed in `intake_ijz_2026-09-16/reads_microbiology.json` under
`_held`:

* `135/0232/26` (P060232) #9.1, #9.2 — the two counts render as `10 CFU/g  < 10 CFU/g`, the first bound lost;
* `76/0119/26` (P060182) #9.1 — `9 x 10' CFU/g`, the exponent lost;
* `74/0117/26` (P060112) #9.1, #9.2 — both `5 x 10' CFU/g`;
* `73/0116/26` (P060132) #9.1 — `3,1 x 10% CFU/g`; #9.3 — `<10³ и 10² CFU/g`, the second sign lost;
* `129/0226/26` (P060172) #9.3 — `< 10 и >10² CFU/g`, the first exponent lost.

Two further cells are held for a reason that is not the page's rendering but the
**figure's meaning**:

* `73/0116/26` (P060132) **#9.2** reads `3,9 x 104 CFU/g`. Written as 3.9 × 10⁴ it is
  above the specification the certificate prints for #9.2 — while the laboratory's own
  conclusion on the same page is ОДГОВАРА, conforms.
* `364/0694/26` (P060382) **#9.2** reads `1,8 x 104 CFU/g`, which falls in the Ph.Eur.
  5.1.4 undetermined band, against the same page's СЕ ВО СОГЛАСНОСТ.

The desk does not put a figure on a certificate of quality that would take a released
batch out of specification on one read of a page whose own verdict contradicts it. Both
are held until the page is read a second time. **This is for the Head of QC to close.**

## 5 · A starred sample, held under the ruling of 16.09.2026

The only microbiology on file for **P060352** is `366/0696/26`, and the batch printed on
that page is **`FB012602＊`** — a starred sample. The Head of QC ruled on 16.09.2026 that
a starred sample is a second sample of the same packaged lot, whose results stay in the
record and in every statistic but never source a certificate of quality. There is no
unstarred microbiology for P060352, so rather than print an experimental arm's result the
desk holds the whole panel and asks. **This is the second thing for the Head of QC to
close**, and it is the same question OI-28 raises for seven other starred lots.

## 6 · What is still short, and why

* **Tranche 3** (30 certificates) awaits its mycotoxin re-analysis at Farmahem — #10.1 and
  #10.3 on all thirty. That is a laboratory turnaround, not a missing document.
* **CC042601, FB042601, JD042601** carry a 220-K and a 220-M certificate and nothing else:
  no initial testing was ever run on them. Two of the three are on no list the desk holds
  and keep no P number — that is OI-33.
* **P060332** (Cash Cow) has a 197-K and a 197-M and no microbiology or metals anywhere,
  including the Drive folder.
* #1, #2 and #7 on nine or ten Tranche 2 certificates are in-house determinations whose
  internal certificate of analysis has not been written for those lots.

## 7 · How to reproduce

```
python3 deliverables/qc_gap_analysis/apply_ijz_intake.py
python3 deliverables/qc_gap_analysis/apply_campaign_result.py
node deliverables/qc_gap_analysis/design_handoff/toolchain/build_v40.js
python3 deliverables/qc_gap_analysis/design_handoff/toolchain/merge_tranches_v40.py \
        --series reissue --tranche 1 --tranche 2
```

Both appliers are idempotent: a certificate whose code is already in the register is
skipped, and a row that already carries a result is left alone.
