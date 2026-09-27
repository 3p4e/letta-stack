# GRC102501/1 (P060142) — its release testing, taken in 27.09.2026

**Head of QC, 27.09.2026:** *"you can't tell me that we don't have any eCoA for those."*

Four certificates of 30.01–12.02.2026 print only the parent code **GRC102501**. They sat on Drive
under the sister lot `P060182 (GRC102501)_…` and no certificate of quality cited them: GRC102501/2
(P060182, -054/-120) has its own set, received 23.02.2026 (`051-6-К/26`, `051-6-ГС/26`,
`136/0233/26`, `1060/2026`). They belong to **GRC102501/1**:

- the sale list to Versa (`VERSA_UVOZ-IZVOZ_KONOPLJA3.xlsx`, #60) gives GRC102501/1 · P060142 at
  **7.05 %** — the figure `031-1-К/26` prints;
- the sample was received 30.01.2026, three weeks after /1's harvest (09.01.2026) and before its
  packaging (23.02.2026); /2 was harvested 20.01.2026 and sampled separately on 23.02.2026.

| certificate | laboratory | issued | fills |
| --- | --- | --- | --- |
| `031-1-К/26` | Farmahem | 10.02.2026 | #3–#6 (THC 7.05 %, CBD and CBN < LOQ) |
| `031-1-ГС/26` | Farmahem | 12.02.2026 | #8 (7.2 %) |
| `76/0119/26` | IPH microbiology | 09.02.2026 | #9.1–#9.5 (conforms) |
| `328/2026` | IPH | 11.02.2026 | #10.2 (2.2 µg/kg), #11.1–#11.4, #12 |

Every value passed two reads (`two_reads.tsv`): the Drive text layer, and the page image read on
27.09.2026. `76/0119/26` prints its receipt date as **02.02.2025** against a request of 30.01.2026;
the Head of QC ruled on 27.09.2026 that the year is a misprint for 2026 — received **02.02.2026**.

**Consequences** (applied by `tracker/apply_first_testing_ruling_2026-09-26.py`, `RELEASE_SET`):
`-050` prints this set and keeps 06.06.2026; B1 and OTA print n/t (IPH reports the total only).
The September 2026 testing (`227-16-К/26`, `227-16-М/26`, `550/1081/26`) is the lot's retest, so
`-152` is reinstated, dated 21.09.2026, superseding `-050`, and carries the loss on drying, metals and
pesticides it did not repeat. **Grade:** 7.05 % falls in no window of the GRC specification (7.20–8.79,
9.00–10.99, 11.00–12.99 in the deployed builder, 27.09.2026), so `-050` is ungraded until the Head of
QC defines one (ruling 7).
