#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Potency study — per-strain distribution figures.

One figure per strain on a fixed 0.0–30.0 % Total Δ⁹-THC horizontal axis:

  • every result ever tested: marker on the axis + a translucent ±1.5 % band
    (the user's requested zone) — overlapping bands stack into a visual
    density of where the strain's results live;
  • a smooth distribution curve (Gaussian KDE, bandwidth 1.5) where n ≥ 3 —
    shape only, no summary statistics (mean/SD/CI) are shown or computed
    into the grade, per owner instruction;
  • the PROPOSED, non-overlapping potency tiers (green spans, labelled
    Pot.-1, Pot.-2 …, each with a full-height shaded zone so the range is
    unmistakable) and the old QCSP standard 4-tier boundaries (faint
    dashed) for contrast.

Also renders an all-strains overview band (one row per strain).
"""
import json
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import sys
sys.path.insert(0, "/root/.claude/skills/synced/pp-document-suite/scripts")
import pp_assets

HERE = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.path.join(HERE, "potency_dataset.json"), encoding="utf-8"))

NAVY = "#2B547E"; GREEN = "#1E8449"; RED = "#C0392B"; GOLD = "#B08424"
INK = "#16232B"; GREY = "#6B7785"
OLD_TIERS = [5.00, 15.90, 22.90, 26.90, 30.00]
BAND = 1.5

plt.rcParams.update(pp_assets.chart_style())
FIGDIR = os.path.join(HERE, "figures")
os.makedirs(FIGDIR, exist_ok=True)


def kde(vals, xs, bw=1.5):
    return [sum(math.exp(-0.5 * ((x - v) / bw) ** 2) for v in vals)
            / (len(vals) * bw * math.sqrt(2 * math.pi)) for x in xs]


def strain_fig(name, st, tiers, stability, fname):
    fig, ax = plt.subplots(figsize=(15.5 / 2.54 * 2.4, 4.6 / 2.54 * 2.4))
    vals = st["values"]

    # full-height shaded zone per proposed tier, drawn first (behind
    # everything) so the potency-grade zone is unmistakable across the
    # whole strip, not just a thin strip near the top
    for i, t in enumerate(tiers):
        lo, hi = t["range"]
        ax.axvspan(lo, hi, ymin=0.0, ymax=1.0, color=GREEN, alpha=0.09, lw=0, zorder=0)
        ax.axvline(lo, color=GREEN, lw=1.0, alpha=0.45, zorder=1)
        ax.axvline(hi, color=GREEN, lw=1.0, alpha=0.45, zorder=1)
        # a genuine, unbridgeable gap: no whole-number nominal exists that
        # could reach this far — hatched red, not a fabricated bridge tier
        if t.get("gap_after") and i + 1 < len(tiers):
            glo, ghi = hi, tiers[i + 1]["range"][0]
            ax.axvspan(glo, ghi, ymin=0.0, ymax=1.0, facecolor=RED, alpha=0.10,
                       hatch="////", edgecolor=RED, lw=0, zorder=0)
            ax.axvline(glo, color=RED, lw=0.9, alpha=0.5, ls=(0, (2, 2)), zorder=1)
            ax.axvline(ghi, color=RED, lw=0.9, alpha=0.5, ls=(0, (2, 2)), zorder=1)

    # ±1.5% zone bands, stacking into a density
    for v in vals:
        ax.axvspan(v - BAND, v + BAND, ymin=0.30, ymax=0.88,
                   color=NAVY, alpha=min(0.14, 0.5 / max(1, len(vals)) + 0.06), lw=0, zorder=2)
    # KDE curve — distribution SHAPE only; no mean/SD/CI is computed or shown
    if len(vals) >= 3:
        xs = [x / 10 for x in range(0, 301)]
        ys = kde(vals, xs)
        top = max(ys)
        ax.plot(xs, [0.30 + 0.56 * y / top for y in ys], color=NAVY, lw=1.6, zorder=5)
    # result markers — enlarged for readability
    ax.scatter(vals, [0.26] * len(vals), marker="o", s=90, color=NAVY,
               edgecolors="white", linewidths=1.1, zorder=7)
    # stability strip (Grape Pie)
    for row in stability:
        y = 0.13
        if row["arm"].startswith("25"):
            ax.scatter([row["total_thc"]], [y], marker="s", s=48, color=GREEN,
                       edgecolors="white", linewidths=0.6, zorder=7)
        else:
            ax.scatter([row["total_thc"]], [y], marker="v", s=52, color=RED,
                       edgecolors="white", linewidths=0.6, zorder=7)
        ax.annotate("M%d" % row["month"], (row["total_thc"], y), textcoords="offset points",
                    xytext=(0, -13), ha="center", fontsize=6.5, color=GREY)
    # proposed tiers — the nominal +/- tolerance label badge, staggered on
    # two rows so neighbouring tiers stay legible
    for i, t in enumerate(tiers):
        lo, hi = t["range"]
        y0 = 0.90 if i % 2 == 0 else 1.00
        ax.add_patch(Rectangle((lo, y0), hi - lo, 0.075, facecolor=GREEN, alpha=0.30,
                               edgecolor=GREEN, lw=1.8, zorder=6))
        ax.text((lo + hi) / 2, y0 + 0.037,
                "Pot.-%d: %.2f%% ±%.2f%%" % (i + 1, t["nominal"], t["tol"]),
                ha="center", va="center", fontsize=8.5, color="#0F3D22", fontweight="bold",
                zorder=8)
    # old tier boundaries
    for x in OLD_TIERS:
        ax.axvline(x, color="#B9C4D0", lw=0.8, ls=(0, (3, 3)), zorder=1)

    ax.set_xlim(0, 30)
    ax.set_ylim(0, 1.12)
    ax.set_yticks([])
    ax.set_xticks(range(0, 31, 5))
    ax.set_xticklabels(["%.1f%%" % x for x in range(0, 31, 5)])
    ax.set_xticks(range(0, 31), minor=True)
    ax.set_xlabel("Вкупен Δ⁹-THC (%w/w)  |  Total Δ⁹-THC (%w/w)", fontsize=9)
    ax.grid(axis="x", which="minor", color="#F0F3F6", linewidth=0.4)
    sub = ("%d резултати · опсег на тестираните резултати %.2f%%–%.2f%% | "
          "%d results · range of tested results %.2f%%–%.2f%%"
          % (st["n"], st["min"], st["max"], st["n"], st["min"], st["max"]))
    ax.set_title("%s   —   %s" % (name, sub), fontsize=10.5, color=INK, loc="left", pad=8)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, fname), dpi=200)
    plt.close(fig)


def overview():
    names = sorted(d["stats"], key=lambda s: -d["stats"][s]["max"])
    fig, ax = plt.subplots(figsize=(15.5 / 2.54 * 2.4, 0.55 * len(names) / 2.54 * 2.4 + 1.2))
    for i, s in enumerate(names):
        st = d["stats"][s]
        y = len(names) - 1 - i
        for v in st["values"]:
            ax.plot([v - BAND, v + BAND], [y, y], color=NAVY, alpha=0.16, lw=7,
                    solid_capstyle="butt")
        ax.scatter(st["values"], [y] * st["n"], s=42, color=NAVY,
                   edgecolors="white", linewidths=0.8, zorder=6)
        for t in d["merged_ranges"].get(s, []):
            lo, hi = t["range"]
            ax.plot([lo, hi], [y - 0.34, y - 0.34], color=GREEN, lw=2.4,
                    solid_capstyle="butt", alpha=0.85)
    for x in OLD_TIERS:
        ax.axvline(x, color="#B9C4D0", lw=0.8, ls=(0, (3, 3)), zorder=1)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(reversed(names), fontsize=8)
    ax.set_xlim(0, 30)
    ax.set_ylim(-0.9, len(names) - 0.1)
    ax.set_xticks(range(0, 31, 5))
    ax.set_xticklabels(["%.1f" % x for x in range(0, 31, 5)])
    ax.set_xticks(range(0, 31), minor=True)
    ax.grid(axis="x", which="minor", color="#F0F3F6", linewidth=0.4)
    ax.set_xlabel("Вкупен Δ⁹-THC (%w/w) — сите резултати (точки), предложени опсези "
                  "(зелено) | all results (dots), proposed tiers (green)", fontsize=8.5)
    ax.set_title("Преглед по сорти — 0,0–30,0 % оска  |  All-strain overview — 0.0–30.0 % axis",
                 fontsize=11, color=INK, loc="left", pad=8)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "overview.png"), dpi=200)
    plt.close(fig)


def main():
    slug = {}
    for i, (s, st) in enumerate(sorted(d["stats"].items()), 1):
        fn = "strain_%02d.png" % i
        # stability points removed from the delivered figures per owner
        # instruction (degradation-evidence section dropped from the documents)
        strain_fig(s, st, d["merged_ranges"].get(s, []), [], fn)
        slug[s] = fn
    overview()
    json.dump(slug, open(os.path.join(FIGDIR, "index.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("figures:", len(slug) + 1)


if __name__ == "__main__":
    main()
