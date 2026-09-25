#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The record of the engagement: what was initiated, what progressed, what completed — by day.

    python3 deliverables/qc_gap_analysis/engagement_report.py
        -> tracker/ENGAGEMENT_REPORT_<today>.md   (reads on GitHub)
        -> tracker/ENGAGEMENT_REPORT_<today>.html (opens in a browser, prints to PDF)

The Head of QC, 17.09.2026: weeks of work, nights and weekends, and nothing to show for the
time because the desk cannot recall it. The desk cannot — but the repository can. Every step
of this work was committed as it was made, with its time, and every stage was raised as a
pull request. This reads that record and writes the report from it, so it can be regenerated
on any day and never depends on anyone's memory.

Sources, all in the repository:
  * `git log --all` — every commit, its timestamp and its message (the work itself);
  * `tracker/pull_requests_<date>.json` — the pull requests, from GitHub;
  * the deliverable folders — what exists today, counted;
  * `open_items.py` — what is decided, what is waiting.

Times are shown in Europe/Skopje (CEST, UTC+2), the Head of QC's clock. A day's "span" is
the time between its first and last commit; work before the first and after the last is not
in it, so it understates the time.
"""
import collections, datetime as dt, glob, html as H, io, json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
TZ = dt.timezone(dt.timedelta(hours=2))
PRS = sorted(glob.glob(os.path.join(HERE, "tracker", "pull_requests_*.json")))


def commits():
    out = subprocess.check_output(["git", "log", "--all", "--format=%H|%ad|%an|%s", "--date=iso-strict"], cwd=ROOT, text=True)
    rows = []
    for line in out.splitlines():
        h, ts, an, subj = line.split("|", 3)
        rows.append((dt.datetime.fromisoformat(ts).astimezone(TZ), an, subj, h[:7]))
    return sorted(rows)


def local(iso):
    return dt.datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(TZ)


def inventory():
    g = lambda p: len(glob.glob(os.path.join(HERE, p), recursive=True))
    return [
        ("Certificates of quality — each as HTML, vector PDF and Word", g("design_handoff/out/**/*.html")),
        ("Internal certificates of analysis", g("icoa_handoff/out/**/*.html")),
        ("CoQ Analysis Master workbook versions in the tracker", g("tracker/CoQ_Analysis_Master_v*.xlsx")),
        ("Desk scripts", g("*.py") + g("tracker/*.py") + g("design_handoff/toolchain/*.py") + g("design_handoff/toolchain/*.js")),
        ("Desk records and reports (Markdown)", g("*.md") + g("tracker/*.md") + g("design_handoff/docs/*.md") + g("design_handoff/dist/*.md")),
        ("Controlled registers and flat data (csv, tsv, json)", g("*.csv") + g("*.tsv") + g("*.json")),
    ]


def open_items():
    try:
        sys.path.insert(0, HERE); import open_items as OI
        return len(OI.ITEMS), dict(collections.Counter(i[2] for i in OI.ITEMS))
    except Exception:
        return None, {}


def gather(today):
    C = commits(); P = json.load(io.open(PRS[-1], encoding="utf-8")) if PRS else []
    days = collections.defaultdict(list)
    for t, an, subj, h in C:
        days[t.date()].append((t, an, subj, h))
    pr_by_day = collections.defaultdict(list)
    for p in P:
        pr_by_day[local(p["created"]).date()].append(("opened", p))
        if p.get("merged"):
            pr_by_day[local(p["merged"]).date()].append(("merged", p))
    weeks = collections.defaultdict(list)
    for d in sorted(days):
        weeks[d.isocalendar()[:2]].append(d)
    span = lambda v: (max(x[0] for x in v) - min(x[0] for x in v)).total_seconds() / 3600
    is_night = lambda t: t.hour < 7 or t.hour >= 22
    rows = []
    for d in sorted(days):
        v = days[d]; heads = []
        for t, an, subj, h in v:
            s = subj.split(" — ")[0].split(": ", 1)[-1].strip()
            if s and s not in heads:
                heads.append(s)
        rows.append({"date": d, "n": len(v), "first": min(x[0] for x in v), "last": max(x[0] for x in v), "span": span(v),
                     "night": sum(1 for x in v if is_night(x[0])), "heads": heads,
                     "prs": ["PR #%d %s" % (p["number"], k) for k, p in pr_by_day.get(d, [])]})
    n, by = open_items()
    return {"today": today, "C": C, "P": P, "days": days, "rows": rows, "weeks": weeks,
            "first": C[0][0].date(), "last": C[-1][0].date(),
            "night": sum(1 for v in days.values() for x in v if is_night(x[0])),
            "weekend": sum(len(v) for d, v in days.items() if d.weekday() >= 5),
            "span": sum(span(v) for v in days.values()),
            "merged": sum(1 for p in P if p.get("merged")), "inventory": inventory(), "oi": (n, by)}


def markdown(D):
    L = ["# Engagement report — Purely Plant QC desk",
         "### %s to %s · written %s from the repository's own record" % (D["first"].strftime("%d.%m.%Y"), D["last"].strftime("%d.%m.%Y"), D["today"].strftime("%d.%m.%Y")), "",
         "Every step of this work was committed the moment it was made, with its time, and every stage was raised as a "
         "pull request. What follows is read from that record by `engagement_report.py`; it can be regenerated on any "
         "day and depends on no one's memory. Times are Europe/Skopje.", "",
         "## In one table", "", "| | |", "| --- | ---: |",
         "| calendar span | %d days (%s – %s) |" % ((D["last"] - D["first"]).days + 1, D["first"].strftime("%d.%m"), D["last"].strftime("%d.%m.%Y")),
         "| days with committed work | %d |" % len(D["days"]),
         "| commits | %d |" % len(D["C"]),
         "| commits between 22:00 and 07:00 | %d |" % D["night"],
         "| commits on Saturdays and Sundays | %d |" % D["weekend"],
         "| sum of the working days' first-to-last-commit spans | %.0f h |" % D["span"],
         "| pull requests raised · merged · open | %d · %d · %d |" % (len(D["P"]), D["merged"], len(D["P"]) - D["merged"])]
    n, by = D["oi"]
    if n:
        L.append("| open items on the register (%s) | %d |" % (" · ".join("%s %d" % kv for kv in sorted(by.items())), n))
    L += ["", "The span counts only the hours between a day's first and last commit; work before the first commit and after "
          "the last is not in it, so it understates the time.", "", "## Stages — the pull requests", "",
          "Each pull request is one stage, raised when the stage was reviewable and merged when it was accepted.", "",
          "| PR | raised | merged | stage |", "| ---: | --- | --- | --- |"]
    for p in D["P"]:
        L.append("| #%d | %s | %s | %s |" % (p["number"], local(p["created"]).strftime("%d.%m.%Y %H:%M"),
                                              local(p["merged"]).strftime("%d.%m.%Y %H:%M") if p.get("merged") else "open (draft)", p["title"].replace("|", "·")))
    L += ["", "## Week by week", ""]
    byday = {r["date"]: r for r in D["rows"]}
    for (y, w), ds in sorted(D["weeks"].items()):
        mon = dt.date.fromisocalendar(y, w, 1)
        L += ["### Week %d · %s – %s · %d working days · %d commits · %.0f h in span" % (
              w, mon.strftime("%d.%m"), (mon + dt.timedelta(days=6)).strftime("%d.%m.%Y"), len(ds), sum(byday[d]["n"] for d in ds), sum(byday[d]["span"] for d in ds)),
              "", "| day | commits | first – last | span | night | what was done |", "| --- | ---: | --- | ---: | ---: | --- |"]
        for d in ds:
            r = byday[d]; what = "; ".join(r["heads"][:4]) + ("; …" if len(r["heads"]) > 4 else "")
            if r["prs"]:
                what = "**" + ", ".join(r["prs"]) + "** — " + what
            L.append("| %s %s | %d | %s – %s | %.1f h | %d | %s |" % (d.strftime("%d.%m"), d.strftime("%a"), r["n"], r["first"].strftime("%H:%M"), r["last"].strftime("%H:%M"), r["span"], r["night"], what.replace("|", "·")))
        L.append("")
    L += ["## Every commit", "", "The full record, oldest first. A commit is a unit of work finished and saved; its message says what it did.", ""]
    cur = None
    for t, an, subj, h in D["C"]:
        if t.date() != cur:
            cur = t.date(); L += ["", "**%s %s**" % (cur.strftime("%d.%m.%Y"), cur.strftime("%A")), ""]
        L.append("* %s · `%s` · %s" % (t.strftime("%H:%M"), h, subj.replace("|", "·")))
    L += ["", "## What exists today", "", "| deliverable | count |", "| --- | ---: |"]
    for k, v in D["inventory"]:
        L.append("| %s | %d |" % (k, v))
    L += ["", "The certificates are in `design_handoff/dist/` as four archives; the internal certificates in `icoa_handoff/out/`; "
          "the master workbook and every desk record in `tracker/`; the open-items register in `tracker/OPEN_ITEMS.md`.", ""]
    return "\n".join(L)


def html_page(D):
    e = H.escape
    css = """
