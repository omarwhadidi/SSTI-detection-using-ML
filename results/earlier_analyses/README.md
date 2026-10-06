# Earlier analyses (20–30 September 2026)

These were produced by separate analysis scripts, not by the current notebook, so their protocols differ from the numbered folders. The main README's Results section refers to some of them.

| File | What it holds | Protocol |
|---|---|---|
| `learning_curve.csv` | AUC as the training set grows | XGBoost (500 trees, depth 6, learning rate 0.03, subsample 0.8), v1 features, grouped subsamples of an 80% pool, one fixed grouped 80/20 split (seed 42), 5 subsample seeds per point |
| `v1_vs_v2_raw.csv`, `v1_vs_v2_summary.csv` | Version 1 against version 2 features | XGBoost (as above) and Random Forest (400 trees, depth 20), grouped 80/20 splits with seeds 0 to 4, cutoff 0.5. `hardneg_auc` scores attacks against hard negatives only, holdout rows only |
| `hard_negative_errors.csv` | Which benign rows XGBoost falsely flags on the external set | XGBoost, v1 features, cutoff 0.5 |
| `baseline_comparison.csv` | 17 features against a character n-gram baseline | One grouped 80/20 split (seed 42); TF-IDF over character 2 to 4-grams with logistic regression, vectorizer fitted on training rows only |
| `threshold_selection.csv` | XGBoost and Random Forest at cutoff 0.5 and a chosen cutoff | An earlier notebook version; cutoff from 5-fold grouped out-of-fold scores at a 5% false-alarm target |
| `notebook_random_split.csv` | All 7 models on the Part 1 random split, once with v1 and once with v2 features | 6 October 2026, Python 3.11 in the cloud, scikit-learn 1.6.1 |

`hard_negative_errors.csv`, `baseline_comparison.csv` and `threshold_selection.csv` were copied from tables in the main README, because the original runs were not saved as files. The scripts behind `learning_curve.csv`, `v1_vs_v2_*.csv` and `baseline_comparison.csv` are not in this repository.
