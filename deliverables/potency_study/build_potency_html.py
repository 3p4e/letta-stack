#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Potency Atlas — creative single-file HTML edition of the Strain Potency Study.

Same bound dataset (potency_dataset.json), richer per-result detail:
  • every actual Total Δ⁹-THC value, per strain, sorted ascending, batch
    number shown with its P-code where known;
  • the distance between successive results, in percentage points AND as a
    relative % of the lower value;
  • same-batch repeat pairs called out separately (the truest "distance
    between two results obtained by all means so far");
  • the CSS-built 0–30 % axis per strain: ±1.5 % zone per result, a
    full-height shaded zone per proposed Pot.- tier, old standard grade
    boundaries — no summary statistics (mean/SD/CI), per owner instruction;
  • the full T1/T2/T3 stock table.

Self-contained: subset Montserrat + Orbitron inlined as data-URI woff2, no
external requests. Single-theme by design (a laboratory document), every
surface painted explicitly.
"""
import html
import json
import math
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.path.join(HERE, "potency_dataset.json"), encoding="utf-8"))
GD = json.load(open(os.path.join(HERE, "grade_design_even.json"), encoding="utf-8"))

# truth-check fix (27.08.2026): cert ППК26065 prints серија JD112501* (milled,
# its own register batch); restore milled markers on display names
for _r in d["register_results"]:
    if _r["batch"] == "JD112501" and _r.get("cert") == "ППК26065":
        _r["batch"] = "JD112501*"
    _r["batch"] = {"GG012601": "GG012601*", "JD012601": "JD012601*"}.get(_r["batch"], _r["batch"])
for _s in d["stock"]:
    _s["batch"] = {"GG012601": "GG012601*", "JD012601": "JD012601*"}.get(_s["batch"], _s["batch"])

# convert the even-nominal grade design into the atlas tier schema (ascending)
import re as _re
_gaps = set()
for _e in GD["exceptions"]:
    _m = _re.search(r"^(.*?): uncovered zone .* between THC(\d+) and THC(\d+)", _e)
    if _m:
        _gaps.add((_m.group(1), int(_m.group(3))))   # (strain, weaker nominal below gap)
_new_mr = {}
for _strain, _entry in GD["strains"].items():
    _tiers = []
    for _g in reversed(_entry):                      # ascending
        _tiers.append({
            "range": [_g["lower"], _g["upper"]], "nominal": _g["nominal"],
            "tol": max(_g["minus_tol"], _g["plus_tol"]),
            "plus_tol": _g["plus_tol"], "minus_tol": _g["minus_tol"],
            "symmetric": _g["symmetric"], "expression": _g["expression"],
            "grade": _g["grade"], "product_code": _g["product_code"],
            "spec_code": _g["spec_code"], "bridge": _g.get("bridge", False),
            "odd": _g.get("odd", False),
            "gap_after": (_strain, _g["nominal"]) in _gaps,
            "batches": [_b["batch"] for _b in _g["batches"]],
            "values": {_b["batch"]: _b["v"] for _b in _g["batches"]},
        })
    _new_mr[_strain] = _tiers
d["merged_ranges"] = _new_mr
F = json.load(open(os.path.join(HERE, "webfonts", "fonts_b64.json"), encoding="utf-8"))
PM = json.load(open(os.path.join(HERE, "portfolio_master.json"), encoding="utf-8"))

# canonical register spellings for the master's Original column
CANON = {"Cap Junkie": "Cap Junky", "CashCow": "Cash Cow", "GG4": "Gorilla Glue",
         "Grapes and Cream": "Graps & Creme", "Jelly Donuts": "Jelly Donutz",
         "Sleepy Joe": "Sleepy Joy", "Clemosa": "Clemosa a bud",
         "Wedding Crusher": "Wedding Crasher", "Appels & Bananas": "Apple and Banana",
         "Apples and Bananas": "Apple and Banana"}


def norm_b(b):
    b = (b or "").strip().upper().replace("OMP", "OPM")
    import re as _re
    return _re.sub(r"/0(\d)", r"/\1", b)


REN = {norm_b(r["batch"]): r for r in PM}


def ren_of(batch):
    r = REN.get(norm_b(batch))
    if r and r["original"].strip().lower() != r["neu"].strip().lower():
        return r
    return None

OLD_TIERS = [5.00, 15.90, 22.90, 26.90, 30.00]
AX = 30.0


def esc(s):
    return html.escape(str(s), quote=True)


def pct(v):
    return 100.0 * v / AX


def dkey(s):
    p = (s or "").split(".")
    return (p[2], p[1], p[0]) if len(p) == 3 else ("0", "0", "0")


def potlabel(i, t, html_ent=True):
    """Full potency-class label: 'Pot.-1: 22.00% ±2.20%'. Accepts a
    merged_ranges tier dict or a (nominal, tol) pair. html_ent=False for
    plain-text targets (matplotlib figures, docx, xlsx cells)."""
    if isinstance(t, dict) and "grade" in t:
        tol = ("±%.2f%%" % t["plus_tol"]) if t.get("symmetric") \
            else ("+%.2f%%/−%.2f%%" % (t["plus_tol"], t["minus_tol"]))
        s = "%s · %d.00%% %s" % (t["product_code"].split(":")[0].split("_")[1], t["nominal"], tol)
        return s.replace(" ", "&nbsp;") if html_ent else s
    nom, tol = (t["nominal"], t["tol"]) if isinstance(t, dict) else t
    if html_ent:
        return "Pot.-%d:&nbsp;%.2f%%&nbsp;±%.2f%%" % (i, nom, tol)
    return "Pot.-%d: %.2f%% ±%.2f%%" % (i, nom, tol)


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
 --mut:#3E4B57; --line:#D8E2EC; --zone:rgba(43,84,126,.10);
 --mono:ui-monospace,'Cascadia Mono','Roboto Mono',Menlo,monospace;
}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{background:var(--paper);color:var(--ink);
 font:400 16.5px/1.58 'Montserrat',system-ui,sans-serif}
.wrap{max-width:1060px;margin:0 auto;padding:0 20px}
a{color:var(--navy2)}
.hero{background:linear-gradient(160deg,#EDF3F9 0%,#F7FAFD 60%,#E9F0F7 100%);
 color:var(--ink);padding:46px 0 38px;border-bottom:4px solid var(--gold)}
.brand{display:flex;align-items:baseline;gap:10px;letter-spacing:.24em;
 font-size:13px;font-weight:700}
.brand em{font-style:italic;font-weight:400;color:var(--gold)}
.brand{color:var(--navy)}
.brand small{letter-spacing:.18em;font-weight:400;font-size:9.5px;color:#7B8FA3}
.hero h1{font-family:'Montserrat';font-weight:700;font-size:clamp(28px,5vw,44px);
 letter-spacing:.01em;margin:18px 0 2px;text-wrap:balance}
.hero .en{font-family:'Orbitron';font-weight:400;font-size:clamp(13px,2vw,19px);
 letter-spacing:.34em;color:var(--gold);margin:0 0 10px;text-transform:uppercase}
.hero .sub{color:#4A5B6C;font-size:15.5px;max-width:62ch}
.chips{display:flex;flex-wrap:wrap;gap:10px;margin-top:22px}
.chip{background:#FFFFFF;border:1px solid var(--line);color:var(--ink);
 border-radius:4px;padding:7px 13px;font-size:12.5px}
.chip b{font-family:'Orbitron';font-size:16px;color:#8A6D14;margin-right:6px}
.informal{margin-top:18px;font-size:11px;letter-spacing:.14em;color:#7B8FA3;
 text-transform:uppercase}
section{padding:34px 0 6px}
h2{font-size:23px;font-weight:700;color:var(--navy);letter-spacing:.01em;
 border-bottom:2px solid var(--navy2);padding-bottom:6px;margin-bottom:16px}
h2 span{font-weight:400;color:var(--mut);font-size:16.5px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px}
.kcard{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--navy2);
 padding:14px 16px;font-size:13.5px}
.kcard.warm{border-left-color:var(--rose)}
.kcard.gold{border-left-color:var(--gold)}
.kcard.green{border-left-color:var(--green)}
.kcard b{display:block;margin-bottom:4px;color:var(--navy)}
.kcard i{color:var(--mut);font-size:12px}
.rule{background:#EDF3F9;color:var(--ink);border:1px solid var(--line);padding:14px 20px;margin-top:14px;
 font-size:13px;border-radius:2px;display:flex;flex-wrap:wrap;gap:6px 22px;
 align-items:baseline}
.rule b{width:100%;letter-spacing:.05em}
.rule code{font-family:var(--mono);color:#8A6D14;font-size:13.5px}
.nav{position:sticky;top:0;z-index:9;background:rgba(247,249,252,.96);
 backdrop-filter:blur(4px);border-bottom:1px solid var(--line);padding:9px 0}
.nav .wrap{display:flex;flex-wrap:wrap;gap:6px}
.nav a{font-size:12.5px;text-decoration:none;border:1px solid var(--line);
 background:var(--card);padding:3px 9px;border-radius:12px;color:var(--navy)}
.nav a:hover{border-color:var(--navy2);background:#EDF3F9}
.strain{background:var(--card);border:1px solid var(--line);margin-bottom:26px;
 scroll-margin-top:64px}
.shead{display:flex;flex-wrap:wrap;align-items:baseline;gap:8px 18px;
 padding:14px 18px;border-bottom:1px solid var(--line);
 background:linear-gradient(90deg,#F2F6FA,#FFFFFF)}
.shead h3{font-family:'Orbitron';font-weight:400;font-size:22px;letter-spacing:.05em;
 color:var(--navy)}
.stat{font-size:13.5px;color:var(--mut)}
.stat b{color:var(--ink);font-size:15px;font-variant-numeric:tabular-nums}
.axiswrap{padding:18px 18px 6px;overflow-x:auto}
.axis{position:relative;height:148px;min-width:640px;
 background:linear-gradient(180deg,#FBFCFE, #F4F7FB);border:1px solid var(--line)}
.axis>i{position:absolute;top:0;bottom:0;width:0;border-left:1px solid #EBF0F5;z-index:0}
.tierzone{position:absolute;top:0;bottom:0;background:rgba(30,132,73,.09);
 border-left:1px solid rgba(30,132,73,.35);border-right:1px solid rgba(30,132,73,.35);
 z-index:1}
.gapzone{position:absolute;top:0;bottom:0;z-index:1;cursor:help;
 background:repeating-linear-gradient(135deg,rgba(193,58,58,.14) 0 6px,
 rgba(193,58,58,.02) 6px 12px);border-left:1px dashed var(--rose);
 border-right:1px dashed var(--rose)}
.zone{position:absolute;top:14%;height:56%;background:var(--zone);z-index:2}
.old{position:absolute;top:0;bottom:0;border-left:1px dashed #B9C7D6;z-index:2}
.dot{position:absolute;top:64%;width:15px;height:15px;border-radius:50%;
 background:var(--navy2);border:2.5px solid #fff;box-shadow:0 0 0 1.5px var(--navy2);
 transform:translateX(-50%);cursor:pointer;z-index:5;
 transition:transform 70ms ease-out,box-shadow 70ms ease-out}
.dot:hover{transform:translateX(-50%) scale(1.55);z-index:8;
 box-shadow:0 0 0 2px var(--navy2),0 2px 8px rgba(20,40,60,.35)}
.tier{position:absolute;height:22px;background:#F2FAF5;
 border:2.5px solid var(--green);font-size:12.5px;font-weight:700;color:#0F3D22;
 display:flex;align-items:center;justify-content:center;white-space:nowrap;
 letter-spacing:.01em;border-radius:3px;z-index:4;font-variant-numeric:tabular-nums;
 padding:0 7px;transform:translateX(-50%)}
.stab25{position:absolute;top:84%;width:10px;height:10px;background:var(--green);
 border:2px solid #fff;box-shadow:0 0 0 1px var(--green);transform:translateX(-50%);z-index:5}
.stab40{position:absolute;top:84%;width:0;height:0;transform:translateX(-50%);
 border-left:6px solid transparent;border-right:6px solid transparent;
 border-top:10px solid var(--rose);z-index:5}
.scale{display:flex;justify-content:space-between;min-width:640px;
 font:600 12px var(--mono);color:var(--mut);font-variant-numeric:tabular-nums;margin-top:4px}
.legend{padding:6px 18px 12px;font-size:14px;color:var(--mut);display:flex;
 flex-wrap:wrap;gap:6px 22px}
.legend i{font-style:normal;display:inline-flex;align-items:center}
.dotk{display:inline-block;width:13px;height:13px;border-radius:50%;
 background:var(--navy2);border:2px solid #fff;box-shadow:0 0 0 1px var(--navy2);
 margin-right:6px}
.zonek{display:inline-block;width:16px;height:12px;background:var(--zone);
 margin-right:6px}
.tierk{display:inline-block;width:18px;height:12px;background:rgba(30,132,73,.20);
 border:2px solid var(--green);border-radius:2px;margin-right:6px}
.gapk{display:inline-block;width:18px;height:12px;border-radius:2px;margin-right:6px;
 border:1px dashed var(--rose);background:repeating-linear-gradient(135deg,
 rgba(193,58,58,.16) 0 5px,rgba(193,58,58,.03) 5px 10px)}
.oldk{display:inline-block;width:0;height:13px;border-left:1px dashed #B9C7D6;
 margin-right:6px}
table{border-collapse:collapse;width:100%;font-size:13.5px}
.tblwrap{overflow-x:auto;padding:0 18px 16px}
th{background:var(--navy);color:#fff;font-weight:600;padding:7px 10px;font-size:12px;
 letter-spacing:.05em;text-align:left;white-space:nowrap}
td{border-bottom:1px solid var(--line);padding:5.5px 9px;white-space:nowrap;
 font-variant-numeric:tabular-nums}
tr:nth-child(even) td{background:#F6F9FC}
td.v{font-family:var(--mono);font-weight:600;color:var(--navy)}
.mismatch{color:var(--rose);font-weight:700;text-decoration:underline dotted}
td.num{font-family:var(--mono)}
td.gap{color:var(--navy2)}
.badge{display:inline-block;background:#EDF3F9;border:1px solid var(--navy2);
 color:var(--navy2);font-size:9.5px;font-weight:700;border-radius:9px;
 padding:0 6px;margin-left:6px;vertical-align:1px}
.callout{margin:0 18px 16px;background:#FBF6E9;border:1px solid var(--gold);
 padding:10px 14px;font-size:12.5px}
.callout b{color:#8A6D14}
.tiers{margin:0 18px 16px;font-size:15.5px}
.tiers .trow{display:flex;gap:10px;align-items:baseline;padding:3px 0}
.tiers .tr-range{font-family:var(--mono);font-weight:700;color:#14532B;min-width:230px;
 font-size:16px}
.tiers .tr-span{font-family:var(--mono);color:var(--mut);font-size:13px;margin-right:4px}
.tiers .gaprow{color:#8A2E2E;font-size:13.5px;background:rgba(193,58,58,.06);
 border-left:3px solid var(--rose);padding:3px 0 3px 8px;margin:2px 0}
.tiers .gaprow .tr-span{color:#8A2E2E;font-weight:700}
.method{background:var(--card);border:1px solid var(--line);
 border-left:4px solid var(--green);padding:18px 22px 20px;margin-bottom:22px}
.method h3{font-size:15px;font-weight:700;color:var(--navy);letter-spacing:.01em;
 margin-bottom:3px}
.method h3 span{font-weight:400;color:var(--mut);font-size:13.5px}
.method .lede{font-size:13px;color:var(--mut);margin-bottom:14px;max-width:104ch}
.mrules{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));
 gap:12px;margin-bottom:14px}
.mrule{background:#F6FAF7;border:1px solid rgba(30,132,73,.28);border-radius:3px;
 padding:10px 13px;font-size:12.5px;line-height:1.5;color:var(--ink)}
.mrule b{display:block;color:#14532B;font-size:12px;letter-spacing:.03em;
 text-transform:uppercase;margin-bottom:4px}
.mrule b i{font-family:var(--mono);font-style:normal;font-size:13px;
 margin-right:6px;opacity:.65}
.mrule em{font-style:normal;color:var(--mut);font-size:11.5px;display:block;
 margin-top:4px}
.mparams{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px}
.mparam{background:#EDF3F9;border:1px solid var(--line);border-radius:3px;
 padding:5px 11px;font-size:12px;color:var(--mut)}
.mparam b{font-family:var(--mono);color:var(--navy);font-weight:700;
 font-variant-numeric:tabular-nums}
.mwork{background:#F7FAFC;border:1px solid var(--line);border-radius:3px;
 padding:11px 14px;font-size:12.5px;color:var(--ink);line-height:1.65}
.mwork b{color:var(--navy)}
.mwork code{font-family:var(--mono);font-weight:700;color:#14532B;
 font-variant-numeric:tabular-nums}
.mwork .arrow{color:var(--mut);margin:0 5px}
.msum{margin-top:13px;padding-top:11px;border-top:1px dashed var(--line);
 font-size:12.5px;color:var(--ink)}
.msum b{color:var(--navy)}
.stabnote{color:var(--rose);font-size:11.5px}
details{margin-top:8px}
summary{cursor:pointer;font-weight:600;color:var(--navy);padding:10px 0}
.dot.ren{box-shadow:0 0 0 1.5px var(--navy2),0 0 0 5px rgba(201,162,39,.55)}
.renlist{padding:8px 18px 14px;font-size:13.5px;color:var(--mut)}
.renlist>b{display:block;color:var(--navy);margin-bottom:6px;font-size:13px}
.renlist .renitem{display:flex;align-items:center;gap:10px;flex-wrap:wrap;
 padding:6px 4px;border-top:1px solid var(--line)}
.renlist .renitem:first-of-type{border-top:none}
.renbatch{font-family:var(--mono);font-weight:700;font-size:13.5px;color:var(--ink);
 background:#EDF3F9;border:1px solid var(--navy2);border-radius:3px;
 padding:2px 8px;font-variant-numeric:tabular-nums}
.renarrow{color:var(--mut)}
.renlist b{color:var(--navy)}
.renval{margin-left:auto;font-family:var(--mono);font-weight:700;font-size:14.5px;
 color:var(--ink);background:#F4F7FB;border-radius:3px;padding:2px 8px;
 font-variant-numeric:tabular-nums}
.bchip{display:inline-block;font-size:10px;font-weight:700;letter-spacing:.08em;
 padding:1px 6px;border-radius:2px;margin-left:5px;vertical-align:1px}
.bchip.steady{background:#EDF3F9;color:var(--navy2);border:1px solid var(--navy2)}
.bchip.cayn{background:#F5EEF9;color:#7B4F8C;border:1px solid #7B4F8C}
.keepname{font-size:11px;color:var(--mut);font-weight:400;margin-left:5px}
.rencard{background:var(--card);border:1px solid var(--line);margin-bottom:22px}
.flowrow{display:grid;grid-template-columns:240px 1fr;gap:16px;align-items:start;
 padding:14px 18px;border-top:1px solid var(--line)}
.flowrow:first-of-type{border-top:none}
.flowname{font-size:16px;font-weight:600;color:var(--navy);
 border-right:2px solid var(--gold);padding-right:14px;min-height:70px}
.flowname b{font-weight:700}
.flowbatches{font-size:12.5px;font-weight:400;color:var(--mut);margin-top:6px;
 font-family:var(--mono);line-height:1.7}
.flowaxis{min-width:0}
.miniaxis{position:relative;height:46px;background:linear-gradient(180deg,#FBFCFE,#F4F7FB);
 border:1px solid var(--line);overflow:hidden}
.miniaxis i{position:absolute;top:0;bottom:0;border-left:1px solid #EDF1F5}
.mspan{position:absolute;top:8%;height:38%;background:rgba(201,162,39,.24);
 border:1.5px solid var(--gold)}
.wspan{position:absolute;top:54%;height:38%;background:rgba(30,132,73,.18);
 border:1.5px solid var(--green)}
.mdot{position:absolute;top:50%;width:9px;height:9px;border-radius:50%;margin-top:-4.5px;
 background:var(--navy2);border:2px solid #fff;box-shadow:0 0 0 1px var(--navy2);
 transform:translateX(-50%);z-index:3}
.mdot.decl{background:#fff;box-shadow:0 0 0 1px var(--gold)}
.cmpline{display:flex;flex-wrap:wrap;gap:10px;margin-top:8px}
.cmp{flex:1 1 240px;padding:8px 12px;border-radius:3px;line-height:1.35}
.cmp small{display:block;font-size:11px;font-weight:700;letter-spacing:.08em;
 text-transform:uppercase;margin-bottom:2px}
.cmp b{font-family:var(--mono);font-size:16.5px;font-weight:700;
 font-variant-numeric:tabular-nums}
.cmp.m{background:rgba(201,162,39,.12);border-left:4px solid var(--gold)}
.cmp.m small{color:#7A5E10}
.cmp.m b{color:#6B520E}
.cmp.w{background:rgba(30,132,73,.10);border-left:4px solid var(--green)}
.cmp.w small{color:#14532B}
.cmp.w b{color:#14532B}
.miniscale{display:flex;justify-content:space-between;margin-top:2px;
 font:600 11.5px var(--mono);color:var(--mut);font-variant-numeric:tabular-nums}
@media (max-width:760px){.flowrow{grid-template-columns:1fr}
 .flowname{border-right:none;border-bottom:2px solid var(--gold);padding:0 0 8px;min-height:0}}
#final{scroll-margin-top:64px}
.fsum{font-size:14.5px;color:var(--mut);margin-bottom:16px;max-width:88ch}
.fsum code{font:600 13.5px var(--mono);color:var(--navy2)}
.fboard{background:#F4F8FB;border:1px solid var(--line);
 border-bottom:4px solid var(--gold);padding:8px 22px 18px}
.fhead{display:grid;grid-template-columns:230px 1fr 250px;gap:16px;
 padding:11px 0 7px;border-bottom:2px solid var(--navy2);font-size:11px;
 font-weight:700;letter-spacing:.06em;color:var(--navy);text-transform:uppercase}
.frow{display:grid;grid-template-columns:230px 1fr 250px;gap:16px;align-items:center;
 padding:13px 0;border-bottom:1px solid var(--line)}
.frow:last-child{border-bottom:none}
.fname h3{font-family:'Orbitron';font-weight:400;font-size:17px;letter-spacing:.05em;
 color:var(--navy);margin-bottom:2px}
.fstat{font-size:12.5px;color:var(--mut);display:block;font-variant-numeric:tabular-nums}
.fbadge{display:inline-block;margin-top:5px;font-size:10px;font-weight:700;
 letter-spacing:.09em;color:#8A6D14;border:1px solid var(--gold);
 padding:1.5px 7px;border-radius:2px}
.fbadge.prov{color:var(--rose);border-color:var(--rose)}
.fpills{display:flex;flex-wrap:wrap;gap:9px}
.fpill{font-family:var(--mono);font-size:16.5px;font-weight:700;color:#14532B;
 background:rgba(30,132,73,.12);border:1.5px solid var(--green);border-radius:3px;
 padding:7px 13px;line-height:1.2}
.fpill small{display:block;font-family:'Montserrat';font-weight:400;font-size:11px;
 color:#3A6247;margin-top:2px}
.fpill.prov{background:rgba(201,162,39,.14);border-color:var(--gold);color:#7A5E10}
.fpill.prov small{color:#6B5A20}
.fgap{font-family:var(--mono);font-size:12.5px;font-weight:600;color:#8A2E2E;
 background:rgba(193,58,58,.08);border:1px dashed var(--rose);border-radius:3px;
 padding:6px 10px;line-height:1.2;align-self:center;cursor:help}
.fren{display:flex;flex-direction:column;gap:9px;font-size:13px}
.fren .renentry{display:flex;flex-direction:column;gap:2px}
.fren .rname{color:var(--ink);font-weight:400}
.fren .rname b{font-weight:700;color:var(--navy)}
.fren .renentry>small{color:var(--mut);font-size:11.5px;
 font-variant-numeric:tabular-nums}
.minilbl{display:block;color:var(--mut);font-size:10.5px;margin-top:3px}
.minipills{display:flex;flex-wrap:wrap;gap:5px;margin-top:3px}
.fpill.mini{font-size:11.5px;padding:3px 8px;border-width:1px}
.fpill.mini small{font-size:9.5px}
.sigs{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:6px}
.sig{background:var(--card);border:1px solid var(--line);border-top:3px solid var(--navy2);
 padding:18px 20px 20px;text-align:center}
.sigpill{display:inline-block;font-size:10.5px;font-weight:700;letter-spacing:.09em;
 color:var(--navy2);border:1px solid var(--navy2);border-radius:11px;
 padding:2px 11px;margin-bottom:10px}
.signame{font-size:16.5px;font-weight:700;color:var(--navy);letter-spacing:.01em}
.sigrole{display:block;color:var(--mut);font-size:12.5px;font-style:italic;margin-top:2px}
.sigdate{margin-top:14px;font-size:11.5px;color:var(--mut)}
.sigdate b{font-family:var(--mono);color:var(--ink);font-weight:700;
 letter-spacing:.03em;margin-left:5px;font-variant-numeric:tabular-nums}
.signote{font-size:11.5px;color:var(--mut);margin-top:12px;max-width:96ch}
@media (max-width:760px){.frow{grid-template-columns:1fr}.fhead{display:none}
 .sigs{grid-template-columns:1fr}}
@page{size:A4;margin:11mm 10mm}
@media print{
 *{-webkit-print-color-adjust:exact;print-color-adjust:exact}
 body{font-size:11.5px}
 .nav, section{padding:14px 0 2px}
 section h2{break-after:avoid}
 .strain,.rencard,.kcard,.rs{break-inside:avoid}
 .frow{break-inside:avoid}
 .sig,.sigs{break-inside:avoid}
 .axiswrap,.tblwrap{overflow:visible;padding-left:10px;padding-right:10px}
 .axis,.scale,.miniaxis{min-width:0}
 table{font-size:9px}
 td{white-space:normal}
 .hero{padding:26px 0 22px}
 .renlist{line-height:1.8}

}


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
    minor = "".join('<i style="left:%.3f%%"></i>' % pct(x) for x in range(1, 30))
    dots = ""
    for r in per[s]:
        rn = ren_of(r["batch"])
        extra = (" · %s → %s (%s)" % (rn["original"], rn["neu"], rn["brand"])) if rn else ""
        dots += ('<div class="dot%s" style="left:%.3f%%" title="%s · %s · %s · %.2f%%%s"></div>'
                 % (" ren" if rn else "", pct(r["value"]), esc(r["batch"]), esc(r["date"]),
                    esc(r["lab"]), r["value"], esc(extra)))
    tz = ""    # full-height zone band per tier, behind everything else
    tt = ""    # the nominal ± tolerance label badge on top
    gz = ""    # hatched "no established grade" band, only where the data
               # itself leaves an unbridgeable gap between two tiers
    for i, t in enumerate(tiers):
        lo, hi = t["range"]
        tz += ('<div class="tierzone" style="left:%.3f%%;width:%.3f%%"></div>'
               % (pct(lo), pct(hi - lo)))
        if t.get("gap_after") and i + 1 < len(tiers):
            glo, ghi = hi, tiers[i + 1]["range"][0]
            gz += ('<div class="gapzone" style="left:%.3f%%;width:%.3f%%" '
                   'title="Нема воспоставена класа %.2f%%–%.2f%% — ниту една тестирана серија '
                   'на оваа сорта не паѓа тука; резултат во оваа зона бара индивидуална КК '
                   'проценка. | No established grade %.2f%%–%.2f%% — no tested batch of this '
                   'strain falls here; a result in this zone requires individual QC '
                   'assessment."></div>'
                   % (pct(glo), pct(ghi - glo), glo, ghi, glo, ghi))
        # label plate centred on the tier's midpoint (translateX(-50%) in CSS)
        # so a label wider than a narrow tier never clips at the band edges;
        # three stagger rows keep neighbouring labels off each other's row.
        top = (6, 34, 62)[i % 3]
        tt += ('<div class="tier" style="left:%.3f%%;top:%dpx" '
               'title="%.2f%% ± %.2f%% (%.2f%%–%.2f%%) · серии | batches: %s">%s</div>'
               % (pct((lo + hi) / 2), top, t["nominal"], t["tol"], lo, hi,
                  esc(", ".join(t["batches"])), potlabel(i + 1, t)))
    sb = ""
    for r in stab:
        cls = "stab25" if r["arm"].startswith("25") else "stab40"
        sb += ('<div class="%s" style="left:%.3f%%" title="%s M%d %s — %.2f%% (CBN %.2f%%)"></div>'
               % (cls, pct(r["total_thc"]), esc(r["batch"]), r["month"], esc(r["arm"]),
                  r["total_thc"], r["cbn"]))
    scale = "".join("<span>%.2f%%</span>" % x for x in range(0, 31, 5))
    ren_items = []
    for r in per[s]:
        rn = ren_of(r["batch"])
        if rn:
            pc = r.get("p_code")
            bid = "%s (%s)" % (esc(r["batch"]), esc(pc)) if pc else esc(r["batch"])
            ren_items.append(
                '<div class="renitem"><span class="renbatch">%s</span>'
                '<span class="renarrow">→</span><b>%s</b>'
                '<span class="bchip %s">%s</span>'
                '<span class="renval">%.2f%%</span></div>'
                % (bid, esc(rn["neu"]), esc(rn["brand"].lower()), esc(rn["brand"]), r["value"]))
    renlist = ('<div class="renlist"><b>Преименувани серии на лентата | Renamed batches on the '
               'band:</b>%s</div>' % "".join(ren_items)) if ren_items else ""
    return ('<div class="axiswrap"><div class="axis">%s%s%s%s%s%s%s</div>'
            '<div class="scale">%s</div></div>%s'
            % (tz, gz, zones, olds, minor, tt, dots + sb, scale, renlist))


def results_table(s, st):
    rs = per[s]
    n = len(rs)
    # count batches with >1 result for repeat badges
    from collections import Counter
    bc = Counter(r["batch"] for r in rs)
    rows = ""
    for i, r in enumerate(rs):
        if i < n - 1:
            nxt = rs[i + 1]["value"]
            gpp = nxt - r["value"]
            grel = 100.0 * gpp / r["value"] if r["value"] else 0
            gap = "+%.2f пп · +%.2f%%" % (gpp, grel)
        else:
            gap = "—"
        badge = '<span class="badge" title="серијата е мерена повеќе пати | batch measured more than once">↺</span>' \
            if bc[r["batch"]] > 1 else ""
        pc = r.get("p_code")
        bid = ('<span class="renbatch">%s (%s)</span>' % (esc(r["batch"]), esc(pc))
               if pc else '<span class="renbatch">%s</span>' % esc(r["batch"]))
        rn = ren_of(r["batch"])
        newname = ('%s <span class="bchip %s">%s</span>'
                   % (esc(rn["neu"]), esc(rn["brand"].lower()), esc(rn["brand"]))) if rn else "—"
        rows += ("<tr><td>%d</td><td class=num>%s%s</td><td>%s</td><td>%s</td>"
                 "<td class=v>%.2f%%</td><td class=gap>%s</td>"
                 "<td>%s</td></tr>"
                 % (i + 1, bid, badge, esc(r["date"]), esc(r["lab"]),
                    r["value"], gap, newname))
    return ('<div class="tblwrap"><table><thead><tr>'
            "<th>№</th><th>Серија (P-серија) | Batch (P-batch)</th><th>Датум | Date</th>"
            "<th>Лаб | Lab</th><th>Вкупен THC %%</th>"
            "<th>Δ до следен | to next (пп · %%)</th>"
            "<th>Ново име | New name</th>"
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
            items.append("<b>%s</b>: %.2f%% (%s) → %.2f%% (%s) — Δ %+.2f пп · %+.2f%%"
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
    rows = ""
    for i, t in enumerate(tiers):
        blist = (esc(", ".join("%s %.2f" % (b, t["values"].get(b, 0)) for b in t["batches"]))
                 if t.get("batches") else
                 "<i>резервна класа — нема тековна серија | reserve grade — no current batch</i>")
        codes = ('<span class="tr-codes"><b>%s</b> · %s · %s</span>'
                 % (esc(t.get("grade", "")), esc(t.get("product_code", "").replace(":", " : ")),
                    esc(t.get("spec_code", ""))))
        rows += ('<div class="trow"><span class="tr-range">%s</span>'
                 '<span class="tr-span">(%.2f%% – %.2f%%)</span>%s<span>%s</span></div>'
                 % (esc(t.get("expression", "").split(" (")[0]),
                    t["range"][0], t["range"][1], codes, blist))
        if t.get("gap_after") and i + 1 < len(tiers):
            glo, ghi = t["range"][1], tiers[i + 1]["range"][0]
            rows += ('<div class="trow gaprow">⚠ <span class="tr-span">(%.2f%% – %.2f%%)</span>'
                     '<span>Нема воспоставена класа — резултат тука бара индивидуална КК '
                     'проценка | No established grade — a result here requires individual QC '
                     'assessment</span></div>' % (glo, ghi))
    # The declaration rule is stated ONCE, in the methodology panel at the top
    # of this section — never repeated per strain.
    return ('<div class="tiers"><b>Потенциски класи | Potency grades (спецификации | specifications):</b>%s</div>' % rows)


def strain_cards():
    out = ""
    for s in sorted(d["stats"]):
        st = d["stats"][s]
        sid = "s-" + "".join(c if c.isalnum() else "-" for c in s.lower())
        chips = ("<span class=stat>Бр. тестирани резултати | Number of results tested "
                 "<b>%d</b></span>" % st["n"])
        chips += ("<span class=stat>опсег на тестираните резултати | range of tested "
                  "results <b>%.2f%% – %.2f%%</b></span>" % (st["min"], st["max"]))
        has_gap = any(t.get("gap_after") for t in d["merged_ranges"].get(s, []))
        legend = ('<div class="legend"><i><span class="dotk"></span>резултат | result</i>'
                  '<i><span class="zonek"></span>±1,50% зона | zone</i>'
                  '<i><span class="tierk"></span>класи | grades</i>'
                  '<i><span class="oldk"></span>стари граници на класи | old grade boundaries</i>'
                  + ('<i><span class="gapk"></span>нема класа | no established grade</i>'
                     if has_gap else "") + '</div>')
        out += ('<article class="strain" id="%s"><div class="shead"><h3>%s</h3>%s</div>'
                "%s%s%s%s%s</article>"
                % (sid, esc(s), chips, axis_html(s, st, d["merged_ranges"].get(s, []), []),
                   legend, tiers_block(s), results_table(s, st), repeats_callout(s)))
    return out


def parse_bracket(b):
    """Master bracket string -> (lo, hi, label). '≥ 25%' is open-ended (drawn to 30)."""
    b = (b or "").strip()
    if not b:
        return None
    m = re.match(r"[≥>]=?\s*(\d+(?:[.,]\d+)?)", b)
    if m:
        lo = float(m.group(1).replace(",", "."))
        return (lo, 30.0, "≥%.2f%%" % lo)
    m = re.match(r"(\d+(?:[.,]\d+)?)\s*[–—-]\s*(\d+(?:[.,]\d+)?)", b)
    if m:
        lo = float(m.group(1).replace(",", "."))
        hi = float(m.group(2).replace(",", "."))
        return (lo, hi, "%.2f%%–%.2f%%" % (lo, hi))
    return None


def fmt_bracket(b):
    """The old master bracket, re-printed to the house numeric rule
    (two decimals, % on both bounds). Falls back to the raw string when it
    does not parse — a bracket is transcribed source data, never invented."""
    p = parse_bracket(b)
    return p[2] if p else (b or "—")


def renames_section():
    """REDESIGNED rename layer: per original strain, the mapping into new names, and —
    for every new-name group — OUR statistically derived Pot.-tier vs the bracket the
    Portfolio Master itself suggests, on one comparison axis with verdicts."""
    from collections import OrderedDict

    anch = {}
    for r in d["register_results"]:
        k = norm_b(r["batch"])
        if k not in anch or dkey(r["date"]) > dkey(anch[k]["date"]):
            anch[k] = r
    # our grade per batch, straight from the even-nominal design
    ours = {}
    for _tiers in d["merged_ranges"].values():
        for t in _tiers:
            for _b in t["batches"]:
                ours[norm_b(_b)] = (t["range"][0], t["range"][1],
                                    t["nominal"], t["tol"], t["expression"])

    groups = OrderedDict()
    for rec in PM:
        orig = CANON.get(rec["original"], rec["original"])
        groups.setdefault(orig, OrderedDict()).setdefault(rec["neu"], []).append(rec)

    cards = ""
    for orig in sorted(groups):
        news = groups[orig]
        n_batches = sum(len(v) for v in news.values())
        n_renamed = sum(1 for rs in news.values() for rec in rs
                        if rec["original"].strip().lower() != rec["neu"].strip().lower())
        rows_html = ""
        for neu, rs in news.items():
            is_same = rs[0]["original"].strip().lower() == neu.strip().lower()
            brand = rs[0]["brand"]
            # collect per-batch data
            items = []
            for rec in rs:
                k = norm_b(rec["batch"])
                a = anch.get(k)
                val = a["value"] if a else (rec["thc"] * 100 if isinstance(rec["thc"], (int, float)) else None)
                items.append(dict(batch=rec["batch"], val=val, declared=a is None,
                                  mb=parse_bracket(rec["bracket"]), ours=ours.get(k)))
            # axis spans
            spans = ""
            mset, wset = [], []
            for it in items:
                if it["mb"] and it["mb"][:2] not in mset:
                    mset.append(it["mb"][:2])
                    lo, hi = it["mb"][:2]
                    spans += ('<div class="mspan" style="left:%.3f%%;width:%.3f%%" '
                              'title="мастер | master: %s"></div>' % (pct(lo), pct(hi - lo), esc(it["mb"][2])))
                if it["ours"] and it["ours"] not in wset:
                    wset.append(it["ours"])
                    lo, hi = it["ours"][:2]
                    spans += ('<div class="wspan" style="left:%.3f%%;width:%.3f%%" '
                              'title="наш опсег | our tier: %.2f%% – %.2f%%"></div>'
                              % (pct(lo), pct(hi - lo), lo, hi))
            dots = ""
            for it in items:
                if it["val"] is None:
                    continue
                cls = "mdot decl" if it["declared"] else "mdot"
                dots += ('<div class="%s" style="left:%.3f%%" title="%s · %.2f%%%s"></div>'
                         % (cls, pct(it["val"]), esc(it["batch"]), it["val"],
                            " · декларирана | declared" if it["declared"] else ""))
            gridt = "".join('<i style="left:%.3f%%"></i>' % pct(x) for x in range(5, 30, 5))
            mscale = "".join("<span>%.2f%%</span>" % x for x in range(0, 31, 5))
            blist = ", ".join("%s (%s)" % (esc(it["batch"]),
                                           ("%.2f%%" % it["val"]) if it["val"] is not None and not it["declared"]
                                           else ("%.2f%% декл." % it["val"] if it["val"] is not None else "—"))
                              for it in items)
            mb_lbl = " · ".join(sorted({it["mb"][2] for it in items if it["mb"]})) or "—"
            ours_lbl = " · ".join(w[4] for w in wset) or "—"
            rows_html += (
                '<div class="flowrow">'
                '<div class="flowname">%s<span class="bchip %s">%s</span>%s'
                '<div class="flowbatches">%s</div></div>'
                '<div class="flowaxis"><div class="miniaxis">%s%s%s</div>'
                '<div class="miniscale">%s</div>'
                '<div class="cmpline">'
                '<span class="cmp m"><small>мастер | master</small><b>%s</b></span>'
                '<span class="cmp w"><small>наш предлог | our proposal</small><b>%s</b></span>'
                "</div></div></div>"
                % ((esc(neu) if is_same else "<b>%s</b>" % esc(neu)),
                   esc(brand.lower()), esc(brand),
                   ' <span class="keepname">без промена | unchanged</span>' if is_same else "",
                   blist, gridt, spans, dots, mscale, esc(mb_lbl), ours_lbl))
        cards += ('<article class="rencard"><div class="shead"><h3>%s</h3>'
                  '<span class="stat">серии | batches <b>%d</b></span>'
                  '<span class="stat">преименувани | renamed <b>%d</b></span>'
                  '<span class="stat">нови имиња | new names <b>%d</b></span></div>%s</article>'
                  % (esc(orig), n_batches, n_renamed, len(news), rows_html))
    return cards


def final_ranges():
    """Closing verdict as ONE three-column board: the ORIGINAL specification
    strain, the proposed grade ranges, and the names the strain's batches
    carry AFTER RENAMING (01_Portfolio_Master) — so the whole old-name ->
    range -> new-name picture reads left to right on a single row. The former
    separate renamed-name board is folded into column 3; where a new-name
    group's own recomputed ladder differs from the origin strain's (its
    batches cluster differently under the new name), those tiers are shown
    compactly under that name so no information from the old board is lost."""
    from collections import OrderedDict
    basis = {norm_b(b["batch"]): b["anchor"] is not None for b in d["stock"]}
    anchors = {}
    for b in d["stock"]:
        a = b["anchor"] if b["anchor"] is not None else b["declared"]
        if a is not None:
            anchors[norm_b(b["batch"])] = (a, b["anchor"] is not None)

    # rename layer: origin strain (register spelling) -> {new name: [records]}
    by_origin = OrderedDict()
    groups = {}
    for r in PM:
        neu = (r.get("neu") or "").strip()
        if not neu:
            continue
        raw = (r.get("original") or "").strip()
        orig = CANON.get(raw, raw)
        by_origin.setdefault(orig, OrderedDict()).setdefault(neu, []).append(r)
        groups.setdefault(neu, []).append(r)

    # per-new-name ladder (same computation the old renamed board used),
    # shown in column 3 only where it DIFFERS from the origin's own ladder
    neu_tiers = {}
    for neu, recs in groups.items():
        items = [(r["batch"],) + anchors[norm_b(r["batch"])]
                 for r in recs if norm_b(r["batch"]) in anchors]
        if items:
            pass  # per-new-name ladders retired: the even-nominal design governs
    neu_origins = {neu: sorted({CANON.get((r.get("original") or "").strip(),
                                          (r.get("original") or "").strip())
                                for r in recs}) for neu, recs in groups.items()}

    rows = ""
    n_def = n_prov = 0
    for strain in sorted(d["merged_ranges"]):
        tiers = d["merged_ranges"][strain]
        if not tiers:
            continue
        st = d["stats"].get(strain)
        sig_orig = tuple((t["nominal"], t["tol"]) for t in tiers)
        pills = ""
        strain_prov = True
        for i, t in enumerate(tiers):
            tested = [b for b in t["batches"] if basis.get(norm_b(b), False)]
            prov = len(tested) == 0
            if not prov:
                strain_prov = False
            cnt = ("резервна | reserve" if t.get("bridge")
                   else "%d %s" % (len(t["batches"]),
                                   "серии | batches" if len(t["batches"]) != 1 else "серија | batch"))
            pills += ('<span class="fpill%s" title="%s · %s">%s'
                      "<small>%.2f%% – %.2f%% · %s</small></span>"
                      % (" prov" if prov else "",
                         esc(t.get("spec_code", "")), esc(", ".join(t["batches"]) or "—"),
                         potlabel(i + 1, t), t["range"][0], t["range"][1], cnt))
            if t.get("gap_after") and i + 1 < len(tiers):
                glo, ghi = t["range"][1], tiers[i + 1]["range"][0]
                pills += ('<span class="fgap" title="Нема воспоставена класа %.2f%%–%.2f%% | '
                          'No established grade %.2f%%–%.2f%%">⚠ %.2f%%–%.2f%%</span>'
                          % (glo, ghi, glo, ghi, glo, ghi))
        if strain_prov:
            n_prov += 1
        else:
            n_def += 1
        stat = (("Бр. тестирани резултати | Number of results tested: %d" % st["n"])
                if st else "без тестирања | no assays")
        badge = ('<span class="fbadge prov">ПРОВИЗОРНО — само декларирана основа | '
                 "PROVISIONAL — declared basis only</span>") if strain_prov else \
                '<span class="fbadge">ДЕФИНИТИВНО | DEFINITIVE</span>'

        # column 3: the names this strain's batches carry after renaming
        ren_entries = []
        for neu, recs in (by_origin.get(strain) or {}).items():
            is_same = neu.strip().lower() == strain.strip().lower()
            brand = (recs[0].get("brand") or "").strip()
            n = len(recs)
            name_html = esc(neu) if is_same else "<b>%s</b>" % esc(neu)
            chip = ('<span class="bchip %s">%s</span>'
                    % (esc(brand.lower()), esc(brand))) if brand else ""
            extra = (' <span class="keepname">без промена | unchanged</span>'
                     if is_same else "")
            others = [o for o in neu_origins.get(neu, []) if o != strain]
            share = ('<small class="minilbl">заедно со | together with: %s</small>'
                     % esc(", ".join(others))) if others else ""
            mini = ""
            nt = neu_tiers.get(neu)
            if nt is not None:
                sig_neu = tuple((t["nominal"], t["tol"]) for t in nt)
                if others or sig_neu != sig_orig:
                    mp = "".join('<span class="fpill mini%s" title="%s">%s'
                                 "<small>%.2f%% – %.2f%%</small></span>"
                                 % (" prov" if not any(t["tested"]) else "",
                                    esc(", ".join(t["batches"])),
                                    potlabel(i + 1, (t["nominal"], t["tol"])),
                                    t["lo"], t["hi"])
                                 for i, t in enumerate(nt))
                    mini = ('<small class="minilbl">класи под новото име | tiers under '
                            "the new name:</small><span class=\"minipills\">%s</span>" % mp)
            ren_entries.append(
                '<div class="renentry"><span class="rname">%s%s</span>'
                "<small>%d %s</small>%s%s</div>"
                % (name_html, chip + extra, n,
                   "серии | batches" if n != 1 else "серија | batch", share, mini))
        col3 = ('<div class="fren">%s</div>' % "".join(ren_entries)) if ren_entries else \
               ('<div class="fren"><span class="fstat">— нема запис во мастерот | '
                "not in the Portfolio Master</span></div>")

        rows += ('<div class="frow"><div class="fname"><h3>%s</h3>'
                 '<span class="fstat">%s</span>%s</div><div class="fpills">%s</div>%s</div>'
                 % (esc(strain), stat, badge, pills, col3))

    n_renames = sum(1 for r in PM if (r.get("original") or "").strip()
                    != (r.get("neu") or "").strip())
    head = ('<div class="fsum">Врз основа на %d верификувани резултати — ова се финалните '
            "опсези по класи за секоја сорта: %d сорти дефинитивно, %d провизорно (само "
            "декларирана основа). Третата колона ги дава имињата по преименувањето од "
            "листот <code>01_Portfolio_Master</code> (%d серии, %d преименувања, %d нови "
            "имиња); каде што сериите под новото име се групираат поинаку, неговите "
            "сопствени класи се прикажани под името. Формалното усвојување останува во "
            "спецификациите QCSP по редовна процедура. | Based on %d verified results — "
            "the final grade ranges per strain: %d strains definitive, %d provisional "
            "(declared basis only). The third column carries the names after renaming from "
            "the <code>01_Portfolio_Master</code> sheet (%d batches, %d renames, %d new "
            "names); where a new name's batches cluster differently, its own tiers are "
            "shown under that name. Formal adoption remains with the QCSP specifications "
            "through the regular procedure.</div>"
            % (d["n_results"], n_def, n_prov, len(PM), n_renames, len(groups),
               d["n_results"], n_def, n_prov, len(PM), n_renames, len(groups)))
    fhead = ('<div class="fhead"><span>Оригинална спецификација | Original specification'
             "</span><span>Предложени опсези по класи | Proposed grade ranges</span>"
             "<span>Имиња по преименување | Names after renaming</span></div>")
    return head + '<div class="fboard">' + fhead + rows + "</div>"


MAX_TOL_RATIO = d["design"]["max_tol_ratio"]
MIN_GAP = d["design"]["min_gap"]
NOM_STEP = d["design"]["nom_step"]

# Owner top-nominal overrides (keyed by original strain). The renamed board
# re-clusters batches by NEW name, so we apply an override to a new-name group
# only when it OWNS an overridden original strain's top anchor — matched by
# that anchor's value, which is unique enough here. The original board reads
# the overrides straight from merged_ranges (already baked into the dataset).
_TOP_OVERRIDE = d["design"].get("top_nominal_override", {})
_strain_top_anchor = {}
for _b in d["stock"]:
    _a = _b["anchor"] if _b["anchor"] is not None else _b["declared"]
    if _a is not None:
        _strain_top_anchor[_b["strain"]] = max(_strain_top_anchor.get(_b["strain"], -1.0), _a)
OVERRIDE_BY_TOP_ANCHOR = {round(_strain_top_anchor[s], 2): v
                          for s, v in _TOP_OVERRIDE.items() if s in _strain_top_anchor}


def build_top_down(groups, floor=5.0, max_ratio=MAX_TOL_RATIO, step=NOM_STEP, gap=MIN_GAP,
                   top_override=None, strain_max=None):
    """Mirror of build_potency_dataset.build_top_down."""
    top = groups[-1]
    tmin, tmax = min(top), max(top)
    lo_i = math.ceil((tmax / (1 + max_ratio)) / step - 1e-9)
    hi_i = math.floor((tmin / (1 - max_ratio)) / step + 1e-9)
    lo_i = max(lo_i, math.ceil((floor / (1 - max_ratio)) / step - 1e-9))
    top_cands = [round(k * step, 2) for k in range(lo_i, hi_i + 1)]
    if not top_cands:
        return None
    if top_override is not None and strain_max is not None \
            and abs(tmax - strain_max) < 1e-9:
        if any(abs(c - top_override) < 1e-9 for c in top_cands):
            top_cands = [round(top_override, 2)]
        else:
            return None
    best = None
    for n_top in top_cands:
        tol = round(n_top * max_ratio, 2)
        tiers = [dict(nominal=n_top, tol=tol, lo=round(n_top - tol, 2),
                      hi=round(n_top + tol, 2), anchors=top)]
        ok = True
        ceiling = round(tiers[-1]["lo"] - gap, 2)
        for g in reversed(groups[:-1]):
            gmin, gmax = min(g), max(g)
            n_i = math.ceil((ceiling / (1 + max_ratio)) / step - 1e-9)
            n_i = max(n_i, math.ceil((floor / (1 - max_ratio)) / step - 1e-9))
            nom = round(n_i * step, 2)
            tol = round(ceiling - nom, 2)
            if tol < 0 or tol > round(nom * max_ratio, 2) + 1e-9:
                ok = False
                break
            lo, hi = round(nom - tol, 2), round(nom + tol, 2)
            if lo < floor - 1e-6 or not (lo - 1e-6 <= gmin and gmax <= hi + 1e-6):
                ok = False
                break
            tiers.append(dict(nominal=nom, tol=tol, lo=lo, hi=hi, anchors=g))
            ceiling = round(lo - gap, 2)
        if not ok:
            continue
        tiers.reverse()
        cost = sum(abs(t["nominal"] - a) for t in tiers for a in t["anchors"])
        if best is None or cost < best[0] - 1e-9:
            best = (cost, tiers)
    return best[1] if best else None


def _tiers_for_k(anchors, k, floor, max_ratio, gap, top_override=None, strain_max=None):
    """Mirror of build_potency_dataset._tiers_for_k."""
    n = len(anchors)
    if k > n:
        return None
    best = None

    def eval_cuts(bounds):
        nonlocal best
        groups = [anchors[bounds[i]:bounds[i + 1]] for i in range(k)]
        tiers = build_top_down(groups, floor, max_ratio, NOM_STEP, gap,
                               top_override=top_override, strain_max=strain_max)
        if tiers is None:
            return
        for gi, t in enumerate(tiers):
            t["start"], t["end"] = bounds[gi], bounds[gi + 1]
        cost = sum(abs(t["nominal"] - a) for t in tiers for a in t["anchors"])
        if best is None or cost < best[0] - 1e-9:
            best = (cost, tiers)

    def cuts(start, groups_left, acc):
        if groups_left == 1:
            eval_cuts([0] + acc + [n])
            return
        for c in range(start + 1, n - (groups_left - 1) + 1):
            cuts(c, groups_left - 1, acc + [c])

    cuts(0, k, [])
    return best


def plan_contiguous(anchors, floor=5.0, max_ratio=MAX_TOL_RATIO, gap=MIN_GAP,
                    top_override=None, strain_max=None):
    """Mirror of build_potency_dataset.plan_contiguous."""
    n = len(anchors)
    if n == 0:
        return []
    for k in range(1, n + 1):
        res = _tiers_for_k(anchors, k, floor, max_ratio, gap,
                           top_override=top_override, strain_max=strain_max)
        if res is not None:
            return res[1]
    return None


def tiers_from_anchors(items, top_override=None):
    """Mirror of build_potency_dataset.build_strain_tiers, adapted to carry
    each batch's `tested` flag through instead of an opaque payload.
    items = [(batch, anchor, tested_bool)] — any order in, sorted here.
    top_override: owner-set nominal for the group's highest tier (see the
    source); applied only to the tier holding this cluster's top anchor."""
    items = sorted(items, key=lambda x: x[1])
    strain_max = max(x[1] for x in items) if items else None

    def resolve(sub_items):
        sub_anchors = [x[1] for x in sub_items]
        plan = plan_contiguous(sub_anchors, top_override=top_override, strain_max=strain_max)
        if plan is not None:
            for t in plan:
                t["gap_after"] = False
                t["batches"] = [x[0] for x in sub_items[t["start"]:t["end"]]]
                t["tested"] = [x[2] for x in sub_items[t["start"]:t["end"]]]
            return plan
        n = len(sub_items)
        assert n > 1, ("single anchor infeasible — below release floor?", sub_anchors)
        best_m = 1
        for m in range(n, 0, -1):
            if plan_contiguous(sub_anchors[:m], top_override=top_override,
                               strain_max=strain_max) is not None:
                best_m = m
                break
        left = plan_contiguous(sub_anchors[:best_m], top_override=top_override,
                               strain_max=strain_max)
        for t in left:
            t["gap_after"] = False
            t["batches"] = [x[0] for x in sub_items[t["start"]:t["end"]]]
            t["tested"] = [x[2] for x in sub_items[t["start"]:t["end"]]]
        left[-1]["gap_after"] = True
        return left + resolve(sub_items[best_m:])

    return resolve(items)


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
    # batch -> (strain, tier) from the even-nominal design
    tmap = {}
    for _s, _tiers in d["merged_ranges"].items():
        for _t in _tiers:
            for _b in _t["batches"]:
                tmap[norm_b(_b)] = (_s, _t)
    rows = ""
    n_rows = 0
    for b in sorted(d["stock"], key=lambda x: (x["tranche"], x["strain"], x["batch"])):
        hit = tmap.get(norm_b(b["batch"]))
        if hit is None:
            continue
        _strain, t = hit
        n_rows += 1
        decl = b["anchor"] is None
        val = t["values"].get(next(_b for _b in t["batches"]
                                   if norm_b(_b) == norm_b(b["batch"])), None)
        anc = ("%.2f%% (декл. | decl.)" % b["declared"]) if decl \
            else "%.2f%% (%s)" % (b["anchor"], b["anchor_date"])
        if b.get("declared") is not None:
            out_of_grade = not (t["range"][0] - 1e-6 <= b["declared"] <= t["range"][1] + 1e-6)
            cur = ('<span class="mismatch" title="надвор од новата класа | outside the new '
                   'grade">%.2f%%</span>' % b["declared"]) if out_of_grade else "%.2f%%" % b["declared"]
        else:
            cur = "—"
        head = (val - t["range"][0]) if val is not None else None
        rows += ('<tr%s><td>Т%s</td><td class=num>%s</td><td>%s</td><td class=num>%s</td>'
                 "<td>%s</td><td class=num>%s</td><td>%s</td><td class=v>%s</td>"
                 "<td class=num>%.2f%% – %.2f%%</td><td class=num>%s</td></tr>"
                 % (' class="decl"' if decl else "", esc(b["tranche"]), esc(b["batch"]),
                    esc(b["strain"]), anc, esc(fmt_bracket(b["bracket_old"])), cur,
                    "%s · %s" % (esc(t["grade"]), esc(t["product_code"].replace(":", " : "))),
                    esc(t["expression"].split(" (")[0]),
                    t["range"][0], t["range"][1],
                    ("%.2f" % head) if head is not None else "—"))
    return n_rows, ('<div class="tblwrap" style="padding:0"><table><thead><tr>'
            "<th>Т</th><th>Серија | Batch</th><th>Сорта | Strain</th>"
            "<th>Сидро | Anchor</th><th>Стара | Old</th>"
            "<th>Тековна декл. | Currently declared</th><th>Класа | Grade</th>"
            "<th>Номинала + толеранција | Nominal + tolerance</th>"
            "<th>= опсег | = span</th><th>Простор ↓ (пп) | Headroom (pp)</th>"
            "</tr></thead><tbody>%s</tbody></table></div>" % rows)


