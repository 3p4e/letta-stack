# Every CoQ filled in: 61 certificates, 23 determinations each, and the document behind every value

31.08.2026 · the CoQ issuance schedule, rebuilt on the owner's own issue plan and filled
from the release register.

---

## The CoQ universe is the owner's, and it is 61, not 102

The `ISSUE_COQ` folder in Drive (`Final_Docs/xCOAs/CoX_DES/ISSUE_COQ`) holds the approved
CoQ master template, **48 rendered initial-release CoQs** and an issue plan generated from
`PP_Potency_MASTER_Spec.xlsx`. Its conventions — now committed as
`deliverables/qc_gap_analysis/ISSUE_COQ_CONVENTIONS.md`, with the plan verbatim as
`coq_issue_plan.json`:

* **One CoQ per packaged lot**, numbered `CoQ-PP-{year}-{NNNN}` sequentially by packaging
  date — `CoQ-PP-2025-0001…0022`, `CoQ-PP-2026-0001…0026`.
* **13 additional-testing CoQs**, `CoQ-PP-2026-0027…0039`, for the lots whose 12-month
  retest fell due. Ordinary sequential numbers; *a CoQ is never labelled "retest"*.
* Every CoQ prints an **`iCoA-PP-{year}-{NNNN}`** reference and the lot's grade acceptance
  range; the banner potency is the actual assay, not the nominal.
* Results the master spec does not hold are **controlled blanks**: *a CoQ must never carry
  a result or a conformity assertion that has not been certified.*

This closes the packaged-lot question three registers carried as open: register batches
with no packaged lot get **no CoQ** — there are 41 of them, and among them sit
**OPM052501 and CJ062501-2, both carrying a TYMC over its acceptance criterion** with no
CoQ to hold the finding.

## What was built

**`PP_CoQ_Parameter_Schedule_2026-08-31.xlsx`** (`build_coq_schedule.py`) — five sheets:

1. **CoQ Parameter Schedule** — 61 × 23 = 1 403 rows: parameter, method and acceptance
   criterion verbatim from QCSP 001 v.03, result, source document code, date, institution,
   status, and the routing for what remains. This is the transcription source for the
   controlled blanks on every CoQ.
2. **CoQ Coverage** — one row per CoQ: number, iCoA reference, banner THC, acceptance
   range, coverage counts, every document the certificate must cite.
3. **iCoA Plan** — the 103 in-house certificates the routing requires.
4. **Sourcing routes** — who *can* perform identity and foreign matter, and who *will*.
5. **QCSP 001 v.03** — the 23 determinations, verbatim.

The registers workbook's **CoQ Issuance** sheet now carries the same 61, from the same
computation, so the two cannot drift.

## The routing (owner's decision, 31.08.2026)

| Determination | At initial release, where no outsourced lab covered it | At retest |
|---|---|---|
| Ident A + B | **Purely Plant laboratory — one iCoA** | Farmahem, with the assay |
| Ident C | outside laboratory (CNP Ident C only, or Farmahem) | Farmahem, with the assay |
| Foreign matter | **Purely Plant laboratory — a second, separate iCoA** | Purely Plant laboratory — one iCoA |

Constraints that shape it: CNP does not sell foreign matter separately — it comes only
inside the full identity-plus-assay package — and the in-house laboratory cannot perform
Ident C. Twelve batches already have Ident A, B and foreign matter **covered by their CNP
Ph. Eur. 11.5 certificate** (the iCoA register's own `covered by CNP` fields, which an
earlier draft of the builder ignored); only Ident C is outstanding there.

Under the routing: **69 × {Ident A+B} + 90 × {foreign matter} in-house certificates over
the old 102-CoQ basis; 45 + 58 = 103 over the plan's 61 CoQs.**

## The counts, over the 61 CoQs of the plan

| | rows |
|---|---|
| covered by a certificate on file | 500 |
| still to be performed — routed | 232 |
| not tested by anyone | 347 |
| additional testing owed — no post-release certificate yet | 173 |
| upon request (P. aeruginosa, S. aureus) | 122 |
| **in-house CoA only — underlying eCoA NOT on file** | **18** |
| laboratory finding recorded, conforming | 5 |
| OUT OF SPECIFICATION | 3 |
| UNDETERMINED — pending the QCSP 001 reading | 3 |
| BLOCKED — declared out of specification | 1 |

## GG1024, and nine lots like it

`GG1024` (CoQ-PP-2025-0003 and 0029) is in the schedule **with every value it has** —
taken from the in-house CoA transcription, whose own footnote attributes the testing to
accredited laboratories — and every one flagged red: **not one underlying eCoA is on
file. Locate the physical certificates, scan, upload.** Nine further lots' cultivation
batches are in the same state (OMP1024_01¹, PUM102501, ACC102501, CF102501, FB012601/1,
JD012603/01, FB012602, CC012603, SCR012603 — the last five also absent from the register
entirely).

