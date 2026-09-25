# Loss on drying by tranche — Farmahem, the Center, or neither

Written 17.09.2026 by `lod_tranche_census.py`. One row per production batch, with the document each of its two certificates cites for #8 — so this is both the census the Head of QC asked for and the check on every citation.

A lot's documents are the release register's rows **and** the documents its own certificates cite: fourteen lots print a loss-on-drying figure whose page never became a register row, reaching the certificate through the Head of QC's 09.09 resolution pass instead (`OI-42` counts those scans). Counting only the register would report a lot as untested while its certificate prints a figure.

The ranking is the Head of QC's ruling of 17.09.2026, which `apply_lod_source.py` holds: **Farmahem's ГС report first, then the Center for Natural Products' ППК page, then the in-house sheet.**

## The count

| tranche | batches | Farmahem ГС | CNP ППК only | in-house only | nothing at all |
| --- | ---: | ---: | ---: | ---: | ---: |
| Tranche 1 | 21 | 2 | 14 | 0 | 5 |
| Tranche 2 | 32 | 5 | 21 | 1 | 5 |
| Tranche 3 | 30 | 5 | 21 | 1 | 3 |
| no tranche | 6 | 0 | 6 | 0 | 0 |
| **all** | **89** | **12** | **62** | **2** | **13** |

**12 of the 89 batches have a Farmahem ГС page** — the ruling's first choice — spread over Tranche 1, Tranche 2, Tranche 3. **62 have only a Center for Natural Products ППК page**, where loss on drying sits on the potency certificate rather than a report of its own. **2 have only the in-house cross-check** (P050192 and P050202), which is neither of the two laboratories the ruling names and is the only record those two lots have. **13 have nothing at all** and print "not tested" — `OI-53`.

**No lot in the set has both**, so the ranking never has to choose today; it stands for the next lot sent to both.

## Tranche 1

### Farmahem ГС — the ruling's first choice — 2 batch(es)

| P lot | Batch | Strain | On file | Release CoQ | cites | Reissue CoQ | cites |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P060152 | J31102501 | Jokerz 31 | 051-1-ГС/26 · 02.03.2026 | CoQ-PP_26-051 | 051-1-ГС/26 · 02.03.2026 = 6.3 | CoQ-PP_26-099 | 051-1-ГС/26 · 02.03.2026 = 6.3 |
| P060242 | OPM122501 | Orange Punch Mimosa | 100-4-ГС/26 · 09.04.2026 | CoQ-PP_26-060 | 100-4-ГС/26 · 09.04.2026 = 6.6 | CoQ-PP_26-103 | 100-4-ГС/26 · 09.04.2026 = 6.6 |

### CNP ППК only — no Farmahem page for this lot — 14 batch(es)

