# docengine.app.house_codes — the document code convention of the Purely Plant QMS and its register.
#
# Head of QC, 18.10.2026: one code form everywhere, the form of the master list QALI 001 (and of the
# QC registry kept with the ACME_SOP drafts): family letters, three digits, an annex as "A" + two digits.
#   QCSOP011   QCT017   QCLB021   QCSPW005   QCCoA001   QCSOP011A01   WHSOP003A04
# Latin letters only (QALI 001 wrote one annex with a Cyrillic "А"), no space, no "_" or "-". Codes typed
# in any of the forms in circulation ("QCSOP 011", "QCSOP_011_A01", "WHSOP_003", "QCSOP011А01") are
# normalised to it at the door; a code that cannot be (a file name, "labels_raw (final) v3") is refused.
#
# A number not yet confirmed is written XXX (Head of QC, 18.10.2026: "all QA SOP drafts should be xxx unknown numbers
# actualy until not confirmed"): QASOPXXX, QASOPXXXA06. "QASOP_0XX" and "qasop xxx" are read as QASOPXXX. A family the
# register marks `unconfirmed_families` (QASOP; EQSOP, whose family itself is not yet approved) is given XXX by
# next_code, never a guessed number.
#
# The register (register/*.yaml) is the engine's working copy of the codes in use. The engine is a research and
# development tool outside the QMS (Head of QC, 18.10.2026): QALI 001 is the master, and where they differ QALI 001 wins.
# The next free number of a family is one above the highest number the register, the document registry
# or any open job holds; numbers are never reused (QCSOP020 was withdrawn, not freed) and gaps are not filled.
import re
from datetime import date
from pathlib import Path

import yaml

REGISTER_DIR = Path(__file__).resolve().parents[1] / "register"

# Cyrillic letters that look like Latin ones and turn up in typed codes.
_LOOKALIKE = str.maketrans("АВСЕНІЈКМОРТХУаесорху", "ABCEHIJKMOPTXYaecopxy")
_CODE = re.compile(r"^(?P<fam>[A-Z]{2,8}?|[A-Z]{2}COA)(?P<num>\d{1,3}|0?XXX|0XX)(?:A(?P<annex>\d{1,2}))?$")
XXX = "XXX"


def normalize(raw: str) -> str | None:
    """The house form of a typed code, or None when it is not a document code."""
    s = (raw or "").translate(_LOOKALIKE).upper()
    s = re.sub(r"[\s_\-./]", "", s)
    m = _CODE.match(s)
    if not m:
        return None
    fam = m["fam"].replace("COA", "CoA") if m["fam"].endswith("COA") else m["fam"]
    out = fam + (XXX if "X" in m["num"] else f"{int(m['num']):03d}")
    if m["annex"]:
        out += f"A{int(m['annex']):02d}"
    return out


def parts(code: str) -> tuple[str, int | None, int | None]:
    """(family, number or None when it is XXX, annex number or None) of a code already in house form."""
    m = _CODE.match(code.upper())
    if not m:
        raise ValueError(f"not a house code: {code!r}")
    fam = code[: len(m["fam"])]
    num = None if "X" in m["num"] else int(m["num"])
    return fam, num, int(m["annex"]) if m["annex"] else None


def unconfirmed_families() -> set[str]:
    """Families whose numbers are not yet confirmed (register key `unconfirmed_families`)."""
    out = set()
    for f in sorted(REGISTER_DIR.glob("*.yaml")):
        out |= set((yaml.safe_load(f.read_text(encoding="utf-8")) or {}).get("unconfirmed_families") or [])
    return out


def load_register() -> list[dict]:
    """Every register row from register/*.yaml, codes in house form, with the review date filled in."""
    rows = []
    for f in sorted(REGISTER_DIR.glob("*.yaml")):
        data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        for r in data.get("documents", []):
            code = normalize(r["code"])
            if not code:
                raise ValueError(f"{f.name}: {r['code']!r} is not a house code")
            row = {"register": f.stem, "department": data.get("department", ""), **r, "code": code}
            eff = r.get("effective_date")
            if isinstance(eff, date) and not r.get("review_date"):
                row["review_date"] = eff.replace(year=eff.year + int(data.get("review_years", 3)))
            for k in ("effective_date", "review_date"):
                if isinstance(row.get(k), date):
                    row[k] = row[k].isoformat()
            rows.append(row)
    return rows


def next_code(family: str = "", parent: str = "", taken: set[str] = frozenset()) -> str:
    """The next free code: of a family (QCSOP → QCSOP025) or, given a parent, of its annexes
    (QCSOP011 → QCSOP011A02). `taken` adds codes held outside the register (built documents, open jobs)."""
    codes = {r["code"] for r in load_register()} | {c for c in (normalize(t) for t in taken) if c}
    if parent:
        p = normalize(parent)
        if not p or parts(p)[2] is not None:
            raise ValueError(f"parent must be a document code without an annex number: {parent!r}")
        used = [parts(c)[2] for c in codes if c.startswith(p + "A") and parts(c)[2] is not None]
        return f"{p}A{max(used, default=0) + 1:02d}"
    fam = (family or "").translate(_LOOKALIKE).upper().replace("COA", "CoA")
    if not re.fullmatch(r"[A-Z]{2,8}|[A-Z]{2}CoA", fam):
        raise ValueError(f"not a code family: {family!r}")
    if fam in unconfirmed_families():
        return fam + XXX
    used = [parts(c)[1] for c in codes if parts(c)[0] == fam and parts(c)[2] is None and parts(c)[1] is not None]
    return f"{fam}{max(used, default=0) + 1:03d}"
