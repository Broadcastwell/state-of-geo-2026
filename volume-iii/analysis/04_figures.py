#!/usr/bin/env python3
"""
Volume III, step 4: the six figures. 300 dpi PNG plus SVG, colourblind-safe,
direct labels, no chartjunk. Every number drawn here is read from
data/results.json, which is itself recomputed row-level from scored.csv, so a
caption can never drift from the dataset.

Palette anchored on the Broadcastwell blues.
"""
import json, os, math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

D, F = "data", "figures"
os.makedirs(F, exist_ok=True)
R = json.load(open(f"{D}/results.json"))

BLUE_D, BLUE = "#1D4ED8", "#3B82F6"
BLUE_L, BLUE_XL = "#93C5FD", "#DBEAFE"
GREY_D, GREY, GREY_L = "#374151", "#6B7280", "#D1D5DB"
BG = "white"
ENGINES = R["engines"]
LABEL = {"chatgpt": "ChatGPT", "claude": "Claude",
         "perplexity": "Perplexity", "google_aio": "Google AI\nOverviews"}
LABEL1 = {k: v.replace("\n", " ") for k, v in LABEL.items()}

plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
    "font.size": 11, "axes.titlesize": 13, "axes.titleweight": "bold",
    "axes.labelcolor": GREY_D, "text.color": GREY_D,
    "xtick.color": GREY, "ytick.color": GREY,
    "axes.edgecolor": GREY_L, "axes.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 100, "savefig.bbox": "tight",
})


def save(fig, name):
    fig.savefig(f"{F}/{name}.png", dpi=300)
    fig.savefig(f"{F}/{name}.svg")
    plt.close(fig)
    print(f"wrote {F}/{name}.png and .svg")


def pct(x, nd=1):
    return "n/a" if x is None else f"{100*x:.{nd}f}%"


# ---------------------------------------------------- fig 1: Jaccard heatmap
m = R["pairwise_jaccard"]["matrix"]
fig, ax = plt.subplots(figsize=(7.2, 6))
vals = [[m[a][b] if m[a][b] is not None else float("nan") for b in ENGINES] for a in ENGINES]
im = ax.imshow(vals, cmap="Blues", vmin=0, vmax=1)
ax.set_xticks(range(4), [LABEL[e] for e in ENGINES])
ax.set_yticks(range(4), [LABEL[e] for e in ENGINES])
for i in range(4):
    for j in range(4):
        v = vals[i][j]
        if v != v:
            continue
        ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                color="white" if v > 0.55 else GREY_D, fontweight="bold", fontsize=13)
ax.set_title("Vendor-set overlap between engines\nMean Jaccard similarity per question", pad=14)
cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
cb.set_label("Jaccard similarity (1.0 = identical shortlists)")
cb.outline.set_visible(False)
ax.set_xticks([x - 0.5 for x in range(1, 4)], minor=True)
ax.set_yticks([y - 0.5 for y in range(1, 4)], minor=True)
ax.grid(which="minor", color=BG, linewidth=2)
ax.tick_params(which="minor", length=0)
n = R["pairwise_jaccard"]["pairs"][f"{ENGINES[0]}|{ENGINES[1]}"]["n_questions"]
fig.text(0.5, -0.02, f"Diagonal fixed at 1.0. Off-diagonal cells are means over questions "
                     f"both engines answered.", ha="center", fontsize=9, color=GREY)
save(fig, "fig1_jaccard_matrix")

# ---------------------------------------------------- fig 2: consensus
# Use the best-powered engine set rather than the four-engine intersection,
# which collapsed to a handful of questions when three API accounts ran dry.
_sets = R["consensus_by_engine_set"]
c = max(_sets.values(), key=lambda x: x["n_questions"] * x["n_engines"])
NE = c["n_engines"]
fig, ax = plt.subplots(figsize=(7.6, 5))
ks = [str(i) for i in range(1, NE + 1)]
vals = [c["by_engine_count"][k] for k in ks]
shares = [c["share"][k] for k in ks]
cols = [BLUE_XL, BLUE_L, BLUE, BLUE_D][-NE:]
bars = ax.bar(range(NE), vals, color=cols, width=0.66)
for b, v, s in zip(bars, vals, shares):
    ax.text(b.get_x() + b.get_width() / 2, v, f"{v:,}\n{pct(s)}",
            ha="center", va="bottom", fontweight="bold", fontsize=11)
