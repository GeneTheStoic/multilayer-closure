"""Step 6: does the inequivalence index find a planted difference, and does it scale?

(a) Validation by simulation. Synthetic register-like populations (households, family,
    work, neighbors; 30% in subgroup A). A planted effect makes A's work networks denser
    and more closed. For each effect size we generate many populations and record how often
    the index flags A as structurally different (p < 0.05), and which layer the
    decomposition points to. With no planted effect, the flag rate is the false-positive rate.
(b) Scaling. Runtime of the pipeline (generation, mlnlib excess closure on sampled egos,
    inequivalence on a sample) for populations of 10,000 and 100,000 people.

Run:  python step6_simulation.py            (both parts, about 6 minutes)
      python step6_simulation.py validation | scaling
      python step6_simulation.py validation 0.5   (one effect size at a time)
"""
import time
import networkx as nx
import numpy as np
import pandas as pd
from config import RESULTS, SEED
from synthetic import generate, LAYERS
from inequivalence import inequivalence

N_SIM = 1000           # people per simulated population
REPS = {0.0: 100, 0.1: 30, 0.25: 30, 0.5: 30, 1.0: 30}
N_PERM = 99


def profiles(mln, egos=None):
    """Degree and clustering per layer, plus multiplexity, for all nodes or a sample of egos."""
    n = mln.N
    idx = np.arange(n) if egos is None else egos
    out = {}
    for k, L in enumerate(LAYERS):
        A = mln.get_layer_adjacency_matrix(k)
        out[f"degree_{L}"] = np.asarray(A[idx].sum(axis=1)).ravel()
        if egos is None:
            cl = nx.clustering(nx.from_scipy_sparse_array(A))
            out[f"clustering_{L}"] = np.array([cl[i] for i in idx])
    A = mln.A
    mult = np.array([np.mean([bin(v).count("1") > 1 for v in A.data[A.indptr[i]:A.indptr[i + 1]]]) if A.indptr[i + 1] > A.indptr[i] else 0 for i in idx])
    out["multiplexity"] = mult
    return pd.DataFrame(out)


def validation(rng, only=None):
    rows = []
    for delta, reps in REPS.items():
        if only is not None and delta != only:
            continue
        for r in range(reps):
            mln, a = generate(N_SIM, delta=delta, seed=int(rng.integers(1e9)))
            P = profiles(mln)
            res = inequivalence(P.values, a, N_PERM, rng)
            top = ""
            if delta > 0:
                by_layer = {L: inequivalence(P[[f"degree_{L}", f"clustering_{L}"]].values, a, N_PERM, rng)["excess"] for L in LAYERS}
                top = max(by_layer, key=by_layer.get)
            rows.append({"delta": delta, "rep": r, "excess": res["excess"], "p": res["p_perm"], "top_layer": top})
        d = pd.DataFrame([x for x in rows if x["delta"] == delta])
        print(f"  delta={delta}: flagged {np.mean(d.p < 0.05):.2f}, median excess {d.excess.median():.2f}, work layer on top {np.mean(d.top_layer == 'work'):.2f}", flush=True)
    sims = pd.DataFrame(rows)
    f = RESULTS / "simulation_runs.csv"
    if only is not None and f.exists():          # run one effect size at a time and accumulate
        old = pd.read_csv(f, keep_default_na=False)
        sims = pd.concat([old[old["delta"] != only], sims], ignore_index=True)
    sims.to_csv(f, index=False)
    summ = sims.groupby("delta").agg(runs=("p", "size"), flag_rate=("p", lambda p: np.mean(p < 0.05)),
                                     median_excess=("excess", "median"),
                                     work_layer_on_top=("top_layer", lambda t: np.mean(t == "work"))).reset_index()
    summ.to_csv(RESULTS / "simulation_summary.csv", index=False)
    return summ


def scaling(rng, sizes=(10_000, 100_000)):
    rows = []
    for n in sizes:
        t0 = time.time(); mln, a = generate(n, delta=0.5, seed=SEED); t1 = time.time()
        egos = rng.choice(n, 5000, replace=False)
        ec = mln.get_excess_closure(selected_nodes=list(egos), node_type="id"); t2 = time.time()
        sample = rng.choice(n, 2000, replace=False)
        P = profiles(mln, egos=sample)
        res = inequivalence(P.values, a[sample], N_PERM, rng); t3 = time.time()
        rows.append({"people": n, "ties": mln.A.nnz // 2, "generate_s": round(t1 - t0, 1),
                     "excess_closure_5000_egos_s": round(t2 - t1, 1), "inequivalence_2000_sample_s": round(t3 - t2, 1),
                     "sample_excess": round(res["excess"], 2), "sample_p": res["p_perm"]})
        print(f"  {n:,} people: {rows[-1]}")
    sc = pd.DataFrame(rows)
    f = RESULTS / "scaling.csv"
    if f.exists():
        old = pd.read_csv(f)
        sc = pd.concat([old[~old["people"].isin(sizes)], sc], ignore_index=True).sort_values("people")
    sc.to_csv(f, index=False)
    return sc


if __name__ == "__main__":
    import sys
    part = sys.argv[1] if len(sys.argv) > 1 else "all"
    rng = np.random.default_rng(SEED)
    if part in ("all", "validation"):
        only = float(sys.argv[2]) if len(sys.argv) > 2 else None
        if only is not None:
            rng = np.random.default_rng(SEED + int(only * 100))
        print("Validation by simulation (population of 1,000; 30% in subgroup A):")
        print(validation(rng, only).round(3).to_string(index=False))
    if part in ("all", "scaling"):
        sizes = (int(sys.argv[2]),) if part == "scaling" and len(sys.argv) > 2 else (10_000, 100_000)
        print("\nScaling:")
        print(scaling(rng, sizes).to_string(index=False))
