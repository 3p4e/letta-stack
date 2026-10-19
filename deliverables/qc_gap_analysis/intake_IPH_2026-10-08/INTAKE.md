# Three IPH contaminant certificates — taken in 08.10.2026

Head of QC, 08.10.2026: the certificates were placed in the eCoA folder on Drive and their results go onto the
corresponding certificates of quality: *"with the correct values and the correct external CoA document code, date of
issuing and the analysis covered"*.

| Drive file | Drive id | SHA-256 | |
| --- | --- | --- | --- |
| `P060342 (SCR012601＊)_IJZ_3160-2026_01.06.2026.pdf` | `1YaYHQExD-1_LDyE1zapH62a3acgE1Y-p` | `85bfbe6e…2878c` | new |
| `P060162 (SJ102501)_IJZ_1065-2026_11.03.2026.pdf` | `1yVAW0WsDyly7XaRiYW-NuP7E3XPM9K3-` | `5feb5be2…0895f` | complete, 4 of 4 pages (replaced the 3-page copy) |
| `P060182 (GRC102501)_IJZ_328-2026_11.02.2026.pdf` | `1pXti2jSM0-T91F5zmXG-9aNZcWmMMOWz` | `7a218838…50b95` | on file since 27.09.2026 |

**Two reads.** Two independent readers read every page from 300 dpi page images (the text layers OCR'd the Cyrillic as
Latin and are unusable: "1065" reads "1055"). A third read settled the four header transcription differences;
both readers were right in every case. A completeness check counted every table: 29 pesticides, 4 metals and 1
mycotoxin on each certificate. That is 102 values, with **no disagreement** (`two_reads.tsv`; the raw reads are
in `reads.json`).

| certificate | sample (printed) | received | pesticides (29) | Pb · Cd · As · Hg mg/kg | total aflatoxins | conformity |
| --- | --- | --- | --- | --- | --- | --- |
| **1065/2026** of 11.03.2026 | SLEEPY JOY, SJ102501 | 23.02.2026 | all н.д. | н.д. · н.д. · н.д.* · н.д. | 2,6 µg/kg (≤ 4) | ОДГОВАРА НА Ph. Eur. 2.8.13 / 2.4.27 / 2.8.18 |
| **3160/2026** of 01.06.2026 | SCRAMBLER, SCR012601* | 21.05.2026 | all printed "0" | 0,006 · 0,007 · 0,006 · 0,001 | < 2 µg/kg (≤ 4) | СЕ ВО СОГЛАСНОСТ со Ph. Eur. 2.8.13 / 2.4.27 / 2.8.18 |
| **328/2026** of 11.02.2026 | GRAPS & CREME, GRC102501 | 30.01.2026 | all н.д. | 0,084 · н.д. · 0,095* · н.д. | 2,2 µg/kg (≤ 4) | as printed, 27.09.2026 |

\* IPH marks arsenic on 1065/2026 and 328/2026 as tested by a non-accredited method. 3160/2026 marks no row.

**Batch.** SCR012601* is P060342 in the owner's workbook (`batch_dates_2026-09-10.csv`), the lot of CoQ-PP_26-073 and
-160. No certificate prints a P number.

**What it changes** (`tracker/apply_iph_intake_2026-10-08.py`):
- **-052** (initial, SJ102501): rows 10.2, 11.1–11.4 and 12 from 1065/2026. These printed `[pending]` since
  26.09.2026 (ruling 8).
- **-162** (retest): 11.1–11.4 and 12 carried from -052.
- **-073** (initial, SCR012601):
  - 10.2, 11.1–11.4 and 12 from 3160/2026. The metals and pesticides were n/t, "requested from the laboratory".
  - With an IPH total on record, ruling 3 applies: B1 and OTA are n/t on the initial.
  - Re-dated 18.09.2026, seven days after Farmahem 227-8-К/26 of 11.09.2026, the last certificate it cites.
- **-160** (retest): 10.1–10.3 are its own Farmahem 227-8-М/26 retest panel; 11.1–11.4 and 12 are carried from -073.
  It supersedes -073 of 18.09.2026.
- **-050 / -152** (GRC102501/1): 328/2026 read again, and it agrees with what they print. Unchanged.
- The two laboratory requests these answer are off `tracker/LAB_REQUESTS_T3_2026-09-26.tsv`.
