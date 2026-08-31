# The IPH physico-chemical certificates, read off their own pages

**Scope:** the register's largest never-verified block — 44 IPH certificates carrying
lead, cadmium, arsenic, mercury, total aflatoxins and pesticides. **30 read so far,
14 remaining.** Every value taken from the rendered page, not from a text layer and
not from the RAG corpus: these are pure scans and `pdftotext` returns nothing.

## Result so far

| | |
|---|---|
| Certificates read | **30 of 44** |
| Register values compared | 178 |
| Agreement | **177 — 99.4%** |
| Substantive differences | **1** |

The register is accurate on this family to a degree the microbiology family was not.
That is worth stating plainly: the 93.2% agreement found in microbiology is not the
register's general standard, and the difference between the two families is itself
informative — microbiology results are superscripts and brackets, these are plain
decimals.

---

## A. The one difference · row 31, mercury

| | |
|---|---|
| Certificate | `2156/2025`, OPM1024_01, 07.05.2025 |
| Page | **`жива 0,001 mg/kg(l)`** |
| Register | `0.011` |

An inserted digit. Re-read at 2.2× magnification before being called, because a
single digit is exactly what a first read can invent. MaxDK on this certificate is
`0,1`, so both the old and the new value comply and the batch's disposition does not
change — but a release register that states a number the laboratory did not is wrong
whether or not the number matters.

Applied by `deliverables/qc_gap_analysis/apply_iph_corrections.py`.

### A note on a correction that was *not* made

An earlier draft of that script also stripped the annotation from a certificate code,
reading `2156/2025 (microbiology sub-report lab-ref not distinctly captured in OCR
text)` as a wrong description of the physico-chemical report. It is not. That
annotation sits on **row 32** — a separate microbiology row for the same batch — and
it is honest: it says the microbiology report's own laboratory reference could not be
read. Row 31 carries the clean code.

The script's refuse-on-mismatch guard is what surfaced this, by reporting the cell as
"already clean" instead of quietly editing it. That guard has now earned its keep
twice.

What row 32 *does* expose belongs to the microbiology work: it holds a complete set of
microbiological results — TAMC, TYMC, GNB, Salmonella, E. coli — whose source document
has never been identified. It was not among the 40 IJZ-MB certificates read on
31.08.2026, because it carries no IJZ-MB laboratory number.

---

## B. The heavy-metal limits are not constant, and the register records only one set

This is not a transcription error. It is a property of the corpus that any check
against a fixed column will get wrong.

| Printed MaxDK, Pb / Cd / As / Hg | Certificates | Period |
|---|---|---|
| `5 / 1 / 2 / 0,1` — the Ph. Eur. 2.4.27 figures | **23** | Feb – Oct 2025 |
| `0,5 / 0,3 / 0,2 / 0,1` | **6** | Dec 2025 onward |
| `0,5 / 0,3 / 0,2 / **0,01**` | 1 | `5697/2025`, 02.12.2025 |

The register's column headers say `≤ 0.5 / ≤ 0.3 / ≤ 0.2 / ≤ 0.1` — the **later** set.
So for 23 of the 30 certificates read, the register's stated limit is ten times
tighter than the limit the issuing laboratory actually applied and declared conformity
against.

Nothing in this set is close to either limit, so no disposition is affected. But the
direction matters: here the register is *stricter* than the paper, so a column-based
check produces false alarms rather than missed failures. The microbiology family had
the same structural gap pointing the other way, where the register's 10⁴ column hid a
result over its own printed 10². **A validator that compares against the column is not
comparing against the certificate, in either direction.**

`5697/2025`'s mercury limit of `0,01` is an order tighter than every neighbouring
certificate's `0,1`. Its result, `0,002`, complies either way. Whether the limit is
real or a typing slip on the certificate is a question for the laboratory.

## C. Two more per-certificate variations

**The conformity reference changes.** Most certificates declare metals against
`Ph. Eur. 2.4.27` and mycotoxins against `Ph. Eur. 2.8.18`. `1767/2025` (GP0824_01)
declares both against the national `Правилник ... (Сл. весник на РСМ бр. 143/2024,
183/2024)`, parts 3 and 1. Same laboratory, same month, different regulatory basis.

**The analytical method changes.** `2472/2025`, `3176/2025`, `3177/2025` and
`3178/2025` use `EN 14084 / EN 13806 / EN 14627`; the rest use `МКС EN 17851:2023`.
The four EN-method certificates are also the ones reporting most metals as `н.д.`,
which is consistent with a different limit of detection rather than a cleaner crop.

## D. One pesticide result in 30 is not "not detected"

`2994/2025` (OPM1024_02) reports **`delta HCH < 0,01 mg/kg(l)`** against MaxDK `0,3`.
Every other pesticide row across all 30 certificates — a fixed 25-row panel plus, from
`4762/2025` onward, a `Пестициди вкупно` summary row — reads `н.д.`.

The register records `N.D.` for this batch. `< 0,01` is at the limit of quantification
and the register's own specification row says `≤ LOQ 0.01 mg/kg`, so the cell is not
wrong in substance. It is worth knowing that the single non-`н.д.` pesticide result in
the corpus is flattened to `N.D.` by the register's one-cell-per-batch design, and
that it was found on page 2 — the page a shortcut method would have skipped.

## E. Three spellings of the same result

Across the metals and pesticide columns the register writes not-detected as `N.D.`,
`Н.д. (not detected)` and `н.д.` — Latin, Cyrillic-with-gloss and Cyrillic. All three
mean the same thing and all three are faithful to some certificate. It is cosmetic,
but it defeats exact-match tooling and is worth normalising in one pass rather than
discovering repeatedly.

## F. A prose sentence sitting in a numeric column

Row 218, `1625/2026`, aflatoxins Σ:

```
COMPLIES (numeric value not present in captured source excerpt for report
1625/2026 — see Bundle cross-reference)
```

A 118-character sentence where the column expects a number in µg/kg. Found from the
register alone, without opening any document. `1625/2026` is among the 14 certificates
not yet read, so the correct value is not supplied here — replacing prose with a guess
would be worse than leaving it visible.

---

## Method

Per certificate: fetch from Drive (the result lands on disk and never enters context),
render every page at 200 DPI with `pdftoppm`, crop to `0.098–0.94` of page height so
the `Број: NNNN/YYYY` line survives — a crop that cannot name its own certificate
cannot be checked against the document it came from — then trim to the left 88% to drop
the `Ед. мерка`, `U`, `MinDK` and `Метода` columns, which are identical on every
certificate and carry nothing being verified. That trim roughly halves the cost of
reading each page.

Both scripts are committed: `render_iph_certificates.py` and the comparison harness
against `iph_physchem_page_reads_2026-08-31.json`, which holds every raw reading.

Classical OCR is not used and is forbidden by `scripts/policy_check.py` rule 1.

## Still to read — 14 certificates

`5888/2025` · `5889/2025` · `80/2026` · `81/2026` · `82/2026` · `83/2026` · `84/2026` ·
`85/2026` · `86/2026` · `87/2026` · `88/2026` · `1625/2026` · `1627/2026` · `1628/2026`

All are downloaded and rendered; continuing costs only the reads.

## Verification coverage of the register, restated

| | |
|---|---|
| Populated result values in the register | ~1 295 |
| Verified against a document before this week | ~30 (~2%) |
| After the microbiology pass (40 certificates) | 146 |
| After this pass so far (30 certificates) | **324 (~25%)** |

Still never checked against any document: every one of the 266 dates of issue, the
CNP potency and loss-on-drying values beyond the two read on 30.08, and the whole
Farmahem family.
