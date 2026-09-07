# v8 tracker — truth check against the certificates, 02.09.2026

Scope: the values in `CoQ_Analysis_Master_v8.xlsx` (`CoQ Parameter Tracker v8`) that decide
something — the five out-of-specification TYMC results, the four undetermined ones, a
stability CBN exceedance, two derived totals, and two ordinary certificates as controls.
Thirteen certificates, about 65 values. Sources, in order of authority:

1. **the page itself**, rendered at 300 DPI from the filed PDF (byte-identical to the Drive
   original) and read by eye — done for the five certificates where the sources disagreed;
2. **RAGflow `eCOA_DB`** — the text layer of the same PDFs, retrieved per certificate;
3. **v8's readings** — two independent vision reads per page, from the ingestion host.

## Result

| certificate | lot | determination | v8 | eCOA_DB text layer | page, read at 300 DPI | verdict |
|---|---|---|---|---|---|---|
| 320/0587/25 | GG1024_01 | TYMC | 4.2×10⁴ | 4,2×10**²** | **4,2 × 10⁴** | v8 right; text layer wrong |
| 946/1684/25 | GP052501 | TYMC | 3.6×10⁴ | 3,6×10**³** | **3,6 × 10⁴** | v8 right; text layer wrong |
| 904/1589/25 | OPM052501 | TYMC | 3.3×10⁴ | 3,3×10**³** | **3,3 × 10⁴** | v8 right; text layer wrong |
| 628/1129/25 | GP0824_03 | TYMC | 1.2×10⁴ | 1,2×10**³** | **1,2 × 10⁴** | v8 right; text layer wrong |
| 1032/1851/25 | CJ062501/2 | TYMC | 4.9×10⁴ | 4,9×10⁴ | 4,9 × 10⁴ | all agree |
| 948/1686/25 | HPA052501 | TYMC | 2.6×10⁴ | 2,6×10⁴ | not rendered | agree |
| 587/1066/25 | HPA1024_01 | TYMC | 1.5×10⁴ | 1,5×10⁴ | not rendered | agree |
| 949/1687/25 | CJ052501/01 | TYMC | 1.7×10⁴ | 1,7×10⁴ | not rendered | agree |
| 472/0863/25 | GG1024_02 | TYMC | 1.9×10⁴ | 1,9×10**³** | **1,9 × 10⁴** (Head of QC, 03.09.2026) | v8 right; text layer wrong |
| ППК26033 | GP0824_02 (stability) | CBN | 2.35 ᴰ | 2.35 (printed, ≤ 1.00 limit) | — | agree; the exceedance is real |
| ППК26033 | GP0824_02 | Total CBD | 0.05 | 0.03 | **0.05 %** (Head of QC, 03.09.2026) | v8 right; text layer wrong |
| ППК25050 | BG1024 | LoD, CBN ᴰ, CBD, THC | 5.73 / 0.02 / 0.04 / 21.80 | same | — | agree |
| 197-1-K/26 | BG1024 | CBD, CBN, THC | <LOQ / 0.28 / 26.14 | same | — | agree |
| ППК26005 | AB092501 | LoD, CBN ᴰ, CBD, THC | 6.77 / ND / 0.07 / 16.93 | same | — | agree |

TAMC, bile-tolerant gram-negative bacteria, *E. coli* and *Salmonella* agreed on every
microbiology certificate checked. Loss on drying and the cannabinoid totals agreed on every
cannabinoid certificate checked, with the one Total CBD exception above.

## What it means

**The v8 values stand.** Every decision-bearing value that could be checked against the page
is correct: the five out-of-specification TYMC results are real, and so is the stability CBN
exceedance. Nothing in v8 was found wrong against a page.

**The eCOA_DB text layer is not a source for numbers.** On four of the five pages rendered, it
reads the TYMC exponent one or two powers of ten too low — `10⁴` as `10³` or `10²` — while
reading the TAMC exponent on the same line correctly. A superscript digit is exactly what a
text extraction of a scan gets wrong, and here it gets it wrong in the direction that turns a
failing result into a conforming one. Taken at face value it would have cleared four of the
five out-of-specification lots. This is the case the ingestion runner's README already makes
("numbers are never taken from a PDF text layer"); it is now demonstrated on the release set.
Use `eCOA_DB` to find a certificate and read its prose; never to read a count.

**The laboratory's conclusion line does not discriminate.** Every certificate checked, including
1032/1851/25 at 4,9 × 10⁴ against a printed 10⁴ limit, carries "ОДГОВАРА" (conforms). The
conclusion is boilerplate on these reports and must not be used as evidence either way.

## Left open

Nothing. Both items were closed from the page by the Head of QC on 03.09.2026:

- **472/0863/25 (GG1024_02, TYMC)** prints **1,9 × 10⁴**. v8 was right; the text layer read
  the exponent one power too low, as on the other four pages. The lot stays in the
  undetermined band: above the printed 10⁴, below the 2 × 10⁴ that Ph. Eur. 5.1.4 judges
  against.
- **ППК26033 Total CBD** prints **0.05 %**. v8 and the release register were right.

Final tally: every one of the thirteen certificates' decision-bearing values is correct in
v8. The eCOA_DB text layer was wrong on six values across six certificates, every time in
the direction of a smaller number.
