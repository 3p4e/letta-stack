# CoQ retests, Tranche 1 and Tranche 2 — 53 documents, HTML

Built 23.09.2026 against the attribution ruling of the same day. **HTML first, as asked**;
PDF and Word follow on your word.

| | |
| --- | --- |
| `CoQ_retest_T1/` | 21 certificates |
| `CoQ_retest_T2/` | 32 certificates |

Every file opens on its own — **no script, no stylesheet, no font and no image fetched from
anywhere**. The three house families are subset to the characters these pages print and
carried inside the file, so the document that opens in Word is the document that was built,
not whatever type the machine happens to have. That is the fix for the runtime error: the
issued set linked four things it was not shipped with and a stylesheet on Google's servers.

Rebuild from source in about ten seconds:

    node design_handoff/toolchain/build_v40.js
    python3 build_selfcontained.py design_handoff/out/REISSUE/T1 --out DELIVER_2026-09-23/CoQ_retest_T1
    python3 build_selfcontained.py design_handoff/out/REISSUE/T2 --out DELIVER_2026-09-23/CoQ_retest_T2

## What the page now says, and why

Section 03 of every one of the 53 reads the way you set it out:

| determination | laboratory |
| --- | --- |
| 1, 2, 7 — Identification A, Identification B, foreign matter | Purely Plant QC Department, in house, on the batch's own iCoA |
| 3, 4, 5, 6, 10 — Identification C, the three assays, the three mycotoxins | Farmahem |
| 9, 11, 12 — microbiological purity, heavy metals, pesticides | Institute of Public Health |
| 8 — loss on drying | Center for Natural Products, or Farmahem where Farmahem did it |

and the **iCoA number is the CoQ number** on all 53 — `CoQ-PP_26-085` carries
`iCoA-PP_26-085`. Across the whole fleet that pairing was true of ten certificates out of
172 before today; it is now true of all 172.

## The eleven that carry something to settle

Forty-two of the fifty-three are complete. These eleven are not, and **nothing was invented
to close them** — where no certificate exists the cell stays empty and is named here.

| tranche | certificate | lot | what is open |
| --- | --- | --- | --- |
| T1 | CoQ-PP_26-087 | P060332 Cash Cow | heavy metals, pesticides, loss on drying — no document on file |
| T1 | CoQ-PP_26-091 | P060352 Fat Bastard | heavy metals, pesticides, loss on drying — no document on file |
| T1 | CoQ-PP_26-097 | HPA1024 High Pro Amnesia | microbiology, metals, pesticides attributed in house; IPH 587/1066/25 and 2995/2025 are on file for this lot |
| T1 | CoQ-PP_26-101 | OPM1024 Orange Punch Mimosa | the same, and IPH 2156/2025 is on file; also the bile-tolerant GNB range below |
| T1 | CoQ-PP_26-105 | P060382 Scrambler | heavy metals, pesticides, loss on drying — no document on file |
| T2 | CoQ-PP_26-107 | P050192 Blue Sunset Sherbet | pesticides at the State Phytosanitary Laboratory, not the Institute; loss on drying in house |
| T2 | CoQ-PP_26-108 | P060372 Cash Cow | heavy metals, pesticides, loss on drying — no document on file |
| T2 | CoQ-PP_26-122 | P060362 Jelly Donuts | heavy metals, pesticides, loss on drying — no document on file |
| T2 | CoQ-PP_26-125 | P060492 Jelly Donuts | microbiology, metals, pesticides, loss on drying — no document on file |
| T2 | CoQ-PP_26-171 | CC042601 Cash Cow | the whole external panel — no document on file |
| T2 | CoQ-PP_26-172 | FB042601 Fat Bastard | the whole external panel — no document on file |

**Every one of these is a gap on the initial certificate, not on the retest.** Checked
across all 83 retests: not one of them drops a value its initial holds. Close the initial
and the retest closes with it.

## One question on the face of a certificate

