# Multilayer closure and subgroup structure in a social network

A small, reproducible study of how social contexts overlap in a multilayer network and how network structure differs between subgroups, tested against null models. It uses **mlnlib**, the library developed for the Dutch population-scale network, and its **excess closure** measure, on a public multiplex network: the Lazega law firm.

## Questions

1. Do social contexts (advice, friendship, coworking) overlap more than each layer's degrees would imply?
2. Which attributes (status, office, practice, gender) organize which layer?
3. Does the structure of personal networks differ between subgroups, and is the difference larger than chance?

## Data

- **Source:** Lazega law firm network (Lazega, 2001), from the Netzschleuder catalogue (`law_firm`, data hosted by Manlio De Domenico). File: `data/raw/network.csv.zip`.
- **Network:** 71 lawyers of a corporate law firm in New England, three layers. Directed nominations are symmetrized (a tie exists if either lawyer names the other): **advice 717, friendship 399, coworker 726** undirected ties.
- **Attributes:** status (36 partners, 35 associates), office (Boston 48, Hartford 19, Providence 4), practice (litigation 41, corporate 30), gender (53 men, 18 women).

## Method

1. **Multilayer network in mlnlib.** Each pair of lawyers stores its layers in one integer (binary encoding), the same format used for the population-scale network of the Netherlands.
2. **Node measures.** Degree (any layer); multiplexity (share of a lawyer's contacts linked in two or more layers); clustering on the aggregated network; **excess closure** (Bokányi et al., 2023, as implemented in mlnlib); and a bounded **cross-layer triangle share**: the share of a lawyer's closed triangles that no single layer closes on its own.
3. **Subgroup comparisons.** Difference in means for every subgroup and measure, with a 90% bootstrap interval (2,000 resamples of lawyers), a label-permutation test (10,000 permutations), and Benjamini–Hochberg correction across all comparisons.
4. **Null models.**
   - *Mixing:* the share of ties within the same subgroup, compared with networks in which attribute labels are shuffled (10,000 times, network fixed).
   - *Layer overlap:* each layer is rewired independently with degree-preserving edge swaps (500 times), so every lawyer keeps its number of contacts in each layer but the layers lose their alignment.

## Results

**Social contexts overlap far more than chance.** 60% of ties are multiplex, against 32% when layers are rewired independently (z = 28.7); mean excess closure is 1.34 against 0.98. Because the same people meet across advice, friendship, and work, most triangles close within a single layer: only 24% of triangles need more than one layer to close, against 62% if layers were independent.

| Measure | Observed | Rewired layers (mean, 90% range) |
|---|---|---|
| Multiplex ties | 0.60 | 0.32 (0.31–0.34) |
| Excess closure (mlnlib) | 1.34 | 0.98 (0.97–0.99) |
| Cross-layer triangle share | 0.24 | 0.62 (0.61–0.64) |

**Status organizes friendship, not work.** Friendship ties stay within the same status 1.56 times as often as with shuffled labels, while coworker ties show no status preference (1.01, not significant). Office organizes all three layers (1.44–1.61 times), and practice organizes advice and coworking (1.46) more than friendship (1.21).

![Mixing by layer](figures/fig1_mixing_by_layer.png)

**Associates have smaller, more closed personal networks.** Associates have fewer contacts than partners (24.8 vs. 31.9; q = 0.02), a lower share of multiplex ties (0.55 vs. 0.63; q = 0.08), and higher clustering (0.60 vs. 0.55; q = 0.08). Partners' ties are more numerous and span more contexts at once. Office size also matters: lawyers in Boston, the largest office, have more contacts (q = 0.05).

![Partners vs associates](figures/fig2_partners_vs_associates.png)

**A note on the measure.** In this small, dense network the multiplicity-weighted clustering in mlnlib exceeds 1 (mean 1.26), so excess closure also exceeds 1. The measure was designed for large, sparse register networks; in dense networks it remains useful for comparisons against a null model, and the bounded cross-layer triangle share gives a complementary reading on a 0–1 scale.

## Limitations

- One firm of 71 lawyers, observed once: the results describe this network, not law firms in general.
- Symmetrizing nominations discards direction, which matters for advice (who asks whom).
- Providence has only 4 lawyers, so its comparisons have little power.
- The rewiring null keeps each lawyer's degree in each layer but nothing else (for example, office composition), so part of the overlap may reflect shared offices.

## What this suggests for population-scale networks

Comparing subgroups layer by layer, against null models that keep each layer's degrees, separates two questions that raw differences mix: whether a group has more contacts, and whether its contacts are organized differently. The same design scales to subgroup and cross-country comparisons in register-based networks, where the layers (family, household, work, school, neighbors) are fixed by definition and the question is how they combine.

## Reproduce

```bash
pip install -r requirements.txt
cd src
python step1_build_mln.py      # builds the mlnlib network from data/raw/network.csv.zip
python step2_closure.py        # node measures and subgroup comparisons
python step3_null_models.py    # mixing and layer-overlap null models (about 2 minutes)
python step4_figures.py
```

## References

- Benjamini, Y., and Hochberg, Y. (1995). Controlling the false discovery rate: a practical and powerful approach to multiple testing. *Journal of the Royal Statistical Society: Series B*, 57(1), 289–300.
- Bokányi, E., Heemskerk, E. M., and Takes, F. W. (2023). The anatomy of a population-scale social network. *Scientific Reports*, 13, 9209.
- Bokányi, E., Kazmina, Y., Heemskerk, E. M., and Takes, F. W. (2026). Fragmentation of a longitudinal population-scale social network: Decreasing network closure in the Netherlands. arXiv:2602.00234.
- Lazega, E. (2001). *The Collegial Phenomenon: The Social Mechanisms of Cooperation Among Peers in a Corporate Law Partnership*. Oxford University Press.
- mlnlib: https://github.com/planet-nl/mlnlib

Author: Eugenio Guilarte Homayden
