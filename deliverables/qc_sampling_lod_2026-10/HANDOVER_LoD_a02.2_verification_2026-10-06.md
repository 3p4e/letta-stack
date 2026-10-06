# HANDOVER — verification of the loss-on-drying method a02.2 (Ph. Eur. 2.2.32, monograph 3028)

From the T1/T2 sampling chat (PP-QC-SP-002/26), 06.10.2026. Purely Plant QC, dry cannabis flower.
That chat only samples and runs LoD to get results before Tranches 1 and 2 ship. Method
verification is yours. Codes: **a02.2** = vacuum-oven LoD (primary, compendial); **SAM_a02.1** = halogen
moisture analyser (HMA, alternative). Correction to the prompt sent on 05.10.2026: it called the oven
method "SAM_a02.2" at "15–25 mbar"; the method documents say a02.2, 20 ± 2 mbar, over molecular sieve R,
cooling at least 30 min, symbols m_B / m₀ / m₁ (section 2).

## 1. What the pharmacopoeia requires

**Monograph 3028 Cannabis flos, Ph. Eur. 11.5 (07/2024:3028), p. 5911**, verbatim from the PDF on Drive
(`Ph.Eur. 11.5 Monograph 3028 Cannabis flos..pdf`, id `1YC2RTrylhQacKNuG8G1axf3YOgov_A-L`):

> Loss on drying (2.2.32): maximum 12.0 per cent, determined on 1.000 g of the cut or milled herbal drug
> (not sieved) by drying over about 100 g of molecular sieve R at a pressure between 1.5 kPa and 2.5 kPa at
> 40 °C for 24 h.

Also in the monograph: storage "in an airtight container"; the same "cut or milled herbal drug (not
sieved)" preparation is used for identification C and the CBN/assay test solutions.

**Ph. Eur. 2.2.32** (not in the Drive set I saw; confirm against the controlled text): loss on drying is
the loss of mass in per cent m/m; the substance goes into a weighing bottle previously dried under the
prescribed conditions and is dried "to constant mass or for the prescribed time".
**General Notices, constant mass**: two consecutive weighings differ by not more than 0.5 mg, the second
after an additional period of drying (confirm wording).

**Consequence to decide.** The monograph prescribes a time (24 h), so the compendial result is the 24 h
value. The site documents use constant mass (Δ ≤ 0.5 mg) as SST/endpoint (AMVP §4, §6; AMVR §3). Either
report the 24 h value and use the further weighing as a check, or dry to constant mass as a documented
site tightening. They differ: on 14–15.07.2026 mass was still falling between +21 h and +24 h in all 7
samples checked (mean +0.366 percentage points; corrected draft record, see section 4).

Other Ph. Eur. texts in play: 2.1.7 (balances), 2.5.12 / 2.5.32 (water, Karl Fischer, orthogonal check),
2.8.20 (herbal drugs: sampling and sample preparation).

## 2. The site method as documented (a02.2)

| Item | Value |
|---|---|
| Governing SOP | QCSOP 009 v1.0 (pathway §6.4(a) compendial → site verification; §6.6 minimum parameters; §6.8 uncertainty; §6.1, §6.10 lifecycle and 12-month review; §6.11 revalidation triggers) |
| Records | QCSOP009_A02 register · A03 outsourced correlation matrix · A04 verification checklist · A05 revalidation trigger; STPa02 |
| Oven | vacuum oven VO29 (QCWI 018, logbook QCLB 017): 40 °C, 20 ± 2 mbar (≈ 2.0 kPa), 24 h, over about 100 g molecular sieve R |
| Balance | Shimadzu AUW220D (QCWI 016, logbook QCLB 008), 220 g / 82 g, d = 0.1 / 0.01 mg, OIML E2 traceability |
| Desiccator | with active desiccant; cool at least 30 min before weighing |
| Procedure (AMVP §6) | tare bottle → m_B; add 1.000 g → G1; m₀ = G1 − m_B; dry; cool; weigh G2; m₁ = G2 − m_B; LoD % = (m₀ − m₁) ÷ m₀ × 100; confirm Δ ≤ 0.5 mg |

## 3. Verification package (all v1.0, dates "__/__/2026", unsigned)

