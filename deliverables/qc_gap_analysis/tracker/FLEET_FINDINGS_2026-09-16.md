# What the audits of 16.09.2026 found

Three fleets were run against the desk on 16.09.2026, twelve agents in all, each reading the
primary records rather than the desk's own conclusions: one on **every starred cultivation
batch** against the owner's ruling of the same day, one on **the eCoA scan database against
every desk record**, and one on **what the certificate of quality asserts** — the in-house
determinations, the potency ladder and the data contract for the design the Head of QC is
preparing.

Everything below is sorted into three classes, and the class is the point:

* **defect** — the desk said something the record does not support. Fixed, or named as not
  fixed and why.
* **question for the owner** — a decision that is not the desk's. Each is on the Open Items
  register with its evidence.
* **no action** — checked, and the desk is right. Recorded so the same question is not asked
  a fourth time.

Two of the twelve agents' claims did not survive checking and are marked so. A finding that
disagreed with the desk was re-derived from the record before anything was changed.

---

## Defects — fixed in v37

### 1 · A reissue asserting a retest it has not had — 39 certificates, 117 rows

39 additional-testing certificates printed **Conforms** for #1 Identification A, #2
Identification B and #7 Foreign matter, citing **their own campaign's** internal certificate,
while the row's own status still read *"to be performed — see route"*. The value did not come
from that campaign: the exporter reads it from the owner's 09.09 pass, which states what the
**release** round's internal certificate carries, and its lookup carried no round.

Confirmed on the export before changing anything: `CoQ-PP_26-083` (BG1024) prints `Conforms`
on #1/#2/#7 against `iCoA-PP_26-098` of 27.07.2026, route *"Farmahem — Ident A + B + C with
the Assay, at retest"*, status *"to be performed"*. A certificate may not assert a result for a
testing round nobody has recorded.

**Fixed.** The pass fills a release certificate's cell only. A reissue carries the release
row (`ST_CARRIED`, the ruling of 15.09.2026) or stays blank.

### 2 · A lot the 09.09 pass names differently — 1 lot, 2 certificates, 6 rows

The pass records `CC012601/1 / P060332` as CITED, `Conforms`, against `iCoA-PP_26-065` for
#1, #2 and #7. The register block is labelled by the P number alone, the export carries the
lot as `P060332`, and the lookup — keyed on the cultivation batch — found nothing, so
`CoQ-PP_26-066` and `CoQ-PP_26-085` printed `—` where the pass holds a result.

**Fixed.** The pass is keyed by its P lot as well as its batch.

### 3 · Two read-backs that were reading nothing

