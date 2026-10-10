# The Tranche 3 mycotoxin re-analysis, read and taken in — 16.09.2026

Thirty Farmahem reports, `227-1-М/26` … `227-30-М/26`, issued 16.09.2026: received
24.08.2026, analysed 15.09.2026, method ИР 7.2.1-43М / 7.2.1-44М (в.03), accredited to
МКС EN ISO/IEC 17025:2018. They are the documents thirty Tranche 3 certificates had been
waiting on — #10.1 and #10.3 printed *"awaiting the mycotoxin re-analysis — Farmahem"* on
every one of them.

## No pipeline was needed, and none was used

The Head of QC asked whether this could go through the RAGFlow container on the KVM server
using the Kimi / Moonshot models, since the Anthropic credit is spent. Two findings:

* **The Moonshot keys in this environment are rejected.** `MOONSHOT_API_KEY`,
  `KIMI_CODE_API_KEY` and `MODERATO_MOONSHOT_API_KEY` each return
  `{"error":{"message":"Incorrect API key provided","type":"incorrect_api_key_error"}}`
  from both `api.moonshot.ai` and `api.moonshot.cn`. That is the key being refused, not the
  proxy. RAGFlow itself answers (HTTP 200), but its ingestion driver has no Drive
  credentials of its own — `ingest_coa_database_2026.py` says so in its own `__main__`.
* **None of it was necessary.** These are digitally generated PDFs, not scans. The code,
  the sample number, the internal ФЛЖС number, the strain, the packaged lot and all five
  analytes come off the page verbatim through the Drive content reader, with no OCR, no
  vision model and no external API call in the path. The cost of reading thirty
  certificates this way is nil.

## Two readers, and the useful thing they disagreed about

The series was read twice and independently — by this desk and by the Head of QC — and the
two failed on **different** certificates:

| | could not extract |
| --- | --- |
| this desk (three attempts each) | `227-13`, `227-18`, `227-20`, `227-30` |
| the Head of QC (two attempts each) | `227-2`, `227-7`, `227-16`, `227-18`, `227-23`, `227-27` |

So the blank page is a property of the reader, not of the scan. The Head of QC's note that
six certificates need opening by hand is right in principle and too wide in fact: **five of
those six this desk read in full**, and their results are below. Between the two reads **29
of the 30 have been read, and no certificate is read differently by the two.**

**`227-18-М/26` (GP062501, P050202) is the one certificate nobody has read** — three
attempts here, two there. It is the only one that needs opening by hand, and #10.1 and
#10.3 stay empty on P050202 until it is. That is **OI-48**.

## What the pages say

Every one of the 29 prints **ND** — below 0.5 µg/kg — for Aflatoxin B1, B2, G1, G2 and
Ochratoxin A. Each page also prints **its own packaged lot**, so the batch mapping is
verified per certificate rather than carried across from the paired cannabinoid
certificate, which is how `_FHM_227M_REGISTER_2026-09-16.csv` had had to infer it.

Written into the release register as `O` (#10.2, total aflatoxins — written ND only
because B1, B2, G1 and G2 each are, the reading the 197-М and 220-М rows already use),
`P` (#10.1) and `Q` (#10.3).

## One document for one determination group

Taking the retest in exposed a second edge of the whole-panel rule. The carry only ever
fills an *empty* row, so fifteen certificates ended up citing Farmahem 2026 for #10.1 and
#10.3 while #10.2 still carried the lot's initial Institute panel from 2025 — three lines
apart on the same page, two laboratories, eighteen months. Assertion A15 refused it, and
rightly: a reader cannot tell which sample the group describes.

`unify_panel_source.py` states the rule — **within a determination group, where one
document the certificate already cites determined the whole group and is later than what
the other rows cite, the group cites that document.** It changes a citation, not a verdict
(`< 2` and `ND` are the same statement about the same analyte), and it never reaches for a
document the page could not already cite. 18 rows re-pointed.

## Where the set stands

| | before | after |
| --- | ---: | ---: |
| Tranche 3 — cells with no result | 135 | **66** |
| Tranche 3 — #10.1 / #10.3 empty | 30 / 30 | **1 / 1** |
| all 172 certificates | 1,129 | **1,060** |

Assertion findings 48, hard 2 — the two pre-existing OPM1024 cells of OI-45. No certificate
prints a partial panel.
