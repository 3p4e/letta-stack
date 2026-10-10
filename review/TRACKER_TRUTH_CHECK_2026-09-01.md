# Truth check — `CoQ_Analysis_Master_v2.xlsx` against the desk's verified data

**Subject.** The owner's tracker workbook in Drive (`1NPq8O3Q60qvTw3469np43RF5k8wkU0Fx`,
title `CoQ_Analysis_Master_v2.xlsx`, four tabs, last modified 01.09.2026 15:22), with the
CU-batch / P-batch column pair the owner added.
**Reference.** The desk's verified data as of chain step 19: the release register
`PP_Batch_Release_QC_Register_SUBLOT_2026-09-01.xlsx`, the CoQ schedule (164 CoQs,
3 772 determination rows), the eCoA receipt register (248 documents, 233 page-verified),
the 227 page reads of 31.08.2026, and the ingested corpus (`all_cert_texts.json`, 291
documents with their page text).
**Method.** Every cell of the tracker's four tabs was parsed and matched to the desk on
a folded key — Cyrillic homoglyphs, `-`/`/` separators, the Farmahem `ГС`/`LoD` naming
and the glued sub-lot digit all folded away — so that only real disagreements remain.
Where the tracker and the desk disagree, the certificate's own page text decides.

## The verdict in one paragraph

The tracker is **right where the desk was wrong**, and **wrong where it reads
identification into certificates that do not carry it.** It correctly lists 21
outsourced certificates — the whole IPH chemical-safety and microbiology campaign of
28–30.04.2026 for nine batches, plus four IPH certificates from 2025 — that the release
register never received and the desk therefore never showed. It also correctly credits
the three in-house Reports of Analysis of 23.04.2025 with appearance and foreign matter.
Against that, it ticks Identification B on 60 certificates that report only THC, CBD and
loss on drying; ticks CBN on 55 certificates that do not report CBN;
and ticks loss on drying on 35 Farmahem cannabinoid certificates whose LoD sits on a
separate certificate. Its summary dashboard inherits all of that. The `1_` codes are
the batch's own sub-lot digit, glued on by the first-underscore split of the Drive
filename; seven certificates are affected in the tracker, none in the desk — but the
same split had cost the desk the `/1` on batch FB012601, now corrected.

## A. What the tracker gets right — real gaps in the desk

### A1. Twenty-one outsourced certificates the release register never received

Each of these exists in the ingested corpus with its page text (laboratory number, batch,
dates), is listed in the tracker's document index, and is absent from the release
register — so the desk shows the batch as never tested for those determinations.

| Laboratory · determinations | Certificate | Date | Batch (as the page prints it) |
|---|---|---|---|
| IPH chemical safety — Pb/Cd/As/Hg, aflatoxins, ochratoxin A, pesticides | `2357/2026` | 29.04.2026 | FB112501 |
| | `2358/2026` | 29.04.2026 | GG112501 |
| | `2359/2026` | 29.04.2026 | CC112501 |
| | `2360/2026` | 29.04.2026 | SCR112501 |
| | `2361/2026` | 30.04.2026 | JD112501 |
| | `2362/2026` | 30.04.2026 | FB012601/1 |
| | `2363/2026` | 30.04.2026 | JD012601* |
| | `2364/2026` | 30.04.2026 | GG012601* |
| | `2365/2026` | 30.04.2026 | JD112501* |
| IPH microbiology — TAMC, TYMC, bile-tolerant GNB, Salmonella, E. coli | `304/0548/26` | 28.04.2026 | GG112501 |
| | `306/0550/26` | 28.04.2026 | JD112501* |
| | `307/0551/26` | 28.04.2026 | JD112501 |
| | `308/0552/26` | 28.04.2026 | FB012601/1 |
| | `309/0553/26` | 28.04.2026 | JD012601* |
| | `310/0554/26` | 28.04.2026 | GG012601* |
| | `311/0555/26` | 28.04.2026 | CC112501 |
| | `312/0556/26` | 28.04.2026 | FB112501 |
| IPH, 2025 | `2471/2025` (chemical safety) | 30.05.2025 | P050022 — GP0824_02 |
| | `471/0862/25` (microbiology) | 22.05.2025 | P050022 — GP0824_02 |
| | `407/0745/25` (microbiology) | 05.05.2025 | P050042 — OPM1024_01 |
| | `319/0586/25` (microbiology) | 14.04.2025 | P050102 — GP0824_01 |

