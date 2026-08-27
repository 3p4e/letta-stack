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

## 3. The rule set (management, 27.08.2026)

R1. The nominal of every grade is a **whole even number** (… 8, 10, 12 … 26), shown as
    `nn.00 %` and in the product code as `THCnn : CBD1`. Where an even nominal cannot carry
    a rule-compliant window, the nominal shifts to the **adjacent odd** whole number (R7).
R2. A grade's tolerance never exceeds **10 % of the nominal**; bounds carry two decimals.
R3. **Symmetric tolerance** (27.08.2026): every grade is `nominal ± t` with the **same t
    above and below** — the window is always centred on the nominal.
R4. Ranges within one strain **never overlap**, and the **strongest grade is given the
    maximum tolerance first**; each weaker grade takes what remains.
R5. Every batch of the strain falls in **exactly one** grade at its anchor value
    (**retest supersession**: retest values are CoQ-forming, superseded results out of scope).
R6. **Contiguity**: consecutive ranges join at 0.01, with **reserve grades** closing
    unbridgeable spans; sole exception below 10 % THC (documented uncovered zone).
R7. **Odd-nominal adjustment**: the adjacent odd whole number replaces an even nominal that
    cannot satisfy R2–R6, and covers isolated results in the even ladder's dead zones.
    No grade tolerance may be below **0.50** (a 0.40 pp-wide grade is not a meaningful
    specification).

## 4. The mathematics

### 4.1 Feasibility of a nominal for a result

A result `v` can carry nominal `N` iff `0.90·N ≤ v ≤ 1.10·N`, i.e.

> **N ∈ [ v/1.1 , v/0.9 ]**

That interval has width `v·(1/0.9 − 1/1.1) ≈ 0.202·v`. It therefore always contains a whole
number once `v ≥ 4.95`, and always contains an **even** number once the interval is at least
2 wide, i.e. `v ≥ 9.9`. Below that, the even ladder has two **dead zones** where consecutive
even windows do not touch:

| junction | stronger window starts | weaker window ends | dead zone |
|---|---|---|---|
| THC10 / THC8 | 9.00 | 8.80 | **8.81 – 8.99** |
| THC8 / THC6 | 7.20 | 6.60 | **6.61 – 7.19** |

(For N ≥ 12 adjacent even windows overlap — `1.1·(N−2) ≥ 0.9·N ⇔ N ≥ 11` — so every value
≥ 10.80 is coverable by evens.) Rule R7 plugs the dead zones: THC9 covers 8.10–9.90 and THC7
covers 6.30–7.70, so **every result above ≈ 5.0 % THC is placeable**. Today exactly one batch
needs it: GRC102501/1 (declared 7.05 → `GRC_THC7:CBD1`, 6.30–7.70).

### 4.2 Grade assignment

Per strain, anchors are processed strongest-first:

1. **Owner-coded batches keep their code** if feasible per §4.1. Infeasible codes are
   escalated to the nearest feasible even (odd only if no even exists) and flagged — one case:
   PM112501, owner code THC12, audited value 13.33 > 13.20 = 1.10·12 → **THC14**.
2. **Uncoded batches join an existing grade** of the strain when their value fits its raw
   ±10 % window (nearest nominal on ties, upward); only when no existing grade fits is a new
   grade created at the nearest feasible even. This keeps grade sets minimal — e.g. the new
   Grape-Pie P16-series batches (26.32, 25.72, 24.78) joined the existing THC24 rather than
   spawning a THC26.
3. **Value-order repair**: no batch may sit at or above the weakest batch of a stronger
   grade; offenders are re-coded upward (e.g. Cap Junky CJ1024 23.00 → THC24, above the
   owner-coded THC24 batch CJ092501 22.30).

### 4.3 The symmetric contiguity law

With symmetric windows `N ± t`, two neighbouring grades `Nₛ > N_w` touching at 0.01 satisfy

> **tₛ + t_w = (Nₛ − N_w) − 0.01**

— an *equality*, not an inequality. For an adjacent even pair the budget is 1.99; inserting
an odd nominal between changes the two budgets to 0.99 and 1.99 halves. Because each
junction is an equality, **every tolerance in a contiguous ladder is an affine function of
the top grade's tolerance** (alternating sign): fixing t₁ fixes the whole ladder. The
solver therefore reduces each ladder to a one-variable feasibility problem — every grade
contributes an interval constraint on t₁ from `max(containment, 0.50) ≤ tₖ ≤ 0.10·Nₖ` —
intersects the intervals, and takes **t₁ = the maximum of the intersection** (R4:
strongest first). Containment means `tₖ ≥ max(Nₖ − vminₖ, vmaxₖ − Nₖ)` over the grade's
batches.

### 4.4 Choosing the nominals — even first, odd only when forced

For every batch cluster the solver tries the initially selected even nominal E, then E+1
and E−1; between clusters it tries direct junctions first, then up to three reserve
nominals. Candidate ladders are ranked: (1) fewest odd batch-grade nominals, (2) fewest
odd reserves, (3) fewest reserves, (4) largest (t₁, t₂, …) lexicographically, (5) smallest
total nominal shift. Worked example — Grape Pie: the top cluster spans 22.61–26.32, so an
even THC24 needs t ≥ 2.32, leaving ≤ −0.33 for any touching grade below (budget 1.99):
**THC24 is infeasible**; the adjacent odd **THC25 ± 2.47** (22.53–27.47) holds the whole
cluster and chains cleanly through a reserve THC22 to THC20/18/16. Cap Junky's mid-ladder
forces three odd shifts (21, 19, 15) for the same reason. Where a sub-10 % bottom cluster
cannot join even through odd bridges without violating the 0.50 minimum tolerance, the
ladder splits and the lowest grade keeps its full ±10 % with a documented uncovered zone
(GRC 7.71–10.79; OPM 8.81–9.10).

### 4.5 Tolerance expression

Every grade prints one symmetric tolerance:

> `nn.00 % ± t.tt % (lower % — upper %)` — e.g. `24.00% ±2.40% (21.60% — 26.40%)`,
> `25.00% ±2.47% (22.53% — 27.47%)`, `21.00% ±0.59% (20.41% — 21.59%)`.

The bounds in parentheses are the governing acceptance limits; nominal − t = lower and
nominal + t = upper hold exactly by construction.

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

## 7. Result (symmetric design, 27.08.2026)

24 strains · **58 grades** (53 batch-bearing + 5 reserve) · **86 batches**, each in exactly
one grade · every window **centred on its nominal** (single ± tolerance) · 21 grades at the
full ±10 % · **9 odd nominals** where the even could not hold a symmetric ladder (Cap Junky
21/19/17R/15, Fat Bastard 21, Grape Pie 25, Jelly Donutz 19, Orange Punch Mimosa 21, and
the GRC THC7 dead-zone fallback) · 2 permitted sub-10 % uncovered zones (GRC 7.71–10.79,
OPM 8.81–9.10) · every constraint machine-asserted and independently re-audited (0 findings).
Full boards: `ImB_Potency_Grade_Ranges.xlsx` (Grade Boards / Batch Assignments / Notes &
Exceptions) and `grade_design_even.json`.
