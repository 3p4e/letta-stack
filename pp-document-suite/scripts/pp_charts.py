"""
pp_charts.py — Purely Plant data-visualisation engine (matplotlib, Agg backend).

Produces house-style PNG charts for statistical/justification figures, then embed them with
pp_format.figure() (skill) or skill_helpers.figure() (AM/validation engine). Chart text is English;
the bilingual MK|EN caption is added in the .docx by the figure() helper.

Palette: navy #2B547E primary, red for fails/limits, mint/cream/rose accents (matches the doc palette).
Each function writes a PNG and returns its path. Requires: matplotlib, numpy.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

NAVY = "#2B547E"; RED = "#C0392B"; GREEN = "#1E8449"; GREY = "#595959"
SERIES = [NAVY, "#2980B9", "#27AE60", "#E67E22", "#8E44AD"]


def _style(ax, title, xlabel, ylabel):
    ax.set_title(title, color=NAVY, fontsize=11, fontweight="bold")
    ax.set_xlabel(xlabel, fontsize=9); ax.set_ylabel(ylabel, fontsize=9)
    ax.grid(True, color="#DDDDDD", linewidth=0.6); ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(labelsize=8)


def _save(fig, out):
    fig.tight_layout(); fig.savefig(out, dpi=150, bbox_inches="tight"); plt.close(fig)
    return out


def horrat_bar(levels, horrat, passmask, out, limit=2.0):
    fig, ax = plt.subplots(figsize=(6.8, 3.6))
    ax.bar(levels, horrat, color=[NAVY if p else RED for p in passmask], width=0.6)
    ax.axhline(limit, color=RED, ls="--", lw=1.2, label=f"Acceptance HorRat_r ≤ {limit}")
    for i, v in enumerate(horrat):
        ax.text(i, v + 0.05, f"{v:.2f}", ha="center", va="bottom", fontsize=8)
    _style(ax, "Repeatability acceptance: HorRat_r by level", "Level", "HorRat_r")
    ax.legend(fontsize=8, frameon=False)
    return _save(fig, out)


def horwitz_plot(means, rsdr, out):
    fig, ax = plt.subplots(figsize=(6.8, 3.8))
    xs = np.linspace(min(means) * 0.8, max(means) * 1.1, 250); Cs = xs / 100.0
    rsdR = 2 * Cs ** (-0.1505)
    ax.plot(xs, rsdR, color=NAVY, lw=1.5, label="Horwitz RSD_R = 2·C^−0.1505")
    ax.plot(xs, 0.66 * rsdR, color=GREEN, lw=1.2, ls="--", label="Predicted repeatability (0.66·RSD_R)")
    ax.plot(xs, 1.32 * rsdR, color=RED, lw=1.0, ls=":", label="HorRat = 2 limit (1.32·RSD_R)")
    ax.scatter(means, rsdr, color=NAVY, zorder=5, s=30, label="Observed RSDr")
    for x, y in zip(means, rsdr):
        ax.annotate(f"{y:.1f}", (x, y), textcoords="offset points", xytext=(4, 4), fontsize=7)
    ax.set_xscale("log")
    _style(ax, "Observed precision vs Horwitz model", "Mean LoD % (log scale)", "RSD %")
    ax.legend(fontsize=7, frameon=False)
    return _save(fig, out)


def guardband(spec, U, out, lo=None, hi=None):
    fig, ax = plt.subplots(figsize=(6.8, 2.4))
    lo = lo if lo is not None else spec - 3 * U; hi = hi if hi is not None else spec + 3 * U
    ax.axvspan(lo, spec - U, color="#EAFAF1", label="PASS")
    ax.axvspan(spec - U, spec + U, color="#FEF9E7", label="Guard band")
    ax.axvspan(spec + U, hi, color="#FDEDEC", label="FAIL")
    ax.axvline(spec, color=NAVY, lw=1.6); ax.text(spec, 0.78, f" Spec {spec:.1f}%", color=NAVY, fontsize=8)
    for v in (spec - U, spec + U):
        ax.axvline(v, color=GREY, ls="--", lw=1); ax.text(v, 0.06, f"{v:.2f}", ha="center", fontsize=7)
    ax.set_yticks([]); ax.set_xlim(lo, hi)
    _style(ax, f"Decision rule (ISO/IEC 17025 §7.8.6) — U = ±{U:.2f}% MC", "LoD % (MC)", "")
    ax.legend(fontsize=7, frameon=False, loc="upper center", ncol=3)
    return _save(fig, out)


def regression_scatter(x, y, groups, slope, intercept, out, r=None):
    fig, ax = plt.subplots(figsize=(6.6, 5.0))
    gl = []
    for g in groups:
        if g not in gl:
            gl.append(g)
    for k, g in enumerate(gl):
        xs = [x[i] for i in range(len(x)) if groups[i] == g]
        ys = [y[i] for i in range(len(y)) if groups[i] == g]
        ax.scatter(xs, ys, color=SERIES[k % len(SERIES)], s=24, label=g, zorder=4)
    lim = [min(min(x), min(y)) * 0.95, max(max(x), max(y)) * 1.05]
    ax.plot(lim, lim, color=GREY, ls=":", lw=1, label="identity y = x")
    xs = np.linspace(lim[0], lim[1], 100)
    ax.plot(xs, slope * xs + intercept, color=RED, lw=1.6,
            label=f"OLS y = {slope:.4f}x {intercept:+.4f}")
    if r is not None:
        ax.text(0.04, 0.92, f"r = {r:.4f},  R² = {r * r:.4f}", transform=ax.transAxes, fontsize=8, color=NAVY)
    _style(ax, "Correlation: Ph.Eur (reference) vs HMA", "HMA LoD %", "Ph.Eur LoD %")
    ax.legend(fontsize=7, frameon=False); ax.set_xlim(lim); ax.set_ylim(lim)
    return _save(fig, out)


def bland_altman(means, diffs, bias, lo, hi, out):
    fig, ax = plt.subplots(figsize=(6.8, 4.2))
    ax.scatter(means, diffs, color=NAVY, s=24, zorder=4)
    ax.axhline(bias, color=RED, lw=1.4, label=f"mean bias {bias:+.3f}")
    ax.axhline(lo, color=GREY, ls="--", lw=1, label=f"−1.96·SD {lo:+.3f}")
    ax.axhline(hi, color=GREY, ls="--", lw=1, label=f"+1.96·SD {hi:+.3f}")
    ax.axhline(0, color="#BBBBBB", lw=0.8)
    _style(ax, "Bland–Altman agreement", "Mean of methods, % MC", "Difference (HMA − Ph.Eur), % MC")
    ax.legend(fontsize=7, frameon=False)
    return _save(fig, out)


def bias_bar(levels, bias, out):
    fig, ax = plt.subplots(figsize=(6.8, 3.4))
    ax.bar(levels, bias, color=NAVY, width=0.6)
    for i, v in enumerate(bias):
        ax.text(i, v + 0.02, f"{v:+.3f}", ha="center", va="bottom", fontsize=8)
    ax.axhline(0, color=GREY, lw=0.8)
    _style(ax, "Systematic bias by range (HMA − Ph.Eur)", "Range", "Bias, % MC")
    return _save(fig, out)


def qratio_bar(levels, q, passmask, out, limit=2.0):
    fig, ax = plt.subplots(figsize=(6.8, 3.4))
    ax.bar(levels, q, color=[NAVY if p else RED for p in passmask], width=0.6)
    ax.axhline(limit, color=RED, ls="--", lw=1.2, label=f"limit Q ≤ {limit}")
    for i, v in enumerate(q):
        ax.text(i, v + 0.05, f"{v:.2f}", ha="center", va="bottom", fontsize=8)
    _style(ax, "Precision ratio Q = s_HMA / s_ref by range", "Range", "Q")
    ax.legend(fontsize=8, frameon=False)
    return _save(fig, out)
