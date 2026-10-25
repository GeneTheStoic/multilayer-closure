"""Step 5: how different is the network structure of each subgroup, and which layer drives it?

(a) Node profiles: degree in each layer, multiplexity, aggregate clustering, cross-layer
    triangle share (from step 2).
(b) Inequivalence index (energy distance on standardized profiles) for each subgroup vs.
    the rest, relative to a label-permutation null; Benjamini-Hochberg across subgroups.
(c) Layer decomposition: the index on the features of one layer at a time (degree and
    clustering within that layer).
(d) Network-level segregation: attribute assortativity per layer (as used for income
    segregation in the Dutch population-scale network, Kazmina et al., 2024), with a
    label-permutation null.

Run:  python step5_structural_inequivalence.py
"""
import networkx as nx
import numpy as np
import pandas as pd
from mlnlib import MultiLayerNetwork
from config import MLN_DIR, RESULTS, GROUPS, SEED
from inequivalence import inequivalence
from step2_closure import bh

N_PERM_INEQ = 5000


def layer_features(mln):
    feats = {}
    for _, r in mln.layers.iterrows():
        A = mln.get_layer_adjacency_matrix(r["layer"])
        g = nx.from_scipy_sparse_array((A > 0).astype(int))
        cl = nx.clustering(g)
        feats[f"degree_{r['label']}"] = np.asarray((A > 0).sum(axis=1)).ravel()
        feats[f"clustering_{r['label']}"] = np.array([cl[i] for i in range(mln.N)])
    return pd.DataFrame(feats)


def main():
    rng = np.random.default_rng(SEED)
    mln = MultiLayerNetwork(load_from_library=True, library_path=str(MLN_DIR))
    nodes = pd.read_csv(RESULTS / "node_measures.csv").sort_values("id").reset_index(drop=True)
    lf = layer_features(mln)
    profile_cols = [c for c in lf if c.startswith("degree_")] + ["multiplexity", "clustering_aggregate", "cross_layer_triangle_share"]
    prof = pd.concat([lf, nodes[["multiplexity", "clustering_aggregate", "cross_layer_triangle_share"]]], axis=1).fillna(0)
    layers = mln.layers["label"].tolist()

    rows, dec = [], []
    for g in GROUPS:
        lab = nodes[g].values
        levels = sorted(pd.unique(lab))
        for a in levels:
            mask = lab == a
            if mask.sum() < 3 or (~mask).sum() < 3:
                continue
            res = inequivalence(prof[profile_cols].values, mask, N_PERM_INEQ, rng)
            rows.append({"attribute": g, "subgroup": a, "n": int(mask.sum()), **res})
            for L in layers:
                rL = inequivalence(lf[[f"degree_{L}", f"clustering_{L}"]].values, mask, 2000, rng)
                dec.append({"attribute": g, "subgroup": a, "layer": L, "excess": rL["excess"], "p_perm": rL["p_perm"]})
            if len(levels) == 2:
                break
    res = pd.DataFrame(rows); res["q_bh"] = bh(res["p_perm"])
    res.to_csv(RESULTS / "structural_inequivalence.csv", index=False)
    dec = pd.DataFrame(dec); dec["q_bh"] = bh(dec["p_perm"])
    dec.to_csv(RESULTS / "structural_inequivalence_by_layer.csv", index=False)
    print("Structural inequivalence (subgroup vs. rest; excess = observed / shuffled-label mean):")
    print(res.round(3).to_string(index=False))
    print("\nBy layer:")
    print(dec.round(3).to_string(index=False))

    # assortativity per layer
    arows = []
    for _, r in mln.layers.iterrows():
        A = mln.get_layer_adjacency_matrix(r["layer"])
        g = nx.from_scipy_sparse_array((A > 0).astype(int))
        for att in GROUPS:
            lab = nodes[att].astype(str).values
            nx.set_node_attributes(g, {i: lab[i] for i in range(mln.N)}, att)
            obs = nx.attribute_assortativity_coefficient(g, att)
            null = []
            for _ in range(1000):
                p = rng.permutation(lab)
                nx.set_node_attributes(g, {i: p[i] for i in range(mln.N)}, "perm")
                null.append(nx.attribute_assortativity_coefficient(g, "perm"))
            null = np.array(null)
            arows.append({"layer": r["label"], "attribute": att, "assortativity": obs, "null_p95": np.quantile(null, 0.95),
                          "p_upper": (np.sum(null >= obs) + 1) / (len(null) + 1)})
    ar = pd.DataFrame(arows); ar["q_bh"] = bh(ar["p_upper"])
    ar.to_csv(RESULTS / "assortativity_by_layer.csv", index=False)
    print("\nAttribute assortativity by layer:")
    print(ar.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
