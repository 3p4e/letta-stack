# -*- coding: utf-8 -*-
"""pp_data.py — dataset binding, analytical statistics, provenance & self-verification
for the Purely Plant document suite.

PRINCIPLE (single source of truth): the bound experimental dataset is the ONLY origin of
every reported figure. Compute each statistic here and INJECT it into the document's prose
AND summary tables at build time; NEVER hand-type an aggregate (mean, SD, RSD, bias, LoA,
CI, r, slope, Q, u_c, U …) into narrative or summary cells — that is exactly how figures
drift from the data. After the document is built, re-derive every figure and assert it
matches what is printed (see assert_consistent / the §6A review).

DOCUMENT-AGNOSTIC: nothing here assumes a particular study, strain, matrix, range set, or
number of levels. A validation with 3 levels of one matrix and a verification with 6 levels
of another are both handled by binding their own dataset and calling the same helpers.
No third-party dependency (pure stdlib) so it runs under any harness with CPython.
"""
import os, csv, json, math, statistics, hashlib, datetime

# ---------------------------------------------------------------- dataset binding
def load_dataset(path):
    """Load a bound dataset and return a native object.
       .json -> the parsed object as-is; .csv/.tsv -> list[dict] (header-keyed rows)."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".json":
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    if ext in (".csv", ".tsv"):
        delim = "\t" if ext == ".tsv" else ","
        with open(path, encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f, delimiter=delim))
    raise ValueError("pp_data.load_dataset: unsupported dataset type %r "
                     "(use .json / .csv / .tsv, or pre-parse and pass the values)" % ext)

def provenance(path):
    """ALCOA+ data-provenance record to print in the document's data note."""
    b = open(path, "rb").read()
    return {"file": os.path.basename(path),
            "sha256": hashlib.sha256(b).hexdigest()[:16],
            "bytes": len(b),
            "modified": datetime.datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M")}

def num(x):
    """Tolerant numeric parse (handles comma decimals, ± signs, blanks)."""
    try:
        return float(str(x).replace("±", "").replace(",", ".").strip())
    except Exception:
        return None

# ---------------------------------------------------------------- descriptive
def mean(v): return statistics.mean(v)
def sd(v):   return statistics.stdev(v)  if len(v) > 1 else 0.0   # sample SD (n-1)
def psd(v):  return statistics.pstdev(v) if len(v) > 1 else 0.0   # population SD (n)
def rsd(v):  m = mean(v); return 100.0 * sd(v) / m if m else 0.0
def sem(v):  return sd(v) / len(v) ** 0.5 if v else 0.0

def t975(df):
    """Two-sided 95% Student-t quantile via Cornish–Fisher expansion (no SciPy needed).
       Accurate to ~1e-3 for df>=5; converges to z=1.95996 for large df."""
    if df < 1:
        return 12.706
    z = 1.959963985
    return (z + (z**3 + z) / (4 * df)
              + (5 * z**5 + 16 * z**3 + 3 * z) / (96 * df**2)
              + (3 * z**7 + 19 * z**5 + 17 * z**3 - 15 * z) / (384 * df**3))

def ci95(v):
    """95% confidence interval of the mean (t-based)."""
    m = mean(v); h = t975(len(v) - 1) * sem(v)
    return (m - h, m + h)

def pooled_sd(groups):
    """Pooled (within-group) SD from a list of value-lists — intermediate precision."""
    num_ = sum((len(g) - 1) * statistics.variance(g) for g in groups if len(g) > 1)
    den_ = sum(len(g) - 1 for g in groups if len(g) > 1)
    return (num_ / den_) ** 0.5 if den_ else 0.0

# ---------------------------------------------------------------- comparison / correlation
def _paired(x, y):
    n = min(len(x), len(y))
    return list(x[:n]), list(y[:n])

def bland_altman(x, y):
    """Method-comparison agreement. bias = mean(x - y); LoA = bias ± 1.96·SD(pop);
       plus the t-based 95% CI of the mean. Returns a dict (all %MC if inputs are %MC)."""
    x, y = _paired(x, y)
    d = [a - b for a, b in zip(x, y)]; n = len(d)
    b = statistics.mean(d); s_pop = psd(d); s_smp = sd(d)
    h = t975(n - 1) * s_smp / n ** 0.5 if n > 1 else 0.0
    return {"n": n, "bias": b, "sd_pop": s_pop, "sd_samp": s_smp,
            "loa_lo": b - 1.96 * s_pop, "loa_hi": b + 1.96 * s_pop,
            "ci_lo": b - h, "ci_hi": b + h}

def pearson(x, y):
    x, y = _paired(x, y); mx = statistics.mean(x); my = statistics.mean(y)
    sxx = sum((a - mx) ** 2 for a in x); syy = sum((b - my) ** 2 for b in y)
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    return sxy / (sxx * syy) ** 0.5 if sxx and syy else 0.0

def ols(x, y):
    """Ordinary least-squares regression y = slope·x + intercept (+ r, r²)."""
    x, y = _paired(x, y); mx = statistics.mean(x); my = statistics.mean(y)
    sxx = sum((a - mx) ** 2 for a in x); sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    m = sxy / sxx if sxx else 0.0; r = pearson(x, y)
    return {"slope": m, "intercept": my - m * mx, "r": r, "r2": r * r}

def q_ratio(alt, ref):
    """Precision ratio SD_alt / SD_ref (compendial-equivalence screen; accept Q ≤ 2.0)."""
    sr = sd(ref)
    return sd(alt) / sr if sr else float("inf")

def expanded_U(bias, s, k=2):
    """Combined & expanded uncertainty: u_c = √(bias² + s²); U = k·u_c."""
    uc = (bias ** 2 + s ** 2) ** 0.5
    return {"u_c": uc, "U": k * uc}

# ---------------------------------------------------------------- self-verification
def assert_consistent(reported, recomputed, tol=0.01, label="figures"):
    """Fail the build if any reported value diverges from the dataset recompute beyond tol.
       reported / recomputed: dicts keyed identically. Use in the §6A pre-delivery review."""
    bad = []
    for k, rep in reported.items():
        rc = recomputed.get(k)
        if rc is None:
            continue
        try:
            if abs(float(rep) - float(rc)) > tol:
                bad.append("%s: doc=%s data=%.4f" % (k, rep, float(rc)))
        except (TypeError, ValueError):
            if str(rep).strip() != str(rc).strip():
                bad.append("%s: doc=%r data=%r" % (k, rep, rc))
    if bad:
        raise AssertionError("[%s] reported != recomputed -> %s" % (label, "; ".join(bad)))
    return True
