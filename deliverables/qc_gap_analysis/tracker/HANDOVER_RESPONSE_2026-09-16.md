# Answer to `HANDOVER_to_ClaudeCode.md` — the CoQ set audit of 16.09.2026

The handover asks two things: **(A)** re-derive the data layer from the current master, and
**(B)** confirm or refute seven findings. This answers (B) finding by finding against the
current build, and says what (A) should be taken from.

Nothing here is a reading of the rendered documents in `Final_Docs/xCOAs/CoX_DES/`. It is a
reading of the data those documents should have been built from, which is the only thing
this desk can speak to. Where a finding is refuted, the refutation is that **the value in
the current master is not the value the finding reports** — the documents were built from
v27/v29 and the master is now v35.

---

## (A) What to re-derive from

Use **v35**, not v33. v34 and v35 both moved the data layer:

* **v34** wrote the IJZ-MB campaign microbiology of 25/26.08.2026 into the release
  register — 29 certificates that had been testing instances only. Before that, 24
  certificates of quality printed microbiology a newer certificate for the same lot
  contradicted.
* **v35** canonicalises the document codes (below, §2.2) and adds the **Result
  Supersession** tab.

The field-to-source mapping in the handover is right, with one addition: the **CoQ
Compilation** tab (added in v33) already holds exactly what §1 asks a builder to assemble —
one row per certificate of quality, and per determination #1…#12 the result, the document,
its date of issue and its laboratory. `CoQ Compilation (long)` is the same one row per
certificate *and* determination, with the method, the acceptance criterion, the sample
receipt date, the status and the route. Reading those two tabs is the whole of §1 and none
of the extraction traps apply to them.

The traps §1 lists are real and this desk has hit four of them. Two more worth adding:

* **A stability certificate is not a release result.** The register marks them. Counting
  them as testing raises 30 findings on the two Grape Pie lots alone that are not findings
  — CBN rising 0.02 % → 2.35 % is a 40 °C/75 % RH study reporting what it exists to report.
* **A register block can hold two sublots.** `J31122501` and `JD112501` each carry two
  parallel certificates per testing, with different results (OI-39, §2.8 below).

---

## (B) The seven findings

### 2.1 — "41 documents have no in-house QC row" · **confirmed, and it is 82, and the cause is different**

Determinations #1, #2 and #7 print nothing on **82 of the 172 certificates, over 44 lots**.
The handover counted 41 and diagnosed a builder that could not find an iCoA row in v29.

That diagnosis does not hold in v35: **every one of the 172 certificates cites an internal
certificate for all three determinations.** `CoQ-PP_26-048` (P060122) cites
`iCoA-PP_26-046`; the row is present, the laboratory is named, and the result is blank with
the status *to be performed — see route*. The desk is not missing the iCoA. It has **no
record of the result** for those 44 lots, and the standing rule — never print a result that
has not been certified — makes a blank the only honest cell.

So the finding is confirmed as a defect in the *documents* and refuted as a defect in the
*builder*. It is now **OI-41**, and the question it puts to the Head of QC is whether the
in-house results exist somewhere this desk has not been given, or whether a certificate of
quality may print Conforms on the strength of the internal certificate alone.

The handover's rule 4 — "params 1, 2, 7 are performed in-house on every batch" — is not in
dispute. Performing a test and holding a written result are different facts.

### 2.2 — "certificate codes carrying analysis tags" · **confirmed; the correct spelling is now established from the pages**

The tag is part of the code, and it is Macedonian. Farmahem numbers a report
`<campaign>-<item>-<analysis>/<year>`, where the analysis letter is `К` for канабиноиди,
`М` for микотоксини and **`ГС` for губитоци при сушење** — loss on drying. Two pages were
read on 16.09.2026 to settle it:

| scan | the page prints |
|---|---|
| `020326_051-1-LoD-26_FHM_J31102501-P060152.pdf` | `Извештај број: 051-1-ГС/26` |
| `110226_031-2-LoD-26_FHM_PUM102501-P060112.pdf` | `Извештај број: 031-2-ГС/26` |

Both are titled «Извештај од анализа на **губитоци при сушење** во цвет од канабис».

So `GS` is a Latin transliteration and `LoD` an English abbreviation — neither is what the
laboratory printed, and the owner's standing rule that Cyrillic `К`/`М` in laboratory codes
are genuine and must not be transliterated applies to `ГС` in exactly the same way. Both
spellings reached this desk honestly: the scans' own file names carry `LoD`, and an earlier
Farmahem extraction carries `GS`. The page outranks both.