Two remarks. The asterisk on `GG012601*`, `JD012601*` and `JD112501*` is **printed on the
certificate itself** (the IPH microbiology page reads `Серија: JD112501*`) — these are
distinct samples the laboratory labelled that way, and `JD112501` and `JD112501*` each
have their own pair of certificates. The desk carries only the plain batch. And
`319/0586/25` is not the certificate the chain moved on row 26 — that row's code was
corrected *from* `319/0586/25` *to* `318/0585/25` because the page read `318/0585/25`;
`319/0586/25` is a second, separate certificate for lot P050102, and it was read off its
own page on 31.08.2026 (`microbiology_page_reads_2026-08-31.json`) without a register
row to land on. That is the "stale page-read key" noted in the after-intervention review,
now explained.

**Twelve batches** are affected. For CC112501, FB112501, GG112501, SCR112501, JD112501,
FB012601/1, GG012601*, JD012601* and JD112501* the desk currently reports "no
microbiology, no heavy metals, no pesticides, no mycotoxins" where the certificates are on
file. This is the single most consequential finding of the check.

**Not done here.** These 21 certificates are *not* written into the release register by
this check. A certificate enters the release register as a QC act performed against the
document — code, date, laboratory and the results — and the results have not been read
off these pages; the corpus text is the extraction layer, not a page read. The list above
is the work order; the receipt register and the desk will carry them the moment the rows
exist.

### A2. The three in-house Reports of Analysis of 23.04.2025

`GG1024`, `HPA1024` and `OPM1024` each have a Purely Plant *Report of Analysis* dated
23.04.2025 (signed Head of QC), carrying Appearance — Confirms (visual), Identification —
Confirms (HPLC retention time), Foreign matter — Confirms (Ph. Eur. 2.8.2), assay, CBN,
mycotoxins, pesticides, heavy metals and microbiology, the outsourced determinations
"tested in accredited laboratories". The tracker credits **#1 Identification A** and
**#7 Foreign matter** from them. It is right: the report states both. The desk credits the
same report for #4, #5, #9, #10.2, #11 and #12 on HPA1024 and OPM1024 but not for #1 or
#7, and GG1024 has no register row at all (open decision B6). The desk under-credits
here; the tracker does not.

### A3. P-numbers

The owner's new column pairs every CU batch with its P batch. Of the 74 pairs, **40 are
confirmed by the potency master, none is contradicted, and 34 cannot be checked** from
anything the desk holds — the potency master covers only the 48 plan lots. The desk's
register carries no P-number for most 2025–2026 batches, so on this column the tracker
carries information the desk lacks. Three rows carry a P-number with the CU batch marked
"NOT ASSIGNED" (`P160012`, `P160022`, `P160032`); the desk keys those three CNP
certificates (ППК26117–26119) to the P-lots directly, under GG012603.

## B. Where the tracker is wrong

### B1. Identification B — 60 false ticks

The tracker ticks #2 on 69 citations. **Sixty of them cite a CNP release form**
(ППК25050, ППК25051, ППК26068, ППК25052, ППК26067 …) whose results table carries
Total THC, Total CBD and loss on drying — and nothing else. Only the **twelve CNP full
Ph. Eur. forms** (ППК26110–26119, ППК26127, ППК26128) print Идентификација
(Макроскопија · Микроскопија) and Страни материи; the desk credits exactly those twelve
with Identification A + B and foreign matter, and no others. The tracker's #2 column
label ("Macroscopy … (microscopy)") also conflates the two: in the specification #1 is
Identification A, appearance · macroscopic, and #2 is Identification B · microscopic.

### B2. Identification C — the tracker's 104 ticks stand, under the ruling of 02.09.2026