:root{--ink:#1B2A3F;--muted:#5D6B7E;--rule:#D9E0E8;--paper:#FBFCFD;--card:#FFFFFF;--accent:#8A6A1F;--navy:#1B3A5C;--bar:#2F5A8A;--night:#8A6A1F}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--ink:#E6ECF3;--muted:#A5B1C0;--rule:#2C3947;--paper:#0F1620;--card:#162031;--accent:#D5B25C;--navy:#BFD3EA;--bar:#6E9AD0;--night:#D5B25C}}
:root[data-theme="dark"]{--ink:#E6ECF3;--muted:#A5B1C0;--rule:#2C3947;--paper:#0F1620;--card:#162031;--accent:#D5B25C;--navy:#BFD3EA;--bar:#6E9AD0;--night:#D5B25C}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.5 "Source Sans 3","Segoe UI",Roboto,Helvetica,Arial,sans-serif;font-variant-numeric:tabular-nums}
main{max-width:1040px;margin:0 auto;padding:32px 16px 64px}
h1{font-family:"Source Serif 4",Georgia,"Times New Roman",serif;font-weight:600;font-size:30px;line-height:1.15;margin:0 0 6px;text-wrap:balance;color:var(--navy)}
h2{font-family:"Source Serif 4",Georgia,serif;font-weight:600;font-size:21px;margin:40px 0 12px;color:var(--navy);border-bottom:1px solid var(--rule);padding-bottom:6px}
h3{font-size:15px;font-weight:600;letter-spacing:.02em;text-transform:uppercase;color:var(--muted);margin:26px 0 8px}
p.lead{color:var(--muted);max-width:70ch;margin:0 0 20px}
.sub{color:var(--muted);font-size:14px;margin:0 0 18px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:18px 0 8px}
.tile{background:var(--card);border:1px solid var(--rule);border-radius:6px;padding:12px 14px}
.tile b{display:block;font-size:26px;font-weight:600;color:var(--navy);line-height:1.1}
.tile span{font-size:12.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
.chart{background:var(--card);border:1px solid var(--rule);border-radius:6px;padding:14px 14px 8px;overflow-x:auto}
.chart svg{display:block;min-width:720px;width:100%;height:auto}
table{border-collapse:collapse;width:100%;font-size:13.5px;background:var(--card)}
th,td{border-bottom:1px solid var(--rule);padding:6px 8px;vertical-align:top;text-align:left}
th{font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);font-weight:600}
td.n,th.n{text-align:right;white-space:nowrap}td.d{white-space:nowrap}
.wrap{overflow-x:auto;border:1px solid var(--rule);border-radius:6px}
.pr{color:var(--accent);font-weight:600}
details{margin:10px 0}summary{cursor:pointer;color:var(--navy);font-weight:600}
ul.log{list-style:none;padding:0;margin:6px 0 0}ul.log li{padding:2px 0;border-bottom:1px dotted var(--rule);font-size:13.5px}
ul.log code{font:12.5px ui-monospace,Menlo,Consolas,monospace;color:var(--muted);margin:0 6px}
.day{font-weight:600;margin-top:14px;color:var(--navy)}
footer{margin-top:40px;color:var(--muted);font-size:13px}
@media print{body{font-size:12px}main{padding:0}h2{margin-top:22px;break-after:avoid}.wrap{border:0}details{display:block}details>*{display:block}summary{display:none}.chart svg{min-width:0}}
"""
    rows = D["rows"]; mx = max(r["n"] for r in rows) or 1
    # commits per calendar day, every day of the span, as one strip
    d0, d1 = D["first"], D["last"]; ndays = (d1 - d0).days + 1
    byday = {r["date"]: r for r in rows}
    W, Hh, pad, bw = 24 * ndays + 40, 150, 30, 24
    bars = []
    for i in range(ndays):
        d = d0 + dt.timedelta(days=i); r = byday.get(d); x = 30 + i * bw
        if r:
            h = max(3, int(100 * r["n"] / mx)); col = "var(--night)" if r["night"] > r["n"] / 2 else "var(--bar)"
            bars.append('<rect x="%d" y="%d" width="%d" height="%d" rx="2" fill="%s"><title>%s · %d commits · %s–%s · %.1f h</title></rect>' % (
                x + 3, 110 - h, bw - 6, h, col, d.strftime("%a %d.%m"), r["n"], r["first"].strftime("%H:%M"), r["last"].strftime("%H:%M"), r["span"]))
            bars.append('<text x="%d" y="%d" font-size="9" text-anchor="middle" fill="var(--muted)">%d</text>' % (x + bw / 2, 106 - h, r["n"]))
        if d.weekday() >= 5:
            bars.append('<rect x="%d" y="8" width="%d" height="104" fill="var(--rule)" opacity=".35"/>' % (x, bw))
        if d.weekday() == 0 or (i == 0 and d.weekday() != 6):
            bars.append('<text x="%d" y="128" font-size="10" text-anchor="middle" fill="var(--muted)">%s</text>' % (x + bw / 2, d.strftime("%d.%m")))
    svg = '<svg viewBox="0 0 %d %d" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="commits per day">%s<line x1="30" y1="112" x2="%d" y2="112" stroke="var(--rule)"/></svg>' % (W, Hh, "".join(bars), W - 10)
    out = ['<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
           '<title>Engagement Report</title><meta name="description" content="What was initiated, progressed and completed on the Purely Plant QC desk, read from the repository record.">',
           '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Serif+4:wght@600&family=Source+Sans+3:wght@400;600&display=swap">',
           '<style>%s</style></head><body><main>' % css,
           '<h1>Engagement report — Purely Plant QC desk</h1>',
           '<p class="sub">%s to %s · written %s from the repository&#8217;s own record · times Europe/Skopje</p>' % (D["first"].strftime("%d.%m.%Y"), D["last"].strftime("%d.%m.%Y"), D["today"].strftime("%d.%m.%Y")),
           '<p class="lead">Every step of this work was committed the moment it was made, with its time, and every stage was raised as a pull request. This page is read from that record by <code>engagement_report.py</code>; it can be regenerated on any day and depends on no one&#8217;s memory.</p>']
    tiles = [(str((D["last"] - D["first"]).days + 1), "calendar days"), (str(len(D["days"])), "days with committed work"), (str(len(D["C"])), "commits"),
             ("%.0f h" % D["span"], "first-to-last span, summed"), (str(D["night"]), "commits 22:00–07:00"), (str(D["weekend"]), "commits on weekends"),
             ("%d · %d" % (len(D["P"]), D["merged"]), "pull requests · merged")]
    n, by = D["oi"]
    if n:
        tiles.append((str(n), "open items on the register"))
    out.append('<div class="tiles">' + "".join('<div class="tile"><b>%s</b><span>%s</span></div>' % (e(a), e(b)) for a, b in tiles) + '</div>')
    out.append('<p class="sub">The span counts only the hours between a day&#8217;s first and last commit; work before the first and after the last is not in it, so it understates the time.</p>')
    out.append('<h2>Commits per day</h2><div class="chart">%s</div><p class="sub">Gold bars: more than half the day&#8217;s commits fell between 22:00 and 07:00. Shaded columns are Saturdays and Sundays.</p>' % svg)
    out.append('<h2>Stages — the pull requests</h2><div class="wrap"><table><thead><tr><th class="n">PR</th><th>raised</th><th>merged</th><th>stage</th></tr></thead><tbody>')
    for p in D["P"]:
        out.append('<tr><td class="n"><span class="pr">#%d</span></td><td class="d">%s</td><td class="d">%s</td><td>%s</td></tr>' % (
            p["number"], local(p["created"]).strftime("%d.%m.%Y %H:%M"), local(p["merged"]).strftime("%d.%m.%Y %H:%M") if p.get("merged") else "open (draft)", e(p["title"])))
    out.append('</tbody></table></div>')
    out.append('<h2>Week by week</h2>')
    for (y, w), ds in sorted(D["weeks"].items()):
        mon = dt.date.fromisocalendar(y, w, 1)
        out.append('<h3>Week %d · %s – %s · %d working days · %d commits · %.0f h in span</h3>' % (
            w, mon.strftime("%d.%m"), (mon + dt.timedelta(days=6)).strftime("%d.%m.%Y"), len(ds), sum(byday[d]["n"] for d in ds), sum(byday[d]["span"] for d in ds)))
        out.append('<div class="wrap"><table><thead><tr><th>day</th><th class="n">commits</th><th>first – last</th><th class="n">span</th><th class="n">night</th><th>what was done</th></tr></thead><tbody>')
        for d in ds:
            r = byday[d]; what = e("; ".join(r["heads"][:4]) + ("; …" if len(r["heads"]) > 4 else ""))
            if r["prs"]:
                what = '<span class="pr">%s</span> — %s' % (e(", ".join(r["prs"])), what)
            out.append('<tr><td class="d">%s %s</td><td class="n">%d</td><td class="d">%s – %s</td><td class="n">%.1f h</td><td class="n">%d</td><td>%s</td></tr>' % (
                d.strftime("%d.%m"), d.strftime("%a"), r["n"], r["first"].strftime("%H:%M"), r["last"].strftime("%H:%M"), r["span"], r["night"], what))
        out.append('</tbody></table></div>')
    out.append('<h2>Every commit</h2><details><summary>The full record, %d commits, oldest first</summary>' % len(D["C"]))
    cur = None
    for t, an, subj, h in D["C"]:
        if t.date() != cur:
            if cur is not None:
                out.append('</ul>')
            cur = t.date(); out.append('<div class="day">%s %s</div><ul class="log">' % (cur.strftime("%d.%m.%Y"), cur.strftime("%A")))
        out.append('<li>%s<code>%s</code>%s</li>' % (t.strftime("%H:%M"), h, e(subj)))
    out.append('</ul></details>')
    out.append('<h2>What exists today</h2><div class="wrap"><table><thead><tr><th>deliverable</th><th class="n">count</th></tr></thead><tbody>')
    for k, v in D["inventory"]:
        out.append('<tr><td>%s</td><td class="n">%d</td></tr>' % (e(k), v))
    out.append('</tbody></table></div>')
    out.append('<footer>The certificates are in <code>design_handoff/dist/</code> as four archives; the internal certificates in <code>icoa_handoff/out/</code>; the master workbook and every desk record in <code>tracker/</code>; the open-items register in <code>tracker/OPEN_ITEMS.md</code>.</footer>')
    out.append('</main></body></html>')
    return "\n".join(out)


def main(argv):
    today = dt.date.today(); D = gather(today)
    base = os.path.join(HERE, "tracker", "ENGAGEMENT_REPORT_%s" % today.isoformat())
    io.open(base + ".md", "w", encoding="utf-8").write(markdown(D) + "\n")
    io.open(base + ".html", "w", encoding="utf-8").write(html_page(D))
    print("wrote", os.path.relpath(base, ROOT) + ".md / .html"); return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