labels = [f"named by\n{i} engine" + ("" if i == 1 else "s") for i in range(1, NE + 1)]
labels[-1] = f"named by\nall {NE} engines"
ax.set_xticks(range(NE), labels)
ax.set_ylabel("Distinct vendor mentions")
ax.set_ylim(0, max(vals) * 1.22 if vals else 1)
_names = ", ".join(LABEL1[e] for e in c["engines"])
ax.set_title(f"How much of a shortlist is shared?\n{c['distinct_vendor_slots']:,} vendor "
             f"mentions across {c['n_questions']} questions answered by all of:\n{_names}",
             pad=14, fontsize=12)
ax.spines["left"].set_visible(False)
ax.tick_params(left=False)
ax.set_yticks([])
save(fig, "fig2_consensus")

# ---------------------------------------------------- fig 3: the money chart
# PER ENGINE, and showing the length controls, because the pooled version hid
# that the separation is real on one engine and a length artefact on another.
DTE = R["decisive_test_per_engine"]
eng_with = [e for e in ENGINES if DTE["engines"][e]["repeat_pairs"] > 0]
MODEL_ROWS = [("full", "Jaccard\n(raw)"), ("topk", "Jaccard\nfirst 5 named"),
              ("overlap", "Overlap coeff.\n(length-normalised)")]

fig, axes = plt.subplots(1, len(eng_with), figsize=(5.4 * len(eng_with), 5.4), sharex=True)
if len(eng_with) == 1:
    axes = [axes]
for ax, e in zip(axes, eng_with):
    blk = DTE["engines"][e]
    ys, labels = [], []
    for i, (mode, lab) in enumerate(MODEL_ROWS):
        m = blk["modes"][mode]
        base = i * 2.4
        for j, (key, col, nm) in enumerate((("within", GREY, "same engine, different run"),
                                            ("between", BLUE_D, "different engines"))):
            v = m[key]
            if v["mean"] is None:
                continue
            y = base + j * 0.85
            ax.barh(y, v["mean"], color=col, height=0.62)
            c = v["ci95"]
            if c:
                ax.plot([c["lo"], c["hi"]], [y, y], color=GREY_D, lw=1.6)
                ax.plot([c["lo"], c["lo"]], [y - 0.15, y + 0.15], color=GREY_D, lw=1.6)
                ax.plot([c["hi"], c["hi"]], [y - 0.15, y + 0.15], color=GREY_D, lw=1.6)
            ax.text(0.015, y, f"{v['mean']:.2f}", va="center", ha="left",
                    fontsize=11, fontweight="bold", color="white")
        g = m["gap"]
        if g:
            sep = g["lo"] > 0
            ax.text(0.995, base + 0.42,
                    # 3dp, because at 2dp a real +0.002 renders as "+0.00" and
                    # reads as an exact zero next to the words "not significant"
                    ("gap " + f"{g['point']:+.3f}" + ("  holds" if sep else "  not significant")),
                    va="center", ha="right", fontsize=9.5,
                    color=(BLUE_D if sep else "#b45309"), fontweight="bold")
        ys.append(base + 0.42)
        labels.append(lab)
    ax.set_yticks(ys, labels, fontsize=9.5)
    ax.invert_yaxis()
    ax.set_xlim(0, 1)
    ax.set_title(f"{LABEL1[e]}\n{blk['repeat_pairs']} repeat pairs", fontsize=12, pad=10)
    ax.spines["left"].set_visible(False)
    ax.tick_params(left=False)
axes[0].set_xlabel("Vendor-set agreement  (1.0 = identical shortlists)")
if len(axes) > 1:
    axes[-1].set_xlabel("Vendor-set agreement  (1.0 = identical shortlists)")
fig.subplots_adjust(wspace=0.42)
h = [plt.Rectangle((0, 0), 1, 1, color=GREY), plt.Rectangle((0, 0), 1, 1, color=BLUE_D)]
fig.legend(h, ["same engine, different run", "different engines, same question"],
           frameon=False, ncol=2, loc="upper center", bbox_to_anchor=(0.5, 0.04), fontsize=10)
fig.suptitle("Is engine-to-engine difference bigger than an engine's own noise?\n"
             f"Same {DTE['stability_questions']} questions, bootstrap 95% intervals, "
             f"and the same comparison rerun under two length controls",
             fontsize=13, fontweight="bold", y=1.06)
save(fig, "fig3_within_vs_between")

# ---------------------------------------------------- fig 4: answer rate
a = R["attrition_main_set"]
fig, ax = plt.subplots(figsize=(8.2, 5))
ok = [a[e]["ok"] for e in ENGINES]
noaio = [a[e]["no_aio"] for e in ENGINES]
err = [a[e]["api_error"] for e in ENGINES]
x = range(4)
ax.bar(x, ok, color=BLUE_D, width=0.6, label="answered")
ax.bar(x, noaio, bottom=ok, color=BLUE_L, width=0.6, label="no AI Overview returned")
ax.bar(x, err, bottom=[o + n for o, n in zip(ok, noaio)], color=GREY_L, width=0.6, label="API error")
cc = R.get("collection_completeness", {}).get("per_engine", {})
for i, e in enumerate(ENGINES):
    tot = a[e]["attempted"]
    ax.text(i, tot + max(1, tot * 0.02), pct(a[e]["answer_rate"], 0),
            ha="center", fontweight="bold", fontsize=12)