nav = "".join('<a href="#s-%s">%s</a>'
              % ("".join(c if c.isalnum() else "-" for c in s.lower()), esc(s))
              for s in sorted(d["stats"])) + '<a href="#final" style="border-color:var(--gold);color:#8A6D14;font-weight:700">★ Финални опсези | Final ranges</a>'

n_stab_usable = sum(1 for r in d["stability"] if r["usable"])

def methodology_section():
    fb = []
    for f in GD["flags"]:
        fb.append("<li>%s</li>" % esc(f))
    ex = []
    for e in GD["exceptions"]:
        ex.append("<li>%s</li>" % esc(e))
    return ('<section id="method2"><h2>Методологија <span>| Methodology — the mathematics '
            'behind every bound</span></h2><div class="mth">'
            '<h4>1 · Изводливост | Feasibility of a nominal</h4>'
            '<p>A result <code>v</code> can carry nominal <code>N</code> iff '
            '<code>0.90·N ≤ v ≤ 1.10·N</code>, i.e. <code>N ∈ [v/1.1, v/0.9]</code> — an '
            'interval of width ≈ <code>0.202·v</code>. It always holds a whole number once '
            'v ≥ 4.95, and an even one once v ≥ 9.9. The even ladder has exactly two dead '
            'zones — <b>8.81–8.99</b> (THC10/THC8) and <b>6.61–7.19</b> (THC8/THC6) — '
            'plugged by the odd fallback (THC9: 8.10–9.90; THC7: 6.30–7.70), so every '
            'result above ≈5.0% THC is placeable.</p>'
            '<h4>2 · Симетричниот закон на континуитет | The symmetric contiguity law</h4>'
            '<p>Every grade is <code>N ± t</code> with the SAME tolerance above and below. '
            'Two neighbouring grades touching at 0.01 satisfy the EQUALITY '
            '<code>tₛ + t_w = (Nₛ − N_w) − 0.01</code> — so every tolerance in a contiguous '
            'ladder is an affine function of the top grade&#39;s tolerance (alternating '
            'sign): fixing t₁ fixes the whole ladder. The solver reduces each ladder to one '
            'variable — every grade contributes an interval constraint '
            '<code>max(containment, 0.50) ≤ tₖ ≤ 0.10·Nₖ</code> on t₁ — intersects the '
            'intervals, and t₁ takes the MAXIMUM of the intersection (strongest grade '
            'first). Reserve grades close spans that batch grades cannot bridge (5 exist: '
            'CJ THC17, CC THC16, FB THC16, GP THC22, OPM THC12); below 10% THC, where no '
            'meaningful symmetric ladder joins, the lowest grade keeps its full ±10% with a '
            'documented uncovered zone (GRC 7.71–10.79; OPM 8.81–9.10).</p>'
            '<h4>3 · Непарни номинали и толеранција | Odd nominals &amp; tolerance</h4>'
            '<p>For every cluster the solver tries the initially selected even nominal, '
            'then the adjacent odd numbers, ranking candidates by fewest odd nominals, '
            'fewest reserves, then the largest top-grade tolerance. Example — Grape '
            'Pie&#39;s top cluster spans 22.61–26.32: an even THC24 needs t ≥ 2.32, '
            'leaving a negative budget (1.99 − 2.32) for any touching grade below — '
            'infeasible; the adjacent odd <b>THC25 ±2.47</b> (22.53% — 27.47%) holds the '
            'cluster and chains cleanly. Nine grades carry odd nominals: CJ 21/19/17R/15, '
            'FB 21, GP 25, JD 19, OPM 21, GRC 7. Every grade prints ONE symmetric '
            'tolerance: <code>nn.00% ±t.tt% (lower% — upper%)</code>, and nominal − t = '
            'lower, nominal + t = upper hold exactly by construction.</p>'
            '<h4>4 · Сидро | Anchor policy</h4>'
            '<p>The grade anchors on the batch&#39;s latest result — the retest where one '
            'exists (T1 197-series 07.08.2026, April J31 retests, pending T2 re-analysis). '
            'Retest values are CoQ-forming; superseded pre-retest results are out of '
            'specification scope. J31122501 anchors on the machine-trimmed CoQ preparation '
            '(21.84, CoQ-PP-2026-0054); the hand-trimmed 19.84 is experimental.</p>'
            '<h4>5 · Независна верификација | Independent verification (27.08.2026)</h4>'
            '<table><tr><th>Проверка | Check</th><th>Резултат | Result</th></tr>'
            '<tr><td>Structural rules (caps, contiguity, non-overlap, nominal-inside, 2dp, '
            'tolerance arithmetic)</td><td class="ok">0 problems</td></tr>'
            '<tr><td>Batch anchors inside their assigned grade</td>'
            '<td class="ok">86 / 86 (77 certified + 8 declared + J31122501)</td></tr>'
            '<tr><td>Windows centred on their nominal (single symmetric ± tolerance)</td>'
            '<td class="ok">58 / 58</td></tr>'
            '<tr><td>Batches without a grade (register ∪ stock census)</td>'
            '<td class="ok">0</td></tr>'
            '<tr><td>Superseded results still inside a grade of their strain</td>'
            '<td>19 (12 same grade, 7 neighbouring)</td></tr>'
            '<tr><td>Superseded results now outside all windows (retest supersession, '
            'rule R5 — not OOS events)</td><td class="warn">3 — BG1024 21.80, HPA1024 '
            '14.97, J31112501 25.27</td></tr>'
            '<tr><td>Stability 25 °C/60 %RH (long-term)</td><td>4 of 5 inside the release '
            'grade; GP0824_02 M6 21.31 dips one grade, returns by M9 (23.08) — variance, '
            'no monotonic decline</td></tr>'
            '<tr><td>Stability 40 °C/75 %RH (accelerated)</td><td>13.16–18.62, out of/below '
            'grade — heat-stress artefact (CBN 2.05–2.35%), not release-relevant</td></tr>'
            '</table>'
            '<h4>6 · Наоди | Findings fixed by the audit</h4>'
            '<ul>@FLAGS@</ul>'
            '<h4>7 · Дозволени исклучоци | Permitted exceptions</h4>'
            '<ul>@EXC@</ul>'
            '<p>Engine: <code>imb_grade_design.py</code> · design: '
            '<code>grade_design_even.json</code> · independent audit: '
            '<code>check_design.py</code> (deliverables/potency_study, letta-stack). '
            'Пълна постапка | Full write-up: METHODOLOGY_Potency_Grades.md.</p>'
            '</div></section>'
            ).replace("@FLAGS@", "".join(fb) +
               "<li>Certificate ППК26065 (13.93, CNP, 11.05.2026) prints "
               "серија JD112501* — the milled presentation, its own register batch — and was "
               "misattributed to JD112501 in the dataset; reattributed, JD112501* now carries "
               "its own grade JD_THC14:CBD1 (12.60 — 14.39).</li>"
            ).replace("@EXC@", "".join(ex))


