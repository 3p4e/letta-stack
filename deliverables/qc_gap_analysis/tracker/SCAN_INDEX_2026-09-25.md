# The 46 approved scans, read once — Head of QC, 25.09.2026

## The ruling

> *"the latest and current scans of the certificates of quality … with their correct document codes,
> their correct data issuing, their superseded document codes, and the internal certificates of
> analysis that are referenced inside each of the certificates of quality — so everything you do in
> the future regarding anything else you will build it upon the information and data contained into
> this folder."*

And, in the same breath, the reason an index exists at all:

> *"why don't you make an index file that contains everything that contains in the documents … which
> are scanned image PDFs … you won't spend that much tokens for vision model to OCR, you will have
> them in a spreadsheet table. Make this rule."*

He is right about the cost, and right that it had already been paid. The 46 scans **were** read on
24.09, across four separate passes, and the readings were sitting in four different files. Nothing
told the next session they existed, so the next session's instinct would have been to open the scans
again. That is the waste the rule removes.

## What was built

| | |
| --- | --- |
| `tracker/SCAN_INDEX_2026-09-25.tsv` | the index — 46 rows, 26 columns |
| `tracker/SCAN_INDEX_2026-09-25.xlsx` | the same as a spreadsheet, filterable, the finding highlighted |
| [the same as a live Google Sheet](https://docs.google.com/spreadsheets/d/1PqQ_59JGwXqqWDWFrCBGFpyHW-I8uaTa7jui7U60PfM/edit) | in the scan folder itself, so it needs neither the repository nor a download |
| `tracker/DRIVE_SCAN_MANIFEST_2026-09-25.tsv` | batch → Drive file id, so any row traces to its scan |
| `tracker/build_scan_index.py` | rebuilds the index from committed sources — **opens no scan** |
| `tracker/scan_index_xlsx.py` | renders the spreadsheet |
| `CLAUDE.md` | the rule itself, at the repository root, where there was none |

It joins the four passes of 24.09 — the drive listing, the internal-certificate list, the phenotype
reading and the distributed-figure reading — and adds the Drive file id. **No scan was opened to build
it.** The builder refuses rather than guess: every batch must join on every source, or it names the
ones that do not and writes nothing.

One filename needed reconciling: the scan is uploaded as `P05022 (1).pdf`, five digits where the
register writes six. It normalises to `P005022`, which is the key the listing already carried, so the
join is exact rather than assumed.

## What the index holds per scan

The current certificate code and its issue date; the **superseded** code it replaces and that
document's date; the internal certificate cited and its date; the parameters credited to that
internal certificate, both as numbers and as the words the scan prints; the phenotype and any split;
the figures the scan reports — total THC, loss on drying, TAMC, TYMC, Pb, Cd, As, Hg; the Drive file
id; and a note where the scan does something unusual.

Three of those notes matter and are now visible without opening anything:

- **`P060402`, `P060412`** — no internal-certificate row at all; the whole set is credited to CNP.
- **`P060362`** — foreign matter credited to CNP, so its internal certificate carries `1, 2` only.
- **`P050192`** — the one scan that cites **two** internal certificates,
  `iCoA-PP_26-122 + iCoA-PP_26-023`, the second an *initial* certificate, and credits loss on drying.

## The finding: all 46 scans disagree with the register

| | |
| --- | ---: |
| scans indexed | **46** |
| cited internal certificate **agrees** with the register | **0** |
| **disagrees** | **46** |

### Correction, 25.09 — the offset is *not* systematic

I first reported this offset as *"systematic, +13 or +14, never random"*, from a five-row sample.
Computed over all 44 citing scans it is **nine distinct offsets spanning +2 to +35**:

| offset | +2 | +11 | +12 | **+13** | **+14** | +15 | +16 | +17 | +35 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| scans | 1 | 3 | 3 | **13** | **14** | 2 | 2 | 5 | 1 |

`+13/+14` is 27 of 44 — the bulk, but not the rule. `P050212` is `+2` and `P060372` is `+35`. The
audit of 24.09 had already recorded it correctly as *"offset +2 to +17, not correctable by
arithmetic"*, and my sample contradicted its own source.

**The consequence is the opposite of what the first wording implied.** A single offset would have
meant one permutation could repair every citation. Nine offsets mean there is no arithmetic repair at
all: each pair resolves only from its own scan. That is why this is a ruling to be asked for and not
a script to be run.

The bulk case, for illustration only:

| batch | certificate of quality | the scan cites | the register says |
| --- | --- | --- | --- |
| BG1024 | `CoQ-PP_26-085` | `iCoA-PP_26-098` | `iCoA-PP_26-085` |
| HPA1024 | `CoQ-PP_26-097` | `iCoA-PP_26-110` | `iCoA-PP_26-097` |
| OPM1024 | `CoQ-PP_26-101` | `iCoA-PP_26-114` | `iCoA-PP_26-101` |
| GG1024 | `CoQ-PP_26-115` | `iCoA-PP_26-129` | `iCoA-PP_26-115` |
| P050042 | `CoQ-PP_26-128` | `iCoA-PP_26-142` | `iCoA-PP_26-128` |

This is the register's own rule showing through: **WP-A** set the internal-certificate number equal to
the certificate-of-quality number across all 172 pairs. Every approved scan says otherwise. The
ruling of 25.09 settles which governs — the scans do — so WP-A holds only where no scan speaks, and
for these 46 batches the register is what needs correcting.

**Nothing already delivered is wrong.** The 44 certificates with him were built from the scans' cited
numbers, which is exactly why `iCoA-PP_26-110` carries HPA1024 and `-114` carries OPM1024 rather than
`-097` and `-101`. The open question is the wider 172-pair numbering, not the delivered set, and it
is put to him rather than resolved here.
