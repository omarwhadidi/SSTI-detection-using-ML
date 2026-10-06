# Superseded readings

Readings from earlier versions of `Model_evaluation.ipynb`. The notebook has since been reorganised into Parts 1 to 4; use the numbered folders for current numbers. These files are kept so older notes and commits still make sense.

| File | Came from | Replaced by |
|---|---|---|
| `notebook_threshold.csv` | Old threshold cell: XGBoost and Random Forest, grouped out-of-fold cutoff, v1 and v2 features | `2_threshold_selection/` |
| `notebook_grouped.csv`, `notebook_grouped_candidates.csv` | Old grouped section: one `StratifiedGroupKFold` fold, two scaling options per model, v1 and v2 features | `3_grouped_evaluation/` |
| `notebook_threshold_random_split.csv` | Cloud run of an intermediate threshold version (best-F1 and 5%-false-alarm rules) | `2_threshold_selection/` |
| `notebook_grouped_comparison.csv` | Cloud run of an intermediate grouped version | `3_grouped_evaluation/` |
| `mechanism_recall.csv`, `mechanism_scores_raw.csv` | Cloud run of the mechanism experiment, grouped folds only | `4_attack_mechanisms/` |

The cloud runs used Python 3.11 on Linux. Most numbers match the current run on Windows exactly; XGBoost and KNN differ by a few rows because of platform differences.