* **The title, on the desk's own Print and Save.** v36 fixed the `<title>` in the bulk
  driver; `fillCoq` itself never touched it, so a certificate printed or saved from the
  interactive desk still carried the master's literal title naming `CoQ-PP-2026-0005 —
  Amsterdam Amnesia — Batch P060052`. **Fixed** at the compiler, so both paths carry it.
* **Section 01.** The build read the compiled page's lockups with `.lk .l` / `.lk .v` —
  classes the master has never had — so the dictionary was empty for all 73 documents and
  nothing read back Prod. Code, Potency, Spec. Ref., Prod. Batch №, Manuf. Date or Pack. Date.
  **Fixed** (`.lk-lbl` / `.lk-val`), and the build now names any document whose Section 01
  does not print its own P lot, a potency and a specification reference.

### 4 · The star split two live lots — fixed with the ruling, as data

`icoa_register.py` looked each lot's packaging date and P number up by the cultivation code
the **register block** carries, while the **batch list** writes the starred spelling. So
`iCoA-PP_26-087` (GG012601, P060302) and `-088` (JD012601, P060312) had no testing date and no
P lot, and their release certificates stood at `— at issue —`, **withheld over a glyph**;
`iCoA-PP_26-090` (SCR012601) had no testing date for the same reason.

**Fixed by recording the ruling rather than by changing the rule.**
`ingestion/ecoa_runner/identity_decisions.tsv` carries a `batch_alias` row for `JD112501*`
(the Head of QC's ruling) and for `GG012601*`, `JD012601*`, `SCR012601*` and `FB012602*` (the
desk, as its consequence — **one word from the Head of QC turns those four into rulings**, and
one word reverses them). `batch_key` applies them after normalising, so the two spellings key
alike everywhere at once, and a star nobody has ruled on still keeps its mark.

Measured: the CoQ register goes from **133 numbered / 13 not yet issuable** to **135 / 7**,
and the two Tranche 3 release certificates are no longer withheld.

---

## Defects — found, not fixed, and why

### 5 · Every Drive link in the export is dead — 258 of 258

The `ecoa` block carries a `pdf` link per certificate, captured from the 31.08.2026 snapshot.
The owner re-uploaded `eCoA_DATABASE` on 09.09.2026 and every file has a new id, so all 258
links resolve to *"Requested entity was not found"* (3 of 3 spot-checked). Nothing on a
certificate of quality prints them; the desk's own artifact page does.

**Not fixed here**: re-capturing 258 ids is an enumeration of the owner's Drive, and the
folder's paging was unstable during the audit (three pages returned the same records). It is
worth doing once, deliberately, against a stable listing — not as a side effect of this build.

### 6 · Specification numerals were renumbered against the desk's own rule

`potency_grades.number()` promises a numeral is *"assigned once … never renumbered"*, but the
first numbering seeded itself from nothing and sorted by nominal, ignoring the numerals the
**issued** QCSP 001 v.01 documents already carry. So `QCSP_001_GP-IV_v.01` named `GP_THC20`
(18.00–22.00 %) on the issued document and names `GP_THC16` (14.40–17.59 %) on the
certificate. **69 certificates over 20 codes** carry such a change.

**Not fixed, and deliberately.** Every one is disclosed on the certificate record —
`spec_status` prints *"for review — replaces the issued QCSP_001_GP-IV_v.01 (was GP_THC20 :
CBD1, 18.00 – 22.00 %); now GP_THC16 : CBD1 14.40 – 17.59 %"* and 88 certificates carry the
`conflict` sentence — and the owner's ruling of 15.09.2026 was that **the potency
specification of 15.09.2026 is used exactly, everywhere**. Renumbering the ladder to match the
issued documents would contradict that ruling; leaving it contradicts `number()`'s docstring.
**That is OI-44** — it needs the owner, not a patch.

---

## Questions for the owner — on the register, with their evidence

| # | question | where |
| --- | --- | --- |
| **OI-28** | The four starred spellings joined as a consequence of the ruling — confirm, and they become rulings | ruled, applied |
| **OI-12** | #9 of `CoQ-PP_26-057` now cites the unstarred `307/0551/26` where the 09.09 pass cited the starred sample's `306-0550-26`; and the "Also on file" note no longer declares the second sample | ruled, two consequences |
| **OI-42** | 44 laboratory scans on Drive that **no desk record holds** — 20 IJZ contaminant reports, 22 IJZ-MB microbiology reports, 2 Farmahem; and 58 more only in the 09.09 pass. Each of the 20 is the **first** metals/mycotoxin/pesticide document for its lot | new |
| **OI-43** | 28 in-house QCCoA scans on Drive with no desk entry — **12 of them for lots OI-41 names**. May the desk take them in as the record of #1/#2/#7? | new |
| **OI-44** | The specification numerals above | new |
| **OI-41** | Now sharper: the 90 certificates that print `Conforms` do not rest on a different kind of record from the 82 that print nothing — they rest on the same 09.09 pass. The line between them is **pass coverage, not evidence** | rewritten |
| **OI-01** | One certificate is outside the ladder: `P060102`, Wedding Cake, 25.15 % — a strain with **no page** in the potency specification. "The nearest grade on file" has no subject here | sharpened |
| **OI-05** | **41 of 67 lots are graded differently on their release and their 12-month certificate**, so one lot carries two product codes (P060412 JD-I → JD-III; P050172 CJ-V → CJ-III). That is the regrade disposition, at corpus scale | sharpened |
| — | **16 release certificates print no Total THC** although their register block holds an assay — the only assay is a 197-/220-/227-series document the desk treats as re-analysis, so the release certificate withholds it | OI-05 |
| — | Three lots on the batch list need a word: **JD032601** (P060472) has two laboratory reports on Drive, no register block and no potency certificate anywhere; **SC062501** and **GOG062501** have no document on Drive at all | OI-42 |
| — | **Design contract**: dates (`05.2026` against `16.05.2026`), the document-code grammar (`CoQ-PP-2026-0005` against `CoQ-PP_26-057`) and the product-code spacing differ between the DS v02 field rules and what the compiler writes. Which is binding for the new template? | for the design |
| — | On 12 certificates the **Spec. Ref. names one specification while the ticked selection bands are read from another**; the certificate prints no trace of it | for the design |
| — | 4 reissues print `(supersedes CODE of DATE)` for an initial certificate the export records as **not issued** | for the design |

---

## No action — checked, and the desk is right

* **No certificate cites a (strain, grade) pair the ladder lacks** — 0 of 155. The parallel
  desk's "35 not on the ladder" is not reproducible by any key; matching by literal strain
  name gives 31, and every one of those is a **spelling variant** (*Cup Junky*, *FatBastard*),
  which is `strains.py`'s CONFLICTS table, not a grading fault.
* **0 of 155 printed Total THC values fall outside the criterion printed beside them** — and
  now by construction, since the criterion is the ladder window the result itself falls in.
* **Every laboratory certificate code the desk holds has a scan on Drive** — 0 of 403 missing.
  The gap is one-directional: scans the desk has not read, never records without a scan.
* **The Farmahem mycotoxin family is fully ingested** (54 of 54) and Drive confirms exactly one
  lot with a second `-M` certificate, so the sweep's "aflatoxin B1 and ochratoxin A were
  comparable on one lot only" is a **testing fact**, not a register gap.
* **The starred-sample ruling fires exactly once on the whole desk.** Over 81 tracker lots, 87
  rows of the batch list and 600 cells of the 09.09 pass there is one label collision after
  star-stripping: `JD112501`. The other four starred batches have one spelling each and their
  own P lot — which is why `EXPERIMENTAL` stays an explicit list of codes and not a rule keyed
  on the asterisk, a rule that would de-certify four live lots.
* **The v36 exclusion changed nothing it should not have.** 3,956 certificate cells compared
  between the v35 and v36 exports: **0 changes** to any result, cited document, date or
  laboratory; the only 4 changes are the "Also on file" note on P060212 losing its starred
  companion — which is OI-12's second question.

---

## Two claims that did not survive checking

* **"The heavy-metal zero would become 2–3 lots with full ingestion."** The direction is
  right — the sweep's zero is a register gap, not a testing fact, which the sweep report
  already says in those words — but the arithmetic rests on scans nobody has read. Until the
  44 are read through the two-read gate the number is unknown, and this report does not print
  it as though it were known.
* **"OI-28: seven starred lots with no internal certificate."** Its own premise was stale:
  only three of the seven are starred anywhere, and all seven have carried an iCoA row since
  the 227-К and 220-М intakes. The item is rewritten around what was actually broken — two
  lots whose release certificate was withheld over a glyph.

---

Built from the three fleets' returns of 16.09.2026, each claim re-derived against the primary
records before it was written here. The per-agent transcripts are in the session's workflow
journals; nothing in this report rests on an agent's summary alone.