¹ OMP1024_01 resolves: the register's own P-number column shows its `OPM1024_01` block IS
lot P050042 — one transposition, on the master spec. Aliased with that evidence.

## Recorded, not resolved

1. **26 lots' banner THC matches no register assay** — the master spec carries analyses
   (the T2 re-analysis round among them) whose certificates the eCoA register has never
   received. Same class as GG1024: certificates to locate and file.
2. **35 lots' grade range disagrees with the signed QCSP 001 PDF** beyond the endpoint
   convention — two owner documents, two grade designs. The plan drives the CoQs; the
   disagreement is flagged per lot.
3. **192 rows cite a document dated after the CoQ's issue date** — the plan dates initial
   CoQs at packaging, and testing routinely finished later. The printed issue date must
   be no earlier than the newest cited document; QC sets it at issue.
4. **Identification C has still never been performed by anyone**, on any lot: 60 of 61
   CoQs owe it (the 61st is blocked).
5. Aflatoxin B1 and Ochratoxin A are certified separately only by Farmahem's `197-*-М`
   and `276-31-М/25`; the IPH `nnnn/yyyy` series reports the aflatoxin sum alone.

6. **`CoQ-PP-2026-0005` is assigned twice**: to GP0824_01 / P050102 in the older
   `deliverables/qc_register/` deliverable, and to P060062 (Permanent Marker) in the
   owner's plan — whose rendered document exists. The plan governs; the older
   deliverable's CoQ numbers are superseded and must not be issued.
7. **The rendered CoQ merges QCSP 001 items 1 and 2** into one appearance row — its
   analytical table has ten §01 rows against the specification's twelve. The schedule
   keys on the specification; transcription onto the form carries 1 and 2 together.

Ochratoxin A's acceptance criterion, incidentally, is settled by QCSP 001: **≤ 20 µg/kg**
— so the register's amber `2.06 — DETECTED, >LOQ` conforms with room to spare, and the
"per PP spec" column finally has its number.

An adversarial verification workflow ran over the whole build (5 agents, glyph-level
reads of all 48 specification PDFs with `pdftotext -bbox`): section 02 is one document
in 48 files with zero content differences; the `10⁵`/`10⁴` superscripts, the aflatoxin
subscripts and the µ/∑/– codepoints are confirmed from glyph baselines; and every source
rule this build implements was independently restated from the repository. Its two
genuinely new findings are items 6 and 7 above.

---

## Extended the same day: the universe around the 61 (owner's ruling, 31.08.2026)

Three further owner decisions arrived after the build above was recorded, and the
schedule was rebuilt on them. **The 61 numbered CoQs stand exactly as described; the
universe around them changed.** Figures above marked "over the 61" are superseded by
the rebuilt workbook.