| P lot | Batch | Strain | On file | Release CoQ | cites | Reissue CoQ | cites |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BG1024 | BG1024 | Blue Gelato | ППК25050 · 26.02.2025 | CoQ-PP_26-003 | ППК25050 · 26.02.2025 = 5.73 | CoQ-PP_26-085 | ППК25050 · 26.02.2025 = 5.73 |
| BSS1024 | BSS1024 | Blue Sunset Sherbet | ППК25051 · 26.02.2025 | CoQ-PP_26-002 | ППК25051 · 26.02.2025 = 5.99 | CoQ-PP_26-086 | ППК25051 · 26.02.2025 = 5.99 |
| P050022 | GP0824_02 | Grape Pie | ППК25139 · 22.05.2025; ППК25174 · 10.07.2025 | CoQ-PP_26-007 | ППК25139 · 22.05.2025 = 7.21 | CoQ-PP_26-095 | ППК25139 · 22.05.2025 = 7.21 |
| P050052 | HPA1024_01 | High Pro Amnesia | ППК25155 · 24.06.2025 | CoQ-PP_26-011 | ППК25155 · 24.06.2025 = 6.36 | CoQ-PP_26-098 | ППК25155 · 24.06.2025 = 6.36 |
| P050062 | OPM1024_02 | Orange Punch Mimosa | ППК25154 · 24.06.2025 | CoQ-PP_26-012 | ППК25154 · 24.06.2025 = 6.89 | CoQ-PP_26-102 | ППК25154 · 24.06.2025 = 6.89 |
| P050092 | GG1024_01 | Gorilla Glue | ППК25104 · 17.04.2025 | CoQ-PP_26-015 | ППК25104 · 17.04.2025 = 7.54 | CoQ-PP_26-093 | ППК25104 · 17.04.2025 = 7.54 |
| P050152 | GP052501 | Grape Pie | ППК25279 · 19.09.2025 | CoQ-PP_26-020 | ППК25279 · 19.09.2025 = 7.30 | CoQ-PP_26-094 | ППК25279 · 19.09.2025 = 7.30 |
| P050162 | CJ052501/01 | Cap Junky | ППК25280 · 17.09.2025 | CoQ-PP_26-022 | ППК25280 · 17.09.2025 = 7.93 | CoQ-PP_26-088 | ППК25280 · 17.09.2025 = 7.93 |
| P050212 | CJ062501-2 | Cap Junkie | ППК25322 · 23.10.2025 | CoQ-PP_26-027 | ППК25322 · 23.10.2025 = 6.70 | CoQ-PP_26-089 | ППК25322 · 23.10.2025 = 6.70 |
| P050322 | GP082501/2 | Grape Pie | ППК25381 · 12.12.2025; PP CoA #021 / ППК25381 · 21.01.2026 | CoQ-PP_26-036 | ППК25381 · 12.12.2025 = 6.88 | CoQ-PP_26-096 | ППК25381 · 12.12.2025 = 6.88 |
| P060032 | CJ082501/2 | Cap Junky | ППК26003 · 21.01.2026 | CoQ-PP_26-039 | ППК26003 · 21.01.2026 = 7.37 | CoQ-PP_26-090 | ППК26003 · 21.01.2026 = 7.37 |
| P060062 | PM092501 | Permanent Marker | ППК26004 · 21.01.2026 | CoQ-PP_26-042 | ППК26004 · 21.01.2026 = 7.97 | CoQ-PP_26-104 | ППК26004 · 21.01.2026 = 7.97 |
| P060212 | JD112501 | Jelly Donuts | ППК26063 · 11.05.2026 | CoQ-PP_26-057 | ППК26063 · 11.05.2026 = 6.69 | CoQ-PP_26-100 | ППК26063 · 11.05.2026 = 6.69 |
| P060402 | GG012603 | Gorilla Glue | ППК26114 · 30.06.2026 | CoQ-PP_26-077 | ППК26114 · 30.06.2026 = 6.48 | CoQ-PP_26-092 | ППК26114 · 30.06.2026 = 6.48 |

### Nothing at all — loss on drying was never determined — 5 batch(es)

| P lot | Batch | Strain | On file | Release CoQ | cites | Reissue CoQ | cites |
| --- | --- | --- | --- | --- | --- | --- | --- |
| — | P060332 | CashCow | — nothing — | CoQ-PP_26-068 | — not tested | CoQ-PP_26-087 | — not tested |
| HPA1024 | HPA1024 | High Pro Amnesia | — nothing — | CoQ-PP_26-005 | — not tested | CoQ-PP_26-097 | — not tested |
| OPM1024 | OPM1024 | Orange Punch Mimosa | — nothing — | CoQ-PP_26-006 | — not tested | CoQ-PP_26-101 | — not tested |
| P060352 | FB012602 | Fat Bastard | — nothing — | CoQ-PP_26-070 | — not tested | CoQ-PP_26-091 | — not tested |
| P060382 | SCR012603 | Scrambler | — nothing — | CoQ-PP_26-074 | — not tested | CoQ-PP_26-105 | — not tested |

## Tranche 2

### Farmahem ГС — the ruling's first choice — 5 batch(es)

