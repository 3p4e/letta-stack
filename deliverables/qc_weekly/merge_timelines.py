#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Consolidated work-time band — four parallel sessions on one hour ruler.

Scope rule (owner's instruction): only Purely Plant CONTENT work is counted.
Platform and infrastructure operations are excluded — container/stack
configuration and repair, test-suite runs, production deploys, and background
monitoring of repositories that carry no PP content. Work on the Letta host
IS counted: its knowledgebase, the memory/agent databases and the QC data that
lives in them are Purely Plant content, not infrastructure.

Every excluded item is named in EXCLUSIONS and printed on the figure, so the
reader sees what was left out rather than a quietly smaller number.

The four sources measure time in four incompatible ways. They are drawn as
separate lanes and NEVER summed into one figure:

  solid   = evidenced      (transcript events, tool/file timestamps, git commits)
  hatched = span/estimate  (PR open->merge elapsed time, or session estimates)

No source's own reported figure is altered here; where a lane is reduced, the
reduction is a subset selection of that source's own itemised rows, and both
the original and the PP-only total are recorded in the output JSON.

Usage:  python3 merge_timelines.py
Writes: merged_sources.json, consolidated_ruler.png
"""
import datetime as dt
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

HERE = os.path.dirname(os.path.abspath(__file__))
TZ = dt.timezone(dt.timedelta(hours=2))          # Europe/Skopje, UTC+2 in August
WIN_A = dt.datetime(2026, 8, 11, 16, 0, tzinfo=TZ)
WIN_B = dt.datetime(2026, 8, 14, 8, 0, tzinfo=TZ)

NAVY = "#2B547E"; GREEN = "#4E7A3F"; PURPLE = "#7B4F8C"; GOLD = "#B08424"; TEAL = "#2E7C86"

# Work counted as Purely Plant content, per source. Times are Skopje.
# `chunks` are (start, end) pairs drawn on the ruler; `hours` is the source's
# own stated figure for the PP-only subset of its rows.
SOURCES = [
    dict(key="QC", label="Сесија за QC-податоци | QC data session",
         method="транскрипт | transcript-witnessed", color=NAVY, style="solid",
         chunks_from="activity_dataset", hours=None, reported=4.9, excluded_h=0.0),

    dict(key="OPS-W", label="Letta host — засведочено | witnessed",
         method="временски печати на алатки | tool timestamps", color=GREEN, style="solid",
         chunks=[("2026-08-12 05:37", "2026-08-12 10:53")], hours=5.3, reported=5.3, excluded_h=0.0),

    dict(key="OPS-C", label="Letta host — распон по PR | checkpoint span",
         method="PR отворен→споен, не е ангажман | PR open→merge, not hands-on",
         color=TEAL, style="hatch",
         chunks=[("2026-08-11 18:00", "2026-08-12 10:51"),      # specs & QC reporting  16.9 h
                 ("2026-08-12 13:24", "2026-08-13 22:56"),      # Letta host audit      33.5 h
                 ("2026-08-14 06:29", "2026-08-14 07:05"),      # deliverable rendering  0.6 h
                 ("2026-08-14 08:11", "2026-08-14 10:00")],     # time-tracking report   1.8 h
         hours=52.8, reported=52.8, excluded_h=13.8),

    dict(key="WWF", label="WWF-платформа — само PP-содржина | PP content only",
         method="git коммити | git commits", color=PURPLE, style="solid",
         chunks=[("2026-08-14 05:45", "2026-08-14 06:22"),      # A  SPC archive analysis
                 ("2026-08-14 06:22", "2026-08-14 06:40"),      # P  plan + owner decisions
                 ("2026-08-14 06:40", "2026-08-14 07:10"),      # I  SPC data implementation
                 ("2026-08-14 07:45", "2026-08-14 08:00")],     # T  this timeline document
         hours=1.7, reported=2.25, excluded_h=0.9),

    dict(key="ImB", label="ImB спецификации | ImB spec design",
         method="проценка од сесиска активност | session estimate", color=GOLD, style="hatch",
         chunks=[("2026-08-11 16:00", "2026-08-11 20:00"), ("2026-08-11 20:00", "2026-08-12 00:00"),
                 ("2026-08-12 09:00", "2026-08-12 14:00"), ("2026-08-12 14:00", "2026-08-12 19:00"),
                 ("2026-08-12 19:00", "2026-08-12 22:00"), ("2026-08-13 09:00", "2026-08-13 13:00"),
                 ("2026-08-13 13:00", "2026-08-13 17:00"), ("2026-08-13 17:00", "2026-08-13 21:00"),
                 ("2026-08-14 06:00", "2026-08-14 08:00")],
         hours=35.0, reported=35.0, excluded_h=0.0),
]

# Named, quantified exclusions — printed under the figure.
EXCLUSIONS = [
    ("Конфигурација и поправка на Docker/стек | container-stack configuration & repair",
     "надвор од опфат | out of scope"),
    ("WWF: тест-суити и продукциски deploy (v88/v128) | test suites & production deploy",
     "0,9 h"),
    ("Позадинско следење на репозиториуми без PP-содржина | background monitoring, non-PP repos",
     "13,8 h"),
]


def parse(s):
    return dt.datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=TZ)


def qc_chunks():
    """QC lane chunks from the transcript-derived activity dataset."""
    d = json.load(open(os.path.join(HERE, "..", "timeline", "activity_dataset.json"),
                       encoding="utf-8"))
    out = []
    for c in d["chunks"]:
        a = dt.datetime.fromisoformat(c["anchor"]).astimezone(TZ)
        out.append((a, a + dt.timedelta(minutes=c["min"])))
    return out, d["active_total_h"]


def build():
    lanes = []
    for s in SOURCES:
        s = dict(s)
        if s.pop("chunks_from", None) == "activity_dataset":
            ch, hrs = qc_chunks()
            s["chunks"] = ch
            s["hours"] = hrs
        else:
            s["chunks"] = [(parse(a), parse(b)) for a, b in s["chunks"]]
        lanes.append(s)

    fig, ax = plt.subplots(figsize=(15.2, 5.6))
    H = 0.62
    for i, s in enumerate(lanes):
        y = len(lanes) - 1 - i
        ax.broken_barh([(WIN_A, WIN_B - WIN_A)], (y - H / 2, H),
                       facecolors="#F4F6F9", edgecolors="#DFE5EC", linewidth=0.6)
        for a, b in s["chunks"]:
            a = max(a, WIN_A); b = min(b, WIN_B)
            if b <= a:
                continue
            ax.broken_barh([(a, b - a)], (y - H / 2, H),
                           facecolors=s["color"] if s["style"] == "solid" else "none",
                           edgecolors=s["color"],
                           hatch=None if s["style"] == "solid" else "////",
                           linewidth=0.9, alpha=0.95 if s["style"] == "solid" else 1.0)
        ax.text(WIN_B + dt.timedelta(minutes=45), y, "%.1f h" % s["hours"],
                va="center", ha="left", fontsize=10, fontweight="bold", color=s["color"])

    ax.set_yticks(range(len(lanes)))
    ax.set_yticklabels([s["label"] for s in reversed(lanes)], fontsize=9)
    ax.set_ylim(-0.7, len(lanes) - 0.3)
    ax.set_xlim(WIN_A, WIN_B + dt.timedelta(hours=3))

    ax.xaxis.set_major_locator(mdates.HourLocator(byhour=[0, 6, 12, 18]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:00", tz=TZ))
    ax.xaxis.set_minor_locator(mdates.HourLocator(interval=1))
    ax.tick_params(axis="x", which="major", length=7, labelsize=8)
    ax.tick_params(axis="x", which="minor", length=3)
    ax.grid(axis="x", which="major", color="#D8E0E8", linewidth=0.7)
    ax.grid(axis="x", which="minor", color="#EDF1F5", linewidth=0.4)
    ax.set_axisbelow(True)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color("#B9C4D0")

    # day separators + day labels
    day = WIN_A.replace(hour=0, minute=0) + dt.timedelta(days=1)
    names = {11: "вторник | Tue 11.08", 12: "среда | Wed 12.08",
             13: "четврток | Thu 13.08", 14: "петок | Fri 14.08"}
    while day < WIN_B:
        ax.axvline(day, color="#8FA3B8", linewidth=1.0, linestyle=(0, (4, 3)), zorder=0)
        day += dt.timedelta(days=1)
    for d0, label in names.items():
        start = dt.datetime(2026, 8, d0, 0, 0, tzinfo=TZ)
        mid = max(start, WIN_A) + (min(start + dt.timedelta(days=1), WIN_B) - max(start, WIN_A)) / 2
        if WIN_A <= mid <= WIN_B:
            ax.text(mid, len(lanes) - 0.45, label, ha="center", va="bottom",
                    fontsize=8.5, color="#5A6B7C")

    ax.set_title("Работно време по сесии — линијар по часови (Скопје, UTC+2)   |   "
                 "Work time by session — hour ruler (Skopje)",
                 fontsize=11.5, color="#16232B", pad=26, fontweight="bold")

    legend = [Patch(facecolor="#7A8A9A", edgecolor="#7A8A9A",
                    label="полно = докажано време | solid = evidenced time"),
              Patch(facecolor="none", edgecolor="#7A8A9A", hatch="////",
                    label="шрафирано = распон или проценка | hatched = span or estimate")]
    ax.legend(handles=legend, loc="upper center", bbox_to_anchor=(0.5, -0.20),
              ncol=2, frameon=False, fontsize=8.5)

    excl = "Исклучено (не е PP-содржина) | Excluded (not PP content):  " + " · ".join(
        "%s — %s" % (a.split(" | ")[0], b) for a, b in EXCLUSIONS)
    fig.text(0.5, 0.015, excl, ha="center", fontsize=7.4, color="#6B7785", style="italic")

    fig.subplots_adjust(left=0.265, right=0.94, top=0.84, bottom=0.24)
    out_png = os.path.join(HERE, "consolidated_ruler.png")
    fig.savefig(out_png, dpi=200)
    plt.close(fig)

    data = dict(
        window=dict(start=WIN_A.isoformat(), end=WIN_B.isoformat(),
                    span_hours=(WIN_B - WIN_A).total_seconds() / 3600,
                    tz="Europe/Skopje (UTC+02:00)"),
        scope_rule=("Only Purely Plant content work is counted. Platform/infrastructure "
                    "operations are excluded; Letta host knowledgebase and memory/agent "
                    "databases count as PP content."),
        summable=False,
        sources=[dict(key=s["key"], label=s["label"], method=s["method"], style=s["style"],
                      pp_hours=round(s["hours"], 2), source_reported_hours=s["reported"],
                      excluded_hours=s["excluded_h"], chunks=len(s["chunks"]))
                 for s in lanes],
        exclusions=[dict(item=a, hours=b) for a, b in EXCLUSIONS],
    )
    out_json = os.path.join(HERE, "merged_sources.json")
    json.dump(data, open(out_json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    for s in lanes:
        print("%-6s %5.1f h  (source reported %.1f, excluded %.1f)  %d chunks"
              % (s["key"], s["hours"], s["reported"], s["excluded_h"], len(s["chunks"])))
    print("wrote", os.path.relpath(out_png, HERE), "and", os.path.relpath(out_json, HERE))
    return data


if __name__ == "__main__":
    build()
