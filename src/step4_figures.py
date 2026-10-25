"""Step 4: figures for the README.

Figure 1: within-subgroup tie share relative to shuffled labels, by layer and attribute.
Figure 2: partners vs. associates on four node-level measures (mean and 90% bootstrap interval).

Run:  python step4_figures.py
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from config import RESULTS, FIGURES, N_BOOT, SEED


def fig_mixing():
    m = pd.read_csv(RESULTS / "mixing_by_subgroup.csv")
    piv = m.pivot(index="layer", columns="attribute", values="ratio").loc[["advice", "friendship", "coworker"], ["status", "office", "practice", "gender"]]
    q = m.pivot(index="layer", columns="attribute", values="q_bh").loc[piv.index, piv.columns]
    fig, ax = plt.subplots(figsize=(7, 3.6))
    im = ax.imshow(piv.values, cmap="Reds", vmin=1, vmax=1.7)
    for i in range(piv.shape[0]):
        for j in range(piv.shape[1]):
            star = "" if q.values[i, j] < 0.05 else " (n.s.)"
            ax.text(j, i, f"{piv.values[i, j]:.2f}{star}", ha="center", va="center", fontsize=9)
    ax.set_xticks(range(piv.shape[1]), [c.capitalize() for c in piv.columns])
    ax.set_yticks(range(piv.shape[0]), [r.capitalize() for r in piv.index])
    ax.set_title("Ties within the same subgroup, relative to shuffled labels\n(1 = no preference; n.s. = not significant at FDR 5%)", fontsize=10)
    fig.colorbar(im, ax=ax, shrink=0.8)
    plt.tight_layout(); plt.savefig(FIGURES / "fig1_mixing_by_layer.png", dpi=200); plt.close()


def fig_status():
    d = pd.read_csv(RESULTS / "node_measures.csv")
    rng = np.random.default_rng(SEED)
    measures = [("degree", "Contacts (any layer)"), ("multiplexity", "Multiplexity"),
                ("clustering_aggregate", "Clustering (aggregate)"), ("cross_layer_triangle_share", "Cross-layer triangle share")]
    fig, axes = plt.subplots(1, 4, figsize=(12, 3.2))
    for ax, (m, label) in zip(axes, measures):
        for k, (grp, col) in enumerate([("partner", "#1F3A5F"), ("associate", "#C44E52")]):
            x = d.loc[d["status"] == grp, m].dropna().values
            boots = [rng.choice(x, len(x)).mean() for _ in range(N_BOOT)]
            lo, hi = np.quantile(boots, [0.05, 0.95])
            ax.errorbar(k, x.mean(), yerr=[[x.mean() - lo], [hi - x.mean()]], fmt="o", color=col, capsize=4)
        ax.set_xticks([0, 1], ["Partners", "Associates"]); ax.set_xlim(-0.6, 1.6); ax.set_title(label, fontsize=10)
    fig.suptitle("Partners vs. associates: mean and 90% bootstrap interval", fontsize=11)
    plt.tight_layout(); plt.savefig(FIGURES / "fig2_partners_vs_associates.png", dpi=200); plt.close()


if __name__ == "__main__":
    FIGURES.mkdir(exist_ok=True)
    fig_mixing(); fig_status()
    print("Saved figures/fig1_mixing_by_layer.png and figures/fig2_partners_vs_associates.png")
