"""Step 3: are the observed patterns more than chance? Two null models.

(a) Layer overlap. Each layer is rewired independently with degree-preserving edge
    swaps, so every lawyer keeps the number of contacts in each layer, but the layers
    lose any alignment with each other. If the observed multiplexity (contacts shared
    across layers) and excess closure are far above the rewired networks, overlapping
    social contexts are a real feature of the network, not a by-product of degrees.
(b) Mixing by subgroup. For each layer and attribute, the share of ties that stay
    within the same subgroup is compared with networks in which attribute labels are
    shuffled across lawyers (network fixed). Benjamini-Hochberg correction across tests.

Run:  python step3_null_models.py
"""
import numpy as np
import pandas as pd
import networkx as nx
from scipy.sparse import csr_matrix
from mlnlib import MultiLayerNetwork
from config import MLN_DIR, RESULTS, GROUPS, N_PERM, N_REWIRE, SEED
from step2_closure import bh, cross_layer_triangles


def layer_graphs(mln):
    gs = {}
    for _, r in mln.layers.iterrows():
        A = mln.get_layer_adjacency_matrix(r["layer"]).tocoo()
        g = nx.Graph(); g.add_nodes_from(range(mln.N))
        g.add_edges_from((int(i), int(j)) for i, j in zip(A.row, A.col) if i < j)
        gs[r["binary"]] = g
    return gs


def combine(gs, n):
    pairs = {}
    for b, g in gs.items():
        for i, j in g.edges():
            for a, c in ((i, j), (j, i)):
                pairs[(a, c)] = pairs.get((a, c), 0) | int(b)
    rows, cols, vals = zip(*[(i, j, v) for (i, j), v in pairs.items()])
    return csr_matrix((np.array(vals, dtype=np.int64), (rows, cols)), shape=(n, n))


def summary(mln_like):
    A = mln_like.A
    mult = np.array([bin(v).count("1") > 1 for v in A.data]).mean()
    ec = mln_like.get_excess_closure()
    _, xshare = cross_layer_triangles(A)
    return mult, np.nanmean(list(ec["excess_closure"].values())), xshare


def overlap_null(mln, rng):
    gs = layer_graphs(mln)
    obs = summary(mln)
    sims = []
    for k in range(N_REWIRE):
        rg = {}
        for b, g in gs.items():
            h = g.copy()
            m = h.number_of_edges()
            nx.double_edge_swap(h, nswap=3 * m, max_tries=100 * m, seed=int(rng.integers(1e9)))
            rg[b] = h
        null = MultiLayerNetwork(nodes=mln.nodes.copy(), edges=combine(rg, mln.N), layers=mln.layers)
        sims.append(summary(null))
        if (k + 1) % 100 == 0:
            print(f"  rewiring {k + 1}/{N_REWIRE}")
    sims = np.array(sims)
    rows = []
    for i, name in enumerate(["multiplexity (share of multi-layer ties)", "mean excess closure (mlnlib)", "share of cross-layer triangles"]):
        s = sims[:, i]
        rows.append({"measure": name, "observed": obs[i], "null_mean": s.mean(), "null_p05": np.quantile(s, 0.05),
                     "null_p95": np.quantile(s, 0.95), "z": (obs[i] - s.mean()) / s.std(ddof=1),
                     "p_upper": (np.sum(s >= obs[i]) + 1) / (len(s) + 1),
                     "p_lower": (np.sum(s <= obs[i]) + 1) / (len(s) + 1)})
    return pd.DataFrame(rows)


def mixing(mln, rng):
    rows = []
    for _, r in mln.layers.iterrows():
        A = mln.get_layer_adjacency_matrix(r["layer"]).tocoo()
        m = A.row < A.col
        i, j = A.row[m], A.col[m]
        for g in GROUPS:
            if g not in mln.nodes:
                continue
            lab = mln.nodes.sort_values("id")[g].values
            obs = np.mean(lab[i] == lab[j])
            perm = np.empty(N_PERM)
            for k in range(N_PERM):
                s = rng.permutation(lab)
                perm[k] = np.mean(s[i] == s[j])
            rows.append({"layer": r["label"], "attribute": g, "ties": int(m.sum()), "within_share": obs,
                         "null_mean": perm.mean(), "ratio": obs / perm.mean(),
                         "p_upper": (np.sum(perm >= obs) + 1) / (N_PERM + 1)})
    res = pd.DataFrame(rows)
    res["q_bh"] = bh(res["p_upper"])
    return res


def main():
    rng = np.random.default_rng(SEED)
    mln = MultiLayerNetwork(load_from_library=True, library_path=str(MLN_DIR))
    RESULTS.mkdir(exist_ok=True)
    mix = mixing(mln, rng)
    mix.to_csv(RESULTS / "mixing_by_subgroup.csv", index=False)
    print("Within-subgroup share of ties vs. shuffled labels:")
    print(mix.round(3).to_string(index=False))
    print(f"\nRewiring each layer {N_REWIRE} times (degree-preserving)...")
    ov = overlap_null(mln, rng)
    ov.to_csv(RESULTS / "layer_overlap_null.csv", index=False)
    print(ov.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