The first pass of this check called all 104 #3 ticks wrong, on the ground that no
certificate prints an Identification C result and no laboratory has performed a
dedicated TLC/HPTLC identification. The owner ruled otherwise on 02.09.2026, on a
certificate basis: a Farmahem `-K-` report declares *идентификација и квантификација
на канабиноиди* by accredited HPLC/DAD against Ph. Eur. 3028 and states the analyte
concentrations, which shows detection, identification and quantification of the API;
a CNP form determines the cannabinoid content by Ph. Eur. 2.2.29. Both discharge
Identification C. **Every one of the tracker's 104 citations is such a certificate,
so every one is right** — and the desk was the one under-crediting. The CoQ's
Identification C row now cites the same certificate as its Total Δ⁹-THC assay row,
the receipt register reports Ident C on every HPLC cannabinoid certificate, and no
batch owes an in-house Identification C document. The dashboard's "#3 — 1 % missing"
is therefore broadly right (on the desk: 0 of 81).

### B3. CBN — 55 false ticks

The tracker ticks #6 on 108 citations. **Fifty-five cite a CNP release form**, which does
not report CBN (see B1). The 49 that cite a Farmahem `-K-` certificate are right — CBN is
on those pages (and the desk holds them page-verified).

### B4. Loss on drying — 35 false ticks

The tracker ticks #8 on 108 citations. **Thirty-five cite a Farmahem `-K-` cannabinoid
certificate**, which does not report loss on drying — Farmahem issues LoD on a separate
`-ГС-` (`-LoD-`) certificate, which the tracker's own document index lists correctly.
The 69 CNP citations are right (the CNP form does report LoD).

### B5. Identification A and foreign matter — under-credited on the CNP full forms

Seven batches hold a CNP full form that prints identification and foreign matter, and the
tracker marks #1 ✗ on all seven and #7 ✗ on six: FB012603 (ППК26112), FB012603V
(ППК26110), FB032601 (ППК26127), GG012603 (ППК26114), GG032601 (ППК26128), JD022601
(ППК26115), SCR022601 (ППК26116). It also marks #2 ✗ on GG012603 (ППК26114), which
prints it.

### B6. The summary dashboard

Because the dashboard is computed from the ticks above, its frequencies are wrong in the
same directions: #2 "23 % missing" (in truth 69 of 81 lack an Identification B
certificate), #6 "1 % missing" (overstated; CBN exists only
where a Farmahem `-K-` or an in-house certificate exists), #8 "1 % missing" (overstated
by the 35 `-K-` citations). Its "Total eCOA documents 253 (QCCoA 001 excluded)" is
consistent with the desk's 248 receipts once the 21 register-absent certificates and the
three Reports of Analysis are counted in and the desk's 24 in-house / UKIM `PP CoA #0xx`
receipts, which the tracker does not index, are counted out.

### B7. Batch identity

| Tracker | Finding |
|---|---|
| `OMP1024_01` | Typo for `OPM1024_01` (Orange Peel Mimosa); its three certificates are the desk's `OPM1024/1`. |
| `SJ0925021` | Typo for `SJ092501`; its three certificates are the desk's. |
| `BSS1024_01/1` | A nested index no certificate prints — ППК25176, 3177/2025 and 626/1127/25 are all `BSS1024_01` on the page. |
| `FB012602*`, `GG012601＊`, `JD012601＊`, `JD112501＊` | Real, distinct samples — the laboratory prints the asterisk (A1). The desk holds `FB012602` via lot P060352 and the others only as the plain batch. |
| `GRC102501` → two P-numbers; `JD012603` → three | The tracker merges sub-lots onto one CU row (`GRC102501_2`; `JD012603_01/_02/_02V`) where the desk keeps them separate, as the identity rule requires. |
| `FB012601` | The batch is `FB012601/1` — see C. |

## C. The `1_` codes — the owner is right, and the desk had the mirror defect

The Drive filename convention is `‹batch›_‹code›, ‹date›_‹lab›.pdf`. Where the batch
carries a sub-lot index, a split at the first underscore hands the index to the code:

