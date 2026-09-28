# -*- coding: utf-8 -*-
"""
Geometrically-correct potency band chart.

Every element is drawn to a single shared linear % THC scale:
  * a grade band is a rectangle spanning its TRUE mathematical extent
    [nominal − tolerance, nominal + tolerance]; adjacent bands therefore
    share an edge exactly, and an open gap shows as real blank width;
  * the nominal is a tick at its exact value;
  * every batch assay is a marker at its exact value.
No element is nudged, padded or rounded for looks.
"""
import importlib.util, sys, datetime as dt
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D

W = "/tmp/claude-0/-home-user-letta-stack/fa8a4b28-563d-5957-9984-7e34a8196007/scratchpad/batch_excel"
spec = importlib.util.spec_from_file_location("bd", f"{W}/build_dist.py")
bd = importlib.util.module_from_spec(spec); sys.modules["bd"] = bd; spec.loader.exec_module(bd)

NAVY="#2B547E"; NAVY2="#4A79A8"; ODD="#C55A11"; RED="#C0392B"; GREY="#595959"; LGREY="#D8DEE6"


def solve_all():
    strains={}
    for s,cul,pp,a in bd.BATCHES: strains.setdefault(s,[]).append((cul,pp,a))
    out={}
    for st,items in strains.items():
        blocks = bd.solve(items) or bd.fallback_single(items)
        flat=[g for blk in blocks for g in blk]
        flat.sort(key=lambda g:-g["nom"])
        for i,g in enumerate(flat): g["grade"]=bd.ROMAN[i]
        out[st]=flat
    return out


def main():
    solved=solve_all()
    # order strains by their top potency, strongest first
    order=sorted(solved, key=lambda s:(-max(g["nom"] for g in solved[s]), s.lower()))

    lo_ax, hi_ax = 6.0, 29.0
    n=len(order)
    fig, ax = plt.subplots(figsize=(15.5, 0.62*n + 2.3))

    for i,st in enumerate(order):
        y = n - i
        grades = sorted(solved[st], key=lambda g:g["nom"])
        for g in grades:
            lo, hi = g["nom"]-g["tol"], g["nom"]+g["tol"]     # TRUE extent -> bands tile exactly
            odd = int(g["nom"])%2==1
            ax.add_patch(Rectangle((lo, y-0.26), hi-lo, 0.52,
                                   facecolor=(ODD if odd else NAVY),
                                   alpha=0.20 if odd else 0.16,
                                   edgecolor=(ODD if odd else NAVY),
                                   linewidth=1.1, zorder=2))
            # nominal tick, at its exact value
            ax.plot([g["nom"], g["nom"]], [y-0.26, y+0.26],
                    color=(ODD if odd else NAVY), lw=1.6, zorder=4)
            ax.text(g["nom"], y+0.30, f"{g['grade']}", ha="center", va="bottom",
                    fontsize=6.4, color=(ODD if odd else NAVY), fontweight="bold", zorder=5)
            if hi-lo >= 1.9:
                ax.text(g["nom"], y-0.40, f"{g['nom']:.0f}±{g['tol']:.1f}", ha="center", va="top",
                        fontsize=5.9, color=(ODD if odd else GREY), zorder=5)
            # assays, at their exact values
            for _,pp,a in g["members"]:
                ax.plot([a],[y], marker="o", ms=5.2, color=RED,
                        markeredgecolor="white", markeredgewidth=0.7, zorder=6)
        # open gaps between consecutive grades in this strain
        for a_,b_ in zip(grades, grades[1:]):
            ga, gb = a_["nom"]+a_["tol"], b_["nom"]-b_["tol"]
            if gb-ga > 1e-9:
                ax.add_patch(Rectangle((ga, y-0.26), gb-ga, 0.52, facecolor="none",
                                       edgecolor=RED, linewidth=0.8, linestyle=":",
                                       hatch="///", alpha=0.55, zorder=1))
                ax.text((ga+gb)/2, y, f"gap {gb-ga:.2f} pp", ha="center", va="center",
                        fontsize=5.8, color=RED, style="italic", zorder=5)

    ax.set_yticks([n-i for i in range(n)])
    ax.set_yticklabels(order, fontsize=8.2)
    ax.set_ylim(0.3, n+0.95)
    ax.set_xlim(lo_ax, hi_ax)
    ax.set_xticks(range(int(lo_ax), int(hi_ax)+1))
    ax.set_xticklabels([f"{v}" for v in range(int(lo_ax), int(hi_ax)+1)], fontsize=7.6)
    ax.set_xlabel("Total Δ9-THC  (% w/w)  —  single linear scale, all bands and results drawn to true position",
                  fontsize=8.6, color=NAVY, labelpad=8)
    ax.grid(True, axis="x", which="major", color="#E3E7EC", lw=0.7, zorder=0)
    ax.set_axisbelow(True)
    for sp in ("top","right","left"): ax.spines[sp].set_visible(False)
    ax.tick_params(axis="y", length=0)

    ax.set_title("Purely Plant — potency grade bands and THC results, per strain",
                 color=NAVY, fontsize=12.5, fontweight="bold", pad=16)

    handles=[
      Rectangle((0,0),1,1,facecolor=NAVY,alpha=0.16,edgecolor=NAVY,label="Grade band, even nominal  [nominal ± tolerance]"),
      Rectangle((0,0),1,1,facecolor=ODD,alpha=0.20,edgecolor=ODD,label="Grade band, ODD nominal (shifted to close a gap)"),
      Line2D([0],[0],marker="o",color="none",markerfacecolor=RED,markeredgecolor="white",ms=6,label="Batch THC assay result"),
      Line2D([0],[0],color=NAVY,lw=1.6,label="Nominal value"),
      Rectangle((0,0),1,1,facecolor="none",edgecolor=RED,linestyle=":",hatch="///",label="Open gap — no grade covers this range"),
    ]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5,-0.055),
              ncol=3, fontsize=7.4, frameon=False)

    fig.tight_layout()
    out=f"{W}/potency_bands.png"
    fig.savefig(out, dpi=190, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    # geometry self-check: verify drawn extents tile and contain their assays
    bad=0
    for st,gl in solved.items():
        gs=sorted(gl,key=lambda g:g["nom"])
        for g in gs:
            for _,pp,a in g["members"]:
                if not (g["nom"]-g["tol"]-1e-9 <= a <= g["nom"]+g["tol"]+1e-9): bad+=1
        for x,y in zip(gs,gs[1:]):
            if y["nom"]-y["tol"] < x["nom"]+x["tol"]-1e-9: bad+=1
    print(f"geometry self-check: {bad} violations (0 expected)")
    print("wrote", out)


if __name__=="__main__":
    main()
