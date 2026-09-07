# The IPH physico-chemical certificates, read off their own pages

**Scope:** the register's largest never-verified block — **all 44** IPH certificates carrying
lead, cadmium, arsenic, mercury, total aflatoxins and pesticides. Every value taken from the
rendered page, not from a text layer and not from the RAG corpus: these are pure scans and
`pdftotext` returns nothing at all.

## Result

| | |
|---|---|
| Certificates read | **44 of 44** |
| Register values compared | 257 |
| Agreement | **256 — 99.6%** |
| Substantive differences | **1** |
| Register values with no source on the certificate | **1** |

The register is accurate on this family to a degree the microbiology family was not, and the
contrast is informative rather than flattering: microbiology results are superscripts and
brackets, these are plain decimals. **93.2% against 99.6% is a measure of the notation, not of
the care taken.** Wherever a value carries an exponent, expect the register to be wrong about
one in fifteen of them.

---

## A. The one difference · row 31, mercury

| | |
|---|---|
| Certificate | `2156/2025`, OPM1024_01, 07.05.2025 |
| Page | **`жива 0,001 mg/kg(l)`** |
| Register | `0.011` |

An inserted digit. Re-read at 2.2× magnification before being called, because a single digit is
exactly what a first read can invent. MaxDK on this certificate is `0,1`, so both values comply
and the batch's disposition does not change — but a release register that states a number the
laboratory did not is wrong whether or not the number matters.

Applied by `deliverables/qc_gap_analysis/apply_iph_corrections.py`.

### A correction that was *not* made

An earlier draft of that script also stripped an annotation from a certificate code, reading
`2156/2025 (microbiology sub-report lab-ref not distinctly captured in OCR text)` as a wrong
description of the physico-chemical report. It is not. That annotation sits on **row 32** — a
separate microbiology row for the same batch — and it is honest: it says that report's own
laboratory reference could not be read. Row 31 carries the clean code.

The script's refuse-on-mismatch guard is what surfaced this, by reporting the cell as "already
clean" instead of quietly editing it.

Row 32 does expose something, and it belongs to the microbiology work: it holds a complete set
of microbiological results — TAMC, TYMC, GNB, Salmonella, E. coli — whose **source document has
never been identified**. It was not among the 40 IJZ-MB certificates read on 31.08.2026, because
it carries no IJZ-MB laboratory number.

---

## B. A certificate that declares conformity without printing the result · `1625/2026`, row 218

The register holds, in a column that expects a number in µg/kg:

```
COMPLIES (numeric value not present in captured source excerpt for report
1625/2026 — see Bundle cross-reference)
```

Whoever wrote that was right that the number is missing and wrong about why. **It is missing
from the certificate.**

`1625/2026` is three pages. Page 2 ends with the last pesticide row, `cis-Chlordane`. Page 3
opens with a table row whose Резултат, Ед. мерка and MaxDK cells are **empty**, followed by:

```
Изјава за сообразност :
Резултатите од испитуваните параметри СЕ ВО СОГЛАСНОСТ со барањата на:
Ph. Eur. 2.8.18
```

Both page boundaries were re-rendered uncropped to be sure the value had not been lost to the
crop. It has not. The laboratory declared conformity to the aflatoxin monograph for a result it
did not report. The certificate also carries **no МЕТАЛИ section at all**, while its sibling
`1628/2026` does.

This is a question for IJZ, not a transcription fix. The prose cell is left in place: replacing
it with a guess would be worse than leaving the gap visible, and the wording should be corrected
to say the certificate omits the value rather than blaming the capture.

## C. Two certificates for one batch that disagree on the batch

`1625/2026` and `1628/2026` are both Jokerz 31, both sampled 27.03.2026, both issued 23.04.2026
— one the trimmed flower, one the hand-trimmed.

| Certificate | Sample | Serial printed |
|---|---|---|
| `1625/2026` | `тримиран цвет` | `J31122501` |
| `1628/2026` | `рачно тримиран цвет` | **`J311122501`** |

Confirmed at 3× magnification. The register writes `J31122501` and agrees with `1625`. `1628`
carries an extra digit — a typo on the certificate, and the kind that turns one batch into two
in any pipeline that keys on the string, which is exactly what `ingestion/common/batch_id.py`
exists to prevent.

---

## D. The heavy-metal limits are not constant, and the register records only one set

Not a transcription error. A property of the corpus that any check against a fixed column will
get wrong.

| Printed MaxDK, Pb / Cd / As / Hg | Certificates | Period |
|---|---|---|
| `5 / 1 / 2 / 0,1` — the Ph. Eur. 2.4.27 figures | **23** | Feb – Oct 2025 |
| `0,5 / 0,3 / 0,2 / 0,1` | **19** | Dec 2025 onward |
| `0,5 / 0,3 / 0,2 / **0,01**` | 1 | `5697/2025`, 02.12.2025 |
| no metals section | 1 | `1625/2026` |

