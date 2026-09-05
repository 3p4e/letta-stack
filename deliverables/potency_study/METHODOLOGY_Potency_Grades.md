# ImB Potency Grade Design — Methodology, Mathematics and Justification

**Purely Plant DOOEL — Intermediate Bulk (ImB) Dry Cannabis Flower, THC chemotype**
Design date: 27.08.2026 · Engine: `imb_grade_design.py` · Independent audit: `check_design.py`
Data lineage: RAGflow **eCoA_DATABASE** (291 certificates, 3-layer sanity-checked) → Batch Release
QC Register (rev.5, 69/69 THC audit) → `potency_dataset.json` → this design.

---

## 1. Purpose

Every strain in the portfolio is sold as one or more **potency grades**. A grade is a named
specification window for Total Δ⁹-THC: a **nominal** strength printed in the product code
(`XX_THCnn:CBD1`) and a **range** (lower–upper, % w/w, two decimals) printed on the product
specification (`QCSP_001_XX-<grade>`). This document records how the grade set of every strain
was determined, the mathematics that fixes every bound, and the verification that the design
holds against every analysis result on file.

## 2. Inputs and the anchor policy

1. **One anchor value per batch** — the batch's **CoQ-forming** Total-THC result. Where a
   batch has been retested (the Tranche-1 197-series campaign of 07.08.2026, the April 2026
   Jokerz retests, and the **Tranche-2 re-analysis reported by Farmahem on 26.08.2026 —
   29 batches, unofficial until the formal eCoAs are filed**), the **retest value is the
   CoQ-forming result** and the grade is designed on it. Superseded pre-retest results are
   **out of specification scope** — they graded the batch once, and the retest replaced them.
   Grades anchored on the unofficial T2 values are provisional pending the certificates.
2. **Owner-requested product codes** for the 48 tranche-list batches are design constraints:
   they are honored wherever the value mathematically permits. Management revised the code
   list on 27.08.2026 against the T1+T2 re-analysis values; the solver carries that revised
   list verbatim.
3. The earlier register-audited sheet corrections (KC102501 17.04, PM112501 13.33,
   BSS052501 20.39) are all **superseded by the T2 re-analysis** (17.06, 10.79, 20.52) and
   are retired.
4. J31122501 is graded on the **machine-trimmed CoQ-forming preparation (21.84,
   CoQ-PP-2026-0054)**; the same-day hand-trimmed 19.84 is an experimental processing
   comparison (it happens to fall inside the same grade window).
5. Batches without any analysis at all (SCR012601, WED102501, GRC102501/1) enter at their
   declared values; their grades are provisional until an eCoA exists.

## 3. The rule set (management, 27.08.2026 — final revision)

R1. **Mandatory product codes**: the 48 tranche-list batches carry exactly the
    `THCnn : CBD1` codes management assigned (27.08.2026 list). The solver treats them as
    fixed constraints; a deviation is permitted only where the assigned codes are mutually
    impossible under R2–R4, is minimal (fewest batches moved), and is flagged. Uncoded
    batches take any feasible **even** nominal (the nominal is not chased after the
    analysis value); the adjacent **odd** whole number only where no even works.
R2. **Symmetric tolerance**: every grade is `nominal ± t` with the **same t above and
    below**; `t ≤ 0.10·N`; bounds carry two decimals; minimum meaningful tolerance 0.50.
R3. **No empty grades**: every grade holds at least one tested batch. Where real grades
    cannot reach each other under the 10 % cap, the result-free span between them stays a
    **documented gap** — never an empty reserve grade.
R4. **Balanced distribution**: where two grades touch, the shared budget
    `(Nₛ − N_w) − 0.01` is split as **equally** as batch containment and the 10 % cap
    allow — no grade is squeezed for the benefit of its neighbour. Grades touch wherever
    the mathematics permits; a grade facing a gap takes its maximum coverage.
R5. Every batch falls in **exactly one** grade at its anchor value (**retest
    supersession**: retest values are CoQ-forming; superseded results out of scope).
R6. Gaps carry **no results by construction**; a future result landing in a gap triggers a
    grade-set revision, not an ad-hoc stretch.

## 4. The mathematics

### 4.1 Feasibility of a nominal for a cluster