**Fixed at source.** `document_codes.py` is the codes' equivalent of `result_vocabulary.py`
— one spelling per document — and the exporter applies it. Nine codes change:
`031-2/4/5-ГС/26` and `051-1…6-ГС/26`. Note that the register already spelled
`100-2-ГС/26` and `100-3-ГС/26` correctly, which is what made the inconsistency visible.

**The reader's note is also out of the code field.** The register's row 32 held
`2156/2025 (microbiology sub-report lab-ref not distinctly captured in OCR text)` as a
document code, so ten certificate rows would have printed a seventy-character note where
the code belongs. The report number is `2156/2025` — row 31 of the same block carries it
bare for the mycotoxins-and-metals half of the same report. The note is a note.

**The `PP CoA #nnn / ППКnnnnn` composites are NOT fixed, and the reason matters.** Reading
the register turns this from a spelling question into a records question: every one of the
six also exists as a bare `ППК` row on the same lot, with an **earlier date and no
results**.

| lot | composite row (carries the results) | bare row (empty) |
|---|---|---|
| P050282 | row 123 `PP CoA #027 / ППК25370` · 21.01.2026 · THC 8.02 | row 124 `ППК25370` · 28.11.2025 |
| P050292 | row 127 `PP CoA #018 / ППК25378` · 21.01.2026 · THC 21.36 | row 128 `ППК25378` · 12.12.2025 |
| P050302 | row 131 `PP CoA #019 / ППК25379` · 21.01.2026 · THC 19.81 | row 132 `ППК25379` · 12.12.2025 |
| P050312 | row 135 `PP CoA #020 / ППК25380` · 21.01.2026 · THC 21.29 | row 136 `ППК25380` · 12.12.2025 |
| P050322 | row 139 `PP CoA #021 / ППК25381` · 21.01.2026 · THC 14.83 | row 140 `ППК25381` · 12.12.2025 |
| P060052 | row 163 `PP CoA #037 / ППК26005` · 21.01.2026 · THC 16.93 | row 165 `ППК26005` · 21.01.2026 |

Which of the two rows is the certificate — and therefore which date the certificate of
quality cites — is the Head of QC's to rule, not a spelling this desk may normalise. It is
**OI-40**.

### 2.3 — "two attribution mismatches" · **refuted for external laboratories; it is 2.1 in another form**

Over all 172 certificates and every determination: **zero** rows credit an external
laboratory for a determination with no result. `CoQ-UNASSIGNED_P060222` #6 and
`CoQ-PP_26-085_P060332` #8/#9/#11/#12 do not reproduce.

There *are* 246 rows that name a laboratory and a document and print no result — and every
single one is #1, #2 or #7 with Purely Plant GmbH (in-house) named and the lot's internal
certificate cited. That is 2.1, counted a different way, and it is OI-41. If the finding
means those rows, it is confirmed; if it means an external laboratory being credited for
nothing, it is refuted.

### 2.4 — "one grade-token mismatch" · **refuted**

Every certificate's grade was compared with the grade in its own specification code, over
all 172: **zero mismatches**. `CoQ-PP_26-097` is v35's Tranche 1 reissue of P060152, grade
**III**, specification `QCSP_001_J31-III_v.01`, Total THC 17.32 % from `197-16-К/26` — the
filename token and the specification code agree. The document numbered `26-097` in the
audited set is not the document numbered `CoQ-PP_26-097` in v35; the register was renumbered
as the intakes landed, which is why the codes do not line up.

### 2.5 — "four banner potencies outside their own window" · **refuted, and the cause is visible**

Every certificate's printed Total THC was compared with its own strain-and-grade window
from the Potency Grades ladder: **120 compared, 0 outside**. (35 more have no strain/grade
pair on the ladder — that is OI-01, a missing specification, not a value out of window.)

The four flagged read, in v35:

| the audit's row | v35 lot | v35 Total THC | v35 window | in window |
|---|---|---|---|---|
| `26-051` P060182 GRC, banner 19.14 % | P060182 Grapes and Cream | **11.53 %** | 11.00 – 12.99 | yes |
| `26-054` P060212 JD, banner 11.53 % | P060212 Jelly Donutz | **19.64 %** | 16.20 – 19.79 | yes |
| `26-056` P060232 PM, banner 25.27 % | P060232 Permanent Marker | **13.33 %** | 13.00 – 14.99 | yes |
| `26-057` P060242 OPM, banner 19.64 % | P060242 Orange Punch Mimosa | **8.09 %** | 7.20 – 8.79 | yes |

