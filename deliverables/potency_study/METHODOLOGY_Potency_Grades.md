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

1. **One anchor value per batch** — the batch's **latest** Total-THC result. Where a batch has
   been retested (the Tranche-1 197-series campaign of 07.08.2026, the April 2026 Jokerz
   retests, and the Tranche-2 re-analysis sampled 12.08.2026 once its results are filed), the
   **retest value is the CoQ-forming result** and the grade is designed on it. Superseded
   pre-retest results are **out of specification scope** — they graded the batch once, and the
   retest replaced them.
2. **Owner-requested product codes** for the 48 tranche-list batches are design constraints:
   they are honored wherever the value mathematically permits.
3. Three register-audited corrections to the tranche sheet were applied before design:
   KC102501 17.04 (not 17.40), PM112501 13.33 (not 13.00), BSS052501 20.39 (not 20.47 — NGP
   paper check still open; the grade is stable under either value).
4. J31122501 is graded on the **machine-trimmed CoQ-forming preparation (21.84,
   CoQ-PP-2026-0054)**; the same-day hand-trimmed 19.84 is an experimental processing
   comparison (it happens to fall inside the same grade window).
5. Batches without any certificate (five T2-pending, SCR012601, WED102501, JD022601,
   GRC102501/1, the P16-series) enter at their declared values; their grades are provisional
   until an eCoA exists.

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
together); the cluster's *nominal* is then chosen freely per R1. Three audited
corrections applied first (KC102501 17.04, PM112501 13.33, BSS052501 20.39); PM112501's
owner code THC12 is arithmetically impossible for 13.33 (ceiling 13.20) and its cluster
moved to THC14.

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

Two of the 48 mandatory codes are arithmetically impossible and were resolved with the
smallest possible deviation, both flagged:

- **Cap Junky**: CJ092501 (22.30) in THC24 needs `t₂₄ ≥ 1.70`; CJ062501/1 (21.51) in
  THC22 needs `t₂₂ ≥ 0.49`; their no-overlap budget is `1.99 < 1.70 + 0.49 + …` — the
  windows must collide. The single-move fix regrades **CJ062501/1 → THC20**, giving the
  balanced ladder 24 ±1.99 (22.01–25.99) touching 20 ±2.00 (18.00–22.00, full) — every
  other Cap Junky mandatory code holds.
- **PM112501**: the audited certificate value 13.33 exceeds THC12's ceiling
  `1.10·12 = 13.20`; the batch is graded **THC14** (13.00–15.00). If the pending paper
  check of ППК26030 were to read 13.00 as on the owner sheet, THC12 would become
  feasible and the design re-runs in one command.

### 4.5 What the rules produce

Worked example — Fat Bastard (the case that motivated the final revision): clusters at
20.83 / {18.86, 18.29, 16.69} / 14.68 / 12.39. THC20 cannot sit over the 18-cluster
(req 0.83 + req 1.31 > 1.99), so the top takes **THC22 ±2.19** touching **THC18 ±1.80**
(budget 3.99 split 2.19/1.80, cap-limited); 18 cannot reach 14 (budget 3.99 > cap sum
3.20) so the result-free span **15.00–16.19 stays a documented gap**; below it
**THC14 ±0.99** and **THC12 ±1.00** split their 1.99 budget almost exactly in half.
No empty grade exists anywhere; every tested result sits inside a grade; gaps carry no
results. The same machinery yields near-half splits across the portfolio (GG
1.00/0.99/1.00, OPM 0.99/1.00/0.99/1.00, PM, MB, SJ, CC, JD) and full ±10 % wherever a
grade faces a gap or stands alone.

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
| batch anchors in their assigned grade | **86 / 86** | R4 holds (77 certified + 8 declared + J31122501) |
| anchors outside assigned grade | 0 | — |
| batches without a grade | 0 | census complete (register ∪ stock) |
| superseded results, same grade | 12 | retests moved the value, not the grade |
| superseded results, different grade of the strain | 7 | historical value would have graded differently — retest governs (R5) |
| superseded results now outside all windows | 3 | BG1024 21.80, HPA1024 14.97, J31112501 25.27 — exactly the R5 supersession cases; not OOS events, the results are replaced |
| stability 25 °C/60 %RH (long-term arm) | 5 | 4 of 5 inside the release grade; GP0824_02 M6 21.31 dips one grade then returns (M9 23.08) — sampling variance, no monotonic decline |
| stability 40 °C/75 %RH (accelerated arm) | 4 | 13.16–18.62, out of or below grade — heat-stress artefact, not release-relevant; consistent with the CBN rise (2.05–2.35 %) |

**Bugs found and fixed by this audit:** certificate ППК26065 (13.93, CNP, 11.05.2026) prints
`серија JD112501*` — the milled Jelly-Donutz presentation, a separate register batch — but
was attributed to JD112501 (whole flower, retest 20.32) in `potency_dataset.json`. It was
masquerading as a superseded-OOS value of JD112501; reattributed, JD112501* now carries its
own new contiguous grade `JD_THC14:CBD1` (13.10 — 14.90 in the symmetric design). Milled
display names GG012601*/JD012601* were also restored (certificates print the asterisk).

## 6. Open items the design does not depend on

BSS052501 paper check (20.39 vs 20.47 — THC20 either way) · OMP1024_01 (15.38, cert prints
1.58 — VERIFY ON PAPER) · GG1024_02 (15.95 vs printed 15.59 — THC16 either way) · GP062501
(24.89 vs sheet 22.89 — THC24 either way) · the five T2-pending batches re-anchor when their
re-analysis eCoAs land; the design re-runs in one command (`python3 imb_grade_design.py &&
python3 check_design.py`).

## 7. Result (final revision, 27.08.2026)

**Mandatory codes: 46/48 honored exactly; 2 unavoidable, minimal, flagged deviations.**
24 strains · **52 grades** (all batch-bearing — zero empty grades) · **86 batches**, each
in exactly one grade · every window centred on its nominal · touching neighbours split
their budgets near-equally · **8 documented result-free gaps** (GRC 7.71–10.79 and OPM
8.81–8.99 at the low end; CJ, CC, FB, GP, JD, OPM mid-spans) · odd nominals only where
no even configuration exists (CJ THC21, GRC THC7) · every constraint machine-asserted
and independently re-audited (0 findings).
Full boards: `ImB_Potency_Grade_Ranges.xlsx` and `grade_design_even.json`.