| P lot | Batch | Strain | On file | Release CoQ | cites | Reissue CoQ | cites |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P060112 | PUM102501 | Pure Michigen | 031-2-ГС/26 · 11.02.2026 | CoQ-PP_26-047 | 031-2-ГС/26 · 11.02.2026 = 6,4 % | CoQ-PP_26-132 | 031-2-ГС/26 · 11.02.2026 = 6,4 % |
| P060122 | ACC102501 | Amnesia Core Cut | 031-5-ГС/26 · 12.02.2026 | CoQ-PP_26-048 | 031-5-ГС/26 · 12.02.2026 = 7,1 % | CoQ-PP_26-106 | 031-5-ГС/26 · 12.02.2026 = 7,1 % |
| P060132 | CF102501 | Chem Flyer | 031-4-ГС/26 · 12.02.2026 | CoQ-PP_26-049 | 031-4-ГС/26 · 12.02.2026 = 5,6 % | CoQ-PP_26-109 | 031-4-ГС/26 · 12.02.2026 = 5,6 % |
| P060172 | KC102501 | Kush Crasher | 051-4-ГС/26 · 02.03.2026 | CoQ-PP_26-053 | 051-4-ГС/26 · 02.03.2026 = 8.6 | CoQ-PP_26-126 | 051-4-ГС/26 · 02.03.2026 = 8.6 |
| P060182 | GRC102501/2 | Grapes and Cream | 051-6-ГС/26 · 02.03.2026 | CoQ-PP_26-054 | 051-6-ГС/26 · 02.03.2026 = 7.7 | CoQ-PP_26-120 | 051-6-ГС/26 · 02.03.2026 = 7.7 |

### CNP ППК only — no Farmahem page for this lot — 21 batch(es)