The windows in the audit are v35's windows, exactly. The banners are not. And the banner
values are not random: **19.14 % is P060152's result, 11.53 % is P060182's, 19.64 % is
P060212's** — each document carries the *previous* lot's assay. 25.27 % is J31112501's, the
lot whose register block carries no P number and which therefore sorts differently. That is
a row-alignment slip in the extraction, of exactly the class §1 of the handover warns
about, and it is on the document side. The grades are right; the assay values are one lot
out.

### 2.6 — "one genuine out-of-specification result" · **confirmed**

`GG1024` prints loss on drying **76.07 %** against ≤ 12.0 %, from `ППК25008`. The desk
already marks it: `CoQ-PP_26-004` (the release certificate) carries the status **OUT OF
SPECIFICATION**, and `CoQ-PP_26-113` (the 12-month reissue) carries it forward with the
same status. Neither can issue with that on it.

It is not plausible for dry flower and this desk agrees it is almost certainly a unit or
transcription fault. Two open items already hold it: **OI-06** (it is one of the 46
disagreements between this desk and the owner's pass of 09.09.2026) and **OI-35**
(`ППК25008` is one of 17 documents that rest on a single page read and were never put
through the two-read gate). The instruction *do not issue either until resolved* is
correct and is now recorded here.

### 2.7 — "three document-code conflicts" · **refuted**

No register code sits on two lots in v35. Every one of the 161 numbered certificates has a
distinct code, and the numbering is contiguous. The only repeated string in the code column
is the placeholder `— at issue —`, carried by the seven certificates whose lot has no
number yet — which is the handover's own rule 1 working as intended, not a conflict.

`26-048`, `26-050` and `26-071` in the audited set map to `CoQ-PP_26-048` (P060122),
`CoQ-PP_26-050` (P060142) and `CoQ-PP_26-071` (P060382) in v35, each on one lot.

### 2.8 — not in the handover, found by the same sweep · **two register blocks carry two sublots**

Worth adding to the audit's list because it will look like a defect on the documents.
`J31122501` (Jokerz 31, P060262) holds three pairs of certificates issued on the same day
by the same laboratory with different results: the microbiology of 07.04.2026, where
`231/0394/26` names its sample *Рачно тримиран цвет* (hand-trimmed) and reads TAMC 850
while `230/0393/26` names *Тримиран цвет* and reads 1900; the Farmahem cannabinoids of
09.04.2026, `100-2-К/26` at 19.84 % against `100-3-К/26` at 21.84 %; and the IJZ mycotoxins
and metals of 23.04.2026, `1628/2026` against `1625/2026`. `JD112501` (Jelly Donutz,
P060212) holds `ППК26063` at 19.64 % against `ППК26065` at 13.93 %.

The certificate of quality prints one of each pair and does not say which sublot it
certifies. The owner's batch list gives each cultivation batch exactly one P lot, so there
is no second number to file the second sublot under. That is **OI-39**.

---

## Summary

| finding | verdict |
|---|---|
| 2.1 · no in-house QC row | **confirmed** as a document defect, **refuted** as a builder defect; 82 certificates over 44 lots, not 41 — OI-41 |
| 2.2 · analysis tags in codes | **confirmed**; the tag is genuine and Cyrillic (`ГС`), fixed at source in `document_codes.py`; the `PP CoA` composites are OI-40 |
| 2.3 · attribution mismatches | **refuted** for external laboratories (0 of 172); the 246 in-house rows are 2.1 |
| 2.4 · grade-token mismatch | **refuted**; 0 of 172 |
| 2.5 · banner potencies out of window | **refuted**; 120 compared, 0 outside — the four banners carry the previous lot's assay |
| 2.6 · loss on drying 76.07 % | **confirmed**; already OUT OF SPECIFICATION on both certificates; OI-06 and OI-35 |
| 2.7 · document-code conflicts | **refuted**; no code on two lots |
| 2.8 · two sublots in one block | **new**; OI-39 |

## Reproducing

    python3 deliverables/qc_gap_analysis/document_codes.py
    python3 deliverables/qc_gap_analysis/result_supersession.py
    python3 deliverables/qc_gap_analysis/open_items.py