The register's column headers say `≤ 0.5 / ≤ 0.3 / ≤ 0.2 / ≤ 0.1` — the **later** set. So for 23
of the 44, the register's stated limit is ten times tighter than the limit the issuing laboratory
applied and declared conformity against.

Nothing in the set is close to either limit — the highest cadmium found is `0,165` on
`1627/2026` against MaxDK `0,3` — so no disposition is affected. But the direction matters: here
the register is *stricter* than the paper, so a column-based check produces false alarms rather
than missed failures. The microbiology family had the same structural gap pointing the other
way, where the register's 10⁴ column hid a result over its own printed 10². **A validator that
compares against the column is not comparing against the certificate, in either direction.**

`5697/2025`'s mercury limit of `0,01` is an order tighter than every neighbouring certificate's
`0,1`. Its result, `0,002`, complies either way. Whether the limit is real or a typing slip is a
question for the laboratory.

## E. Copper is tested on nine certificates and recorded nowhere

From `80/2026` onward the metals table adds a **бакар** row: 1,859 to 3,661 mg/kg(l) across nine
certificates, with **no MaxDK printed** — a measured value against no limit. The register has no
copper column, so nine real results are not recorded anywhere.

On `87/2026` copper sits under its own **МИНЕРАЛИ** heading and its unit is printed
**`mg/tableta`** — per tablet, on a dried-flower sample. A unit slip on the certificate.

This is the third instance of the same shape: a tested parameter with nowhere to go. The
microbiology pass found *S. aureus* and *P. aeruginosa* in the same position.

## F. Two more per-certificate variations

**The conformity reference changes.** Most certificates declare metals against `Ph. Eur. 2.4.27`
and mycotoxins against `Ph. Eur. 2.8.18`. `1767/2025` (GP0824_01) declares both against the
national `Правилник ... (Сл. весник на РСМ бр. 143/2024, 183/2024)`, parts 3 and 1. Same
laboratory, same month, different regulatory basis.

**The conformity wording changes.** The 2026 certificates say `Резултатите ... СЕ ВО СОГЛАСНОСТ`
where earlier ones say `примерокот ОДГОВАРА НА`. Any parser keyed on the old wording will read
the newer certificates as having no verdict — the same trap the microbiology pass found on
`305/0549/26`.

**The analytical method changes.** `2472/2025`, `3176/2025`, `3177/2025`, `3178/2025` and the
2026 series use `EN 14084 / EN 13806 / EN 14627`; the rest use `МКС EN 17851:2023`. The
EN-method certificates are also the ones reporting most metals as `н.д.`, consistent with a
different limit of detection rather than a cleaner crop.

## G. One pesticide result in 44 is not "not detected"

`2994/2025` (OPM1024_02) reports **`delta HCH < 0,01 mg/kg(l)`** against MaxDK `0,3`. Every other
pesticide row across all 44 certificates — a fixed 25-row panel, plus a `Пестициди вкупно`
summary row from `4762/2025` onward — reads `н.д.`.

The register records `N.D.` for that batch. `< 0,01` is at the limit of quantification and the
register's specification row says `≤ LOQ 0.01 mg/kg`, so the cell is not wrong in substance. It
is worth knowing that the single non-`н.д.` pesticide result in the corpus is flattened to `N.D.`
by the register's one-cell-per-batch design, and that it was found on **page 2** — the page a
shortcut method would have skipped.

## H. Three spellings of the same result

Across the metals and pesticide columns the register writes not-detected as `N.D.`,
`Н.д. (not detected)` and `н.д.` — Latin, Cyrillic-with-gloss and Cyrillic. All three mean the
same thing and all three are faithful to some certificate. Cosmetic, but it defeats exact-match
tooling and is worth normalising in one pass rather than rediscovering.

---

## Method

Per certificate: fetch from Drive — the result lands on disk and never enters context, which is
what makes 44 documents and 173 pages affordable — render every page at 200 DPI with
`pdftoppm`, crop to `0.098–0.94` of page height so the `Број: NNNN/YYYY` line survives (a crop
that cannot name its own certificate cannot be checked against the document it came from), then
trim to the left 88% to drop the `Ед. мерка`, `U`, `MinDK` and `Метода` columns, which are
identical on every certificate and carry nothing being verified. That trim roughly halves the
cost of each page.

Where a value mattered and a single character decided it — the mercury digit, the two batch
serials — the region was re-rendered and magnified 2.2–3× before the reading was called.

Committed: `render_iph_certificates.py`, and `iph_physchem_page_reads_2026-08-31.json` with
every raw reading.

Classical OCR is not used and is forbidden by `scripts/policy_check.py` rule 1.

## Verification coverage of the register

| | |
|---|---|
| Populated result values in the register | ~1 295 |
| Verified against a document before this week | ~30 (~2%) |
| After the microbiology pass (40 certificates) | 146 |
| After this pass (44 certificates) | **403 (~31%)** |

Still never checked against any document: every one of the 266 dates of issue; the CNP potency
and loss-on-drying values beyond the two read on 30.08; and the entire Farmahem family.
