"""Synthetic register-like multilayer population for simulation studies.

Layers mimic the structure of register networks: households (complete), extended family
(links between members of related households), workplaces, and neighborhoods. A share of
the population belongs to subgroup A. The planted effect `delta` raises the tie
probability inside workplaces for members of A (their work networks become denser and
more closed); delta = 0 means no structural difference between groups.
"""
import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix
from mlnlib import MultiLayerNetwork

LAYERS = ["household", "family", "work", "neighbor"]


def _block_pairs(members, p, rng):
    m = len(members)
    if m < 2:
        return np.empty((0, 2), int)
    i, j = np.triu_indices(m, 1)
    keep = rng.random(len(i)) < (p if np.isscalar(p) else p[i, j])
    return np.c_[members[i[keep]], members[j[keep]]]


def generate(n, share_a=0.3, delta=0.0, seed=0):
    rng = np.random.default_rng(seed)
    group_a = rng.random(n) < share_a
    pairs = {}
    # households of size 1-4
    sizes = rng.choice([1, 2, 3, 4], size=n, p=[0.35, 0.3, 0.15, 0.2])
    hh = np.repeat(np.arange(n), sizes)[:n]
    hh_members = pd.Series(np.arange(n)).groupby(hh).apply(np.array)
    pairs["household"] = np.vstack([_block_pairs(m, 1.0, rng) for m in hh_members])
    # extended family: clusters of 3 households, ties with probability 0.4
    fam_id = hh // 3
    fam = pd.Series(np.arange(n)).groupby(fam_id).apply(np.array)
    fp = [_block_pairs(m, 0.4, rng) for m in fam]
    fp = np.vstack(fp)
    pairs["family"] = fp[hh[fp[:, 0]] != hh[fp[:, 1]]]
    # workplaces: 70% employed, workplaces of about 25 people
    employed = np.where(rng.random(n) < 0.7)[0]
    wp = rng.integers(0, max(1, len(employed) // 25), len(employed))
    wpp = []
    for w in np.unique(wp):
        m = employed[wp == w]
        a = group_a[m]
        base = 0.15
        P = np.full((len(m), len(m)), base)
        P[np.ix_(a, a)] = min(1.0, base * (1 + delta))          # denser among A colleagues
        P[np.ix_(a, ~a)] = P[np.ix_(~a, a)] = min(1.0, base * (1 + delta / 2))
        wpp.append(_block_pairs(m, P, rng))
    pairs["work"] = np.vstack(wpp)
    # neighborhoods: blocks of about 60 consecutive households' members, ties with probability 0.05
    nb = hh // 25
    nbm = pd.Series(np.arange(n)).groupby(nb).apply(np.array)
    pairs["neighbor"] = np.vstack([_block_pairs(m, 0.05, rng) for m in nbm])
    # combine into an mlnlib network (binary layer encoding, symmetric)
    rows, cols, vals = [], [], []
    for k, L in enumerate(LAYERS):
        p = pairs[L]
        rows += [p[:, 0], p[:, 1]]; cols += [p[:, 1], p[:, 0]]; vals += [np.full(len(p) * 2, 2 ** k)]
    r, c, v = np.concatenate(rows), np.concatenate(cols), np.concatenate(vals)
    A = coo_matrix((v, (r, c)), shape=(n, n)).tocsr()
    nodes = pd.DataFrame({"label": np.arange(n), "id": np.arange(n), "group": np.where(group_a, "A", "B")})
    layers = pd.DataFrame({"layer": range(4), "label": LAYERS, "binary": [1, 2, 4, 8], "group": LAYERS})
    return MultiLayerNetwork(nodes=nodes, edges=A, layers=layers), group_a
