#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A counted result above its criterion is marked, by Ph. Eur. 5.1.4, on every certificate.

    python3 deliverables/qc_gap_analysis/mark_microbial_band.py [--dry-run]

Ph. Eur. 5.1.4 does not read an acceptance criterion as a hard ceiling. For a criterion
of 10^n the maximum acceptable count is 2 x 10^n: "10^1 CFU: maximum acceptable count =
20; 10^2 CFU: maximum acceptable count = 200; 10^3 CFU: maximum acceptable count = 2000;
and so forth." So a colony count between its criterion and twice it is not out of
specification — it is undetermined, and the certificate marks it rather than passing it in
silence. Above twice the criterion it is out of specification.

The Claude Design package already checks this (assertion A12) and already colours the
cell from the determination's status — amber for UNDETERMINED, red for OUT OF
SPECIFICATION. What was missing was the step that puts the word in the status, so a
counted result that landed in the band printed in the ordinary weight and A12 reported an
unmarked cell. This is that step, and it is a rule over every row rather than a note
against the rows that happened to raise it.

Only #9.1, #9.2 and #9.3 are counted determinations — the criterion carries CFU/g and the
result is a colony count. #9.4 and #9.5 are absence tests and #10 to #12 are chemistry,
where a limit is a limit.
"""
import argparse, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "coq_artifact_data.json")
SUP = {"⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4",
       "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9"}
_SUPRUN = re.compile("([\u2070\u00b9\u00b2\u00b3\u2074\u2075\u2076\u2077\u2078\u2079]+)")
_MANT = re.compile(r"(\d+(?:[.,]\d+)?)\s*(?:\u00d7|x)\s*10\^(\d+)")
_POW = re.compile(r"10\^(\d+)")
_PLAIN = re.compile(r"(\d+(?:[.,]\d+)?)")
BAND = "UNDETERMINED (Ph. Eur. 5.1.4)"
OOS = "OUT OF SPECIFICATION"


def value(s):
    """The number a counted cell states, or None.

    >>> value("1.8 \u00d7 10\u2074 CFU/g")
    18000.0
    >>> value("\u2264 10\u2074 CFU/g")
    10000.0
    >>> value("3.9 \u00d7 10\u2074 CFU/g")
    39000.0
    >>> value("< 10") is None
    True
    >>> value("Absent | \u041e\u0442\u0441\u0443\u0442\u043d\u0430") is None
    True
    """
    s = str(s or "").split("|")[0].strip()
    if not s or s.startswith("<"):
        return None                      # a bound below the criterion is never in the band
    t = _SUPRUN.sub(lambda m: "^" + "".join(SUP[c] for c in m.group(1)), s)
    m = _MANT.search(t)
    if m:
        return float(m.group(1).replace(",", ".")) * (10.0 ** int(m.group(2)))
    m = _POW.search(t)
    if m:
        return 10.0 ** int(m.group(1))
    m = _PLAIN.search(t)
    return float(m.group(1).replace(",", ".")) if m else None


def mark(data):
    """Put the band word in the status of every counted row that is above its criterion."""
    changed = []
    for c in data["coqs"]:
        for r in c["rows"]:
            crit = str(r.get("crit") or "")
            if "CFU/g" not in crit:
                continue
            lim, got = value(crit), value(r.get("res"))
            if lim is None or got is None or got <= lim + 1e-9:
                continue
            st = str(r.get("st") or "").strip()
            # The desk's own word wins. Where the register already calls the cell out of
            # specification or undetermined, that sentence carries the desk's reasoning and
            # its ordering, and this rule has nothing to add; it exists for a counted
            # result that arrived with neither.
            if re.search(r"OUT OF SPECIFICATION|UNDETERMINED", st, re.I):
                continue
            word = BAND if got <= 2 * lim + 1e-9 else OOS
            r["st"] = word + (" — " + st if st else "")
            changed.append((c.get("regcode") or c.get("n"), c.get("pp") or c.get("cb"),
                            r["no"], str(r.get("res")), crit, word))
    return changed


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--src", default=SRC)
    a = ap.parse_args(argv[1:])
    data = json.load(open(a.src, encoding="utf-8"))
    changed = mark(data)
    print("counted results marked against Ph. Eur. 5.1.4: %d" % len(changed))
    for row in changed:
        print("   %-16s %-11s #%-5s %-16s vs %-14s -> %s" % row)
    if not a.dry_run and changed:
        with open(a.src, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))
        print("written:", a.src)
    return 0


if __name__ == "__main__":
    import doctest
    f, t = doctest.testmod()
    print("%d/%d doctests passed" % (t - f, t))
    raise SystemExit(main(sys.argv) if not f else 1)
