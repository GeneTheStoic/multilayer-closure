"""Step 7: figures for steps 5 and 6.

Figure 3: structural inequivalence by layer (excess over shuffled labels) next to
          attribute assortativity by layer: two different notions of group difference.
Figure 4: simulation: how often the index flags a planted difference, by effect size.

Run:  python step7_figures_inequivalence.py
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from config import RESULTS, FIGURES

LAYERS = ["advice", "friendship", "coworker"]


def fig3():
    dec = pd.read_csv(RESULTS / "structural_inequivalence_by_layer.csv")
    ar = pd.read_csv(RESULTS / "assortativity_by_layer.csv")
    keep = [("status", "associate"), ("gender", "man"), ("practice", "corporate"), ("office", "Boston")]
    labels = ["Status\n(associates)", "Gender\n(men)", "Practice\n(corporate)", "Office\n(Boston)"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 3.8))
    M = np.array([[dec[(dec.attribute == a) & (dec.subgroup == s) & (dec.layer == L)]["excess"].iloc[0] for L in LAYERS] for a, s in keep])
    Q = np.array([[dec[(dec.attribute == a) & (dec.subgroup == s) & (dec.layer == L)]["q_bh"].iloc[0] for L in LAYERS] for a, s in keep])
    im = axes[0].imshow(M, cmap="Blues", vmin=0, vmax=6)
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            axes[0].text(j, i, f"{M[i, j]:.1f}" + ("" if Q[i, j] < 0.05 else " (n.s.)"), ha="center", va="center", fontsize=9)
    axes[0].set_xticks(range(3), [l.capitalize() for l in LAYERS]); axes[0].set_yticks(range(4), labels)
    axes[0].set_title("Structural inequivalence by layer\n(personal-network profiles vs. shuffled labels; 1 = none)", fontsize=10)
    A = np.array([[ar[(ar.attribute == a) & (ar.layer == L)]["assortativity"].iloc[0] for L in LAYERS] for a, _ in keep])
    im2 = axes[1].imshow(A, cmap="Reds", vmin=-0.1, vmax=0.6)
    for i in range(A.shape[0]):
        for j in range(A.shape[1]):
            axes[1].text(j, i, f"{A[i, j]:.2f}", ha="center", va="center", fontsize=9)
    axes[1].set_xticks(range(3), [l.capitalize() for l in LAYERS]); axes[1].set_yticks(range(4), labels)
    axes[1].set_title("Assortativity by layer\n(who connects to whom; 0 = no preference)", fontsize=10)
    plt.tight_layout(); plt.savefig(FIGURES / "fig3_inequivalence_vs_assortativity.png", dpi=200); plt.close()


def fig4():
    s = pd.read_csv(RESULTS / "simulation_summary.csv")
    fig, ax = plt.subplots(figsize=(6.5, 3.8))
    ax.plot(s["delta"], s["flag_rate"], "o-", color="#1F3A5F", label="Flagged as different (p < 0.05)")
    ax.plot(s["delta"][s.delta > 0], s["work_layer_on_top"][s.delta > 0], "s--", color="#C44E52", label="Decomposition points to the work layer")
    ax.axhline(0.05, color="grey", lw=0.8, ls=":")
    ax.set_xlabel("Planted effect: relative increase in work-tie probability for subgroup A (0.5 = +50%)")
    ax.set_ylabel("Share of simulated populations"); ax.set_ylim(-0.02, 1.05)
    ax.set_title("Simulation: the index finds planted differences\nand stays at its nominal level when there are none", fontsize=10)
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    plt.tight_layout(); plt.savefig(FIGURES / "fig4_simulation_power.png", dpi=200); plt.close()


if __name__ == "__main__":
    fig3(); fig4()
    print("Saved figures/fig3_inequivalence_vs_assortativity.png and figures/fig4_simulation_power.png")