**1 — The 48 lots are Tranche 01 + 02 only (19 + 29), and every batch on record gets
one initial CoQ, first to last.** Production stands at more than 80 batches. The
35 record batches past Tranche 02 now carry **predicted initial CoQs** — no packaged
lot, grade or number exists for them yet; a number is copied from the issuance record
at issue, never computed in advance. The earlier statement "register batches with no
packaged lot get no CoQ — there are 41 of them" is withdrawn: **six of those 41 were
not batches at all** but the register's P-number-keyed rows holding the Farmahem
197-series re-analyses *of plan lots* (`P060152`→J31102501, `P060212`→JD112501,
`P060242`→OPM122501, `P060352`→FB012602, `P060382`→SCR012603, `P060402`→GG012603 —
matched by the plan's own packaged-lot numbers), and their results now fold into
those lots. This also resolves four of the 26 banner-THC mismatches — the "missing"
analyses were on file under the P-rows all along — leaving **22**. OPM052501 and
CJ062501-2, the two lots whose over-criterion TYMC had no CoQ to hold it, now have
predicted CoQs carrying the finding.

**2 — The 12-month cannabinoid + mycotoxin retest programme is universal: every batch
gets a CoQ reissue, starting from the beginning of Tranche 01/02.** The 13 numbered
additional-testing CoQs are the ones already due; the remaining **35 of the 48** are
predicted at packaging + 12 months, and every batch past Tranche 02 at release + 12
months. On a reissue, only identity (Farmahem, with the assay), foreign matter (one
in-house iCoA), cannabinoids and mycotoxins are re-certified — every other
determination is *outside the retest scope; the release determination stands on the
initial CoQ*.

**3 — The CoQ SOP has been in use since 11.05.2026, and no CoQ may print an earlier
issue date.** The plan's per-CoQ dates are packaging dates — the basis of the
numbering series — never issue dates. Item 3 under "Recorded, not resolved" above
(192 rows citing documents dated after the CoQ's date) is thereby **dissolved, not
fixed**: there was never a violation, only a misread of what the plan's dates were.
The schedule now prints, per CoQ, the basis date and the earliest permissible issue
date — the SOP date, the newest cited document, or (for a reissue that cites nothing
yet) the 12-month due date, whichever is latest. 75 CoQs may be issued from
11.05.2026; 91 are bound later.

**The rebuilt totals: 166 CoQ documents** — 48 issued initial + 13 issued additional
testing + 35 predicted initial + 35 predicted Tranche-01/02 reissues + 35 predicted
later reissues — **× 23 determinations = 3 818 rows**; the iCoA plan grows to
**137** (45 × Ident A+B, 92 × foreign matter, every reissue owing exactly one).

Two findings the extension exposed:

* **Five ISSUED additional-testing CoQs cite no 197-series certificate on file** —
  `0029` GG1024 (retest per plan 11.03.2026), `0033` OMP1024_01 (20.06.2026),
  `0036` GP0824_03 (14.07.2026), `0037` OPM1024_03 (22.07.2026), `0039` MB0824_05
  (25.08.2026). The plan records the retests; the certificates never reached the
  file. Same defect class as GG1024's initial testing: locate, scan, upload.
* **Thirteen batches are re-analysed early** — the Farmahem pair is already on file,
  ahead of the 12-month mark for most — so their reissue CoQs can be numbered and
  issued now: GP052501, CJ052501/01, GP082501/2, CJ082501/2, PM092501, CJ062501-2,
  and the six P-row lots above, plus **P060332** (Cash Cow), which matches no plan
  lot and no register cultivation batch — its identity is an open question for QC
  (CC112501, the only Cash Cow on record, assayed 13.35 % against the P-row's
  17.67 %: not obviously the same material).

All 21 Farmahem 197-series pairs in the register land on exactly 21 distinct reissue
CoQs — 8 issued, 13 predicted — none lost, none double-cited.

---

## Reviewed adversarially, 31.08.2026 — what the review changed

Seven independent verifiers plus a completeness critic were run against the build above,
each recomputing one claim cluster from the primary sources and instructed to default to
DEFECT. Most of the universe held: the 166 documents, the tranche split, the ordering,
the whole dating rule, the P-lot identities and the 197-series conservation were all
confirmed by independent recomputation. **Six things did not, and all six are now
fixed.**

**1 — The in-house certificate plan was understated by 87 documents: 137, not 224.**
Three defects compounded in `icoa_plan()`:

* its dedup key was `(packaged lot, type, scope)`, and a predicted CoQ has no packaged
  lot — so all 70 predicted CoQs collapsed onto two rows, losing 50 owed certificates;
* it decided "is this a reissue?" by testing `type != "initial release"`, which sent
  all 35 *predicted initial* releases down the retest route, where Farmahem covers
  identity — dropping 26 Ident A + B certificates the schedule's own rows say the
  in-house laboratory owes;
* `outstanding_of()` let a batch's release-time CNP coverage excuse the same
  determination on its 12-month reissue. It cannot: the owner's routing sends identity
  to Farmahem and foreign matter in-house **on every reissue**, and a certificate from
  the release round cannot stand behind a determination dated a year later — the same
  rule that stops an initial CoQ citing the 197 series, running the other way.

Corrected: **224 in-house certificates — 71 Ident A + B and 153 foreign matter.**

**2 — "Thirteen batches re-analysed early, reissue issuable now" was wrong on the second
half.** A 197-К certificate carries Total Δ⁹-THC, Total CBD and Total CBN and nothing
else; its М sibling carries the six mycotoxins. Identity A, B and C and foreign matter
are outstanding on all thirteen, and *a CoQ must never carry a conformity assertion that
has not been certified*. They are **first in the queue**, not issuable: order Farmahem's
identity, issue the in-house foreign-matter iCoA, then number and issue.

**3 — "54 CoQs disagree with the QCSP 001 PDF" silently doubled a 27-lot finding.** A
lot has one grade range and two CoQs, and the note lands on both. Now reported as
**27 lots, shown on 54 CoQ documents**, and the builder's docstring — which still said
26 banner mismatches and 35 range conflicts — is corrected to 22 and 27.

**4 — The register has 80 batch blocks, not 81.** The iCoA register's 81st row is
GG1024, which has no register block at all. The mapping itself was airtight: all 80
blocks map, none dropped, none doubled.

**5 — One transposed pair, found by sweeping all 42 Farmahem certificates cell by
cell.** `197-7-К/26` (Fat Bastard, FB012602 / P060352) reports Total CBD `<LOQ` and
Total CBN `0.22 %`; the register carried them swapped. Total Δ⁹-THC was right, so no
potency cross-check could see it. It is the **only** disagreement in the series.
Corrected as chain step 16; neither value changes a disposition, but the reissue CoQ
would have printed both results in the wrong rows.

**6 — P060332's cultivation batch is CC012601/1.** Recorded as an open question in the
previous pass; the certificate table answers it. A third Cash Cow lot, in neither the
register's batch column nor the issue plan, and **nothing but its two Farmahem panels
exists for it anywhere** — no identity, foreign matter, loss on drying, heavy metals,
pesticides or microbiology. Same class as GG1024, one lot further on. Recorded on the
block rather than written into the batch column, which would invent an 81st batch out
of a transcription.

### And one finding the review surfaced that nobody had asked about

**Nineteen initial-release CoQs would print the 12-month re-analysis as their banner
potency, not the release assay.** The check that found four "resolved" banner mismatches
was looking at the wrong thing: the master spec's banner for those lots *is* the August
2026 Farmahem result. Extended to every lot, nineteen initial CoQs are in that state —
BSS1024 25.01 against a release assay of 21.03, BG1024 26.14 against 21.80, CJ052501/01
24.05 against 20.29, and sixteen more; two of them (FB012602, SCR012603) have no release
assay in the register at all.

This is not an error, and the SOP dating rule is exactly what makes it defensible: no
CoQ may now issue before 11.05.2026, and a certificate of quality speaks as of its date
of issue, by which date the re-analysis exists. But it is **a decision QC should take
knowingly**, on nineteen documents, and the schedule now prints the list.

## The microbiology acceptance criteria, checked parameter by parameter

Asked to pinpoint every microbiology acceptance-criterion error and whether TAMC should
read 10⁵. **It should, it does, and no TAMC result in this register is over any reading
of it** — the highest is 5.1 × 10⁴ against a maximum acceptable count of 200 000. Every
microbiological exceedance is TYMC, and TYMC is `≤ 10⁴` on the certificates, in QCSP 001
v.03 and on the CoQ master template alike.

The owner confirmed all microbiological purity testing is **Ph. Eur. 5.1.8 category C**,
and the documents name it: seventeen IPH certificates print `Microbiological quality
(Ph.Eur. 5.1.8 cat. C) — Total aerobic microbial count (TAMC) ≤ 10^5 CFU/g` and its
siblings, and Purely Plant's in-house form writes `Ph. Eur. 5.1.8, category C`. Against
that, all seven criteria are correct:

| № | Parameter | Criterion | |
|---|---|---|---|
| 9.1 | TAMC | ≤ 10⁵ CFU/g (max 200 000) | ✓ |
| 9.2 | TYMC | ≤ 10⁴ CFU/g (max 20 000) | ✓ |
| 9.3 | Bile-tolerant gram-negative | ≤ 10⁴ CFU/g (max 20 000) | ✓ |
| 9.4 | Salmonella | absence / 25 g | ✓ |
| 9.5 | E. coli | absence / 1 g | ✓ |
| 9.6 | P. aeruginosa | absence / 1 g, upon request | ✓ |
| 9.7 | S. aureus | absence / 1 g, upon request | ✓ |

**This withdraws a finding of my own.** Chain step 14's comment on the four undetermined
TYMC results claimed Ph. Eur. 5.1.8 category C was TYMC 10², and that QCSP 001
contradicted itself by printing `cat. C` beside `10⁴`. That came from memory rather than
from the documents, the documents pair `5.1.8 cat. C` with 10⁵ / 10⁴ / 10⁴ seventeen
times and never with 10², and no result's disposition ever turned on it. Withdrawn in
chain step 15.

Two documentary corrections were applied (step 15): the bile-tolerant GNB column heading
read `/1 g`, the absence qualifier belonging to E. coli, on an enumerated parameter whose
own limit is a count — and Ochratoxin A's criterion was still `per PP spec`, where QCSP
001 gives `≤ 20 µg/kg`. Four findings are recorded rather than changed, each a QA
determination on a signed document:

* **Purely Plant's in-house CoA form multiplies by five** — `<10^5, max 500 000` and
  `<10^4, max 50 000`, where Ph. Eur. 5.1.4 gives ×2: 200 000 and 20 000. Three
  documents carry it; no disposition turns on it; the form is still wrong and issues on
  every batch it is used for.
* **The HPA1024 in-house CoA prints `<10^ CFU/g`** for bile-tolerant GNB — no exponent.
* **Six certificates apply criteria tighter than category C to a category C product**
  (`1220/2171/25`, `1221/2172/25`, `406/0744/25`, `587/1066/25`, `627/1128/25`, and one
  GNB at 10³). Every result on them conforms anyway. One question to IPH, not a
  correction here.
* **QCSP 001 cites the categories in the wrong chapter** — `2.6.12 cat. C`, `2.6.31
  cat. C`, `2.6.13 cat. C`. Those are the test methods; the categories and their
  criteria live in 5.1.8, which is how the certificates cite them. A citation defect on
  the signed specification, not a numeric one.
