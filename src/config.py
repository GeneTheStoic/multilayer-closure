from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW_ZIP = ROOT / "data" / "raw" / "network.csv.zip"    # Netzschleuder export of the Lazega law firm network (law_firm)
MLN_DIR = ROOT / "data" / "mln"                        # mlnlib library folder (edges.npz, nodes.csv.gz, layers.csv)
RESULTS = ROOT / "results"
FIGURES = ROOT / "figures"
LAYER_LABELS = {1: "advice", 2: "friendship", 3: "coworker"}   # layer codes in the Netzschleuder file
GROUPS = ["status", "office", "practice", "gender"]
N_PERM = 10000      # label permutations for subgroup tests
N_REWIRE = 500      # degree-preserving rewirings per layer for the closure null model
N_BOOT = 2000       # bootstrap resamples of nodes
SEED = 42
