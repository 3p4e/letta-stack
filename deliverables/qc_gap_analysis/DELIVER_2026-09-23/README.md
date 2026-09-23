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