`CoQ-PP_26-101` (and its initial, `CoQ-PP_26-006`) print bile-tolerant gram-negative
bacteria as **`< 10² > 10³ CFU/g`** — below a hundred and above a thousand at the same
time, which no count can be. The other nineteen certificates in the fleet that report this
bracket read `< 10³ and > 10²`. Both the register and the independent page read of
09.09.2026 carry the same garbled string, so this has to be read off the certificate
itself. Disposition does not turn on it — the criterion is ≤ 10⁴ CFU/g and either reading
conforms — so it is a transcription question, not a release question.

## What the gate says

`coq_check.js` runs on every document before it ships. Across the full fleet of 172 it
reports 27 findings, down from 46 this morning:

* **2 hard** — the two certificates above, and nothing else;
* **11** total yeast and mould counts between 10⁴ and 2 × 10⁴, the Ph. Eur. 5.1.4 band where
  the count is undetermined rather than failing; each is marked amber on the page;
* **14** above 2 × 10⁴, out of specification; each is marked red on the page.

The nineteen OI-27 findings — determinations 1, 2 and 7 credited to the Center for Natural
Products — are gone, because you ruled they are ours.

---

# The internal certificates of the same batches — 53 documents, HTML

| | |
| --- | --- |
| `iCoA_retest_T1/` | 21 internal certificates |
| `iCoA_retest_T2/` | 32 internal certificates |

Same rule as the certificates of quality: every file opens on its own, no script, nothing
fetched from anywhere, the house type carried inside.

Each one carries **its certificate of quality's number** — `CoQ-PP_26-085` ↔
`iCoA-PP_26-085` — names that certificate's own lot and cultivation batch, is labelled a
retest, and certifies **Identification A, Identification B and foreign matter in house**,
which is the scope you set.

## Why these were rebuilt rather than reprinted

The fleet was being printed from `icoa_v44_recs.json`, a record file the register has moved
past. Against the certificates of quality that cite them, **six of the 172 numbers named the
same lot**. Three fleets on disk disagree pairwise about `iCoA-PP_26-085` alone:

| where | what it says `iCoA-PP_26-085` is |
| --- | --- |
| `icoa_v44_recs.json` | GG012603 · P060402 · Gorilla Glue |
| `icoa_handoff/out/INITIAL/` | P060382 · Scrambler |
| `SIGNED_2026-09-21/iCoA/Initial/` | P160022 · Grape Pie |

A number that names three lots is not a number, and this predates today — it is not a
consequence of the renumbering. So the fleet is now built from the one record the
certificates actually cite: `icoa_handoff/v3/build_from_register.js` synthesises each
internal certificate from the certificate of quality that names it — its lot, strain,
series, tested and issue dates, and the results its own rows 1, 2 and 7 carry. The lot is
the lot by construction instead of by a lookup that can drift. **The generator itself is
untouched**: `icoa3_gen.js` is the design system and is called exactly as before; only the
records come from somewhere else.

Checked on all 172: every number pairs with its certificate of quality, every lot is that
certificate's lot, all 172 conform, and none is carried from an external laboratory any
more — which is your ruling that Identification A and B are ours.

Nineteen batches have no cultivar record on file (phenotype, processing). On those the
generator leaves the boxes open rather than ticking Hybrid and Hand, because that would
assert something nobody recorded.

    node icoa_handoff/v3/build_from_register.js
    python3 build_selfcontained.py <staged retest dir> --out DELIVER_2026-09-23/iCoA_retest_T1

---

# The ImB product specifications of the same batches — 39 sheets, HTML

`ImB_Spec_T1_T2/` — the specification sheet every one of the 53 T1 and T2 retest batches
cites, and nothing else. **None is missing.** Thirty-nine rather than fifty-three because a
specification is a product's, not a batch's: three Cap Junky Grade II lots share
`QCSP 001_CJ-II_v.01`. `ImB_Spec_T1_T2_map.json` lists which batches each sheet serves.

These are the sheets already built on the canonical template (`specs/QCSP_001_ImB/SHEETS`,
57 in all), self-contained here the same way. Checked on all 39: the header code is the one
the batch's certificate of quality cites, the bottom-right corner is **empty** — the
template has no document code there, as you said — and each opens on its own.

    python3 build_selfcontained.py <staged sheets> --out DELIVER_2026-09-23/ImB_Spec_T1_T2

## What is delivered so far

