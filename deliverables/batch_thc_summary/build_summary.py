# -*- coding: utf-8 -*-
"""Builds ONE table, nothing else: the 12 requested P-batch numbers, their
cultivation batch numbers, last-tested Total Delta9-THC, eCoA code (labeled PP
where the certificate is an in-house PurelyPlant document), and date of issue.
Bound to dataset.json; the self-check re-derives every printed figure and
asserts it matches before the file is saved (pp-document-suite §6B).
"""
import json
import hashlib
import sys
import os

sys.path.insert(0, os.path.expanduser(
    "~/.claude/skills/synced/pp-document-suite/scripts"))

from docx import Document
import pp_report as pr

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.expanduser(
    "~/.claude/skills/synced/pp-document-suite/assets/PP_BASE_TEMPLATE.docx")
DATASET = os.path.join(HERE, "dataset.json")
OUT = os.path.join(HERE, "P-Batch_Total_THC_Summary.docx")


def load_dataset():
    with open(DATASET, encoding="utf-8") as f:
        data = json.load(f)
    sha = hashlib.sha256(open(DATASET, "rb").read()).hexdigest()
    return data, sha


def fmt_date(iso):
    if not iso:
        return "—"
    y, m, d = iso.split("-")
    return f"{d}.{m}.{y}"


def fmt_pct(v):
    """House numeric rule: exactly two decimals, % immediately after the digit,
    no space; Macedonian uses a decimal comma, English a decimal point."""
    if v is None:
        return None, None
    return f"{v:.2f}".replace(".", ",") + "%", f"{v:.2f}%"


def ecoa_label(row):
    if row["ecoa_code"] is None:
        return "—"
    return ("PP · " if row.get("is_pp") else "") + row["ecoa_code"]


def build(data):
    d = Document(TEMPLATE)
    pr.informal_header(
        d,
        "Табела: вкупен Δ9-ТХЦ по бараните P-броеви",
        "Table: Total Δ9-THC by requested P-numbers",
        tag_mk="Работен извадок", tag_en="Working extract",
    )
    pr.wipe_body(d)

    headers = ["P-број | P-number", "Култивациска серија | Cultivation batch",
               "Вкупно Δ9-ТХЦ | Total Δ9-THC",
               "еКоА код | eCoA code", "Датум на издавање | Date of issue"]
    rows = data["rows"]
    t = d.add_table(rows=len(rows) + 1, cols=len(headers))
    for j, h in enumerate(headers):
        pr.cellfmt(t.cell(0, j), h, None, 9, pr.WHITE, bold=True, fill=pr.NAVYF)
    for i, row in enumerate(rows, start=1):
        pr.cellfmt(t.cell(i, 0), row["p_number"], None, 10, pr.BLACK, bold=True)
        pr.cellfmt(t.cell(i, 1), row["cultivation_batch"], None, 10, pr.BLACK)
        mk, en = fmt_pct(row["thc_pct"])
        if mk is None:
            pr.cellfmt(t.cell(i, 2), "—", None, 10, pr.GREY)
        else:
            pr.cellfmt(t.cell(i, 2), mk, en, 10, pr.BLACK)
        pr.cellfmt(t.cell(i, 3), ecoa_label(row), None, 9, pr.BLACK)
        pr.cellfmt(t.cell(i, 4), fmt_date(row["date"]), None, 9, pr.BLACK)
    pr.fixed(t, weights=[2.3, 3.4, 2.7, 5.36, 2.7])

    d.save(OUT)
    return OUT


def self_check(data):
    rows = data["rows"]
    assert len(rows) == 12, f"expected 12 requested batches, dataset has {len(rows)}"
    assert len(set(r["p_number"] for r in rows)) == 12, "duplicate P-number in dataset"
    missing = [r["p_number"] for r in rows if r["thc_pct"] is None]
    assert missing == ["P060122", "P060132"], f"unexpected missing set: {missing}"
    assert sum(1 for r in rows if r["thc_pct"] is not None) == 10
    pp_rows = [r["p_number"] for r in rows if r.get("is_pp")]
    assert pp_rows == ["P050192", "GG1024"], f"unexpected PP-labeled set: {pp_rows}"
    for r in rows:
        if r["thc_pct"] is None:
            continue
        mk, en = fmt_pct(r["thc_pct"])
        assert mk.endswith("%") and "," in mk and " " not in mk, f"house format violated: {mk}"
        assert en.endswith("%") and "." in en and " " not in en, f"house format violated: {en}"
    print("SELF-CHECK OK — 12 rows, 2 confirmed-absent, 10 certified, "
          "2 correctly labeled PP in-house.")


if __name__ == "__main__":
    data, sha = load_dataset()
    self_check(data)
    out = build(data)
    print(f"dataset sha256={sha}")
    print(f"built: {out}")
