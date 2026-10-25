"""Structural (in)equivalence between subgroups of a multilayer network.

Each node is described by a multilayer profile: its degree in every layer, multiplexity,
aggregate clustering, and the share of cross-layer triangles. Two subgroups are
structurally equivalent if their profile distributions are the same.

Index: multivariate energy distance between the profile distributions of a subgroup and
the rest (Szekely and Rizzo, 2013), on standardized profiles. It is zero only if the two
distributions are identical. Its scale depends on group sizes, so we report it relative to
a label-permutation null: excess = observed / mean under shuffled labels (1 = no difference).
Layer decomposition: the same index computed on the features of one layer at a time.
"""
import numpy as np
from scipy.spatial.distance import cdist


def energy_from_D(D, mask):
    a, b = np.where(mask)[0], np.where(~mask)[0]
    return 2 * D[np.ix_(a, b)].mean() - D[np.ix_(a, a)].mean() - D[np.ix_(b, b)].mean()


def inequivalence(X, mask, n_perm, rng):
    """Energy distance between X[mask] and X[~mask], with a label-permutation null."""
    Z = (X - X.mean(0)) / np.where(X.std(0) > 0, X.std(0), 1)
    D = cdist(Z, Z)
    obs = energy_from_D(D, mask)
    null = np.empty(n_perm)
    for k in range(n_perm):
        null[k] = energy_from_D(D, rng.permutation(mask))
    return {"energy": obs, "null_mean": null.mean(), "excess": obs / null.mean(),
            "p_perm": (np.sum(null >= obs) + 1) / (n_perm + 1)}