Drive folder `PurelyPlant_AM_a02.2_DryingOven-LoD` (`12gqaRoiEeDbI9JGiTFAQUYetFWWgkEMX`; copy
`1E1XY0yiBPhMYhS1cjJzvn7AjN6hESyy7`): 01_AMRRF-a02.2-001-2026 (not reviewed) · 02_AMSF PROVISIONAL ·
03_AMVP-a02.2-001-2026 (`1wO0ReRHrDOYRhHdVTOmMeqt4ptgFKJT-`) · 04_AMVR-a02.2-001-2026
(`1_Ug9D4oo_zu7moxLFtnajkE5lWuw2VIx`) · 05_QCSOP009_A04-a02.2-001-2026 (`18tXMU5ijr60IT7piiG9_-V4Fe2J2boK9`)
· 06_AMSF-a02.2 VERIFIED (`18GHEHoGLRzT8rah3fLANY4T5giofW-Tg`). QCSOP 009 itself:
`11PX8OmYcji9XCFWdjUeT7c5bSsFLgQZ1` (29.07.2026). Signatories: prepared/approved B. Nikolov, M.Pharm.;
reviewed J. Romevska (QA); AMVP/AMVR approved (Site/GM) Z. Keskovski.

**§6.6 criteria (AMVP §5):** repeatability RSD ≤ 2.0 % (n ≥ 6) at the working concentration (~12 % MC);
HorRat_r ≤ 2.0 per level across the range (≥ 6 determinations × ≥ 5 levels); intermediate precision
RSD_iP ≤ 2.0 % at working concentration (≤ 3.0 % across the range); accuracy inherent from the calibrated
balance; constant mass Δ ≤ 0.5 mg; U (k = 2) < ⅓ of the spec range; specificity and linearity not
applicable.

**Data (batch CJ072501, 28.10–27.11.2025, % loss):**

| Level | Date | n | Mean | SD | RSDr % | HorRat_r | Verdict |
|---|---|---|---|---|---|---|---|
| R1 | 28.10.2025 | 8 | 61.42 | 0.5955 | 0.97 | 0.68 | pass |
| R2 | 29.10.2025 | 9 | 35.47 | 0.7163 | 2.02 | 1.31 | pass |
| R3 | 30.10.2025 | 8 | 18.05 | 0.1786 | 0.99 | 0.58 | pass |
| R4 | 03.11.2025 | 10 | 6.37 | 0.1748 | 2.75 | 1.37 | pass |
| R5 | 27.11.2025 | 10 | 2.14 | 0.2192 | 10.26 | 4.36 | fail |

Pooled RSD_iP 1.92 % (R1–R4), 5.15 % with R5. Uncertainty: top-down u_c = 1.92 % rel, U (k = 2) =
3.83 % rel = ± 0.46 % at 12.0 %; bottom-up (u_Rw; u_cal 0.115 mg/m₀ provisional; u_dry 0.289 mg/m₀)
converges. Decision rule (ISO/IEC 17025 §7.8.6): pass ≤ 11.54 %, fail ≥ 12.46 %. Verified range about
6–61 %; below about 3 % report "< 3 %" or replicate more. AMSF status VERIFIED = internal QC / IPQC /
trending, not batch release (release via accredited external laboratory, §6.6, §6.9).

## 4. Gaps and inconsistencies found

1. **No level near the 12.0 % limit.** Levels sit at 2.1, 6.4, 18.0, 35.5 and 61.4 %. The n ≥ 6 series at
   ~12 % (AMVP form "NEW for §6.6") is not executed; A04 marks repeatability met through the pooled value.
2. **Intermediate precision** is one occasion per level, so 1.92 % is pooled across occasions, not a
   crossed day × analyst estimate (AMVR §6 design note). Analyst names are blank.
3. **Accuracy**: bias provisionally 0; Karl Fischer (2.5.32) on the matrix pending; no hydrate CRM is valid
   at 40 °C (sodium tartrate dihydrate releases at ~150 °C); AUW220D calibration certificate and VO29
   IQ/OQ/PQ not entered (u_cal provisional).
4. **Endpoint**: AMSF/A04 say "constant-mass endpoint confirmed"; the routine data of July show mass still
   falling at 24 h (section 1). The monograph is a fixed 24 h.
5. **Raw masses**: the AMVR holds % values only. Raw data likely in `PPlant MV a02.2.xlsx`
   (`1nP06mR6CndNGdTc6roWyoMefKNTjuira`, never opened); HMA/oven pairs in `PPlant MV_SAM (1).xlsx`
   (`1Ab0yr4Y503ieuHMx6wlV_l_sztAsLkoS`).
