#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FILM 2 — "Патот на еден сертификат"

A completely different engine and visual language from film 1: no browser,
no DOM.  Every frame is composed procedurally with Pillow as a technical
drafting sheet on warm paper, where the system is *drawn* line by line.
Rendered at 2x and box-reduced for clean anti-aliasing, then piped as MJPEG
straight into ffmpeg alongside the Macedonian narration.

  python3 film2.py stills 3 14 26 40 50 62 76 88
  python3 film2.py render
"""
import json, math, os, subprocess, sys, io
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

DIR = os.path.dirname(os.path.abspath(__file__))
TL = json.load(open(os.path.join(DIR, "film2_timeline.json"), encoding="utf-8"))
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
FPS, W, H, S = 24, 1920, 1080, 2          # S = supersample factor

# ── drafting-sheet palette ────────────────────────────────────────────
PAPER   = (238, 235, 226)
PAPER_D = (228, 224, 212)
GRID    = (214, 209, 194)
GRID_H  = (203, 197, 179)
INK     = (26, 38, 51)
GRAPH   = (95, 112, 129)
FAINT   = (150, 162, 174)
RED     = (183, 62, 43)
BLUE    = (38, 98, 150)
GREEN   = (46, 110, 78)
AMBER   = (176, 122, 24)

F = os.path.join(DIR, "fonts")
def font(name, size):
    return ImageFont.truetype(os.path.join(F, name), int(size * S))

# PT Sans (Cyrillic-native humanist) + IBM Plex Mono (technical annotation)
FT = {}
def ft(key, name, size):
    k = (key, size)
    if k not in FT:
        FT[k] = font(name, size)
    return FT[k]
def sans(sz):  return ft("s",  "PTSans-Regular.ttf", sz)
def sansb(sz): return ft("sb", "PTSans-Bold.ttf",    sz)
def mono(sz):  return ft("m",  "IBMPlexMono-Regular.ttf",  sz)
def monob(sz): return ft("mb", "IBMPlexMono-SemiBold.ttf", sz)

# ── timing helpers ────────────────────────────────────────────────────
def cl(x, a=0.0, b=1.0): return max(a, min(b, x))
def P(t, at, dur): return cl((t - at) / dur)
def eo(x):  return 1 - (1 - x) ** 3
def eio(x): return 4*x*x*x if x < .5 else 1 - (-2*x + 2) ** 3 / 2
def A(c, a): return (c[0], c[1], c[2], int(255 * cl(a)))

# ── drawing primitives (design-space coords, scaled on the way in) ────
class Sheet:
    def __init__(self, img):
        self.d = ImageDraw.Draw(img, "RGBA")
    def line(self, p1, p2, color, w=2, a=1.0, prog=1.0):
        """A line that draws itself from p1 toward p2."""
        if prog <= 0 or a <= 0: return
        x1, y1 = p1; x2, y2 = p2
        x2 = x1 + (x2 - x1) * prog; y2 = y1 + (y2 - y1) * prog
        self.d.line([x1*S, y1*S, x2*S, y2*S], fill=A(color, a), width=int(w*S))
    def rect(self, box, color, w=2, a=1.0, prog=1.0, fill=None):
        """A rectangle whose outline is traced clockwise from the top-left."""
        x1, y1, x2, y2 = box
        if fill is not None and a > 0:
            self.d.rectangle([x1*S, y1*S, x2*S, y2*S], fill=A(fill, a))
        if prog <= 0 or a <= 0: return
        segs = [((x1,y1),(x2,y1)), ((x2,y1),(x2,y2)), ((x2,y2),(x1,y2)), ((x1,y2),(x1,y1))]
        lens = [abs(x2-x1), abs(y2-y1), abs(x2-x1), abs(y2-y1)]
        tot = sum(lens); run = tot * prog
        for (p1, p2), L in zip(segs, lens):
            if run <= 0: break
            self.line(p1, p2, color, w, a, min(1.0, run / L) if L else 1)
            run -= L
    def text(self, xy, s, f, color, a=1.0, anchor="la", spacing=4):
        if a <= 0: return
        self.d.multiline_text((xy[0]*S, xy[1]*S), s, font=f, fill=A(color, a),
                              anchor=anchor if "\n" not in s else None,
                              align="left", spacing=spacing*S)
    def circle(self, c, r, color, w=2, a=1.0, fill=None):
        if a <= 0: return
        b = [(c[0]-r)*S, (c[1]-r)*S, (c[0]+r)*S, (c[1]+r)*S]
        self.d.ellipse(b, outline=A(color, a), width=int(w*S),
                       fill=A(fill, a) if fill else None)
    def dot(self, c, r, color, a=1.0):
        if a <= 0: return
        self.d.ellipse([(c[0]-r)*S, (c[1]-r)*S, (c[0]+r)*S, (c[1]+r)*S], fill=A(color, a))
    def arrow(self, p1, p2, color, w=2, a=1.0, prog=1.0, head=11):
        if prog <= 0 or a <= 0: return
        self.line(p1, p2, color, w, a, prog)
        if prog > .82:
            ang = math.atan2(p2[1]-p1[1], p2[0]-p1[0])
            ha = (a - 0) * cl((prog - .82) / .18)
            for s_ in (2.6, -2.6):
                self.line(p2, (p2[0]+head*math.cos(ang+s_), p2[1]+head*math.sin(ang+s_)),
                          color, w, ha)
    def dashed(self, p1, p2, color, w=2, a=1.0, dash=10, gap=8, prog=1.0):
        if prog <= 0 or a <= 0: return
        x1, y1 = p1; x2, y2 = p2
        L = math.hypot(x2-x1, y2-y1) * prog
        if L <= 0: return
        ux, uy = (x2-x1)/max(1e-6, math.hypot(x2-x1, y2-y1)), (y2-y1)/max(1e-6, math.hypot(x2-x1, y2-y1))
        p = 0.0
        while p < L:
            q = min(p + dash, L)
            self.d.line([(x1+ux*p)*S, (y1+uy*p)*S, (x1+ux*q)*S, (y1+uy*q)*S],
                        fill=A(color, a), width=int(w*S))
            p = q + gap

# ── static paper background, built once ───────────────────────────────
def build_paper():
    img = Image.new("RGB", (W*S, H*S), PAPER)
    d = ImageDraw.Draw(img, "RGBA")
    for x in range(0, W+1, 40):                       # fine grid
        d.line([x*S, 0, x*S, H*S], fill=A(GRID, .55), width=S)
    for y in range(0, H+1, 40):
        d.line([0, y*S, W*S, y*S], fill=A(GRID, .55), width=S)
    for x in range(0, W+1, 200):                      # major grid
        d.line([x*S, 0, x*S, H*S], fill=A(GRID_H, .75), width=S)
    for y in range(0, H+1, 200):
        d.line([0, y*S, W*S, y*S], fill=A(GRID_H, .75), width=S)
    # drafting border + title block
    d.rectangle([56*S, 56*S, (W-56)*S, (H-56)*S], outline=A(GRAPH, .40), width=int(1.5*S))
    d.rectangle([56*S, (H-136)*S, (W-56)*S, (H-56)*S], outline=A(GRAPH, .40), width=int(1.5*S))
    d.line([(W-560)*S, (H-136)*S, (W-560)*S, (H-56)*S], fill=A(GRAPH, .40), width=int(1.5*S))
    d.line([(W-300)*S, (H-136)*S, (W-300)*S, (H-56)*S], fill=A(GRAPH, .40), width=int(1.5*S))
    d.text((84*S, (H-108)*S), "PURELY PLANT GMBH  ·  ОДДЕЛЕНИЕ ЗА КОНТРОЛА НА КВАЛИТЕТ",
           font=mono(19), fill=A(GRAPH, .95))
    d.text((84*S, (H-82)*S), "ПАТОТ НА ЕДЕН СЕРТИФИКАТ ЗА АНАЛИЗА  —  RAGFLOW · KVM4",
           font=mono(15), fill=A(FAINT, 1))
    d.text(((W-536)*S, (H-108)*S), "РАЗМЕР  1:1", font=mono(15), fill=A(FAINT, 1))
    d.text(((W-536)*S, (H-82)*S),  "АВГУСТ 2026", font=mono(15), fill=A(FAINT, 1))
    return img

PAPER_IMG = build_paper()

# ── shared furniture ──────────────────────────────────────────────────
def header(sh, t, num, label, title, tin=0.0):
    a = eo(P(t, tin, .7))
    sh.text((92, 92), f"{num:02d}", monob(30), RED, a)
    sh.line((92, 132), (92+52, 132), RED, 3, a, eo(P(t, tin+.15, .5)))
    sh.text((160, 96), label.upper(), mono(19), GRAPH, a)
    sh.text((92, 158), title, sansb(62), INK, eo(P(t, tin+.2, .8)))
    sh.line((92, 240), (92+560, 240), GRAPH, 1.5, a*.5, eo(P(t, tin+.35, .8)))

def doc_page(sh, x, y, w, h, a=1.0, prog=1.0, lines=9, stamp=True,
             tint=None, label=None, lc=INK):
    """A certificate drawn as a technical illustration."""
    sh.rect((x, y, x+w, y+h), lc, 2, a, prog, fill=tint or PAPER_D)
    if prog < .98: return
    inner = eo(P(prog, .0, 1))
    for i in range(lines):
        yy = y + 44 + i*((h-84)/max(1, lines))
        ww = w - 56 if i % 3 else w * .55
        sh.line((x+28, yy), (x+28+ww, yy), FAINT, 2, a*.85*inner)
    if stamp:
        sh.circle((x+w-58, y+h-56), 30, RED, 2, a*.75)
        sh.text((x+w-58, y+h-56), "QC", mono(17), RED, a*.75, anchor="mm")
    if label:
        sh.text((x+14, y-30), label, mono(18), lc, a)

# ═══════════════════════════════════════════════════════════════════════
#  SCENES
# ═══════════════════════════════════════════════════════════════════════
def sc_paper(sh, t, d):
    header(sh, t, 1, "Појдовна точка", "Еден документ")
    px, py, pw, ph = 720, 330, 470, 600
    sh.rect((px, py, px+pw, py+ph), INK, 2, 1, eo(P(t, .5, 1.2)), fill=PAPER_D)
    if P(t, 1.6, .01):
        a = eo(P(t, 1.6, .9))
        for i in range(11):
            yy = py + 60 + i*46
            ww = (pw-64) if i % 3 else pw*.5
            sh.line((px+32, yy), (px+32+ww, yy), FAINT, 2,
                    a*.9*eo(P(t, 1.6+i*.07, .5)))
    sh.circle((px+pw-74, py+ph-84), 38, RED, 2, eo(P(t, 3.4, .7))*.8)
    sh.text((px+pw-74, py+ph-84), "QC", monob(20), RED, eo(P(t, 3.6, .5))*.8, anchor="mm")
    # annotation callouts
    a1 = eo(P(t, 4.4, .7))
    sh.dashed((px-30, py+120), (px-250, py+120), GRAPH, 1.5, a1, prog=a1)
    sh.text((px-260, py+120), "ЛАБОРАТОРИСКИ БРОЈ", mono(19), GRAPH, a1, anchor="rm")
    a2 = eo(P(t, 5.3, .7))
    sh.dashed((px+pw+30, py+300), (px+pw+250, py+300), GRAPH, 1.5, a2, prog=a2)
    sh.text((px+pw+260, py+300), "РЕЗУЛТАТИ", mono(19), GRAPH, a2, anchor="lm")
    a3 = eo(P(t, 6.0, .7))
    sh.dashed((px+pw-74, py+ph+50), (px+pw+180, py+ph+120), GRAPH, 1.5, a3, prog=a3)
    sh.text((px+pw+190, py+ph+120), "ПЕЧАТ И ПОТПИС", mono(19), GRAPH, a3, anchor="lm")
    sh.text((92, 330), "Хартија.\nПечат.\nБроеви.", sans(46), GRAPH, eo(P(t, 1.0, .9)), spacing=14)

def sc_arrival(sh, t, d):
    header(sh, t, 2, "Прием и отпечаток", "Отпечаток на содржината")
    doc_page(sh, 150, 400, 300, 390, eo(P(t, .3, .7)), eo(P(t, .3, .8)), 8,
             label="ВЛЕЗЕН ДОКУМЕНТ")
    sh.arrow((480, 595), (700, 595), BLUE, 2.5, 1, eo(P(t, 1.5, .8)))
    b = (730, 470, 1290, 720)
    sh.rect(b, INK, 2.5, 1, eo(P(t, 2.2, .9)), fill=PAPER_D)
    sh.text((760, 500), "SHA-256", monob(26), BLUE, eo(P(t, 2.9, .5)))
    h = "a3f10c94e7b28d56f0a1c73e9b45d8207fe6c1a94b3d02e8"
    n = int(len(h) * eo(P(t, 3.3, 3.2)))
    for i, ch in enumerate(h[:n]):
        sh.text((762 + (i % 24)*22, 548 + (i // 24)*34), ch, mono(24), INK, 1)
    sh.text((760, 640), "Отпечаток на содржината, пресметан при прием.",
            sans(24), GRAPH, eo(P(t, 6.6, .8)))
    a = eo(P(t, 7.4, .9))
    sh.rect((730, 760, 1290, 838), GREEN, 2, a, a)
    sh.text((760, 785), "Од овој момент секоја промена е видлива.", sans(28), GREEN, a)
    sh.text((1340, 470), "ПОТЕКЛО", mono(19), GRAPH, eo(P(t, 8.0, .6)))
    for i, (k, v) in enumerate([("ЛАБОРАТОРИЈА", "Фармахем"),
                                ("ПРИМЕН", "07.08.2026"),
                                ("СТРАНИЦИ", "3")]):
        aa = eo(P(t, 8.2 + i*.35, .6))
        sh.text((1340, 516 + i*62), k, mono(16), FAINT, aa)
        sh.text((1340, 540 + i*62), v, sansb(28), INK, aa)

def sc_ocr(sh, t, d):
    header(sh, t, 3, "Читање на документот", "Не скенирање — разбирање")
    px, py, pw, ph = 150, 380, 430, 520
    doc_page(sh, px, py, pw, ph, 1, eo(P(t, .3, .7)), 10, stamp=True)
    # scan sweep
    sp = P(t, 1.2, 2.6)
    if 0 < sp < 1:
        sy = py + ph * sp
        sh.line((px, sy), (px+pw, sy), BLUE, 3, .9)
        sh.text((px+pw+14, sy), "ЧИТАЊЕ", mono(16), BLUE, .9, anchor="lm")
    # detected regions
    regions = [("ТАБЕЛА", (px+24, py+150, px+pw-24, py+300), 3.6),
               ("ПЕЧАТ",  (px+pw-120, py+ph-110, px+pw-20, py+ph-20), 4.2),
               ("ПОТПИС", (px+24, py+ph-92, px+220, py+ph-40), 4.7)]
    for name, box, at in regions:
        a = eo(P(t, at, .6))
        sh.rect(box, RED, 2, a, eo(P(t, at, .7)))
        sh.text((box[0], box[1]-26), name, mono(16), RED, a)
    # model cascade
    models = [("ПРВ", "kimi-k2.6", BLUE, 5.6),
              ("РЕЗЕРВА", "moonshot-v1-128k-vision", AMBER, 7.6),
              ("РЕЗЕРВА", "gpt-4o", GREEN, 9.4)]
    for i, (tag, name, col, at) in enumerate(models):
        y = 400 + i*126
        a = eo(P(t, at, .7))
        sh.rect((720, y, 1770, y+94), col, 2, a, eo(P(t, at, .8)))
        sh.text((746, y+22), tag, mono(16), col, a)
        sh.text((746, y+46), name, monob(30), INK, a)
        if i < 2:
            aa = eo(P(t, at+1.4, .5))
            sh.arrow((1245, y+100), (1245, y+120), FAINT, 2, aa)
            sh.text((1266, y+110), "ПРИ НЕУСПЕХ", mono(15), FAINT, aa, anchor="lm")
    a = eo(P(t, 11.4, .8))
    sh.text((720, 790), "Табелите, печатите и потписите се препознаваат како структура,",
            sans(26), GRAPH, a)
    sh.text((720, 824), "не како пиксели.", sansb(26), INK, a)

def sc_identity(sh, t, d):
    header(sh, t, 4, "Идентитет на содржината", "Три податоци, еден клуч")
    items = [("ЛАБОРАТОРИСКИ БРОЈ", "197-2026", .6),
             ("ДАТУМ НА МОСТРА",    "07.08.2026", 1.9),
             ("БРОЈ НА СТРАНИЦИ",   "3", 3.2)]
    cx = 1230
    for i, (k, v, at) in enumerate(items):
        y = 380 + i*150
        a = eo(P(t, at, .7))
        sh.rect((150, y, 700, y+112), INK, 2, a, eo(P(t, at, .8)), fill=PAPER_D)
        sh.text((178, y+22), k, mono(17), GRAPH, a)
        sh.text((178, y+50), v, sansb(40), INK, a)
        pa = eo(P(t, at+.5, .8))
        sh.line((700, y+56), (900, y+56), BLUE, 2, a, pa)
        sh.line((900, y+56), (900, 606), BLUE, 2, a, eo(P(t, at+.9, .6)))
    ka = eo(P(t, 5.0, .9))
    sh.arrow((900, 606), (1010, 606), BLUE, 2.5, ka)
    sh.rect((1030, 500, 1780, 712), GREEN, 3, ka, eo(P(t, 5.0, 1.0)), fill=PAPER_D)
    sh.text((1060, 530), "ЕДИНСТВЕН КЛУЧ НА СОДРЖИНАТА", mono(18), GREEN, ka)
    sh.text((1060, 566), "197-2026 · 07.08.2026 · 3", monob(34), INK, eo(P(t, 5.5, .7)))
    sh.text((1060, 632), "Ист клуч ⇒ ист документ.\nДупликат никогаш не влегува двапати.",
            sans(25), GRAPH, eo(P(t, 6.3, .8)), spacing=8)

def sc_chunks(sh, t, d):
    header(sh, t, 5, "Векторизација", "Значењето станува мерливо")
    doc_page(sh, 130, 400, 300, 400, eo(P(t, .2, .6)), eo(P(t, .2, .7)), 9, stamp=False)
    sh.arrow((460, 600), (600, 600), BLUE, 2.5, 1, eo(P(t, 1.0, .6)))
    cols, rows = 6, 4
    for r in range(rows):
        for c in range(cols):
            i = r*cols + c
            at = 1.5 + i*.075
            a = eo(P(t, at, .5))
            x, y = 650 + c*186, 400 + r*106
            sh.rect((x, y, x+164, y+84), GRAPH, 1.5, a*.9, eo(P(t, at, .55)), fill=PAPER_D)
            for k in range(7):                       # miniature vector signature
                hgt = 8 + 40 * abs(math.sin(i*1.7 + k*.9))
                ba = a * eo(P(t, at+.25, .5))
                sh.line((x+18+k*19, y+68), (x+18+k*19, y+68-hgt), BLUE, 3, ba*.85)
    a = eo(P(t, 5.6, .8))
    sh.text((650, 840), "1.583 сегменти · 1.024 димензии по сегмент · voyage-3-large",
            mono(24), INK, a)
    sh.text((650, 878), "Секој сегмент го носи своето значење како број.",
            sans(25), GRAPH, eo(P(t, 6.2, .8)))

def sc_query(sh, t, d):
    header(sh, t, 6, "Прашање и одговор", "Обичен јазик, следлив одговор")
    b = (150, 360, 1770, 468)
    sh.rect(b, INK, 2.5, 1, eo(P(t, .3, .8)), fill=PAPER_D)
    q = "Кои серии имаат ТХЦ над 20 % и чиста микробиологија?"
    n = int(len(q) * cl(P(t, 1.0, 3.0)))
    sh.text((186, 392), "?", monob(34), RED, eo(P(t, .6, .4)))
    sh.text((228, 398), q[:n], sans(34), INK, 1)
    if 0 < P(t, 1.0, 3.4) < 1 and int(t*2.2) % 2 == 0:
        sh.line((232+_w(q[:n], sans(34)), 396), (232+_w(q[:n], sans(34)), 434), INK, 2, .8)
    rows = [("КБ-2601", "24,1 %", "ОДГОВАРА", "197-2026 · с.2"),
            ("ЏД-2603", "22,8 %", "ОДГОВАРА", "198-2026 · с.1"),
            ("ГРЦ-2501", "21,4 %", "ОДГОВАРА", "201-2026 · с.3")]
    for i, (bt, v, st, src) in enumerate(rows):
        at = 5.0 + i*.7
        a = eo(P(t, at, .6))
        y = 540 + i*104
        sh.rect((150, y, 1770, y+84), GREEN, 2, a, eo(P(t, at, .7)), fill=PAPER_D)
        sh.text((186, y+26), bt, monob(30), INK, a)
        sh.text((480, y+26), v, sansb(30), INK, a)
        sh.text((720, y+30), st, mono(21), GREEN, a)
        sh.dashed((980, y+42), (1180, y+42), FAINT, 1.5, a, dash=7, gap=6)
        sh.text((1200, y+30), "ИЗВОР: " + src, mono(20), GRAPH, a)
    a = eo(P(t, 8.0, .8))
    sh.text((150, 876), "Секој број води назад до својот сертификат и страница.",
            sansb(28), INK, a)

def _w(s, f):
    return f.getbbox(s)[2] / S if s else 0

def sc_reissue(sh, t, d):
    header(sh, t, 7, "Преиздавање", "Заменува, не додава")
    doc_page(sh, 190, 420, 330, 420, eo(P(t, .3, .6)), eo(P(t, .3, .7)), 8,
             label="ВЕРЗИЈА 1  ·  04.2026")
    sh.text((190, 880), "Оригинален извештај", sans(25), GRAPH, eo(P(t, .8, .6)))
    ta = eo(P(t, 1.8, .8))
    sh.dashed((560, 630), (1020, 630), GRAPH, 2, ta, dash=12, gap=9, prog=ta)
    sh.text((790, 596), "3 НЕДЕЛИ", mono(21), GRAPH, ta, anchor="mm")
    doc_page(sh, 1060, 420, 330, 420, eo(P(t, 3.0, .6)), eo(P(t, 3.0, .7)), 8,
             label="ВЕРЗИЈА 2  ·  07.2026", lc=GREEN)
    sh.text((1060, 880), "Преиздаден извештај", sans(25), GRAPH, eo(P(t, 3.4, .6)))
    # the old one is struck out and greyed
    xa = eo(P(t, 5.4, .8))
    sh.line((190, 420), (520, 840), RED, 4, xa, eo(P(t, 5.4, .55)))
    sh.line((520, 420), (190, 840), RED, 4, xa, eo(P(t, 5.75, .55)))
    sh.rect((190, 420, 520, 840), PAPER, 0, xa*.52, 0, fill=PAPER)
    ba = eo(P(t, 6.6, .8))
    sh.rect((190, 906, 520, 968), RED, 2, ba, ba)
    sh.text((355, 937), "ИЗБРИШАН", monob(26), RED, ba, anchor="mm")
    ga = eo(P(t, 7.2, .8))
    sh.rect((1060, 906, 1390, 968), GREEN, 2, ga, ga)
    sh.text((1225, 937), "ЕДИНСТВЕНА ЖИВА ВЕРЗИЈА", mono(20), GREEN, ga, anchor="mm")
    na = eo(P(t, 8.6, .9))
    sh.rect((1450, 420, 1790, 700), INK, 2, na, eo(P(t, 8.6, .9)), fill=PAPER_D)
    sh.text((1478, 448), "ВГРАДЕНО ВО КОДОТ", mono(18), RED, na)
    sh.text((1478, 492), "delete(old_id)\nupload(new_pdf)\nassert new_id\n  is not None",
            mono(24), INK, eo(P(t, 9.0, .8)), spacing=12)
    sh.text((1450, 726), "Никогаш две верзии\nво исто време.", sansb(28), INK,
            eo(P(t, 10.2, .8)), spacing=8)

def sc_close(sh, t, d):
    a0 = eo(P(t, .2, .8))
    sh.text((92, 300), "Еден сертификат.", sansb(88), INK, a0)
    sh.text((92, 400), "Седум чекори.", sansb(88), INK, eo(P(t, .9, .8)))
    y = 620
    steps = ["ПРИЕМ", "ЧИТАЊЕ", "ИДЕНТИТЕТ", "ВЕКТОРИ", "ПРАШАЊЕ", "ПРЕИЗДАВАЊЕ", "ТРАГА"]
    x0, gap = 150, 248
    lp = eo(P(t, 2.0, 1.8))
    sh.line((x0, y), (x0 + gap*6, y), GRAPH, 2, .8, lp)
    for i, s in enumerate(steps):
        at = 2.1 + i*.24
        a = eo(P(t, at, .5))
        x = x0 + i*gap
        sh.dot((x, y), 9, BLUE if i < 6 else GREEN, a)
        sh.circle((x, y), 17, BLUE if i < 6 else GREEN, 2, a*.7)
        sh.text((x, y+46), s, mono(18), GRAPH, a, anchor="ma")
        sh.text((x, y-44), f"{i+1:02d}", monob(20), INK, a, anchor="md")
    a2 = eo(P(t, 4.6, .9))
    sh.line((92, 792), (92+180, 792), RED, 4, a2, eo(P(t, 4.6, .7)))
    sh.text((92, 826), "Целосна следливост — од лабораторијата до одлуката за пуштање.",
            sans(38), INK, a2)
    sh.text((92, 890), "EU GMP ANNEX 11  ·  RAGFLOW v0.26.4  ·  СОПСТВЕН СЕРВЕР KVM4",
            mono(21), GRAPH, eo(P(t, 5.6, .8)))

SCENES = [sc_paper, sc_arrival, sc_ocr, sc_identity, sc_chunks,
          sc_query, sc_reissue, sc_close]

# ── frame assembly ────────────────────────────────────────────────────
def frame(t):
    img = PAPER_IMG.copy()
    sh = Sheet(img)
    for i, s in enumerate(TL["scenes"]):
        a, b = s["scene_start"], s["scene_start"] + s["scene_dur"]
        FADE = .45
        if t < a - FADE or t > b + FADE:
            continue
        o = min(P(t, a, FADE), 1 - P(t, b - FADE*.7, FADE))
        if o <= 0:
            continue
        if o >= .999:
            SCENES[i](sh, t - a, s["scene_dur"])
        else:                                    # cross-fade via a scratch layer
            lay = Image.new("RGB", img.size, PAPER)
            l2 = Sheet(lay)
            SCENES[i](l2, t - a, s["scene_dur"])
            img.paste(Image.blend(img, lay, o), (0, 0))
            sh = Sheet(img)
    return img.reduce(S)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "render"
    if mode == "stills":
        os.makedirs(os.path.join(DIR, "stills2"), exist_ok=True)
        for t in map(float, sys.argv[2:]):
            p = os.path.join(DIR, "stills2", f"g_{t:06.1f}.png")
            frame(t).save(p)
            print("  still", t, "->", os.path.basename(p))
        return

    out = os.path.join(DIR, "out", "film2_pat_na_sertifikat.mp4")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    audio = os.path.join(DIR, "audio", "film2_master.m4a")
    total = math.ceil(TL["total"] * FPS)
    ff = subprocess.Popen([
        FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
        "-f", "image2pipe", "-c:v", "mjpeg", "-framerate", str(FPS), "-i", "pipe:0",
        "-i", audio, "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-preset", "medium", "-crf", "19",
        "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.2",
        "-r", str(FPS), "-g", str(FPS*2),
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
        "-movflags", "+faststart", "-shortest", out], stdin=subprocess.PIPE)
    import time
    t0 = time.time()
    for i in range(total):
        buf = io.BytesIO()
        frame(i / FPS).save(buf, "JPEG", quality=94)
        ff.stdin.write(buf.getvalue())
        if i % 120 == 0 or i == total-1:
            el = time.time() - t0
            print(f"  frame {i+1}/{total}  {(i+1)/total*100:5.1f}%  "
                  f"{el:5.0f}s elapsed  ~{el/(i+1)*(total-i-1):5.0f}s left", flush=True)
    ff.stdin.close()
    if ff.wait() != 0:
        raise SystemExit("ffmpeg failed")
    print(f"\n  ✔ {out}  ({os.path.getsize(out)/1048576:.1f} MB, {TL['total']:.1f}s)")


if __name__ == "__main__":
    main()
