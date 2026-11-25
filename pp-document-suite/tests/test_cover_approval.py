"""Approval table on the cover page (pp_report.cover_page).

Until 25.11.2026 `cover_page(..., approval_rows=[...])` replaced the whole default
table with the caller's rows and silently dropped `approval_qp` / `approval_qp_name`.
The HPLC verification protocol, QCWI 023, the AMVR template and the resource plan
all went out with no approver row. These tests build the cover on the house
template and read the approval table back off the document.

They run without LibreOffice, Letta or a network.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

pytest.importorskip("docx", reason="python-docx is the engine's own dependency")
from docx import Document                                          # noqa: E402
import pp_format as pf                                             # noqa: E402
import pp_report as R                                              # noqa: E402

PREPARED = ("Изготвил (Менаџер на Сектор Контрола на Квалитет) | Prepared (QC Department Manager)",
            "Blagoj Nikolov, M.Pharm.")
REVIEWED = ("Прегледал (QA) | Reviewed (QA)", "Jovana Romevska, M.Pharm.")
QP_LABEL = "Одобрил (QP) | Approved (QP)"
QP_NAME = "Sofija Petrova, M.Pharm."
APPROVAL_HEADER = "Дејство"        # head_cell prints the pair without the pipe: "Дејство Action"


def approval_rows_of(**kw):
    """Build a cover and return the (label, name) rows of its approval table."""
    d = Document(pf.PP_TEMPLATE)
    R.wipe_body(d)
    R.cover_page(d, "НАСЛОВ", "TITLE", [("Документ | Document", "TEST")], **kw)
    tables = [t for t in d.tables if t.cell(0, 0).text.strip().startswith(APPROVAL_HEADER)]
    assert len(tables) == 1, "the cover must carry exactly one approval table"
    t = tables[0]
    return [(r.cells[0].text.strip(), r.cells[1].text.strip()) for r in t.rows[1:]]


def test_custom_rows_keep_the_approver():
    """The defect: custom rows + approval_qp gave a table with no approver row."""
    rows = approval_rows_of(approval_rows=[PREPARED, REVIEWED],
                            approval_qp=QP_LABEL, approval_qp_name=QP_NAME)
    assert rows == [PREPARED, REVIEWED, (QP_LABEL, QP_NAME)]
    assert sum(1 for a, _ in rows if a == QP_LABEL) == 1


def test_approver_already_in_custom_rows_is_not_doubled():
    """A caller that already lists the approver must not get it twice; the label
    match ignores case and whitespace runs."""
    rows = approval_rows_of(approval_rows=[PREPARED, REVIEWED, ("  одобрил (QP)  |  Approved (QP)", QP_NAME)],
                            approval_qp=QP_LABEL, approval_qp_name=QP_NAME)
    assert len(rows) == 3
    assert sum(1 for a, _ in rows if R._approval_label_key(a) == R._approval_label_key(QP_LABEL)) == 1


def test_custom_rows_without_approver_argument_are_left_alone():
    """Builders that put their own approver under another label (QA, QP) and pass
    no approval_qp must not get the default QC-manager approver added: that would be
    a signatory nobody chose."""
    own = [PREPARED, REVIEWED, ("Одобрил | Approved (QA)", "")]
    assert approval_rows_of(approval_rows=own) == own


def test_default_table_unchanged():
    """No approval_rows: prepared / reviewed / approver, as before."""
    rows = approval_rows_of()
    assert rows == [R._COVER_PREPARED, R._COVER_REVIEWED, R._COVER_APPROVER]


def test_default_table_takes_the_given_approver():
    rows = approval_rows_of(approval_qp=QP_LABEL, approval_qp_name=QP_NAME)
    assert rows[-1] == (QP_LABEL, QP_NAME) and len(rows) == 3
