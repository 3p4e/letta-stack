# Handover — Purely Plant QC documents, for Claude Cowork

Written 23.09.2026. Assumes no knowledge of the conversation it came from. Read this first.

---

## 1 · What this folder is

`…\My Drive\1. PP\DATA_B\QC_eCoA\DELIV\END_FIN` holds three things:

| | |
| --- | --- |
| **the design system** | already in place — `styles.css`, `tokens/`, `components/`, `templates/`, `guidelines/`, `assets/`, `Final_Docs/`, `readme.md`, `HANDOFF.md`, `SKILL.md`, plus `SP-COA-COQ.zip` (280 MB) which is the same system zipped |
| **the master workbook** | `CoQ_Analysis_Master_v56.xlsx`, placed by the owner |
| **this kit** | `iCOA_AUDIT_KIT\` — this brief, two checkers, and the audit already run |

**The design system is read-only input. Adopt it; do not edit it.** Nothing in it is to be
rewritten, reformatted or "fixed".

**Where a later decision was made deliberately, it stands.** The design system is a snapshot and
does not carry the rulings taken after it. Those are listed in §7 and they win. Do not let the
design system overwrite them, and do not silently resolve a conflict either way — record it.

---

## 2 · The three tasks, in the owner's order

1. **First, the fullness of the master workbook** — is every analysis result there, and is there
   enough in it to compile both the **CoQ** (certificate of quality) and the **iCoA** (internal
   certificate of analysis)? **This is done. §4 is the answer.**
2. **The per-batch iCoA folder structure** — check the **Result column** of every document against
   the workbook. Each result must carry the **correct institution**, the external laboratory's
   **certificate code**, its **date of issue**, and the **correct analysis reference** (method).
   `verify_icoa_folder.py` does this; point it at the folder.
3. **The rule** — *one iCoA for every certificate of quality*: the initial testing for batch
   release, and **every retest**. Verified at 172 ↔ 172 in the workbook (§5); still to be verified
   across the documents on disk.

Separately, the owner wants the documents as **Word files that are exact replicas of the HTML**,
not reflowed approximations. §6 is the method, and §6.4 is the trap to avoid.

---

## 3 · Run it

    pip install openpyxl
    python3 verify_fullness.py --md FULLNESS.md               # step 1, the workbook alone
    python3 verify_icoa_folder.py <folder> --md FOLDER.md     # step 2, documents against it

Both find the highest `CoQ_Analysis_Master_v*.xlsx` lying beside them, so a later version is
picked up on its own. Exit **0** clean, **1** findings, **2** a check could not be performed.
**Exit 2 is never a pass** — a false clean is worse than no answer. Both are stdlib + `openpyxl`,
and neither writes to the workbook.

---

## 4 · Step 1, answered: the workbook is full, with 27 findings

Full output in `FULLNESS_2026-09-23.md`; the counts as measured in `reference/BASELINE.json`, so a
later run can prove it read the same workbook.

**Complete as a grid.** `CoQ Compilation (long)` holds **3,956 rows = 172 certificates × 23
determinations**, with **no blank result cell** and no short panel. 3,175 results stated; 781
absences, all three in the controlled vocabulary — `not tested` 350, `upon request — not required
for release` 344, `carried from the initial testing — not tested` 87.

**Provenance all but complete.** Method and acceptance criterion on **3,175 of 3,175**; laboratory,
document and date of issue on **3,164 of 3,175**.

| n | finding |
| --- | --- |
| 11 | `#3 Identification C · HPLC/HPTLC` states a result with **no laboratory, no document, no date** — status *to be performed — see route* — on CoQ-PP_26-021, 050, 069, 070, 071, 072, 073, 074, 084, 166, 167 |
| 3 | **a laboratory under two names** — `IJZ` 22 rows vs `IPH — Institute of Public Health` 1,559 · `CNP` 52 vs `UKIM Faculty of Pharmacy — Center for Natural Products` 365 · `FHM` 11 vs `Farmahem` 642. **85 rows name the institution in the short form**, against a requirement that says *the correct institution* |
| 1 | the DAB-2018 method string reads *"(CNP, before its Ph. Eur. 3028 accreditation)"*, but **41 rows of the same laboratories carry the Ph. Eur. method with an issue date earlier than the last DAB row** (11.05.2026). The split is consistent per document, so the wording claims a date boundary the dates do not have |
| 3 | an external laboratory with **no sample-receipt date on any result** — `IJZ` 22 · `FHM` 11 · `State Phytosanitary Laboratory` 2 |
| 4 | an iCoA with **no basis date** — iCoA-PP_26-078, 079, 134, 135 |
| 4 | an iCoA whose **scope is wider than the other 168** — iCoA-PP_26-005 and 006 carry 16 determinations, 023 and 024 carry 6. **The documents are not all three-determination certificates** |
| 1 | three lots carry a retest round with **no lower round on file** — P050022 I/R5 · P050072 I/R4 · P050202 I/R5. If the round is a campaign label this is expected; if it counts a lot's retests, the earlier ones are missing |