| folder | documents |
| --- | --- |
| `CoQ_retest_T1` · `CoQ_retest_T2` | 53 certificates of quality |
| `iCoA_retest_T1` · `iCoA_retest_T2` | 53 internal certificates, numbered alike |
| `ImB_Spec_T1_T2` | 39 product specifications, covering all 53 |

145 documents. Next, in your order: the initial-release internal certificates and
certificates of quality, then Tranche 3 — retests, then initials.

---

# The initial release — 89 certificates of quality and 89 internal certificates

| | |
| --- | --- |
| `CoQ_initial/` | 89 certificates of quality |
| `iCoA_initial/` | 89 internal certificates, each carrying its certificate's number |

All 89 pairs print side by side. Same self-containment: nothing fetched from anywhere, no
script, the house type inside the file.

**Fifty-six of the 89 read exactly as the ruling sets it out.** Thirty-three carry
something to settle, and they fall into three groups.

## 1 · Twelve lots that Farmahem tested and the Center for Natural Products never saw

`CoQ-PP_26-046, 047, 048, 049, 051, 052, 053, 054, 055, 056, 060, 062` print **Farmahem**
for Identification C and the three assays, where the ruling says the Center for Natural
Products on an initial certificate. Checked against the receipt register, lot by lot:

| certificate | batch | what is on file for the assays and Identification C |
| --- | --- | --- |
| 046 · 047 · 048 · 049 · 060 | WED102501 · PUM102501 · ACC102501 · CF102501 · OPM122501 | **nothing** |
| 051 · 052 · 053 · 054 · 055 · 056 · 062 | J31102501 · SJ102501 · KC102501 · GRC102501/2 · SJ112501 · J31112501 · J31122501 | Farmahem only — the 051-K/26 campaign, and later rounds |

**There is no Center for Natural Products certificate for any of the twelve.** The page is
therefore reporting who actually measured the batch. Two ways to settle it, both yours: the
ruling has an exception for the 051-K/26 release campaign, or those twelve need a certificate
from the Center for Natural Products before they can read that way.

## 2 · Four lots whose release panel was routed in house

`CoQ-PP_26-005` (HPA1024), `006` (OPM1024), `025` (BSS052501), `026` (GP062501) attribute
assays — and on 005 and 006 also microbiology, mycotoxins, heavy metals and pesticides — to
the in-house laboratory. External certificates exist for most of it:

| certificate | on file, not yet on the page |
| --- | --- |
| 005 HPA1024 | IPH 587/1066/25 (microbiology) · IPH 2995/2025 (metals, pesticides, mycotoxins) · CNP ППК25155 (assays, loss on drying, Ident C) |
| 006 OPM1024 | IPH 2156/2025 (microbiology, metals, pesticides, mycotoxins) · CNP ППК25117 (assays, loss on drying, Ident C) |
| 025 BSS052501 | IPH 1157/2058/25 · IPH 5661/2025 · Farmahem 276-31-М/25 — no CNP certificate for Identification C |
| 026 GP062501 | CNP ППК26036, but that is a **stability timepoint** (month 3, 25 °C / 60 % RH), not the release test |

Five of these are page-verified reads already held in `review/` and can be transcribed onto
the certificates on your word. `025` and `026` cannot be closed for Identification C without
a release certificate.

## 3 · Seventeen lots with no certificate on file for a whole panel

`CoQ-PP_26-004, 009, 019, 021, 031, 046, 050, 052, 058, 068, 070, 071, 072, 073, 074, 082,
084, 166, 167`. On `021` a page read exists for every panel (IPH 626/1127/25, IPH 3177/2025,
CNP ППК25176) and it can be closed. On `004` the assays and Identification C are on
CNP ППК25104. **The rest have nothing on file at all** — eleven lots with no external
certificate in the receipt register, which is a document-supply question rather than a
transcription one.

Nothing was invented on any of the 89. Where no certificate exists the cell stays empty and
the certificate is named above.

---

# Tranche 3 — 30 retest certificates of quality and 30 internal certificates

| | |
| --- | --- |
| `CoQ_retest_T3/` | 30 certificates of quality |
| `iCoA_retest_T3/` | 30 internal certificates, numbered alike |

