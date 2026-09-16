# Potency grades per strain — 15.09.2026

`Potency_specifications_233.pdf` is the Head of QC's potency specification (Drive id
`1NEZSRNPt5GtPvUfpi1dotAG9dkorEAGn`, created 15.09.2026, 60,398 bytes, SHA-256
`998daf310944c1fc2b94b8f9880b6427f4f55b208238cd306922c458c1a17677`): one page per strain
with the grade nominals, tolerances and specification windows (starting nominals QCSP 001
v.03, results CoQ_Analysis_Master_v25), and the measured Total Δ9-THC results each page
rests on. `Potency_specifications_233.txt` is its text layer (pdftotext, not OCR);
`../potency_grades.py` parses it into `../potency_grades_2026-09-15.csv`, one row per strain
and grade, checking the number of grade rows parsed against the count each page states.
The workbook's `Potency Grades` tab renders the CSV (v29).