Rows not counted as faults, deliberately: a determination performed **in house** has no external
institution to receive the sample, so it has no receipt date to be missing; and a row with no
laboratory at all is reported once, by the provenance check, not twice.

---

## 5 · The workbook: what to read, and the one trap

`CoQ_Analysis_Master_v56.xlsx`, 12 sheets. Work from **`CoQ Compilation (long)`** — one row per
printed cell, 18 columns, **fully literal, no formulas**:

    CoQ code · Series · Batch (cultivation) · P lot · Strain · Date of issue · # · Parameter ·
    Method · Acceptance criterion · Result · Document · Issued · Laboratory ·
    Received by the laboratory · Status · Route · Also on file

**The trap.** Several register columns are **live Excel formulas, and openpyxl caches no value for
them** — read them and they come back empty:

| sheet | formula columns |
| --- | --- |
| `CoQ Register` | `No.` · **`CoQ code`** · `Issue date (planned)` · `Rule date` · **`iCoA (register)`** · `iCoA issue date` |
| `iCoA Register` | `Issue date (planned)` · `Test date (packaging)` · `Packaging complete` · **`CoQ (register)`** · `CoQ issue (planned)` |

Two of those carry the **iCoA-to-CoQ link**. A checker that believes the blanks invents gaps that
do not exist. Three ways through, in order of preference:

1. **Join on `Key`.** Both registers carry a **literal** `Key` — `CJ1024|I`, `P050202|R2` — lot and
   testing round. The link needs nothing else. This is what `verify_fullness.py` check H does, and
   it gives **172 ↔ 172**: 89 initial, 83 retests (R 48 · R2 32 · R4 1 · R5 2).
2. **Reconstruct the CoQ code from the rule its own formula states**: walk `CoQ Register` top to
   bottom, count rows whose `Issuable` is `yes`, `allocated` or `ruled`; the *n*-th is
   `CoQ-PP_26-%03d`. Exact, and needs no LibreOffice.
3. **Recalculate** through LibreOffice — only needed for the planned dates.

**Identity.** A lot and its starred spelling are one lot (`GG012601＊` = `GG012601`). Compare
document codes with separators and case normalised. `—` is the workbook's own *not applicable* — it
is not a value and not an empty cell; eleven Identification C results turn on that distinction.

---

## 6 · The Word replica: how it is done

The owner's standard, stated plainly earlier: a Word file whose page is **visually identical** to
the HTML. *"Your conversion from HTML to Word is a totally different file, different design,
different structure — that will not do in a GMP environment."* What follows is the method that met
it, verified to placement medians of **0.015–0.02 pt**.

### 6.1 Print the HTML deterministically

Headless Chromium, `prefer_css_page_size`, `print_background` on, `@page{size:A4;margin:0}` with
`.page` fixed at 210 × 297 mm — exactly one A4 page, no printer margin of its own. Fonts
(Montserrat, Roboto Mono, Orbitron) are **subset to the characters the documents actually print**
and inlined as data URIs, and Google's font hosts are **blocked at the network layer** for the run,
so the PDF is byte-identical whether or not the machine can reach them. A controlled document that
changes appearance depending on a third party's reachability is not one to hand a regulator.

Two details that cost a rebuild each. Uppercasing is done by `text-transform`, so the **subset must
contain both cases** of every character or a transform asks for a glyph the face lacks and one
letter silently falls to a substitute face. And **every italic weight the stylesheet uses must be
declared**, or the browser synthesises the slant, embeds it as a Type 3 font, and that text can no
longer be extracted at all.

### 6.2 PDF → Word, without reflow

The page is **not** re-laid-out. For each page:

* the page's own graphics go in as a single floating `wp:anchor` image, `behindDoc`, at full page
  size — that is the background, and it is pixel-exact;
* every text span is emitted as its **own paragraph carrying `w:framePr`** with an absolute
  position, so the text sits exactly where the print put it and stays selectable, searchable and
  editable.

No reflow, so nothing can move. Four things are required for it to actually work:

1. **OOXML child order.** `w:rPr` and `w:pPr` have ordered content models. A child in the wrong
   place makes Word declare the file unreadable — this is the real cause of that error, not font
   keys. Keep an explicit order list and insert into it.
