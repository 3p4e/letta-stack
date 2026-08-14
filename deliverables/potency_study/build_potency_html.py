#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Potency Atlas — creative single-file HTML edition of the Strain Potency Study.

Same bound dataset (potency_dataset.json), richer per-result detail:
  • every actual Total Δ⁹-THC value, per strain, sorted ascending;
  • ‖x̄−v‖ — the absolute deviation of each result from the strain mean;
  • the distance between successive results, in percentage points AND as a
    relative % of the lower value;
  • same-batch repeat pairs called out separately (the truest "distance
    between two results obtained by all means so far");
  • the CSS-built 0–35 % axis per strain: ±1,5 % zone per result, mean line,
    95 % CI band (n≥3), proposed W-tiers, old standard grade boundaries;
  • degradation evidence (stability program) and the full T1/T2/T3 stock table.

Self-contained: subset Montserrat + Orbitron inlined as data-URI woff2, no
external requests. Single-theme by design (a laboratory document), every
surface painted explicitly.
"""
import html
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.path.join(HERE, "potency_dataset.json"), encoding="utf-8"))
F = json.load(open(os.path.join(HERE, "webfonts", "fonts_b64.json"), encoding="utf-8"))

OLD_TIERS = [5.00, 15.90, 22.90, 26.90, 30.00]
AX = 35.0


def esc(s):
    return html.escape(str(s), quote=True)


def pct(v):
    return 100.0 * v / AX


def dkey(s):
    p = (s or "").split(".")
    return (p[2], p[1], p[0]) if len(p) == 3 else ("0", "0", "0")


# group register results per strain
per = {}
for r in d["register_results"]:
    per.setdefault(r["strain"], []).append(r)
for s in per:
    per[s].sort(key=lambda r: r["value"])

css_fonts = """
@font-face{font-family:'Montserrat';font-weight:400;font-style:normal;
 src:url(data:font/woff2;base64,%s) format('woff2')}
@font-face{font-family:'Montserrat';font-weight:600;font-style:normal;
 src:url(data:font/woff2;base64,%s) format('woff2')}
@font-face{font-family:'Montserrat';font-weight:700;font-style:normal;
 src:url(data:font/woff2;base64,%s) format('woff2')}
@font-face{font-family:'Orbitron';font-weight:400;font-style:normal;
 src:url(data:font/woff2;base64,%s) format('woff2')}
""" % (F["mont_r"], F["mont_sb"], F["mont_b"], F["orb_r"])

CSS = css_fonts + """
:root{
 --navy:#1B3A5C; --navy2:#2B547E; --gold:#C9A227; --green:#1E8449;
 --rose:#C0392B; --paper:#F7F9FC; --card:#FFFFFF; --ink:#16232B;
 --mut:#5A6B7C; --line:#D8E2EC; --zone:rgba(43,84,126,.10);
 --mono:ui-monospace,'Cascadia Mono','Roboto Mono',Menlo,monospace;
}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{background:var(--paper);color:var(--ink);
 font:400 15px/1.55 'Montserrat',system-ui,sans-serif}
.wrap{max-width:1060px;margin:0 auto;padding:0 20px}
a{color:var(--navy2)}
.hero{background:linear-gradient(160deg,#132B45 0%,var(--navy) 55%,#234B74 100%);
 color:#EAF1F8;padding:46px 0 38px;border-bottom:4px solid var(--gold)}
.brand{display:flex;align-items:baseline;gap:10px;letter-spacing:.24em;
 font-size:13px;font-weight:700}
.brand em{font-style:italic;font-weight:400;color:var(--gold)}
.brand small{letter-spacing:.18em;font-weight:400;font-size:9.5px;color:#9FB4C9}
.hero h1{font-family:'Montserrat';font-weight:700;font-size:clamp(28px,5vw,44px);
 letter-spacing:.01em;margin:18px 0 2px;text-wrap:balance}
.hero .en{font-family:'Orbitron';font-weight:400;font-size:clamp(13px,2vw,19px);
 letter-spacing:.34em;color:var(--gold);margin:0 0 10px;text-transform:uppercase}
.hero .sub{color:#B9CBDD;font-size:14px;max-width:62ch}
.chips{display:flex;flex-wrap:wrap;gap:10px;margin-top:22px}
.chip{background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.18);
 border-radius:4px;padding:7px 13px;font-size:12.5px}
.chip b{font-family:'Orbitron';font-size:16px;color:var(--gold);margin-right:6px}
.informal{margin-top:18px;font-size:11px;letter-spacing:.14em;color:#9FB4C9;
 text-transform:uppercase}
section{padding:34px 0 6px}
h2{font-size:21px;font-weight:700;color:var(--navy);letter-spacing:.01em;
 border-bottom:2px solid var(--navy2);padding-bottom:6px;margin-bottom:16px}
h2 span{font-weight:400;color:var(--mut);font-size:15px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px}
.kcard{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--navy2);
 padding:14px 16px;font-size:13.5px}
.kcard.warm{border-left-color:var(--rose)}
.kcard.gold{border-left-color:var(--gold)}
.kcard.green{border-left-color:var(--green)}
.kcard b{display:block;margin-bottom:4px;color:var(--navy)}
.kcard i{color:var(--mut);font-size:12px}
.rule{background:var(--navy);color:#EAF1F8;padding:14px 20px;margin-top:14px;
 font-size:13px;border-radius:2px;display:flex;flex-wrap:wrap;gap:6px 22px;
 align-items:baseline}
.rule b{width:100%;letter-spacing:.05em}
.rule code{font-family:var(--mono);color:var(--gold);font-size:13.5px}
.nav{position:sticky;top:0;z-index:9;background:rgba(247,249,252,.96);
 backdrop-filter:blur(4px);border-bottom:1px solid var(--line);padding:9px 0}
.nav .wrap{display:flex;flex-wrap:wrap;gap:6px}
.nav a{font-size:11.5px;text-decoration:none;border:1px solid var(--line);
 background:var(--card);padding:3px 9px;border-radius:12px;color:var(--navy)}
.nav a:hover{border-color:var(--navy2);background:#EDF3F9}
.strain{background:var(--card);border:1px solid var(--line);margin-bottom:26px;
 scroll-margin-top:64px}
.shead{display:flex;flex-wrap:wrap;align-items:baseline;gap:8px 18px;
 padding:14px 18px;border-bottom:1px solid var(--line);
 background:linear-gradient(90deg,#F2F6FA,#FFFFFF)}
.shead h3{font-family:'Orbitron';font-weight:400;font-size:22px;letter-spacing:.05em;
 color:var(--navy)}
.stat{font-size:12px;color:var(--mut)}
.stat b{color:var(--ink);font-size:13.5px;font-variant-numeric:tabular-nums}
.axiswrap{padding:18px 18px 6px;overflow-x:auto}
.axis{position:relative;height:118px;min-width:640px;
 background:linear-gradient(180deg,#FBFCFE, #F4F7FB);border:1px solid var(--line)}
.zone{position:absolute;top:14%;height:56%;background:var(--zone)}
.old{position:absolute;top:0;bottom:0;border-left:1px dashed #B9C7D6}
.ci{position:absolute;top:14%;height:56%;background:rgba(201,162,39,.20)}
.mean{position:absolute;top:10%;height:64%;width:3px;background:var(--gold)}
.dot{position:absolute;top:64%;width:11px;height:11px;border-radius:50%;
 background:var(--navy2);border:2px solid #fff;box-shadow:0 0 0 1px var(--navy2);
 transform:translateX(-50%)}
.tier{position:absolute;height:13px;background:rgba(30,132,73,.16);
 border:1.5px solid var(--green);font-size:9.5px;font-weight:700;color:var(--green);
 display:flex;align-items:center;justify-content:center;white-space:nowrap;
 letter-spacing:.03em}
.stab25{position:absolute;top:84%;width:10px;height:10px;background:var(--green);
 border:2px solid #fff;box-shadow:0 0 0 1px var(--green);transform:translateX(-50%)}
.stab40{position:absolute;top:84%;width:0;height:0;transform:translateX(-50%);
 border-left:6px solid transparent;border-right:6px solid transparent;
 border-top:10px solid var(--rose)}
.scale{display:flex;justify-content:space-between;min-width:640px;
 font-size:10px;color:var(--mut);font-variant-numeric:tabular-nums;margin-top:3px}
.legend{padding:2px 18px 8px;font-size:11px;color:var(--mut)}
.legend i{font-style:normal;margin-right:14px}
.dotk{display:inline-block;width:9px;height:9px;border-radius:50%;
 background:var(--navy2);vertical-align:-1px;margin-right:4px}
.meank{display:inline-block;width:10px;height:3px;background:var(--gold);
 vertical-align:2px;margin-right:4px}
.zonek{display:inline-block;width:12px;height:9px;background:var(--zone);
 vertical-align:-1px;margin-right:4px}
.tierk{display:inline-block;width:12px;height:8px;background:rgba(30,132,73,.16);
 border:1px solid var(--green);vertical-align:-1px;margin-right:4px}
table{border-collapse:collapse;width:100%;font-size:12.5px}
.tblwrap{overflow-x:auto;padding:0 18px 16px}
th{background:var(--navy);color:#fff;font-weight:600;padding:6px 9px;font-size:11px;
 letter-spacing:.05em;text-align:left;white-space:nowrap}
td{border-bottom:1px solid var(--line);padding:5.5px 9px;white-space:nowrap;
 font-variant-numeric:tabular-nums}
tr:nth-child(even) td{background:#F6F9FC}
td.v{font-family:var(--mono);font-weight:600;color:var(--navy)}
td.num{font-family:var(--mono)}
td.gap{color:var(--navy2)}
td.dev{color:var(--mut)}
.badge{display:inline-block;background:#EDF3F9;border:1px solid var(--navy2);
 color:var(--navy2);font-size:9.5px;font-weight:700;border-radius:9px;
 padding:0 6px;margin-left:6px;vertical-align:1px}
.callout{margin:0 18px 16px;background:#FBF6E9;border:1px solid var(--gold);
 padding:10px 14px;font-size:12.5px}
.callout b{color:#8A6D14}
.tiers{margin:0 18px 16px;font-size:12.5px}
.tiers .trow{display:flex;gap:10px;align-items:baseline;padding:3px 0}
.tiers .tr-range{font-family:var(--mono);font-weight:600;color:var(--green);min-width:110px}
.stabnote{color:var(--rose);font-size:11.5px}
details{margin-top:8px}
summary{cursor:pointer;font-weight:600;color:var(--navy);padding:10px 0}
.decl td{background:#FFF8E7 !important}
tr.rej td{color:#9AA7B4;text-decoration:line-through}
tr.rej td.keep{text-decoration:none;color:var(--rose);font-size:11px;white-space:normal}
footer{margin-top:40px;background:var(--navy);color:#B9CBDD;padding:26px 0 34px;
 font-size:12px}
footer .wrap{display:grid;gap:6px}
footer b{color:#EAF1F8}
@media (prefers-reduced-motion:no-preference){
 .strain{transition:box-shadow .2s}
 .strain:hover{box-shadow:0 3px 14px rgba(27,58,92,.10)}
}
"""


def axis_html(s, st, tiers, stab):
    zones = "".join(
        '<div class="zone" style="left:%.3f%%;width:%.3f%%"></div>'
        % (pct(max(0, r["value"] - 1.5)), pct(min(AX, r["value"] + 1.5) - max(0, r["value"] - 1.5)))
        for r in per[s])
    olds = "".join('<div class="old" style="left:%.3f%%"></div>' % pct(x) for x in OLD_TIERS)
    ci = ""
    if st["ci95"]:
        ci = '<div class="ci" style="left:%.3f%%;width:%.3f%%"></div>' % (
            pct(st["ci95"][0]), pct(st["ci95"][1] - st["ci95"][0]))
    mean = '<div class="mean" style="left:calc(%.3f%% - 1px)"></div>' % pct(st["mean"])
    dots = "".join(
        '<div class="dot" style="left:%.3f%%" title="%s · %s · %s · %.2f%%"></div>'
        % (pct(r["value"]), esc(r["batch"]), esc(r["date"]), esc(r["lab"]), r["value"])
        for r in per[s])
    tt = ""
    for i, t in enumerate(tiers):
        lo, hi = t["range"]
        top = 4 if i % 2 == 0 else 22
        tt += ('<div class="tier" style="left:%.3f%%;width:%.3f%%;top:%dpx" '
               'title="серии | batches: %s">W-%d %.1f–%.1f</div>'
               % (pct(lo), pct(hi - lo), top, esc(", ".join(t["batches"])), i + 1, lo, hi))
    sb = ""
    for r in stab:
        cls = "stab25" if r["arm"].startswith("25") else "stab40"
        sb += ('<div class="%s" style="left:%.3f%%" title="%s M%d %s — %.2f%% (CBN %.2f%%)"></div>'
               % (cls, pct(r["total_thc"]), esc(r["batch"]), r["month"], esc(r["arm"]),
                  r["total_thc"], r["cbn"]))
    scale = "".join("<span>%d</span>" % x for x in range(0, 36, 5))
    return ('<div class="axiswrap"><div class="axis">%s%s%s%s%s%s%s</div>'
            '<div class="scale">%s</div></div>'
            % (zones, olds, ci, mean, tt, dots, sb, scale))


def results_table(s, st):
    rs = per[s]
    n = len(rs)
    # count batches with >1 result for repeat badges
    from collections import Counter
    bc = Counter(r["batch"] for r in rs)
    rows = ""
    for i, r in enumerate(rs):
        dev = abs(st["mean"] - r["value"])
        if i < n - 1:
            nxt = rs[i + 1]["value"]
            gpp = nxt - r["value"]
            grel = 100.0 * gpp / r["value"] if r["value"] else 0
            gap = "+%.2f пп · +%.1f%%" % (gpp, grel)
        else:
            gap = "—"
        badge = '<span class="badge" title="серијата е мерена повеќе пати | batch measured more than once">↺</span>' \
            if bc[r["batch"]] > 1 else ""
        rows += ("<tr><td>%d</td><td class=num>%s%s</td><td>%s</td><td>%s</td>"
                 "<td class=v>%.2f</td><td class=dev>%.2f</td><td class=gap>%s</td></tr>"
                 % (i + 1, esc(r["batch"]), badge, esc(r["date"]), esc(r["lab"]),
                    r["value"], dev, gap))
    return ('<div class="tblwrap"><table><thead><tr>'
            "<th>№</th><th>Серија | Batch</th><th>Датум | Date</th><th>Лаб | Lab</th>"
            "<th>Вкупен THC %%</th><th>‖x̄−v‖ (пп)</th><th>Δ до следен | to next</th>"
            "</tr></thead><tbody>%s</tbody></table></div>" % rows)


def repeats_callout(s):
    from collections import defaultdict
    groups = defaultdict(list)
    for r in per[s]:
        groups[r["batch"]].append(r)
    items = []
    for b, rs in groups.items():
        if len(rs) < 2:
            continue
        rs = sorted(rs, key=lambda r: dkey(r["date"]))
        for a, z in zip(rs, rs[1:]):
            dpp = z["value"] - a["value"]
            rel = 100.0 * dpp / a["value"]
            items.append("<b>%s</b>: %.2f (%s) → %.2f (%s) — Δ %+.2f пп · %+.1f%%"
                         % (esc(b), a["value"], esc(a["date"]), z["value"], esc(z["date"]),
                            dpp, rel))
    if not items:
        return ""
    return ('<div class="callout">Повторени мерења на иста серија | '
            "Same-batch repeat measurements:<br>%s</div>" % "<br>".join(items))


def tiers_block(s):
    tiers = d["merged_ranges"].get(s, [])
    if not tiers:
        return ('<div class="tiers"><i>Нема серии на залиха во Т1/Т2/Т3 | '
                "No T1/T2/T3 stock batches.</i></div>")
    rows = "".join(
        '<div class="trow"><span class="tr-range">W-%d %.1f – %.1f</span>'
        "<span>%s</span></div>"
        % (i + 1, t["range"][0], t["range"][1], esc(", ".join(t["batches"])))
        for i, t in enumerate(tiers))
    return ('<div class="tiers"><b>Предложени класи | Proposed tiers:</b>%s</div>' % rows)


def strain_cards():
    out = ""
    for s in sorted(d["stats"]):
        st = d["stats"][s]
        stab = [r for r in d["stability"] if r["strain"] == s and r["usable"]]
        sid = "s-" + "".join(c if c.isalnum() else "-" for c in s.lower())
        chips = "<span class=stat>n <b>%d</b></span><span class=stat>x̄ <b>%.2f</b></span>" % (st["n"], st["mean"])
        if st["sd"] is not None:
            chips += "<span class=stat>SD <b>%.2f</b></span>" % st["sd"]
        if st["ci95"]:
            chips += "<span class=stat>95%% CI <b>%.2f–%.2f</b></span>" % tuple(st["ci95"])
        chips += "<span class=stat>опсег | range <b>%.2f–%.2f</b></span>" % (st["min"], st["max"])
        stabnote = ""
        if stab:
            stabnote = ('<i><span class="dotk" style="background:var(--green);border-radius:1px"></span>'
                        "стабилност 25°C | stability 25°C</i>"
                        '<i><span style="color:var(--rose)">▼</span> стабилност 40°C | 40°C</i>')
        legend = ('<div class="legend"><i><span class="dotk"></span>резултат | result</i>'
                  '<i><span class="zonek"></span>±1,5%% зона | zone</i>'
                  '<i><span class="meank"></span>средна | mean</i>'
                  '<i><span class="tierk"></span>W-класи | tiers</i>%s</div>' % stabnote)
        out += ('<article class="strain" id="%s"><div class="shead"><h3>%s</h3>%s</div>'
                "%s%s%s%s%s</article>"
                % (sid, esc(s), chips, axis_html(s, st, d["merged_ranges"].get(s, []), stab),
                   legend, tiers_block(s), results_table(s, st), repeats_callout(s)))
    return out


def stab_table():
    rows = ""
    for r in d["stability"]:
        if r["usable"]:
            rows += ("<tr><td>%s</td><td class=num>%s</td><td>%s</td><td>M%d</td>"
                     "<td class=v>%.2f</td><td class=num>%.2f</td></tr>"
                     % (esc(r["report"]), esc(r["batch"]), esc(r["arm"]), r["month"],
                        r["total_thc"], r["cbn"]))
        else:
            rows += ('<tr class="rej"><td>%s</td><td class=num>%s</td><td>%s</td><td>M%d</td>'
                     '<td>%.2f</td><td class="keep">ОДБИЕН | REJECTED — PP-QC-ERR-002 '
                     "(неуспешна масена рамнотежа | failed mass balance)</td></tr>"
                     % (esc(r["report"]), esc(r["batch"]), esc(r["arm"]), r["month"],
                        r["total_thc"]))
    return ('<div class="tblwrap" style="padding:0"><table><thead><tr>'
            "<th>Сертификат | Report</th><th>Серија | Batch</th><th>Крак | Arm</th>"
            "<th>Месец | Month</th><th>Вкупен THC %%</th><th>CBN %%</th></tr></thead>"
            "<tbody>%s</tbody></table></div>" % rows)


def stock_table():
    rows = ""
    for b in sorted(d["stock"], key=lambda x: (x["tranche"], x["strain"], x["batch"])):
        if not b.get("proposed"):
            continue
        decl = b["anchor"] is None
        anc = ("%.2f (декл. | decl.)" % b["declared"]) if decl \
            else "%.2f (%s)" % (b["anchor"], b["anchor_date"])
        rows += ('<tr%s><td>Т%s</td><td class=num>%s</td><td>%s</td><td class=num>%s</td>'
                 "<td>%s</td><td>W-%s</td><td class=v>%.1f – %.1f</td><td class=num>%.2f</td></tr>"
                 % (' class="decl"' if decl else "", esc(b["tranche"]), esc(b["batch"]),
                    esc(b["strain"]), anc, esc(b["bracket_old"] or "—"),
                    b.get("tier", "—"), b["proposed"][0], b["proposed"][1], b["headroom_down"]))
    return ('<div class="tblwrap" style="padding:0"><table><thead><tr>'
            "<th>Т</th><th>Серија | Batch</th><th>Сорта | Strain</th>"
            "<th>Сидро | Anchor (%%)</th><th>Стара | Old</th><th>Класа | Tier</th>"
            "<th>Предлог | Proposed (%%)</th><th>Простор ↓ | Headroom</th>"
            "</tr></thead><tbody>%s</tbody></table></div>" % rows)


nav = "".join('<a href="#s-%s">%s</a>'
              % ("".join(c if c.isalnum() else "-" for c in s.lower()), esc(s))
              for s in sorted(d["stats"]))

n_stab_usable = sum(1 for r in d["stability"] if r["usable"])

HTML = """<!doctype html>
<html lang="mk"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Potency Atlas</title>
<style>%s</style></head>
<body>
<header class="hero"><div class="wrap">
 <div class="brand">PURELY<em>PLANT</em> <small>THE FUTURE OF CANNABIS</small></div>
 <h1>Атлас на потенца</h1>
 <div class="en">Potency Atlas</div>
 <div class="sub">Сите некогаш тестирани резултати за Вкупен Δ⁹-THC, по сорта,
 со растојанија меѓу резултатите и предлог за нови опсези по класи за залихата од Транша 1/2/3.
 | Every Total Δ⁹-THC result ever tested, per strain, with between-result distances and the
 proposed new warehouse grade tiers for the Tranche 1/2/3 stock.</div>
 <div class="chips">
  <span class="chip"><b>%d</b>резултати | results</span>
  <span class="chip"><b>%d</b>сорти | strains</span>
  <span class="chip"><b>%d</b>серии | batches</span>
  <span class="chip"><b>%d</b>стабилносни | stability</span>
  <span class="chip"><b>4 134</b>пасуси проверени | passages swept</span>
 </div>
 <div class="informal">Неформален работен документ · не е контролиран запис · 14.08.2026 |
 Informal working document · not a controlled record</div>
</div></header>

<nav class="nav"><div class="wrap">%s</div></nav>

<div class="wrap">
<section><h2>Клучни наоди <span>| Key Findings</span></h2>
<div class="cards">
 <div class="kcard green"><b>25°C: нема опаѓање | no decline</b>
  Стабилносните краци на 25°C/60%%RH не покажуваат пад на Вкупен Δ⁹-THC низ 3–9 месеци
  (22,83→24,51 · 21,31→23,08). <i>25°C/60%%RH arms show no decline over 3–9 months.</i></div>
 <div class="kcard warm"><b>Топлината е ризикот | Heat is the risk</b>
  Краците на 40°C/75%%RH паѓаат на 13,16–17,05%% со CBN 2,05–2,35%%.
  <i>40°C/75%%RH arms collapse with CBN above 2%%.</i></div>
 <div class="kcard"><b>Варијансата доминира | Variance dominates</b>
  Разликите меѓу мерења од ±1,5–2,5%% се поголем ризик за „испаѓање“ од класа отколку
  стареењето. <i>Between-measurement variance outweighs ageing.</i></div>
 <div class="kcard gold"><b>Гаранција на новите класи | The tier guarantee</b>
  Повторно мерење денес или по уште една година складирање останува во декларираната класа.
  <i>A remeasure now or in a year still reads in grade.</i></div>
</div>
<div class="rule"><b>Правило за опсег | Range rule</b>
<span><code>долна | floor = сидро − D − U</code></span>
<span><code>горна | ceiling = сидро + U</code></span>
<span><code>D = 1,5 пп/год | pp/yr</code></span>
<span><code>U ≈ 6,2%% од вредноста | of value (k=2)</code></span>
<span>класи ≤ 6,5 пп широки, никогаш под 5,00%% | tiers ≤ 6.5 pp wide, never below the
5.00%% release criterion</span></div>
</section>

<section><h2>Докази за деградација <span>| Degradation Evidence — Grape Pie стабилносна
програма (UKIM-CNP)</span></h2>%s
<p style="font-size:12px;color:var(--mut);margin-top:8px">P050022 = GP0824_02 ·
P050072 = GP0824_03 · P050202 = GP062501. Редот на ППК26037 е задржан во податоците,
но исклучен од сите статистики. | The ППК26037 row is retained in the data but excluded
from all statistics.</p></section>

<section><h2>Сорти <span>| Strains — дистрибуции, растојанија и класи</span></h2>
<p style="font-size:12.5px;color:var(--mut);margin-bottom:14px">
‖x̄−v‖ = апсолутна разлика меѓу средната вредност на сортата и секој резултат (процентни
поени). Δ до следен = растојание до следниот повисок резултат, во процентни поени и како
релативен %% од помалата вредност. | ‖x̄−v‖ = absolute difference between the strain mean and
each result (percentage points). Δ to next = distance to the next higher result, in
percentage points and as a relative %% of the lower value.</p>
%s</section>

<section><h2>Залиха Т1/Т2/Т3 <span>| Stock — предложени класи по серија</span></h2>
<details open><summary>78 серии | batches — сидро, стара класа, нова класа, простор надолу
| anchor, old grade, new tier, downward headroom</summary>%s</details>
<p style="font-size:12px;color:var(--mut);margin-top:8px">Жолти редови: без ниту еден
сертификат — основа е декларираната вредност; тестирајте пред формално декларирање класа. |
Yellow rows: no certificate on file — declared value used; test before declaring a grade.</p>
</section>
</div>

<footer><div class="wrap">
<b>Потекло | Provenance</b>
<span>Корпус: %d резултати од регистарот на eCoA (77 серии, %d сорти) + %d употребливи
стабилносни резултати; сите вредности проверени во живо на изворот ImB_QC_COAs
(4 134 пасуси). | Corpus: %d register results + %d usable stability results; all values
live-verified against the ImB_QC_COAs source (4,134 passages).</span>
<span>Датасет и обработка | Dataset &amp; build: deliverables/potency_study/
(potency_dataset.json · build_potency_dataset.py · build_potency_html.py) —
летта-stack. Резиме запишано во споделената меморија на хостот (агент
ecoa_retrieval_gpt4o). | Study summary logged to the host's shared memory.</span>
<span>Меродавни остануваат лабораториските сертификати во СМК. |
The laboratory certificates in the QMS remain authoritative.</span>
</div></footer>
</body></html>
""" % (CSS, d["n_results"] + n_stab_usable, d["n_strains"], d["n_batches"], n_stab_usable,
       nav, stab_table(), strain_cards(), stock_table(),
       d["n_results"], d["n_strains"], n_stab_usable, d["n_results"], n_stab_usable)

out = os.path.join(HERE, "Potency_Atlas.html")
open(out, "w", encoding="utf-8").write(HTML)
print("wrote", out, "%.1f KB" % (os.path.getsize(out) / 1024))