| P lot | Batch | Strain | On file | Release CoQ | cites | Reissue CoQ | cites |
| --- | --- | --- | --- | --- | --- | --- | --- |
| GG1024 | GG1024 | Gorilla Glue | ППК25008 · 29.01.2025 | CoQ-PP_26-004 | ППК25008 · 29.01.2025 = 7.8 | CoQ-PP_26-115 | ППК25008 · 29.01.2025 = 7.8 |
| P050042 | OMP1024_01 | Orange Punch Mimosa | ППК25117 · 06.05.2025 | CoQ-PP_26-010 | ППК25117 · 06.05.2025 = 5.86 | CoQ-PP_26-128 | ППК25117 · 06.05.2025 = 5.86 |
| P050072 | GP0824_03 | Grape Pie | ППК25175 · 10.07.2025 | CoQ-PP_26-013 | ППК25175 · 10.07.2025 = 6.58 | CoQ-PP_26-117 | ППК25175 · 10.07.2025 = 6.58 |
| P050082 | OPM1024_03 | Orange Punch Mimosa | ППК25210 · 28.07.2025 | CoQ-PP_26-014 | ППК25210 · 28.07.2025 = 6.38 | CoQ-PP_26-130 | ППК25210 · 28.07.2025 = 6.38 |
| P050112 | MB0824_05 | Motor Breath | ППК25211 · 28.07.2025 | CoQ-PP_26-017 | ППК25211 · 28.07.2025 = 6.56 | CoQ-PP_26-127 | ППК25211 · 28.07.2025 = 6.56 |
| P050182 | HPA052501 | High Pro Amnesia | ППК25278 · 19.09.2025 | CoQ-PP_26-024 | ППК25278 · 19.09.2025 = 7.29 | CoQ-PP_26-121 | ППК25278 · 19.09.2025 = 7.29 |
| P050222 | CJ062501/1 | Cap Junky | ППК25321 · 23.10.2025 | CoQ-PP_26-028 | ППК25321 · 23.10.2025 = 7.77 | CoQ-PP_26-110 | ППК25321 · 23.10.2025 = 7.77 |
| P050282 | CLE072501 | Clemosa A Bud | ППК25370 · 28.11.2025; PP CoA #027 / ППК25370 · 21.01.2026 | CoQ-PP_26-032 | ППК25370 · 28.11.2025 = 9.68 | CoQ-PP_26-113 | ППК25370 · 28.11.2025 = 9.68 |
| P050302 | GP072501/2 | Grape Pie | ППК25379 · 12.12.2025; PP CoA #019 / ППК25379 · 21.01.2026 | CoQ-PP_26-034 | ППК25379 · 12.12.2025 = 7.41 | CoQ-PP_26-116 | ППК25379 · 12.12.2025 = 7.41 |
| P050312 | GP082501/1 | Grape Pie | ППК25380 · 12.12.2025; PP CoA #020 / ППК25380 · 21.01.2026 | CoQ-PP_26-035 | ППК25380 · 12.12.2025 = 6.29 | CoQ-PP_26-118 | ППК25380 · 12.12.2025 = 6.29 |
| P060012 | WC082501 | Wedding Crusher | ППК26001 · 21.01.2026 | CoQ-PP_26-037 | ППК26001 · 21.01.2026 = 7.50 | CoQ-PP_26-135 | ППК26001 · 21.01.2026 = 7.50 |
| P060022 | CJ082501/1 | Cap Junky | ППК26002 · 21.01.2026 | CoQ-PP_26-038 | ППК26002 · 21.01.2026 = 7.21 | CoQ-PP_26-111 | ППК26002 · 21.01.2026 = 7.21 |
| P060042 | OPM092501 | Orange Punch Mimosa | ППК26008 · 21.01.2026 | CoQ-PP_26-040 | ППК26008 · 21.01.2026 = 7.85 | CoQ-PP_26-129 | ППК26008 · 21.01.2026 = 7.85 |
| P060072 | CJ092501 | Cap Junky | ППК26007 · 21.01.2026 | CoQ-PP_26-043 | ППК26007 · 21.01.2026 = 7.64 | CoQ-PP_26-112 | ППК26007 · 21.01.2026 = 7.64 |
| P060082 | SJ092501 | Sleepy Joe | ППК26006 · 21.01.2026 | CoQ-PP_26-044 | ППК26006 · 21.01.2026 = 8.68 | CoQ-PP_26-134 | ППК26006 · 21.01.2026 = 8.68 |
| P060092 | GP092501 | Grape Pie | ППК26009 · 21.01.2026 | CoQ-PP_26-045 | ППК26009 · 21.01.2026 = 6.91 | CoQ-PP_26-119 | ППК26009 · 21.01.2026 = 6.91 |
| P060232 | PM112501 | Permanent Marker | ППК26030 · 05.03.2026 | CoQ-PP_26-059 | ППК26030 · 05.03.2026 = 8.61 | CoQ-PP_26-131 | ППК26030 · 05.03.2026 = 8.61 |
| P060282 | SCR112501 | Scrambler | ППК26069 · 11.05.2026 | CoQ-PP_26-064 | ППК26069 · 11.05.2026 = 6.84 | CoQ-PP_26-133 | ППК26069 · 11.05.2026 = 6.84 |
| P060322 | FB012601/1 | Fat Bastard | ППК26067 · 11.05.2026 | CoQ-PP_26-069 | ППК26067 · 11.05.2026 = 7.67 | CoQ-PP_26-114 | ППК26067 · 11.05.2026 = 7.67 |
| P060412 | JD012603/02 | Jelly Donuts | ППК26113 · 30.06.2026 | CoQ-PP_26-078 | ППК26113 · 30.06.2026 = 7.52 | CoQ-PP_26-123 | ППК26113 · 30.06.2026 = 7.52 |
| P060422 | JD012603/02V | Jelly Donuts | ППК26111 · 30.06.2026 | CoQ-PP_26-076 | ППК26111 · 30.06.2026 = 7.04 | CoQ-PP_26-124 | ППК26111 · 30.06.2026 = 7.04 |

### In-house only — neither laboratory has a page — 1 batch(es)