2. **Type size is half-points only.** 15.975 pt must be written as `w:sz` 32 directly; going
   through a convenience API truncates it to 15.5 pt.
3. **Letter-spacing is spread over the gaps, `n − 1`, not the characters.** Dividing by the
   character count drifts the line. Sub-twip precision comes from splitting the run in two and
   giving each half a different `w:spacing`; a single character cannot be spaced, so set it outright.
4. **Suppress shadow twins.** CSS `text-shadow` makes Chromium draw the glyphs **twice** in the
   PDF text layer, so the Word file gets doubled, slightly offset text. Detect the pair by same
   text, same size, same x within 0.1 pt, ~0.75 pt lower, different colour — and drop the lower.
   Do not compare the font face: a synthesised face is a new object on every draw.

Gaps between spans are bridged with a **measured space**, never by letter-spacing the preceding
word — that distorts the word and still falls short.

### 6.3 A template is different from a certificate

A certificate is a record nobody edits, so one box per PDF text span is right. A **template** is
typed into, and a span is whatever the renderer happened to draw — `[MANUFACTURE DATE]` arrives as
`[MANUFACTUR` + `E DATE]`, and nobody can type a date into two boxes.

Merging boxes by their positions on the page was tried and measured and **is not safe**: taking
neighbours on one baseline joined two separate tick pills into `HYBRIDINDICA`, and tightening the
rule until that stopped left the median box at two words. **Ink position does not say what belongs
together — the DOM does.** Read the field boundaries from the **DOM in the same pass that prints
the page** (a probe callback on the laid-out page, with print media emulated), and let the PDF say
only where the ink goes. One box per whole field, each taking its element's own width so a longer
value wraps inside the field instead of running off the page.

Two things that bite: a placeholder set in a synthesised italic has **no family name in the PDF at
all**, so take the face from the DOM's computed style; and to measure whether a value is clipped,
measure the **nearest ancestor with `overflow` hidden or clip** — an inline `<span>`'s `scrollWidth`
measures nothing. Where the page would clip a placeholder, shorten it along a ladder that **keeps
the number**, because the number is the field's identity: `[COLOUR 3]` → `[COL 3]` → `[C 3]` → `[3]`,
stopping at the first rung that fits.

### 6.4 **Do not use the shipped PowerShell script's Word step**

The design system ships `Final_Docs\Export_HTML_PDF_DOCX.ps1`. Its **PDF step is sound** and worth
keeping: it finds every `*.html` under `xCOAs\CoX_DES\ISSUE_COQ\COQ_FIN`,
`xCOAs\CoX_DES\ISSUE_iCOA\iCOA_FIN` and `ImB_SPC\SPC_FINAL_ImB` (excluding `iCoA_P01-02-07*`), and
prints each with Edge or Chrome `--headless=new --no-pdf-header-footer
--run-all-compositor-stages-before-draw --virtual-time-budget=4000 --print-to-pdf`. The HTML is
self-contained, so it works offline.

Its **Word step is the problem**. It drives Word by COM, opens each PDF and `SaveAs2`s a `.docx` —
that is **Word's PDF Reflow**, which re-lays-out the page from scratch. It is precisely the
"different design, different structure" outcome the owner rejected. Replace that step with the
method in §6.2. Keep step 1 and step 3 (step 3 checks that every HTML got a PDF and a DOCX, which
is a good gate).

---

## 7 · Divergences between the design system and current decisions

Record each; do not resolve one silently, and do not let the design system overwrite the later
decision.

| the design system | what holds now |
| --- | --- |
| `Final_Docs\V49_COMPLETENESS_2026-09-20.md` works against workbook **v49** | **v49 must not be used at all.** The current workbook is **v56** |
| its `readme.md` names the repo of record as `3p4e/coa_track`, PR #20, branch `claude/elegant-feynman-9PiII` | **the design system is not in that repository** — checked on `main` and on that branch, neither has `styles.css`, `tokens/`, `components/` or `templates/`. Treat the folder here as the only copy |
| `cox.css` in `templates\*\` is **22,141 bytes** | the copy carried in the project tree is **30,429 bytes** — a modified descendant, not the same file. Diff before assuming either is canonical |
| iCoA signoff described as **3-tier**, Analyst → Senior → Head of QC | the issued fleet signs in **three blocks with different roles** — Analysis Performed by (Analyst, QC Laboratory) · Reviewed by (QA Manager) · Approved by (QC Manager) |
| iCoA is "all testing in house, **never** external" | true for the results themselves, but the iCoA **cites an external eCoA for Identification C**, and the register carries that citation per lot |
| iCoA scope, generally | **168 of 172** are Ident A + Ident B + Foreign matter; **4 are wider** (§4). The `icoa-single` and `icoa-ident-ab-fm` template variants are consistent with this — pick the variant from the register's `iCoA scope`, never by assumption |

Agreements worth keeping explicit, because they are easy to break: **"MK GMP Certified Facility",
never "EU GMP"** on flower documents; navy `#1B3A5C` with gold `#A67C2E`/`#C9A227` and bronze
`#8C6B3F`; Montserrat + Roboto Mono with Orbitron for strain names and document codes; exactly one
A4 page; and *decoration bleeds, text does not* — bands and rules run to the page edge, text never
enters the 0.3 in safe frame.