All 30 pairs print side by side. **Twenty-five of the 30 read exactly as the ruling sets it
out**; five carry something to settle, and all five are the same upstream gap:

| certificate | what is open |
| --- | --- |
| CoQ-PP_26-138 | heavy metals, pesticides, loss on drying — no document on the initial to carry |
| CoQ-PP_26-149 | mycotoxins absent; loss on drying attributed in house |
| CoQ-PP_26-152 | heavy metals, pesticides, loss on drying — no document on the initial |
| CoQ-PP_26-160 | heavy metals, pesticides, loss on drying — no document on the initial |
| CoQ-PP_26-162 | heavy metals — no document on the initial |

**The Tranche 3 initial certificates are already delivered**: `CoQ_initial/` and
`iCoA_initial/` hold all 89 initial-release documents, Tranche 1, 2 and 3 together, because
the initial series is numbered as one run and not split by tranche.

---

# Everything delivered

| folder | documents |
| --- | --- |
| `CoQ_retest_T1` · `T2` · `T3` | 83 retest certificates of quality |
| `iCoA_retest_T1` · `T2` · `T3` | 83 retest internal certificates |
| `CoQ_initial` | 89 initial-release certificates of quality |
| `iCoA_initial` | 89 initial-release internal certificates |
| `ImB_Spec_T1_T2` | 39 product specifications |

**383 documents.** The full fleet is 172 certificates of quality and 172 internal
certificates — one each, numbered alike, all 172 pairs — plus the specifications.

Against the attribution ruling: **123 of the 172 certificates of quality are complete**, and
49 carry something to settle. Every one of the 49 is named in this note with what is open
and what is on file for it. Nothing was invented anywhere.

---

# The T1 and T2 retests as Word, and the HTML as a zip

| file | what is in it |
| --- | --- |
| `CoQ_retest_T1_WORD.zip` | 21 Word certificates — `COMPLETE/` 16, `OPEN_ITEM/` 5 |
| `CoQ_retest_T2_WORD.zip` | 32 Word certificates — `COMPLETE/` 26, `OPEN_ITEM/` 6 |
| `CoQ_retest_T1_T2_HTML.zip` | the same 53 as self-contained HTML, `CoQ_retest_T1/` and `CoQ_retest_T2/` |

The Word set is split by tranche only because one archive of all 53 came to 41 MB and the
delivery limit here is 30 MB. `WORD_CoQ_retest_T1_T2/` on disk holds all 53 in one place.

**The 42 that are complete are in `COMPLETE/`.** The other 11 are in `OPEN_ITEM/` rather than
held back — they are the certificates tabled earlier in this note, and you should have them
in front of you when you rule on what is missing. Nothing separates the two folders but that
table.

## How the Word file was made, and why it is the page

Certificate → PDF → Word, never HTML → Word. An HTML-to-Word writer re-flows the document:
it decides where lines break and how tall a row is, and the page that comes out is a page
nobody approved. Here the printed page is the page — its graphics are one anchored image
behind the text, and every text span is a real Word run positioned at the PDF's own
coordinates, with the house faces embedded.

Converted back to PDF and measured against the original, run by run, on 208 runs:

| | median | p95 | max |
| --- | ---: | ---: | ---: |
| left edge | 0.010 pt | 0.023 | **0.025 pt** |
| top edge | 0.012 pt | 0.027 | **0.047 pt** |

A point is a third of a millimetre, so every run starts within a hundredth of one. The one
larger figure in the report is the footer page number `1 | 1`, whose measured **right** edge
moves 8.55 pt — it starts in exactly the right place (+0.01, −0.03) and only its trailing
advance differs. That is not new: the same measurement on the issued `SIGNED_2026-09-21`
certificate gives the identical numbers, to three decimals.

Checked on all 53 Word files: each opens as a valid document, carries its page as an image
and its text as positioned runs, embeds the house type, is one page, and names its own
certificate number, lot and internal certificate.

## The HTML zip

The same 53 files already in `CoQ_retest_T1/` and `CoQ_retest_T2/`. Each opens in Word from
the desktop with nothing fetched from anywhere — no script, no stylesheet, no font, no image
off the machine.