| P lot | Batch | Strain | On file | Release CoQ | cites | Reissue CoQ | cites |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P050192 | BSS052501 | Blue Sunset Sherbet | In-house GC cross-check NGP/QCG/SOP-024 · 28.11.2025; iCoA-PP_26-023 · 03.06.2026 | CoQ-PP_26-025 | iCoA-PP_26-023 · 03.06.2026 = 8.60 | CoQ-PP_26-107 | iCoA-PP_26-023 · 03.06.2026 = 8.60 |

### Nothing at all — loss on drying was never determined — 5 batch(es)

| P lot | Batch | Strain | On file | Release CoQ | cites | Reissue CoQ | cites |
| --- | --- | --- | --- | --- | --- | --- | --- |
| — | CC042601 | Cash Cow | — nothing — | — at issue — | — not tested | — at issue — | — not tested |
| — | FB042601 | Fat Bastard | — nothing — | — at issue — | — not tested | — at issue — | — not tested |
| P060362 | JD012603/01 | Jelly Donuts | — nothing — | CoQ-PP_26-071 | — not tested | CoQ-PP_26-122 | — not tested |
| P060372 | CC012603 | Cash Cow | — nothing — | CoQ-PP_26-072 | — not tested | CoQ-PP_26-108 | — not tested |
| P060492 | JD042601 | Jelly Donutz | — nothing — | CoQ-PP_26-084 | — not tested | CoQ-PP_26-125 | — not tested |

## Tranche 3

### Farmahem ГС — the ruling's first choice — 5 batch(es)

| P lot | Batch | Strain | On file | Release CoQ | cites | Reissue CoQ | cites |
| --- | --- | --- | --- | --- | --- | --- | --- |
| — | J31112501 | Jokerz 31 | 051-5-ГС/26 · 02.03.2026; 100-1-ГС/26 · 09.04.2026 | CoQ-PP_26-056 | 051-5-ГС/26 · 02.03.2026 = 8.4 | CoQ-PP_26-153 | 051-5-ГС/26 · 02.03.2026 = 8.4 |
| — | J31122501 | Jokerz 31 | 100-2-ГС/26 · 09.04.2026; 100-3-ГС/26 · 09.04.2026 | CoQ-PP_26-062 | 100-2-ГС/26 · 09.04.2026 = 10.3 | CoQ-PP_26-154 | 100-2-ГС/26 · 09.04.2026 = 10.3 |
| — | SJ102501 | Sleepy Joy | 051-3-ГС/26 · 02.03.2026 | CoQ-PP_26-052 | 051-3-ГС/26 · 02.03.2026 = 7.8 | CoQ-PP_26-162 | 051-3-ГС/26 · 02.03.2026 = 7.8 |
| — | SJ112501 | Sleepy Joy | 051-2-ГС/26 · 02.03.2026 | CoQ-PP_26-055 | 051-2-ГС/26 · 02.03.2026 = 6.7 | CoQ-PP_26-163 | 051-2-ГС/26 · 02.03.2026 = 6.7 |
| P060102 | WED102501 | Wedding Cake | 031-3-ГС/26 · 12.02.2026 | CoQ-PP_26-046 | 031-3-ГС/26 · 12.02.2026 = 6,8 % | CoQ-PP_26-165 | 031-3-ГС/26 · 12.02.2026 = 6,8 % |

### CNP ППК only — no Farmahem page for this lot — 21 batch(es)

