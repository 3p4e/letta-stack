import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, json
NAVY="#2B547E"; RED="#C0392B"; GREEN="#1E8449"; GREY="#595959"
GRADES=list(range(8,29,2))
def band(N): return (0.9*N,1.1*N)
def grade(v):
    c=[N for N in GRADES if band(N)[0]-1e-9<=v<=band(N)[1]+1e-9]
    return min(c,key=lambda N:abs(v-N)) if c else None

R=json.load(open("thc_dataset.json"))
for r in R:
    r["g_prev"]=grade(r["prev"]) if r["prev"] is not None else None
    r["g_ret"]=grade(r["retest"])

def fig_scatter(out):
    fig,ax=plt.subplots(figsize=(7.2,4.4),dpi=200)
    for N in GRADES:
        lo,hi=band(N); ax.axhspan(lo,hi,color=NAVY,alpha=0.045,lw=0)
    comp=[r for r in R if r["prev"] is not None]
    hold=[r for r in comp if band(r["g_prev"])[0]-1e-9<=r["retest"]<=band(r["g_prev"])[1]+1e-9]
    mv=[r for r in comp if r not in hold]
    ax.plot([6,30],[6,30],ls="--",lw=0.9,color=GREY,zorder=1)
    ax.scatter([r["prev"] for r in hold],[r["retest"] for r in hold],s=34,color=NAVY,zorder=3,label="Grade retained (n=%d)"%len(hold))
    ax.scatter([r["prev"] for r in mv],[r["retest"] for r in mv],s=40,color=RED,marker="D",zorder=4,label="Grade changed (n=%d)"%len(mv))
    ax.set_xlabel("Previous release result — Total Δ9-THC (% w/w)",fontsize=8,color=GREY)
    ax.set_ylabel("Re-test — Total Δ9-THC (% w/w)",fontsize=8,color=GREY)
    ax.set_xlim(6,30); ax.set_ylim(6,30)
    ax.tick_params(labelsize=7,colors=GREY)
    for s in ("top","right"): ax.spines[s].set_visible(False)
    for s in ("left","bottom"): ax.spines[s].set_color(GREY)
    ax.grid(alpha=0.18,lw=0.5)
    ax.legend(fontsize=7,frameon=False)
    fig.tight_layout(); fig.savefig(out); plt.close(fig); return out

def fig_migration(out):
    fig,ax=plt.subplots(figsize=(7.2,3.6),dpi=200)
    prevc=[sum(1 for r in R if r["g_prev"]==N) for N in GRADES]
    retc =[sum(1 for r in R if r["g_ret"] ==N and r["prev"] is not None) for N in GRADES]
    x=range(len(GRADES)); w=0.4
    ax.bar([i-w/2 for i in x],prevc,w,color=GREY,label="Previous result")
    ax.bar([i+w/2 for i in x],retc,w,color=NAVY,label="Re-test")
    ax.set_xticks(list(x)); ax.set_xticklabels(["G%d"%N for N in GRADES],fontsize=7,color=GREY)
    ax.set_ylabel("Batches (n)",fontsize=8,color=GREY)
    ax.tick_params(labelsize=7,colors=GREY)
    for s in ("top","right"): ax.spines[s].set_visible(False)
    for s in ("left","bottom"): ax.spines[s].set_color(GREY)
    ax.grid(axis="y",alpha=0.18,lw=0.5); ax.legend(fontsize=7,frameon=False)
    fig.tight_layout(); fig.savefig(out); plt.close(fig); return out
