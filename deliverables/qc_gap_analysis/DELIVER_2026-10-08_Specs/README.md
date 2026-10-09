# Specifications, 08.10.2026

Head of QC, 08.10.2026: *"make the pinpoint edits only to these word documents and then give me merged word files
with all of these changes, and one final merged word document with all the specs"*, and *"grapes and cream grade
7.00% into 8.00% +-0.8%"*.

What changed (nine sheets; every other sheet is as on 07.10.2026):

| sheet | THC | phenotype |
| --- | --- | --- |
| OPM-I | 20.00 | Hybrid · INDICA DOMINANT (OPM-II to V already) |
| KC-I | 18.00 | Hybrid |
| HPA-III, HPA-II, HPA-I | 15.00, 18.00, 22.00 | Hybrid |
| BG-II, BG-I | 22.00, 26.00 | Hybrid |
| BSS-III | 20.00 | Hybrid |
| GRC-IV | **8.00 ± 0.80** (7.20–8.79 %), `GRC_THC8 : CBD1` | unchanged |

| file | holds |
| --- | --- |
| `QCSP_001_<strain>_v.01_…_all_grades.pdf` / `.docx` | one per changed strain (OPM, KC, HPA, BG, BSS, GRC): all its grades, PDF and Word |
| `QCSP_001_ImB_all_58_specifications_2026-10-08.pdf` / `.docx` | all 58 sheets in one file |

The Word files are the PDF pages with real, editable text in the house faces (`pdf_to_docx_exact.py`); each has as
many pages as its PDF. The single sheets are in `../specs/QCSP_001_ImB/{PDF,DOCX}/`.

    python3 tracker/apply_grc_grade_8_2026-10-08.py --apply
    python3 specs/build_qcsp_imb.py && python3 specs/print_qcsp_imb.py <sheets>
    python3 specs/merge_qcsp_by_strain.py
    python3 tracker/build_spec_word_set_2026-10-08.py