| P lot | Batch | Strain | On file | Release CoQ | cites | Reissue CoQ | cites |
| --- | --- | --- | --- | --- | --- | --- | --- |
| — | CC112501 | Cash Cow | ППК26068 · 11.05.2026 | CoQ-PP_26-063 | ППК26068 · 11.05.2026 = 7.39 | CoQ-PP_26-139 | ППК26068 · 11.05.2026 = 7.39 |
| — | CJ1024 | Cup Junky | ППК25052 · 26.02.2025 | CoQ-PP_26-001 | ППК25052 · 26.02.2025 = 5.91 | CoQ-PP_26-142 | ППК25052 · 26.02.2025 = 5.91 |
| — | FB012603 | Fat Bastard | ППК26112 · 30.06.2026 | CoQ-PP_26-079 | ППК26112 · 30.06.2026 = 7.04 | CoQ-PP_26-143 | ППК26112 · 30.06.2026 = 7.04 |
| — | FB012603V | FatBastard | ППК26110 · 30.06.2026 | CoQ-PP_26-075 | ППК26110 · 30.06.2026 = 6.36 | CoQ-PP_26-144 | ППК26110 · 30.06.2026 = 6.36 |
| — | FB112501 | Fat Bastard | ППК26066 · 11.05.2026 | CoQ-PP_26-065 | ППК26066 · 11.05.2026 = 6.09 | CoQ-PP_26-145 | ППК26066 · 11.05.2026 = 6.09 |
| — | GG012601 | Gorilla Glue | ППК26062 · 11.05.2026 | CoQ-PP_26-066 | ППК26062 · 11.05.2026 = 6.13 | CoQ-PP_26-146 | ППК26062 · 11.05.2026 = 6.13 |
| — | GG112501 | Gorilla Glue | ППК26061 · 11.05.2026 | CoQ-PP_26-061 | ППК26061 · 11.05.2026 = 6.31 | CoQ-PP_26-148 | ППК26061 · 11.05.2026 = 6.31 |
| — | JD012601 | Jelly Donutz | ППК26064 · 11.05.2026 | CoQ-PP_26-067 | ППК26064 · 11.05.2026 = 6.68 | CoQ-PP_26-155 | ППК26064 · 11.05.2026 = 6.68 |
| — | OPM112501 | Orange Punch Mimosa | ППК26031 · 05.03.2026 | CoQ-PP_26-058 | ППК26031 · 05.03.2026 = 8.06 | CoQ-PP_26-158 | ППК26031 · 05.03.2026 = 8.06 |
| — | SCR022601 | Scrambler | ППК26116 · 06.07.2026 | CoQ-PP_26-080 | ППК26116 · 06.07.2026 = 7.06 | CoQ-PP_26-161 | ППК26116 · 06.07.2026 = 7.06 |
| P050012 | GG1024_02 | Gorilla Glue | ППК25140 · 22.05.2025 | CoQ-PP_26-008 | ППК25140 · 22.05.2025 = 6.88 | CoQ-PP_26-147 | ППК25140 · 22.05.2025 = 6.88 |
| P050032 | MB0824_04 | Motor Breath | ППК25118 · 06.05.2025 | CoQ-PP_26-009 | ППК25118 · 06.05.2025 = 6.01 | CoQ-PP_26-156 | ППК25118 · 06.05.2025 = 6.01 |
| P050102 | GP0824_01 | Grape Pie | ППК25105 · 17.04.2025 | CoQ-PP_26-016 | ППК25105 · 17.04.2025 = 6.73 | CoQ-PP_26-151 | ППК25105 · 17.04.2025 = 6.73 |
| P050122 | BSS1024_01 | Blue Sunset Sherbet | ППК25176 · 10.07.2025 | CoQ-PP_26-018 | ППК25176 · 10.07.2025 = 6.38 | CoQ-PP_26-137 | ППК25176 · 10.07.2025 = 6.38 |
| P050132 | OPM052501 | Orange Punch Mimosa | ППК25257 · 05.09.2025 | CoQ-PP_26-019 | ППК25257 · 05.09.2025 = 8.28 | CoQ-PP_26-157 | ППК25257 · 05.09.2025 = 8.28 |
| P050172 | CJ052501-2 | Cup Junky | ППК25281 · 17.09.2025 | CoQ-PP_26-023 | ППК25281 · 17.09.2025 = 6.63 | CoQ-PP_26-140 | ППК25281 · 17.09.2025 = 6.63 |
| P050252 | CJ072501 | Cup Junky | ППК25367 · 28.11.2025 | CoQ-PP_26-029 | ППК25367 · 28.11.2025 = 8.22 | CoQ-PP_26-141 | ППК25367 · 28.11.2025 = 8.22 |
| P050262 | WC072501 | Wedding Crasher | ППК25369 · 28.11.2025 | CoQ-PP_26-030 | ППК25369 · 28.11.2025 = 8.94 | CoQ-PP_26-164 | ППК25369 · 28.11.2025 = 8.94 |
| P050272 | PM072501 | Permanent Market | ППК25368 · 28.11.2025 | CoQ-PP_26-031 | ППК25368 · 28.11.2025 = 9.52 | CoQ-PP_26-159 | ППК25368 · 28.11.2025 = 9.52 |
| P050292 | GP072501-1 | Grape Pie | ППК25378 · 12.12.2025; PP CoA #018 / ППК25378 · 21.01.2026 | CoQ-PP_26-033 | ППК25378 · 12.12.2025 = 6.62 | CoQ-PP_26-150 | ППК25378 · 12.12.2025 = 6.62 |
| P060052 | AB092501 | Apple and Banana | PP CoA #037 / ППК26005 · 21.01.2026; ППК26005 · 21.01.2026 | CoQ-PP_26-041 | ППК26005 · 21.01.2026 = 6.77 | CoQ-PP_26-136 | ППК26005 · 21.01.2026 = 6.77 |