---

## 8 · Verify the document ID against the register, never the filename

Not hypothetical. The iCoA design copy in circulation,
`iCoA-PP_26-036_P060012_WC_Wedding_Crasher_Initial.html`, is **headed** `iCoA-PP_26-036` for lot
`P060012`. The register gives `P060012|I` the code **`iCoA-PP_26-035`**, strain **`Wedding
Crusher`**, and gives `036` to **`P060022` / Cap Junky**. The issued fleet agrees with the register.
So that copy carries a wrong document ID **and** a wrong strain spelling, and anything generated
from it inherits both. `verify_icoa_folder.py` checks the ID, the strain and the batch against the
register for the lot and round the document itself states.

---

## 9 · Comparing a printed cell to the workbook

Exact string equality is the wrong test, and testing against an issued certificate proved it: the
naive rule called **all twelve rows of a correct document defective**. Three reasons, all real:

* the workbook stores a bilingual value as **`English | Македонски`** (`Conforms | Одговара`), while
  the certificate prints the two in separate elements — so strip the gloss from **both** sides;
* the certificate prints the **short** form of a method (`Ph. Eur. 2.8.23 · mon. 3028`) where the
  workbook holds the long one (`Ph. Eur. 2.8.23 (microscopy)`) — same determination, different
  wording;
* an **in-house** determination names the analyst and the QC laboratory, not
  `Purely Plant GmbH (in-house)`, so looking for the company's own name in the page is looking for
  the wrong thing.

The rule that works: the document's words are all in the workbook's → **match**; the pharmacopoeial
citations agree but the wording differs → **a note**, for the owner's eye, not a mismatch; the
citations **conflict** → **a finding**, because a certificate citing 2.2.29 where the record says
2.8.23 names the wrong method whatever the wording. On that basis the issued certificate passes with
**no findings and four honest notes**.

---

## 10 · Rules that must not be broken

* **Never move an `Issuable` state** (allocated → issued). That transition is the owner's GMP
  authorisation, not an automated step.
* **Workbook v49 must not be used.** `CoQ_Analysis_Master_v44.xlsx` and the three 17.09 lists in
  `CoXTemp` are **pre-renumbering** and must not be distributed.
* **`QCSP_001_v04` is superseded** — not to be issued or cited. The current specification sheets are
  **v.03**, and they carry **no document code in the bottom-right corner**.
* The **packaging-date question was resolved on 20.09.2026** and must not be reopened.
* **Vendor independence**: a release-critical number and the document carrying it come from the
  laboratory's own certificate, never inferred from another source.
* Nothing is uploaded to the owner's Drive uninvited; `eCoA_DB` is not deleted without an explicit
  confirmation given at the time.
* **The design system is not edited.** Adopt it, record divergences, leave it as it is.

---

## 11 · Open questions for the owner

1. The **eleven Identification C rows** with no laboratory, document or date. Either the route
   resolves to a certificate that has not been entered, or those eleven certificates cannot state
   Identification C.
2. The **DAB parenthetical** that 41 rows contradict — is the wording wrong, or the rows?
3. **P050022 / P050072 / P050202** carrying round R5 / R4 / R5 with no lower round: campaign label,
   or missing retests?
4. The **iCoA signoff roles** — 3-tier as the design system describes, or the three blocks the
   issued fleet uses?

---

## 12 · Done looks like

* `verify_fullness.py` reproduces `reference/BASELINE.json` on the owner's copy of the workbook —
  if it does not, the workbook changed or the read is wrong, and that is worth knowing before
  anything else.
* `verify_icoa_folder.py` runs over the per-batch folders and every disagreement names the
  document, the determination, what the folder says and what the workbook says. Never a bare count.
* One iCoA per CoQ confirmed across the documents, initial release and every retest, against the
  register's 172.
* Word files that are replicas: one A4 page each, text selectable and in place, no doubled glyphs,
  no reflow, and for templates one text box per whole field with nothing clipped.
* Divergences recorded rather than resolved; the design system unchanged.
