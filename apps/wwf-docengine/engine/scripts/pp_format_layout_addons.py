# -*- coding: utf-8 -*-
"""
pp_format_layout_addons.py — INTELLIGENT COMPACT LAYOUT for pp-document-suite.

NOTE (2026-06-30): the implementation was promoted into scripts/pp_format.py so that
kv_block()/cell08()/value_span() are first-class `pf.` primitives (consistent with every
other engine helper). This module is now a thin RE-EXPORT shim kept so that the §6D
filename reference and any existing `import pp_format_layout_addons` continue to resolve —
there is ONE source of truth (pp_format.py); nothing is duplicated here.

Captures the Head-of-QC corrections (2026-06-30):
 * VALUE cells are sized to the EXPECTED HAND-ENTRY, never maximised (a Date/Batch needs ~2.6 cm).
 * LABEL ("action") cells are minimal width.
 * Multiple label|value pairs PACK per row (6-col grid); long values SPAN.
 * Line spacing 0.8, NO space before/after in every cell (incl. label cells).
 * Two sections (e.g. Transfer information + Material description) merge into ONE table.

Usage (either import path works):
    import pp_format as pf
    pf.kv_block(d, sections)                 # preferred — first-class primitive
or
    from pp_format_layout_addons import kv_block, cell08, value_span
    kv_block(d, sections)
"""
from pp_format import cell08, _merge, value_span, kv_block

__all__ = ["cell08", "_merge", "value_span", "kv_block"]

# ---------------------------------------------------------------------------
# Example (this is exactly how QCSOP 011_A02's metadata block is built):
#
# import pp_format as pf
# pf.kv_block(d, [
#     ("Информации за преносот", "Transfer information", [
#         ("Запис бр.", "Record No.", "[ГГГГ-NNN]", "[YYYY-NNN]", 10),
#         ("Датум", "Date", "__________", "", 10),
#         ("Образложение", "Rationale", "____ (зошто)", "(why)", 10),
#         ("Тип на пренос", "Transfer type",
#          "☐ Производство→Преработка ☐ Магацин→КК ☐ КК→Магацин ☐ Друго",
#          "☐ Prod.→Proc. ☐ WH→QC ☐ QC→WH ☐ Other", 60),
#         ("Основа (реф. док.)", "Basis",
#          "согласно план QCSPL 001.1/26 на основ на налог PP-CEO-ORD-001/26",
#          "per plan QCSPL 001.1/26 on order …", 40),
#         ("Услови", "Conditions",
#          "____ (асептично; враќање со ажур. етикети)",
#          "(aseptic; return w/ updated labels)", 40),
#     ]),
#     ("Опис на материјалот", "Material description", [
#         ("Сорта", "Strain", "__________", "", 10),
#         ("Серија / Лот", "Batch / Lot", "__________", "", 10),
#         ("Форма", "Form", "☐ Готов ☐ bulk ☐ loose", "", 12),
#         ("Прим. пакување", "Primary pack",
#          "на пр. 400 g трослојна кеса, 10 кеси/картон",
#          "e.g. 400 g triple-foil bag, 10/carton", 40),
#     ]),
# ])
