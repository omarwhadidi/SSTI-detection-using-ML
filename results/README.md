# Results

This folder keeps the raw numbers behind every result reported in the main README, so they can be compared with future runs. The main README gives the interpretation; this folder gives the data and the exact protocol.

Every number here is provisional. Each block comes from a single machine, most use 5 splits or seeds, and the external test set has only 47 positives. Do not compare numbers across blocks without reading the protocol column, because the blocks differ in split, hyperparameters, threshold and number of runs.

## Index

| File | What it holds | Main README block |
|---|---|---|
| `learning_curve.csv` | AUC as the training set grows, 5 seeds per point | 1 |
| `threshold_selection.csv` | Precision, recall and F1 at cutoff 0.5 and at a cutoff chosen from training data | 2 |
| `v1_vs_v2_raw.csv`, `v1_vs_v2_summary.csv` | Version 1 against version 2 features, per split and averaged | 3 |
| `hard_negative_errors.csv` | Which benign rows the model falsely flags | 4 |
| `baseline_comparison.csv` | 17 features against a character n-gram baseline | 5 |
| `dl_multiseed_raw.csv`, `dl_multiseed_summary.csv` | RNN, LSTM and CNN-LSTM over 5 seeds | 6 |
| `notebook_random_split.csv`, `notebook_threshold.csv`, `notebook_grouped.csv`, `notebook_grouped_candidates.csv` | Every reading from `Model_evaluation.ipynb`, run once with v1 and once with v2 features | 2, and the notebook |

## Protocol for each block

| Block | Model and hyperparameters | Training data | Split | Runs | Cutoff |
|---|---|---|---|---|---|
| 1 | XGBoost, 500 trees, depth 6, learning rate 0.03, subsample 0.8 | v1 features, grouped subsamples of an 80% pool | one fixed grouped 80/20 split (seed 42) | 5 subsample seeds per point | 0.5 for recall and precision columns |
| 2 | XGBoost and Random Forest from the notebook's own training functions (random hyperparameter search) | v2 features, the random 80% split from the first cells of `Model_evaluation.ipynb` | external set | 1 | 0.5, and a cutoff from 5-fold grouped out-of-fold scores on training data at a 5% false-alarm target |
| 3 | XGBoost (as block 1) and Random Forest (400 trees, depth 20) | v1 and v2 features | grouped 80/20, seeds 0 to 4 | 5 | 0.5 |
| 4 | XGBoost, v1 features | full training data | as stated in the main README | see README | 0.5 |
| 5 | XGBoost (as block 1) and TF-IDF over character 2 to 4-grams with logistic regression | v1 features or raw text | one grouped 80/20 split (seed 42); vectorizer fitted on training rows only | 1 | AUC only |
| 6 | Character-level RNN, LSTM and CNN-LSTM from `deep_learning/dl_models.ipynb`, sequence length 96 | raw payload text | grouped, 10% of training rows held out for validation, 5 seeds (0 to 4) | 5 | chosen on validation rows at a 5% false-positive rate |

The main reason one algorithm shows several numbers is this table. Blocks 1, 3 and 5 use a fixed XGBoost configuration, block 2 uses a tuned one, and the cutoff and the number of runs also differ.

## Notebook readings, v1 against v2 (6 October 2026)

`model_evaluation/Model_evaluation.ipynb` was run end to end twice, once with `FEATURE_VERSION = 'v1'` and once with `'v2'` in cell 4. That switch now controls every section of the notebook. Both runs used Python 3.11, scikit-learn 1.6.1 and XGBoost 3.2.0. Every file has a `feature_version` column.

| File | Notebook cells | What it holds |
|---|---|---|
| `notebook_random_split.csv` | 1 to 8 | All 7 models on the random, ungrouped 80/20 split (seed 15), 782 test rows. Leaky by design; kept as the original baseline |
| `notebook_threshold.csv` | 10 | XGBoost and Random Forest at cutoff 0.5 and at a cutoff chosen from grouped out-of-fold training scores (5% false-alarm target), on the 782 test rows and the external set |
| `notebook_grouped.csv` | 11 to 20 | All 7 models on one grouped split (outer fold 2 of `StratifiedGroupKFold`, 744 holdout rows) and on the external set |
| `notebook_grouped_candidates.csv` | 13 to 19 | Inner grouped CV macro-F1 for each model under both preprocessing options, and which one was selected |

Each reading is a single run. Running the same notebook on a different machine (Windows, Python 3.13, the same library versions) gave identical numbers for most models but small differences for XGBoost and KNN: up to 2 false alarms, a different chosen cutoff (0.839 against 0.821), and in the grouped section a different preprocessing choice where the two options tied to the third decimal. Differences of that size are not meaningful.

## Notes on specific files

**`dl_multiseed_*.csv`** were produced on 30 September 2026 with TensorFlow 2.21 on CPU by running the multi-seed cell of `dl_models.ipynb` unchanged. An earlier run of the same cell on 23 September gave identical RNN numbers but different LSTM and CNN-LSTM numbers: LSTM external AUC 0.961 against 0.948, and CNN-LSTM external standard deviation 0.005 against 0.011. So rerunning with the same seeds can move a result by about 0.01 AUC, and differences smaller than that should not be read as real. Both runs agree that CNN-LSTM has the highest external AUC.

**`threshold_selection.csv`, `hard_negative_errors.csv` and `baseline_comparison.csv`** are copied from the tables in the main README. They are single-run results and were not saved as files when they were produced, so they hold only the numbers shown there.

**`v1_vs_v2_raw.csv`** has one row per model, feature version, reading (holdout or external) and seed. `hardneg_auc` is filled only for holdout rows and scores attacks against hard negatives only.

## Reproducibility

The analysis scripts behind blocks 1, 3 and 5 were run ad hoc on 20 to 24 September 2026 and are not part of this repository. The notebooks reproduce blocks 2 and 6. Porting the other scripts here would make every block reproducible from the repository.