6. **Routine records**: `AM02.1-R01_Moisture_Record AM02.2` (16.07.2026, `1v8AXjiYZ3yrC3p7JsYFH5mdbM82A31pF`)
   has no document code and percentages only. Its corrected draft (`DRAFT_R01_Moisture_Record`, Google Doc
   `1RnuD-_UCdmvid6tkww9IFZ61ldj7ZHF-MVvyi3gfPSY`, 21.08.2026) found: GG1024_01 without an oven value; mass
   still falling 21 → 24 h; workbook `AM02.1_&_AM02.2_Analysis.xlsx` divides by a hard-coded N = 13 for 15
   samples (mean 10.554 / SD 2.511 wrong, correct 9.146 / 1.812); HMA display truncation up to 0.15 pp.
7. **Housekeeping**: the a02.2 documents carry the copied header "PP-QC-AMVR-a02.1-001/2025"; the final
   code (a02 vs a02.2) awaits ratification in QCSOP009_A02.

## 5. HMA (SAM_a02.1) against the oven, for the correlation work

- Paired 2025 levels (HMA mean → oven mean): 3.21 → 2.14 · 8.55 → 6.37 · 19.51 → 18.05 · 37.84 → 35.47 ·
  62.64 → 61.42. Fit on the five means: oven % = 1.00095 × HMA % − 1.68774 (r² 0.9994). The a02.1 AMVR
  gives oven = 0.9913 × HMA − 1.5424 (r 0.99713), bias +1.759 % (1.077–2.369); status CHARACTERISED,
  IPQC only.
- Routine pairs 14–15.07.2026, 15 T1 lots, oven at 24 h: HMA − oven mean +1.467 pp, SD 0.412, range
  +0.43 to +1.94.
- No paired level between 6.4 and 18 % oven LoD: the product range around the 12 % limit is interpolated.

## 6. What the T1/T2 LoD campaign can give you (PP-QC-SP-002/26, record LOD-01)

- As executed (Head of QC, 06.10.2026): 46 lots, one bag opened per lot and one sample from it, all
  sampled on one day; one test portion of 1.000 g per lot, cut, 46 portions dried together in one oven
  run. There are **no replicates**: the campaign gives one determination per lot, so no within-lot
  precision. The draft of 05.10.2026 (composites from 1.5·√N bags, k = 1/2/3, 88 portions, two days) was
  not executed.
- Expected range: certificate values on record 5.6–8.6 % (40 lots); July in-house 24 h values up to 12.3 %.
  Lots near the limit in July, all in T1: OPM1024_02 12.27 %, GP0824_02 11.90 %, CJ052501/01 11.30 %,
  HPA1024_01 10.89 %.
- Every portion records m_B, G1, G2 at 24 h, the next G2 and Δ; extra weighings until Δ ≤ 0.5 mg go in a
  further-weighings table with date and time; oven-in and weighing times are recorded per run. Each
  portion therefore gives both the 24 h value and the constant-mass value, on VO29 and the AUW220D.
- The sample remainder is kept closed and labelled until the record is approved, so HMA or Karl Fischer
  pairing on the same material is possible.
- The campaign adds no verification design. Anything you need from it (e.g. n ≥ 6 portions from one
  sample remainder near 12 %, HMA duplicates per remainder, KF on a subset) must reach the sampling chat
  before the record is approved; it would be a separate run on the remainders, since the oven run
  of 06.10.2026 is already under way.
- Files: GitHub `3p4e/letta-stack`, branch `claude/google-drive-links-d932ku`,
  `deliverables/qc_sampling_lod_2026-10/` (plan, `SAMPLING_PLAN_T1_T2_2026-10.tsv`, the LoD record in
  `out/3_LOD_ANALYSIS_EXECUTION/`).

## 7. Decisions for the verification chat

1. Endpoint: compendial 24 h, or constant mass after 24 h as a site tightening, and the additional drying
   period (the sampling plan leaves it open).
2. The n ≥ 6 series at ~12 %: run it on a campaign sample remainder near the limit, or separately.
3. Intermediate precision with a crossed day × analyst design.
4. Bias: Karl Fischer (2.5.32) on the matrix; equipment qualification and calibration entries.
5. Status and use of results: VERIFIED (internal QC) vs release use, given that the T1/T2 results are
   wanted before shipment.