| Filename | Tracker code | Correct code | Correct batch |
|---|---|---|---|
| `FB012601_1_ППК26067, 11.05.2026_CNP.pdf` | `1_ППК26067` | `ППК26067` | `FB012601/1` |
| `FB012601_1_2362-2026, 30.04.2026_IJZ.pdf` | `1_2362-2026` | `2362/2026` | `FB012601/1` |
| `FB012601_1_308-0552-26, 28.04.2026_IJZ-MB.pdf` | `1_308-0552-26` | `308/0552/26` | `FB012601/1` |
| `GRC102501_2_051-6-LoD-26, 02.03.2026_FHM.pdf` | `2_051-6-LoD-26` | `051-6-ГС/26` | `GRC102501/2` |
| `GRC102501_2_051-6-K-26, 04.03.2026_FHM.pdf` | `2_051-6-K-26` | `051-6-К/26` | `GRC102501/2` |
| `JD012603_02_ППК26113, 30.06.2026_CNP.pdf` | `02_ППК26113` | `ППК26113` | `JD012603/2` |
| `JD012603_02V_ППК26111, 30.06.2026_CNP.pdf` | `02V_ППК26111` | `ППК26111` | `JD012603/2V` |
| `P050192_10802_2845-2 MK, 17.11.2025_DFL.pdf` | `10802_2845-2 MK` | `10802_2845/2` — **correct as is**: the State Phytosanitary code itself contains the underscore | `BSS052501` |

Seven certificates, three batches. **No certificate in the desk, the registers, the
corpus or the repository's history carries a glued digit** — an exhaustive scan of every
JSON payload, every workbook cell and every parser confirmed it. What the desk had was the
other half of the same split: register ref 53 read `FB012601` where every document prints
`FB012601/1`. Under the identity rule the index nests and carries meaning, so the bare row
could never join the plan's `FB012601/1`: the CoQ schedule was inventing a second,
predicted CoQ pair for a batch that already had one, and the two IPH certificates filed
under `FB012601_1` had no row to attach to.

**Applied today, on the owner's ruling that the digit is part of the batch number:**

- **Chain step 19** (`apply_fb012601_sublot.py` → `PP_Batch_Release_QC_Register_SUBLOT_2026-09-01.xlsx`): register ref 53 and the per-strain sheet read `FB012601/1`; the 19-step chain replays exactly from the owner's original. The gap-analysis row 53 follows. The CoQ schedule drops from 166 to **164** documents and the iCoA plan from 224 to **221** — the phantom pair is gone. The two IPH certificates are still not in the register (A1).
- `render_iph_certificates.py` no longer splits at the first underscore — it tries every split and keeps the one whose right-hand side is a known code, as the Farmahem and CNP renderers already did. It was the one live producer of a `1_…` code, and it had been silently dropping `FB012601_1_2362-2026` from the page-verification render.
- `rectify_ecoa_receipts.py` keys its batch fallback through `batch_key`, so `FB012601_1` in the corpus and `FB012601/1` in the register join.
- Not edited, recorded: `deliverables/qc_register/consolidate.py` keys batches on a raw string (`FB0126011`) — that deliverable is superseded. `ingest_coa_database_2026.py` chooses its split rule by laboratory (first underscore for DFL) rather than by which side is a known code; correct for every file it has seen, fragile for the first DFL certificate on a sub-lot batch.

## D. What this does not settle

- The 21 certificates in A1 need to enter the release register as a QC act — code, date,
  laboratory, results — read off the pages. The 2026 IPH pages render cleanly and the
  render pipeline is fixed; this is roughly a day of page reads.
- `GG1024` still has no register row (B6), so its Report of Analysis has nowhere to land.
- The 41 `QCCoA 001v02` in-house CoAs and whether they discharge Identification A and
  foreign matter (the 69 → 37 + 32 split) remain the standing open ruling; the tracker
  excludes those files outright.
- The 34 P-numbers the potency master does not cover are the owner's to confirm; nothing
  the desk holds contradicts them.