planned = R.get("collection_completeness", {}).get("planned_questions", 280)
ax.set_ylim(0, planned * 1.12)
ax.set_xticks(x, [LABEL[e] + f"\n{a[e]['attempted']} of {planned} collected" for e in ENGINES],
              fontsize=10)
ax.set_ylabel("Questions")
ax.set_title("Not every engine answers every buyer question\n"
             "Bars are questions attempted, not questions planned", pad=14, fontsize=12)
ax.legend(frameon=False, ncol=3, fontsize=9, loc="upper center", bbox_to_anchor=(0.5, -0.17))
fig.text(0.5, -0.20, "Three of the four accounts ran out of API credit during collection, "
                     "which is why the bars differ in height.",
         ha="center", fontsize=9, color=GREY)
save(fig, "fig4_answer_rate")

# ---------------------------------------------------- fig 5: citation mix
cm = R["citation_mix"]
order = ["vendor_owned", "review_platform", "editorial", "analyst", "community", "other"]
pretty = {"vendor_owned": "Vendor-owned", "review_platform": "Review platform",
          "editorial": "Editorial", "analyst": "Analyst", "community": "Community", "other": "Other"}
cols = {"vendor_owned": BLUE_D, "review_platform": BLUE, "editorial": BLUE_L,
        "analyst": "#1E3A8A", "community": GREY, "other": GREY_L}
fig, ax = plt.subplots(figsize=(8.6, 5))
left = [0.0] * 4
for k in order:
    vals = [(cm[e]["share"].get(k) or 0) for e in ENGINES]
    ax.barh(range(4), vals, left=left, color=cols[k], height=0.6, label=pretty[k])
    for i, v in enumerate(vals):
        if v > 0.07:
            ax.text(left[i] + v / 2, i, f"{100*v:.0f}%", ha="center", va="center",
                    color="white" if k in ("vendor_owned", "analyst", "community") else GREY_D,
                    fontsize=10, fontweight="bold")
    left = [l + v for l, v in zip(left, vals)]
ax.set_yticks(range(4), [LABEL[e] for e in ENGINES])
ax.invert_yaxis()
ax.set_xlim(0, 1)
ax.xaxis.set_major_formatter(PercentFormatter(1.0))
ax.set_xlabel("Share of citations")
ax.set_title("What each engine cites", pad=14)
ax.legend(frameon=False, ncol=3, fontsize=9, loc="upper center", bbox_to_anchor=(0.5, -0.16))
ax.spines["left"].set_visible(False)
ax.tick_params(left=False)
save(fig, "fig5_citation_mix")

# ---------------------------------------------------- fig 6: Vol I vs Vol III
tb = R["vol1_tieback"]["rows"]
fig, ax = plt.subplots(figsize=(7.2, 6))
if tb:
    xs = [t["vol1_claude_named_rate_category_mean"] for t in tb]
    ys = [t["vol3_multi_engine_named_rate"] for t in tb]
    ax.scatter(xs, ys, s=44, color=BLUE, edgecolor=BLUE_D, linewidth=0.8, alpha=0.85, zorder=3)
    lim = max([0.05] + xs + ys) * 1.12
    ax.plot([0, lim], [0, lim], color=GREY_L, lw=1.2, ls="--", zorder=1)
    ax.text(lim * 0.62, lim * 0.66, "equal visibility", color=GREY, fontsize=9, rotation=38)
    ax.set_xlim(0, lim)
    ax.set_ylim(0, lim)
    r = R["vol1_tieback"]["pearson_r"]
    ax.set_title("Volume I single-engine baseline vs Volume III four-engine visibility\n"
                 + (f"Pearson r = {r:.2f}, n = {len(tb)} companies" if r is not None
                    else f"n = {len(tb)} companies"), pad=14)
else:
    ax.text(0.5, 0.5, "no overlapping companies", ha="center", transform=ax.transAxes)
ax.xaxis.set_major_formatter(PercentFormatter(1.0))
ax.yaxis.set_major_formatter(PercentFormatter(1.0))
ax.set_xlabel("Volume I: mean Claude-engine named rate for the company's category")
ax.set_ylabel("Volume III: mean named rate across all four engines")
save(fig, "fig6_vol1_vs_vol3")

print("all six figures written")
