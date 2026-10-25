"""Step 1: read the Lazega law firm network and store it as an mlnlib multilayer network.

Layers (advice, friendship, coworker) are symmetrized: two lawyers are linked in a layer
if either one names the other. Each node pair stores its layers in one integer
(binary encoding, as in mlnlib and the Dutch population-scale network).

Run:  python step1_build_mln.py
"""
import io
import zipfile
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from mlnlib import MultiLayerNetwork
from config import RAW_ZIP, MLN_DIR, LAYER_LABELS


def read_zip(path):
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        edges = pd.read_csv(io.BytesIO(z.read([n for n in names if n.endswith("edges.csv")][0])))
        nodes = pd.read_csv(io.BytesIO(z.read([n for n in names if n.endswith("nodes.csv")][0])))
    edges.columns = [c.strip("# ").strip() for c in edges.columns]
    nodes.columns = [c.strip("# ").strip() for c in nodes.columns]
    return nodes, edges


def clean_nodes(nodes):
    out = pd.DataFrame({"label": nodes["index"].astype(int)})
    rename = {"nodeStatus": "status", "nodeGender": "gender", "nodeOffice": "office", "nodeSeniority": "seniority",
              "nodeAge": "age", "nodePractice": "practice", "nodeLawSchool": "law_school"}
    for raw, new in rename.items():
        if raw in nodes.columns:
            out[new] = nodes[raw].values
    maps = {"status": {1: "partner", 2: "associate"}, "gender": {1: "man", 2: "woman"},
            "office": {1: "Boston", 2: "Hartford", 3: "Providence"}, "practice": {1: "litigation", 2: "corporate"}}
    for col, m in maps.items():
        if col in out:
            out[col] = out[col].map(lambda v: m.get(int(v), str(v)))
    out["id"] = np.arange(len(out))
    return out


def build(nodes, edges):
    layer_col = "layer"
    codes = sorted(edges[layer_col].unique())
    layers = pd.DataFrame({"layer": list(range(len(codes))),
                           "label": [LAYER_LABELS.get(int(c), f"layer_{c}") for c in codes],
                           "binary": [2 ** i for i in range(len(codes))],
                           "group": [LAYER_LABELS.get(int(c), f"layer_{c}") for c in codes]})
    code_to_bin = dict(zip(codes, layers["binary"]))
    idx = dict(zip(nodes["label"], nodes["id"]))
    s = edges["source"].map(idx).values
    t = edges["target"].map(idx).values
    b = edges[layer_col].map(code_to_bin).values
    keep = s != t
    s, t, b = s[keep], t[keep], b[keep]
    # symmetrize and combine layers with bitwise OR
    pairs = {}
    for i, j, v in zip(np.r_[s, t], np.r_[t, s], np.r_[b, b]):
        pairs[(i, j)] = pairs.get((i, j), 0) | int(v)
    rows, cols, vals = zip(*[(i, j, v) for (i, j), v in pairs.items()])
    n = len(nodes)
    A = csr_matrix((np.array(vals, dtype=np.int64), (rows, cols)), shape=(n, n))
    return MultiLayerNetwork(nodes=nodes, edges=A, layers=layers), layers


def main():
    raw_nodes, raw_edges = read_zip(RAW_ZIP)
    nodes = clean_nodes(raw_nodes)
    mln, layers = build(nodes, raw_edges)
    MLN_DIR.mkdir(parents=True, exist_ok=True)
    mln.save(str(MLN_DIR), overwrite=True)
    print(f"{mln.N} lawyers, {len(layers)} layers: {', '.join(layers['label'])}")
    for _, r in layers.iterrows():
        A = mln.get_layer_adjacency_matrix(r["layer"])
        print(f"  {r['label']}: {A.nnz // 2} undirected ties")
    print(f"Saved mlnlib network to {MLN_DIR}")


if __name__ == "__main__":
    main()
