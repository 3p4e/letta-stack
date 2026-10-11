# -*- coding: utf-8 -*-
"""Geometrically-correct band chart for the fixed-nominal / full-10% ladder."""
import importlib.util, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D
W="/tmp/claude-0/-home-user-letta-stack/fa8a4b28-563d-5957-9984-7e34a8196007/scratchpad/batch_excel"
spec=importlib.util.spec_from_file_location("f10",f"{W}/build_final10.py")
m=importlib.util.module_from_spec(spec); sys.modules["f10"]=m; spec.loader.exec_module(m)
NAVY="#2B547E"; RED="#C0392B"; GREY="#595959"

bs={}; noms={}
for s,cul,pp,a,n in m.ASSIGNED:
    bs.setdefault(s,{}).setdefault(n,[]).append((pp,a)); noms.setdefault(s,set()).add(n)
ROMAN=["I","II","III","IV","V","VI","VII","VIII"]
grade={}
for s,ns in noms.items():
    for i,n in enumerate(sorted(ns,reverse=True)): grade[(s,n)]=ROMAN[i]

order=sorted(bs,key=lambda s:(-max(bs[s]), s.lower()))
n=len(order)
fig,ax=plt.subplots(figsize=(15.5,0.63*n+2.4))
for i,s in enumerate(order):
    y=n-i
    for k,nm in enumerate(sorted(bs[s])):
        t,lo,hi=m.band(nm)
        # true extent: nominal +/- tolerance
        ax.add_patch(Rectangle((nm-t,y-0.27),2*t,0.54,facecolor=NAVY,alpha=0.13,
                               edgecolor=NAVY,linewidth=1.0,zorder=2))
        ax.plot([nm,nm],[y-0.27,y+0.27],color=NAVY,lw=1.7,zorder=4)
        ax.text(nm,y+0.31,grade[(s,nm)],ha="center",va="bottom",fontsize=6.5,
                color=NAVY,fontweight="bold",zorder=5)
        ax.text(nm,y-0.42,f"{nm}±{t:.1f}",ha="center",va="top",fontsize=5.9,color=GREY,zorder=5)
        for pp,a in bs[s][nm]:
            ax.plot([a],[y],marker="o",ms=5.3,color=RED,markeredgecolor="white",
                    markeredgewidth=0.7,zorder=6)
ax.set_yticks([n-i for i in range(n)]); ax.set_yticklabels(order,fontsize=8.2)
ax.set_ylim(0.3,n+1.0); ax.set_xlim(6.5,29.5)
ax.set_xticks(range(7,30)); ax.tick_params(axis="x",labelsize=7.6); ax.tick_params(axis="y",length=0)
ax.set_xlabel("Total Δ9-THC (% w/w) — single linear scale; every band and result at true position",
              fontsize=8.6,color=NAVY,labelpad=8)
ax.grid(True,axis="x",color="#E3E7EC",lw=0.7,zorder=0); ax.set_axisbelow(True)
for sp in ("top","right","left"): ax.spines[sp].set_visible(False)
ax.set_title("Purely Plant — declared potency classes at full ±10%, with all THC results",
             color=NAVY,fontsize=12.5,fontweight="bold",pad=16)
ax.legend(handles=[
  Rectangle((0,0),1,1,facecolor=NAVY,alpha=0.13,edgecolor=NAVY,label="Declared class band  [nominal ± 10% of nominal]"),
  Line2D([0],[0],color=NAVY,lw=1.7,label="Nominal value (as declared)"),
  Line2D([0],[0],marker="o",color="none",markerfacecolor=RED,markeredgecolor="white",ms=6,label="Batch THC assay result"),
],loc="upper center",bbox_to_anchor=(0.5,-0.05),ncol=3,fontsize=7.5,frameon=False)
fig.tight_layout(); fig.savefig(f"{W}/potency_bands_10pct.png",dpi=190,bbox_inches="tight",facecolor="white")
plt.close(fig)
bad=sum(1 for s,c,pp,a,nm in m.ASSIGNED if not (nm-nm*0.10-1e-9<=a<=nm+nm*0.10+1e-9))
print("geometry/containment violations:",bad)