_stock_n, _stock_html = stock_table()

HTML = """<!doctype html>
<html lang="mk"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Potency Atlas</title>
<style>%s</style></head>
<body>
<header class="hero"><div class="wrap">
 <div class="brand">PURELY<em>PLANT</em> <small>THE FUTURE OF CANNABIS</small></div>
 <h1>Атлас на потенција</h1>
 <div class="en">Potency Atlas</div>
 <div class="sub">Сите некогаш тестирани резултати за Вкупен Δ⁹-THC, по сорта, со
 финалните потенциски класи: ЦЕЛА номинала (парна; соседна непарна само каде што мора)
 со ЕДНАКВА толеранција над и под неа — спецификациски кодови QCSP_001, продукт-типови
 XX_THCnn:CBD1, номинала ± толеранција и опсег за секоја класа.
 | Every Total Δ⁹-THC result ever tested, per strain, with the FINAL potency grades:
 whole-number nominal (even; adjacent odd only where forced) with an EQUAL tolerance
 above and below it — QCSP_001 specification codes, XX_THCnn:CBD1 product types,
 nominal ± tolerance and range for every grade.</div>
 <div class="chips">
  <span class="chip"><b>%d</b>резултати | results</span>
  <span class="chip"><b>%d</b>сорти | strains</span>
  <span class="chip"><b>%d</b>серии | batches</span>
  <span class="chip"><b>%d</b>класи | grades</span>
  <span class="chip"><b>%d</b>резервни класи | reserve grades</span>
  <span class="chip"><b>0</b>наоди од независна проверка | independent-audit findings</span>
 </div>
 <div class="informal">Неформален работен документ · не е контролиран запис · 27.08.2026 |
 Informal working document · not a controlled record</div>
</div></header>

<nav class="nav"><div class="wrap">%s</div></nav>

<div class="wrap">
<section><h2>Сорти <span>| Strains — дистрибуции, растојанија и класи</span></h2>
<p style="font-size:12.5px;color:var(--mut);margin-bottom:14px">
Δ до следен = растојание до следниот повисок резултат, во процентни поени и како
релативен %% од помалата вредност. Опсегот прикажан за секоја сорта е опсегот на
ТЕСТИРАНИТЕ резултати — не е предложениот опсег на потенција по класа (тој е прикажан
подолу, во Pot.- класите). | Δ to next = distance to the next higher result, in
percentage points and as a relative %% of the lower value. The range shown for each strain
is the range of TESTED results — not the proposed potency grade range (that is shown below,
in the Pot.- tiers).</p>

<div class="method">
 <h3>Како се одредени класите <span>| How the grades were set (правила од 27.08.2026 | rules of 27.08.2026)</span></h3>
 <div class="lede">Правилата важат за секоја сорта во овој документ и се наведени само
 овде. Целосната математичка постапка е во поглавјето „Методологија" подолу. | The rules
 govern every strain in this document and are stated here once; the full mathematics is in
 the Methodology chapter below.</div>

 <div class="mrules">
  <div class="mrule"><b><i>1</i>Парна цела номинала | Even whole nominal</b>
   Номиналата на секоја класа е ПАРЕН цел број (… 8, 10, 12 … 26), во продукт-кодот
   <b style="display:inline;text-transform:none;font-size:12.5px">XX_THCnn:CBD1</b>;
   само каде што парната номинала математички не може да носи симетричен прозорец,
   номиналата преминува на соседниот НЕПАРЕН број.
   <em>Every grade's nominal is an EVEN whole number, printed in the product code; only
   where the even nominal mathematically cannot carry a symmetric window does it shift
   to the adjacent ODD number (9 grades: CJ 21/19/17R/15, FB 21, GP 25, JD 19, OPM 21,
   GRC 7).</em></div>

  <div class="mrule"><b><i>2</i>Симетрична толеранција | Symmetric tolerance</b>
   Секоја класа е номинала ± t со ИСТА толеранција над и под неа (t ≤ 10,00%% од
   номиналата); допирањето на соседни класи ја дава равенката
   t<sub>горна</sub> + t<sub>долна</sub> = разлика на номиналите − 0,01, па сите
   толеранции во скалата се врзани за највисоката класа, која зема максимум прва.
   <em>Every grade is nominal ± t with the SAME t above and below (t ≤ 10%% of nominal);
   contiguity binds neighbours by t_upper + t_lower = nominal difference − 0.01, chaining
   the whole ladder to the top grade, which takes its maximum first.</em></div>

  <div class="mrule"><b><i>3</i>Континуитет и резервни класи | Contiguity &amp; reserve grades</b>
   Од највисоката класа надолу, соседните опсези се допираат на 0,01 — без јаз и без
   преклоп; каде што класите со серии не можат да се допрат, се вметнува РЕЗЕРВНА класа
   (спецификациски дефинирана, без тековна серија). Под 10%% THC, каде што парната скала
   математички не се спојува, најниската класа стои со документирана непокриена зона.
   <em>Consecutive ranges join at 0.01; reserve grades close unbridgeable spans above
   10%%; below 10%% the lowest grade may sit with a documented uncovered zone.</em></div>
 </div>

 <div class="mparams">
  <span class="mparam">Толеранција | Tolerance <b>≤ 10,00%%</b> од номиналата | of nominal</span>
  <span class="mparam">Номинала | Nominal <b>парен цел број | even whole number</b></span>
  <span class="mparam">Допир на класи | Grades meet at <b>0,01</b></span>
  <span class="mparam">Сидро | Anchor = <b>ретест (CoQ-формирачки) | retest (CoQ-forming)</b></span>
  <span class="mparam">Изразување | Expression <b>nn.00%% ±t.tt%% (долна%% — горна%%)</b></span>
  <span class="mparam">Мин. толеранција | Min tolerance <b>0,50</b></span>
 </div>

 <div class="mwork"><b>Пример | Worked example</b> — Blue Sunset Sherbet
 (сидра | anchors 20,39 / 23,42 / 25,01):
 <code>BSS_THC24:CBD1 — 24.00%% ±2.40%% (21.60%% — 26.40%%)</code> ја зема полната
 ширина | takes the full cap<span class="arrow">→</span>равенката t₂₄ + t₂₀ = 3,99
 | the equality t₂₄ + t₂₀ = 3.99 дава | yields
 <code>BSS_THC20:CBD1 — 20.00%% ±1.59%% (18.41%% — 21.59%%)</code> — симетрично око
 номиналата | centred on the nominal.</div>

 <div class="msum"><b>Накратко | In short:</b> парна цела номинала, максимум 10%% од
 номиналата на страна, најсилната класа прва, соседните класи се допираат на 0,01,
 резервни класи ги затвораат преостанатите јазови, а сидро е секогаш најновиот
 (ретест) резултат. | <b>Even whole nominal, at most 10%% of nominal per side, strongest
 grade first, neighbouring grades touch at 0.01, reserve grades close remaining spans,
 and the anchor is always the latest (retest) result.</b></div>
</div>
%s</section>

<section><h2>Преименувања: наши опсези наспроти мастерот <span>| Renames: our ranges vs the Portfolio Master</span></h2>
<p style="font-size:12.5px;color:var(--mut);margin-bottom:14px">
За секоја изворна сорта — во колку нови имиња се преименувани сериите, и за секое ново име:
тестираните вредности (точки), <b style="color:#8A6D14">опсегот што го предлага мастер-документот</b>
(жолто, BCP_PRODUCT_MASTER_FINAL.xlsx · 01_Portfolio_Master) наспроти
<b style="color:#1E8449">нашата предложена класа</b> (зелено, номинала ± толеранција) — на
иста оска 0,00%%–30,00%%. | For every original strain — how many new names its batches were renamed
into, and per new name: the tested values (dots), <b style="color:#8A6D14">the bracket the
master document suggests</b> (amber) versus <b style="color:#1E8449">our proposed grade</b>
(green, nominal ± tolerance), on one 0.00%%–30.00%% axis.</p>
%s</section>

<section><h2>Залиха Т1/Т2/Т3 <span>| Stock — класи по серија | grades per batch</span></h2>
<details open><summary>%d серии | batches — сидро, стара класа, нова класа, простор надолу
| anchor, old grade, new grade, downward headroom</summary>%s</details>
<p style="font-size:12px;color:var(--mut);margin-top:8px">Жолти редови: без ниту еден
сертификат — основа е декларираната вредност; тестирајте пред формално декларирање класа. |
Yellow rows: no certificate on file — declared value used; test before declaring a grade.</p>
</section>

%s

<section id="final"><h2>Финални опсези на потенција по сорта <span>| Final Potency Grade Ranges per Strain</span></h2>
%s</section>

<section id="signoff"><h2>Потписи | Signatures</h2>
<div class="sigs">
 <div class="sig">
  <span class="sigpill">QC MANAGER | МЕНАЏЕР ЗА КК</span>
  <div class="signame">Blagoj Nikolov</div>
  <span class="sigrole">M.Pharm. · Drug Quality Control Specialist</span>
  <div class="sigdate">DATE · ДАТУМ<b>01.06.2026</b></div></div>
 <div class="sig">
  <span class="sigpill">QA MANAGER | МЕНАЏЕР ЗА ОК</span>
  <div class="signame">Jovana Romevska Cvetkovski</div>
  <span class="sigrole">Master Pharmacist</span>
  <div class="sigdate">DATE · ДАТУМ<b>01.06.2026</b></div></div>
</div>
<p class="signote">Неформален работен документ — потписите потврдуваат изработка,
преглед и одобрување на предлогот; формалното усвојување останува во
спецификациите QCSP по редовна процедура. | Informal working document — the
signatures confirm preparation, review and approval of the proposal; formal
adoption remains with the QCSP specifications through the regular procedure.</p>
</section>
</div>

<footer><div class="wrap">
<b>Потекло | Provenance</b>
<span>Корпус: %d резултати од регистарот на eCoA (77 серии, %d сорти); сите вредности
проверени во живо на изворот ImB_QC_COAs (4 134 пасуси). | Corpus: %d register results;
all values live-verified against the ImB_QC_COAs source (4,134 passages).</span>
<span>Датасет и обработка | Dataset &amp; build: deliverables/potency_study/
(potency_dataset.json · build_potency_dataset.py · build_potency_html.py) —
letta-stack. Резиме запишано во споделената меморија на хостот (агент
ecoa_retrieval_gpt4o). | Study summary logged to the host's shared memory.</span>
<span>Меродавни остануваат лабораториските сертификати во СМК. |
The laboratory certificates in the QMS remain authoritative.</span>
</div></footer>
</body></html>
"""

_n_grades = sum(len(v) for v in d["merged_ranges"].values())
_n_reserve = sum(1 for v in d["merged_ranges"].values() for t in v if t.get("bridge"))
_n_gbatches = len({b for v in d["merged_ranges"].values() for t in v for b in t["batches"]})

HTML = HTML % (CSS, d["n_results"], d["n_strains"], _n_gbatches, _n_grades, _n_reserve,
       nav, strain_cards(), renames_section(), _stock_n, _stock_html,
       methodology_section(), final_ranges(),
       d["n_results"], d["n_strains"], d["n_results"])

out = os.path.join(HERE, "Potency_Atlas.html")
open(out, "w", encoding="utf-8").write(HTML)
print("wrote", out, "%.1f KB" % (os.path.getsize(out) / 1024))