A cluster of results `[vmin, vmax]` can carry nominal `N` iff its containment requirement
`req(N) = max(N − vmin, vmax − N, 0.50)` does not exceed the cap `0.10·N`. The even
ladder's low-end dead zones (8.81–8.99 and 6.61–7.19) are the only places where no even
nominal exists for an isolated result — the odd fallback covers them (one case today:
GRC102501/1 at 7.05 → `GRC_THC7:CBD1`).

### 4.2 Grade assignment

Batches keep the owner's product codes as *cluster* membership (which batches grade
together); the cluster's *nominal* is then chosen freely per R1. Where an owner code is
arithmetically impossible for the batch's CoQ-forming value (§4.4), the batch is moved to
the nearest feasible even nominal and the deviation is flagged.

### 4.3 The symmetric budget law and the balance objective

Two grades touching at 0.01 satisfy **tₛ + t_w = (Nₛ − N_w) − 0.01** — an equality that
chains every tolerance in a touching run to one free variable. Two grades merely
*coexisting* (gap allowed) satisfy the same expression as an **inequality** (no overlap).
The solver enumerates, per strain: every feasible nominal per cluster (evens first),
every subset of junctions allowed to gap, and solves each configuration exactly —
tolerances inside a touching run are affine in the run's top tolerance, and the optimum
of the piecewise-linear balance objective lies at a breakpoint. Configurations are
ranked: (1) fewest odd nominals, (2) fewest gaps, (3) smallest total imbalance
`Σ|tₖ − tₖ₊₁|` over junctions whose windows actually touch, (4) smallest total gap
length, (5) nominals closest to the cluster centres, (6) largest total tolerance.

### 4.4 Mandatory-code feasibility and minimal deviation

Six of the 48 mandatory codes (revised 27.08.2026 against the T1+T2 re-analysis values)
are arithmetically impossible and were resolved with the smallest possible deviation,
all flagged:

- **FB012601/1**: 17.99 exceeds THC16's ceiling `1.10·16 = 17.60` → **THC18** (it lands
  at 17.99, just inside THC18's balanced window 17.15–18.85). The uncoded FB112501
  (16.69) is re-joined to THC16 so the FB ladder stays solvable.
- **GRC102501/2**: 9.80 is below THC12's floor `0.90·12 = 10.80` → **THC10** (9.00–11.00,
  full ±10 %).
- **JD012603/02**: 14.43 is far below THC20's floor 18.00 → **THC14** (13.10–14.90),
  where it grades beside JD112501* 13.93.
- **PM112501**: 10.79 misses THC12's floor `0.90·12 = 10.80` by **exactly 0.01** →
  **THC10** (9.00–11.00). The near-miss is worth an owner review: a paper value of 10.80
  would make THC12 feasible and the design re-runs in one command.
- **GP092501 (25.24) and GP082501/1 (25.13), coded THC26**: the THC26 floor they force
  needs `t₂₆ ≥ 26 − 25.13 = 0.87`, while the mandatory THC24 holding GP0824_02 (22.61)
  needs `t₂₄ ≥ 1.39`; `0.87 + 1.39 = 2.26 > 1.99`, the 26/24 no-overlap budget — the
  windows must collide whatever the split. The minimal fix regrades **both → THC24**
  (22.61–25.39), leaving THC26 (25.40–26.60) to the uncoded P160012 26.32 and
  P160022 25.72; no smaller move set (including any single-batch move) is feasible.

### 4.5 What the rules produce

