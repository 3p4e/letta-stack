# Shimadzu HPLC training course (30.10.2026)

`Shimadzu_HPLC_Training_Course_2026-10-30.pdf`: a 67-page, step-by-step course for the Cannabis Analyzer for Potency (Shimadzu i-Series LC with PDA, LabSolutions DB).
It covers 12 modules, an assessment with answer key, a training record and references. Status: draft for QA review; QA assigns the document code.

## Sources
- The five Shimadzu manuals in the Drive folder `17FXzOkFeaBVk6P16yZhrTnYFC5t3O3pn`:
  - LC Getting Started Guide 223-10811C
  - Operators Guide 223-10821H
  - System Users Guide 223-10815S
  - Installation & Maintenance Guide 223-10817AC
  - Data Acquisition & Processing Theory Guide 223-60090O
- The Shimadzu i-Series Virtual Advisor and LC Troubleshooting Guide SSI-12-24.
- QCWI 001 v01.
- Screen photographs of our instrument from 15.09 and 30.10.2026.

Every procedure cites the manual page it comes from.

## Rebuild
1. Put the five manuals in `pdf/` as `GS.pdf`, `OPG.pdf`, `SUG.pdf`, `IM.pdf`, `TH.pdf`. The Drive download link works for this folder: `https://drive.google.com/uc?export=download&id=<file id>`.
2. Put the screen photos in `photos/`, or point `PP_PHOTOS` at their directories.
3. Run:

```bash
pip install pymupdf pillow
python3 crop2.py GS:4,12,... OPG:11,... SUG:5,... IM:66,...   # crops the figures to fig/; page lists are in the build history
python3 build.py "$PWD/Shimadzu_HPLC_Training_Course_2026-10-30.pdf"   # Chromium via Playwright
```

The figures are cropped from Shimadzu's copyrighted manuals and are for internal training only. They are not committed; only the PDF is.
