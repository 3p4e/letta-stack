# The customer's query of 24.09.2026, held against the register

Cvetanka lists ten batches. Every one is checked below against
`coq_artifact_data.json` — what the register holds, which laboratory, which document, which
date — so the reply separates *a scan we can send today* from *a result that does not exist*.

Eight of the ten match findings the attribution audit of 23.09.2026 already raised
(`tracker/ATTRIBUTION_2026-09-23.md`). Three of her points are not missing paperwork at all.

---

## 1 · What can be sent today — the result exists and the certificate cites it

| batch | certificate | what she asked for | on file |
| --- | --- | --- | --- |
| **P050062** | CoQ-PP_26-012 | the complete set | **complete.** CNP ППК25154 (loss on drying 6.89, Ident C, assays) · IPH 588/1067/25 (microbiology) · IPH 2994/2025 (metals, pesticides, aflatoxins) |
| **P060242** | CoQ-PP_26-060 | the complete set | **complete.** Farmahem 100-4-К/26 + 100-4-ГС/26 (Ident C, assays, loss on drying 6.6) · IPH 229/0392/26 (microbiology) · IPH 1627/2026 (metals, pesticides, aflatoxins) |
| **BG1024** | CoQ-PP_26-003 | loss on drying | **exists** — 5.73, CNP ППК25050, 26.02.2025. The scan was not sent; the result is not missing |
| **P060352** | CoQ-PP_26-070 | microbiology | **exists** — IPH 366/0696/26, 01.06.2026 (TAMC 6.3 × 10⁴, TYMC 2.2 × 10⁴, GNB < 10) |
| **P060382** | CoQ-PP_26-074 | — | microbiology exists — IPH 364/0694/26, 01.06.2026 |

## 2 · What genuinely does not exist — no document is on file

| batch | certificate | absent |
| --- | --- | --- |
| **P060352** | CoQ-PP_26-070 | loss on drying, heavy metals, pesticides, mycotoxins, Ident C **and the assays** — she noticed two of six |
| **P060382** | CoQ-PP_26-074 | loss on drying, heavy metals, pesticides, mycotoxins, Ident C **and the assays** — her list is exactly right |
| **OPM1024** | CoQ-PP_26-006 | loss on drying, Ident C |
| **HPA1024** | CoQ-PP_26-005 | loss on drying, Ident C |

## 3 · The three findings that are not about a missing scan

### 3.1 · OPM1024 and HPA1024 — the whole panel is routed in house

She reports HPA1024 as missing microbiology, loss on drying, pesticides and heavy metals.
The register does hold figures for microbiology, metals, pesticides and mycotoxins on both
lots — but **attributed to our own internal certificate**, `iCoA-PP_26-005` and
`iCoA-PP_26-006`, not to an external laboratory. There is therefore no external scan to
send, which is why she cannot reconcile them.

External certificates **do exist on file for both lots** and are not cited:

| lot | on file, not on the certificate |
| --- | --- |
| HPA1024 | IPH 587/1066/25 (microbiology) · IPH 2995/2025 (metals, pesticides, mycotoxins) · CNP ППК25155 (loss on drying, Ident C, assays) |
| OPM1024 | IPH 2156/2025 (microbiology, metals, pesticides, mycotoxins) · CNP ППК25117 (loss on drying, Ident C, assays) |

Five of those are page-verified reads already held in `review/`. This is the same item the
attribution audit raised: microbiology, heavy metals and pesticides must be the Institute of
Public Health, and on these two lots they are not.

**OPM1024 additionally prints bile-tolerant gram-negative bacteria as `< 10² > 10³ CFU/g`** —
below a hundred and above a thousand at once. The other nineteen certificates carrying this
bracket read `< 10³ and > 10²`.

### 3.2 · P050212 — two versions of one certificate disagree

She reports different microbiological results in the signed and the unsigned certificate,
and says the scan matches the unsigned one.

The register holds **IPH 1032/1851/25, 17.10.2025 — TAMC 2.2 × 10⁴, TYMC 4.9 × 10⁴,
bile-tolerant GNB `< 10⁴ and > 10³`**. If the signed certificate carries anything else, the
signed document is wrong, not the scan.

Note also that **TYMC 4.9 × 10⁴ exceeds the ≤ 10⁴ criterion** the certificate prints. This
certificate (CoQ-PP_26-027) is already on the build gate's out-of-specification list.

### 3.3 · P050192 — documents from another producer

She states that everything except potency and mycotoxins arrived as **NJU GARDEN FARMA**
documents. The register cites no New Garden Farma document anywhere on this lot:

| determination | what the register cites |
| --- | --- |
| microbiology | IPH 1157/2058/25, 24.11.2025 |
| heavy metals | IPH 5661/2025, 01.12.2025 |
| **pesticides** | **State Phytosanitary Laboratory 10802_2845/2, 17.11.2025** |
| mycotoxins | Farmahem 276-31-М/25, 04.12.2025 |
| loss on drying, assays | in house, iCoA-PP_26-025 |
| Ident C | **absent** |

The pesticide line is the only one in the whole fleet that is not the Institute of Public
Health, and the attribution audit flagged it this morning on its own. Whatever she received
is not what the register says — the physical documents have to be pulled.

### 3.4 · P050042 — the sample number is another batch's

She is right. The certificate is CoQ-PP_26-010, cultivation batch **OMP1024_01**, and the
supporting documents carry **OPM1024_1** — while **OPM1024** is a separate series with its
own certificate, CoQ-PP_26-006. Worse: **IPH 2156/2025 is cited on both lots** — on P050042
for metals and pesticides, and on OPM1024 for the whole external panel. One document number
against two batches.

## 4 · The cannabinoid divergence between the two laboratories

She is right, and it is not a few lots. **55 lots were measured for total Δ⁹-THC by the
Center for Natural Products at release and by Farmahem at retest.** Holding the two side by
side:

| | |
| --- | --- |
| median difference | **+1.83 percentage points** (Farmahem higher) |
| mean | +1.60 |
| widest | **+7.89** (P050102, 20.79 → 28.68) and **−6.11** (P060412, 20.54 → 14.43) |
| lots differing by more than 2 points | **30 of 55** |

The bias is one-directional — Farmahem reads higher on most lots — which points at method or
reference standard rather than at sampling. Worth putting to both laboratories.

| lot | CNP | Farmahem | difference |
| --- | ---: | ---: | ---: |
| P050102 | 20.79 | 28.68 | +7.89 |
| P050172 | 14.93 | 21.30 | +6.37 |
| P060412 | 20.54 | 14.43 | −6.11 |
| P060052 | 16.93 | 22.97 | +6.04 |
| SCR022601 | 21.92 | 16.68 | −5.24 |
| P050292 | 21.36 | 26.54 | +5.18 |
| CJ1024 | 23.00 | 28.12 | +5.12 |