Worked example — Fat Bastard (T2-revised): clusters at {20.83, 18.86} / {18.29, 17.99} /
16.69 / 12.39. **THC20 ±1.14**, **THC18 ±0.85** and **THC16 ±1.14** touch in a chain
(each 1.99 budget split as evenly as containment allows: 18.86 pins t₂₀, 17.99+18.29 pin
t₁₈'s centre); THC16 cannot reach THC12 (budget 3.99 > cap sum 2.80) so the result-free
span **13.21–14.85 stays a documented gap**; **THC12 ±1.00** takes its full ±10 % window.
No empty grade exists anywhere; every tested result sits inside a grade; gaps carry no
results. The same machinery yields near-even splits across the portfolio (CJ
1.00/0.99/1.00 at the top, HPA 1.00/0.99/1.00, PM, SJ, GG 0.99/1.00) and full ±10 %
wherever a grade faces a gap or stands alone.

### 4.6 Tolerance expression

> `nn.00 % ± t.tt % (lower % — upper %)` — e.g. `22.00% ±2.19% (19.81% — 24.19%)`,
> `12.00% ±1.00% (11.00% — 13.00%)`. Nominal − t = lower and nominal + t = upper hold
> exactly by construction; the bounds are the governing acceptance limits.

## 5. Verification protocol and results (27.08.2026)

`check_design.py` is an independent auditor: it reads only the emitted design and the source
dataset, re-deriving nothing from the design code. It verifies per grade: 2-decimal bounds,
both R2 caps, nominal-inside, even/odd flags, tolerance arithmetic and the printed
expression, width, batch containment, strict descending order, no overlap, exact contiguity
at every junction not declared as a permitted gap. It then classifies **every Total-THC
result on file** against the strain windows:

| category | count | verdict |
|---|---|---|
| structural problems | **0** | design internally consistent |
| batch anchors in their assigned grade | **86 / 86** | R4 holds (53 register-certified + 29 T2 re-analysis + 3 declared + J31122501) |
| anchors outside assigned grade | 0 | — |
| batches without a grade | 0 | census complete (register ∪ stock) |
| superseded results, same grade | 26 | retests moved the value, not the grade |
| superseded results, different grade of the strain | 11 | historical value would have graded differently — retest governs (R5) |
| superseded results now outside all windows | 9 | BG1024 21.80, GG1024 13.34, HPA1024 14.97, CJ092501 22.30, PM092501 14.06, GRC102501/2 11.53, J31112501 25.27, PM112501 13.33, FB012601/1 14.68 — exactly the R5 supersession cases; not OOS events, the results are replaced |
| stability 25 °C/60 %RH (long-term arm) | 5 | 3 of 5 inside the release grade; GP0824_02 M6 21.31 dips one grade then returns (M9 23.08) — sampling variance; GP0824_03 M6 24.62 sits one grade below its **new** THC28 anchor (28.03, T2) — the anchor moved up, the batch did not decline |
| stability 40 °C/75 %RH (accelerated arm) | 4 | 13.16–18.62, out of or below grade — heat-stress artefact, not release-relevant; consistent with the CBN rise (2.05–2.35 %) |

**Bugs found and fixed by this audit:** certificate ППК26065 (13.93, CNP, 11.05.2026) prints
`серија JD112501*` — the milled Jelly-Donutz presentation, a separate register batch — but
was attributed to JD112501 (whole flower, retest 20.32) in `potency_dataset.json`. It was
masquerading as a superseded-OOS value of JD112501; reattributed, JD112501* now grades in
`JD_THC14:CBD1` (13.10 — 14.90) beside the T2-regraded JD012603/02. Milled
display names GG012601*/JD012601* were also restored (certificates print the asterisk).

## 6. Open items the design does not depend on

GG1024_02 (15.95 vs printed 15.59 — THC16 either way) · GP062501 (24.89 vs sheet 22.89 —
THC24 either way) · the 29 T2-anchored grades firm up when the formal Farmahem eCoAs are
filed (the earlier BSS052501 / OMP1024_01 / PM112501 paper checks are superseded by T2);
the design re-runs in one command (`python3 imb_grade_design.py && python3 check_design.py`).

## 7. Result (final revision, 27.08.2026)

**Mandatory codes: 42/48 honored exactly; 6 unavoidable, minimal, flagged deviations**
(FB012601/1, GRC102501/2, JD012603/02, PM112501, GP092501, GP082501/1 — §4.4).
24 strains · **51 grades** (all batch-bearing — zero empty grades) · **86 batches**, each
in exactly one grade (53 register-certified + 29 T2 re-analysis + 3 declared +
J31122501) · every window centred on its nominal · touching neighbours split their
budgets near-equally · **11 documented result-free gaps** (GRC 7.71–8.99 and OPM
8.81–8.99 at the low end; CJ, CC, FB, GP, JD, OPM mid-spans) · the only odd nominal is
the GRC_THC7 dead-zone fallback · every constraint machine-asserted and independently
re-audited (0 findings). Grades anchored on the unofficial 26.08.2026 T2 values are
provisional until the formal eCoAs are filed.
Full boards: `ImB_Potency_Grade_Ranges.xlsx` and `grade_design_even.json`.
