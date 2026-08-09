# Questionnaire Library (Mode A — content development)

## Principles (non-negotiable)
1. All answers **pre-populated** — the user *selects*, never types. Present with the `AskUserQuestion` tool, multi-select where logical.
2. Every option is truthful, applicable, and **verified against the regulatory hierarchy**; never present GMP-violating or invented options, and never a leading question with only one valid answer.
3. **Analyse before asking** — parse the request + uploaded examples; map regulations; pick category; decide rounds.
4. **Auto-completion** — unanswered → most compliant option (see regulatory_and_context.md defaults).

## Round count by complexity
| Complexity | SOP rounds | Annex rounds |
|---|---|---|
| Simple (single process / label template) | 3 | 2 |
| Medium (multi-step / request form) | 4 | 3 |
| Complex (cross-functional / CoA template) | 5+ | 4+ |

---

## SOP question banks

### Quality Control (QC)
- **R1 Scope:** primary testing focus (Identity[Annex 8 §2 — ALL containers]/Potency/Purity/Contaminants/Micro/Water/Sample mgmt); sample types [multi]; batch-release vs monitoring; method source (Ph. Eur. preferred/USP/in-house/ISO/contract).
- **R2 Technical:** techniques [HPLC-DAD/GC-MS/ICP-MS/LC-MS-MS/Microscopy/LOD/Karl Fischer/Micro]; acceptance criteria [cannabinoid ±10 % Ph.Eur 3028 / LOD NMT 12 % / foreign matter NMT 2 % / heavy metals / pesticides / mycotoxins / microbial]; external testing; reference standards [CRS/secondary/SST/internal].
- **R3 Responsibilities:** primary performer; review chain (single/two-tier/three-tier+QP/cross-functional); trigger; turnaround.
- **R4 Records:** records generated [worksheets 6.17/printouts/sample-prep/SST/CoA/OOS]; retention; annexes needed.

### Production / Manufacturing
- **R1 Scope:** phase (pre-prod/primary/packaging-primary/secondary/IPC/completion); product (flos Grade D/pre-rolls/ground/bulk); cleanroom class.
- **R2 Technical:** CPPs [temp/RH/time/airflow/light/ΔP]; IPCs [weight/moisture/visual/label/count/env]; equipment.
- **R3 Responsibilities:** personnel [operator/supervisor/Head Prod/QA/QP]; documentation [BMR mandatory/equipment logs/IPC/env/line-clearance/reconciliation].

### Cultivation (GACP)
- **R1 Scope:** phase (propagation/veg/flowering/harvest/post-harvest/mother/IPM); system; regulatory (WHO GACP/Annex 7/MALMED).
- **R2 Technical:** parameters [temp day/night, RH, photoperiod, CO₂, airflow, nutrients pH/EC]; monitoring frequency; pest management (IPM/preventive/no-chemicals/approved list Ph.Eur 2.8.13).

### Quality Assurance (QA)
- **R1 Scope:** element (doc control/deviation-CAPA/change control/audit/training/supplier qual/batch release/PQR); GMP-critical (default yes).
- **R2 Requirements:** primary regulation (EU GMP Ch.1/ICH Q10/Ch.8/Annex 16/Ch.4); timelines (immediate/24-48 h/30 d/90 d/annual).

---

## Annex question banks

### Forms
- **R1 Purpose:** request/recording/verification/approval; who initiates; trigger.
- **R2 Content [multi]:** ID fields [Doc ID 4.2 / Version 4.3 / Date 4.8 / Batch]; requester [Name 4.20 / Dept / Position / Contact]; main content [item list/qty/description/priority].
- **R3 Approval:** levels (single/two/three/cross); signatures [Prepared+Date / Reviewed / Approved]; comments field.

### Logs / Registers
- **R1:** what is tracked; frequency.
- **R2 Columns [multi]:** ID [Seq No. / Date-Time 4.8 / Batch / Doc-Label ID]; content [description/qty/recipient/purpose/status]; verification [Issued By 4.20 / Signature / Received By / Witness].
- **R3 Management:** rows per page (10/15/20/25+); pagination "Page X of Y".

### Templates (FPS, CoA, labels)
- **R1:** document type (spec/certificate/label/instruction); who completes.
- **R2 Fields:** fixed [company/logo/header/column headers/spec limits/regulatory text]; variable [batch/results/dates/analyst/pass-fail].
- **R3 Compliance [multi]:** required statements [Ph. Eur. / EU GMP / ISO 17025 / stability].

### Checklists
- **R1:** what is verified; when completed.
- **R2 Items:** response format [Yes/No mandatory critical · Yes/No/N-A · Pass/Fail · checkbox]; criteria column (recommended).
- **R3 Verification:** on fail → deviation (1.4) / corrective action / supervisor notify.

---

## Output of Mode A
- **SOP:** clean English 9-section content (see SKILL §2.1), ready for Mode B formatting.
- **Annex:** structured content (header/ID fields, body table columns, approval/signatures, pagination) for the annex category, ready for Mode B.
Present to the user, get approval, then format.
