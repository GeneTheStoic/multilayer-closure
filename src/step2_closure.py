"""Step 2: node-level multilayer measures and how they differ between subgroups.

For each lawyer: degree (any layer), multiplexity (share of contacts linked in two or
more layers), local clustering, and excess closure (Bokanyi et al., 2023; computed with
mlnlib), the measure used for the Dutch population-scale network: closure that comes
from triangles spanning different layers, net of what single-layer clustering gives.

Subgroups (partners vs. associates, offices, practice, gender) are compared on each
measure. Uncertainty: 90% bootstrap interval of the difference in means (resampling
lawyers). Significance: label-permutation test, with Benjamini-Hochberg correction
across all comparisons.

Note: mlnlib's clustering counts multi-layer triangles with their multiplicity, so in a small,
dense network it can exceed 1; plain clustering on the aggregated network and a bounded share of\ncross-layer triangles (closed only by combining different layers) are reported alongside.

Run:  python step2_closure.py
"""
import networkx as nx
import numpy as np
import pandas as pd
from mlnlib import MultiLayerNetwork
from config import MLN_DIR, RESULTS, GROUPS, N_PERM, N_BOOT, SEED


def bh(p):
    p = np.asarray(p, float); n = len(p); o = np.argsort(p)
    q = np.minimum.accumulate((p[o] * n / np.arange(1, n + 1))[::-1])[::-1]
    out = np.empty(n); out[o] = np.minimum(q, 1); return out


def cross_layer_triangles(A):
    """For each node: share of its closed triangles (any layer) that no single layer closes.

    A triangle i-j-k is 'single-layer' if one layer is present on all three ties
    (bitwise AND of the three layer codes is non-zero); otherwise it is closed only by
    combining different contexts. The share is bounded in [0, 1], which makes it usable
    in small, dense networks where the multiplicity-weighted measure exceeds 1.
    Also returns the network-level share over all triangles.
    """
    A = A.tolil(); n = A.shape[0]
    nbr = [dict(zip(A.rows[i], A.data[i])) for i in range(n)]
    tot = np.zeros(n); cross = np.zeros(n); T = X = 0
    for i in range(n):
        ni = sorted(nbr[i])
        for a in range(len(ni)):
            j = ni[a]
            for b in range(a + 1, len(ni)):
                k = ni[b]
                if k in nbr[j]:
                    c = (nbr[i][j] & nbr[i][k] & nbr[j][k]) == 0
                    tot[i] += 1; cross[i] += c
                    if i < j < k:
                        T += 1; X += c
    share = np.divide(cross, tot, out=np.full(n, np.nan), where=tot > 0)
    return share, X / T if T else np.nan


def node_measures(mln):
    A = mln.A.copy(); A.eliminate_zeros()
    deg = np.diff(A.indptr)
    multiplex = np.array([bin(v).count("1") > 1 for v in A.data])
    mshare = np.array([multiplex[A.indptr[i]:A.indptr[i + 1]].mean() if deg[i] else np.nan for i in range(mln.N)])
    ec = mln.get_excess_closure()
    lab = mln.nodes["label"].tolist()
    df = mln.nodes.copy()
    df["degree"] = deg
    df["multiplexity"] = mshare
    df["clustering"] = [ec["clustering_coefficient"].get(l, np.nan) for l in lab]
    df["excess_closure"] = [ec["excess_closure"].get(l, np.nan) for l in lab]
    # plain clustering on the aggregated (any-layer) network, bounded in [0, 1], as a reference
    agg = nx.from_scipy_sparse_array((A > 0).astype(int))
    cb = nx.clustering(agg)
    df["clustering_aggregate"] = [cb[i] for i in range(mln.N)]
    share, _ = cross_layer_triangles(mln.A)
    df["cross_layer_triangle_share"] = share
    return df


def compare(df, group, measure, rng):
    d = df[[group, measure]].dropna()
    levels = sorted(d[group].unique())
    rows = []
    x = d[measure].values; g = d[group].values
    for a in levels:
        ina = g == a
        if ina.sum() < 3 or (~ina).sum() < 3:
            continue
        obs = x[ina].mean() - x[~ina].mean()
        perm = np.empty(N_PERM)
        for k in range(N_PERM):
            s = rng.permutation(ina)
            perm[k] = x[s].mean() - x[~s].mean()
        p = (np.sum(np.abs(perm) >= abs(obs)) + 1) / (N_PERM + 1)
        boot = np.empty(N_BOOT)
        ia, ib = np.where(ina)[0], np.where(~ina)[0]
        for k in range(N_BOOT):
            boot[k] = x[rng.choice(ia, len(ia))].mean() - x[rng.choice(ib, len(ib))].mean()
        rows.append({"grouping": group, "subgroup": a, "measure": measure, "n": int(ina.sum()),
                     "mean_subgroup": x[ina].mean(), "mean_rest": x[~ina].mean(), "difference": obs,
                     "ci05": np.quantile(boot, 0.05), "ci95": np.quantile(boot, 0.95), "p_perm": p})
        if len(levels) == 2:
            break   # two groups: one comparison is enough
    return rows


def main():
    rng = np.random.default_rng(SEED)
    mln = MultiLayerNetwork(load_from_library=True, library_path=str(MLN_DIR))
    df = node_measures(mln)
    RESULTS.mkdir(exist_ok=True)
    df.to_csv(RESULTS / "node_measures.csv", index=False)
    print("Network averages:")
    print(df[["degree", "multiplexity", "clustering_aggregate", "clustering", "excess_closure", "cross_layer_triangle_share"]].mean().round(3).to_string())
    rows = []
    for g in GROUPS:
        if g in df:
            for m in ["degree", "multiplexity", "clustering_aggregate", "excess_closure", "cross_layer_triangle_share"]:
                rows += compare(df, g, m, rng)
    res = pd.DataFrame(rows)
    res["q_bh"] = bh(res["p_perm"])
    res.to_csv(RESULTS / "subgroup_differences.csv", index=False)
    print("\nSubgroup differences (subgroup minus rest), 90% bootstrap interval, permutation p, BH q:")
    print(res.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