### In-house only — neither laboratory has a page — 1 batch(es)

| P lot | Batch | Strain | On file | Release CoQ | cites | Reissue CoQ | cites |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P050202 | GP062501 | Grape Pie | In-house HPLC cross-check NPCCC/SCP-02, NGP/QCG/SOP-024 · 28.11.2025; iCoA-PP_26-024 · 03.06.2026 | CoQ-PP_26-026 | iCoA-PP_26-024 · 03.06.2026 = 8.19 (avg of 4 weighings 51-1,51-2,52-1,52-2) | CoQ-PP_26-149 | iCoA-PP_26-024 · 03.06.2026 = 8.19 (avg of 4 weighings 51-1,51-2,52-1,52-2) |

### Nothing at all — loss on drying was never determined — 3 batch(es)

| P lot | Batch | Strain | On file | Release CoQ | cites | Reissue CoQ | cites |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P050142 | BSS1024_01/2 | Blue Sunset Sherbet | — nothing — | CoQ-PP_26-021 | — not tested | CoQ-PP_26-138 | — not tested |
| P060142 | GRC102501/1 | Graps & Creme | — nothing — | CoQ-PP_26-050 | — not tested | CoQ-PP_26-152 | — not tested |
| P060342 | SCR012601 | Scrambler | — nothing — | CoQ-PP_26-073 | — not tested | CoQ-PP_26-160 | — not tested |

## Belonging to no tranche

### CNP ППК only — no Farmahem page for this lot — 6 batch(es)

| P lot | Batch | Strain | On file | Release CoQ | cites | Reissue CoQ | cites |
| --- | --- | --- | --- | --- | --- | --- | --- |
| — | FB032601 | FatBastard | ППК26127 · 21.07.2026 | CoQ-PP_26-081 | ППК26127 · 21.07.2026 = 7.77 | — | — |
| — | GG032601 | GorillaGlue | ППК26128 · 21.07.2026 | CoQ-PP_26-082 | ППК26128 · 21.07.2026 = 7.88 | — | — |
| — | JD022601 | JellyDonutz | ППК26115 · 30.06.2026 | CoQ-PP_26-083 | ППК26115 · 30.06.2026 = 7.73 | — | — |
| — | P160012 | GrapePie | ППК26117 · 06.07.2026 | — at issue — | ППК26117 · 06.07.2026 = 6.31 | — | — |
| — | P160022 | GrapePie | ППК26118 · 06.07.2026 | — at issue — | ППК26118 · 06.07.2026 = 6.67 | — | — |
| — | P160032 | GrapePie | ППК26119 · 06.07.2026 | — at issue — | ППК26119 · 06.07.2026 = 6.78 | — | — |

