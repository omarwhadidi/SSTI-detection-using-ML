# Results

Raw numbers behind the results in the main README, organised in the same order as `model_evaluation/Model_evaluation.ipynb`. Each numbered folder matches one part of the notebook.

**External-set figures in this results folder use the earlier 47-positive release.** The active test set now has 51 positives and 500 benign rows; these saved results have not been recomputed for it.

## How to read these numbers

- **Test set:** rows held out from the training data before training (20%). In Part 1 the split is random, so about a third of the test rows have a near-copy in training (same `base_id`). In Part 3 the split keeps each `base_id` on one side.
- **External set (historical results below):** a separate test set collected from write-ups, CVE proofs of concept and a HackerOne report: 47 attacks and 500 benign rows (about 9% attacks). It is the closest thing to real traffic here, but with only 47 attacks one missed attack moves recall by about 2 points.
- **ROC-AUC:** how often the model scores a random attack above a random benign input (1.0 = always, 0.5 = coin flip). It does not depend on the cutoff.
- **Precision / recall / F1:** depend on the cutoff. Precision = of the inputs flagged, how many were attacks. Recall = of the attacks, how many were flagged.
- **False alarms:** benign inputs flagged as attacks. **Missed attacks:** attacks not flagged.

Every reading is a single run. Differences of one or two rows between models are noise.

## Current run (6 October 2026)

Notebook run end to end on Windows, Python 3.13, scikit-learn 1.6.1, XGBoost 3.2.0, version 2 features (18 features). Training data: 3,906 rows (1,905 attacks). Part 1 test set: 782 rows. Part 3 grouped test set: 715 rows.

| Folder | Notebook part | Files |
|---|---|---|
| [`1_basic_evaluation/`](1_basic_evaluation/) | Part 1: random split, cutoff 0.5 | `test_set_threshold_0.5.csv`, `external_set_threshold_0.5.csv` |
| [`2_threshold_selection/`](2_threshold_selection/) | Part 2: cutoff chosen from the training data at a 5% false-alarm rate | `thresholds.csv`, `test_set_random_folds_threshold.csv`, `external_set_random_vs_grouped_threshold.csv` |
| [`3_grouped_evaluation/`](3_grouped_evaluation/) | Part 3: split by `base_id`, cutoff 0.5 | `random_vs_grouped_vs_external.csv` |
| [`4_attack_mechanisms/`](4_attack_mechanisms/) | Part 4: recall per attack mechanism, XGBoost and Random Forest, 5 folds | `recall_random_folds.csv`, `recall_grouped_folds.csv`, `random_vs_grouped.csv`, `missed_examples_xgboost.csv` |

### Part 1: random split, cutoff 0.5

| Model | Test AUC | Test precision | Test recall | External AUC | External precision | External recall |
|---|---:|---:|---:|---:|---:|---:|
| XGBoost | 0.980 | 0.931 | 0.926 | 0.992 | 0.65 | 0.96 |
| Random Forest | 0.978 | 0.920 | 0.931 | 0.988 | 0.63 | 0.94 |
| SVM | 0.975 | 0.937 | 0.903 | 0.979 | 0.65 | 0.89 |
| KNN | 0.951 | 0.935 | 0.908 | 0.957 | 0.62 | 0.87 |
| Logistic Regression | 0.958 | 0.907 | 0.840 | 0.978 | 0.49 | 0.96 |
| Decision Tree | 0.918 | 0.909 | 0.911 | 0.918 | 0.57 | 0.89 |
| Naive Bayes | 0.932 | 0.973 | 0.634 | 0.967 | 0.80 | 0.68 |

External precision and recall in Part 1 come from the printed classification reports, so they have two decimals.

### Part 2: chosen cutoff, external set

| Model | Cutoff (random folds) | Precision | Recall | F1 | Cutoff (grouped folds) | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| XGBoost | 0.645 | 0.750 | 0.957 | 0.841 | 0.827 | **0.837** | 0.872 | **0.854** |
| Random Forest | 0.644 | 0.683 | 0.915 | 0.782 | 0.803 | 0.771 | 0.787 | 0.779 |
| SVM | 0.673 | 0.683 | 0.872 | 0.766 | 0.791 | 0.736 | 0.830 | 0.780 |
| KNN | 0.684 | 0.678 | 0.851 | 0.755 | 1.000 | 0.717 | 0.809 | 0.760 |
| Logistic Regression | 0.660 | 0.536 | 0.787 | 0.638 | 0.694 | 0.581 | 0.766 | 0.661 |
| Decision Tree | 1.000 | 0.609 | 0.894 | 0.724 | 1.000 | 0.609 | 0.894 | 0.724 |
| Naive Bayes | 0.000 | 0.650 | 0.830 | 0.729 | 0.000 | 0.650 | 0.830 | 0.729 |

Naive Bayes and Decision Tree output almost only 0 or 1, so their cutoffs land at 0 or 1 and cannot be tuned.

### Part 3: random split against grouped split, cutoff 0.5

| Model | AUC: random → grouped → external | Precision: random → grouped → external | False alarms: random → grouped → external |
|---|---|---|---|
| XGBoost | 0.980 → 0.966 → 0.991 | 0.931 → 0.882 → 0.638 | 27 → 46 → 25 |
| Random Forest | 0.978 → 0.965 → 0.987 | 0.920 → 0.891 → 0.634 | 32 → 43 → 26 |
| SVM | 0.975 → 0.957 → 0.981 | 0.937 → 0.904 → 0.614 | 24 → 36 → 27 |
| KNN | 0.951 → 0.917 → 0.967 | 0.935 → 0.887 → 0.583 | 25 → 44 → 30 |
| Logistic Regression | 0.958 → 0.946 → 0.974 | 0.907 → 0.868 → 0.478 | 34 → 49 → 47 |
| Decision Tree | 0.918 → 0.874 → 0.960 | 0.909 → 0.862 → 0.554 | 36 → 55 → 37 |
| Naive Bayes | 0.932 → 0.909 → 0.966 | 0.973 → 0.936 → 0.686 | 7 → 18 → 16 |

The random test set has 389 benign rows and the grouped test set 331, so the false-alarm rate roughly doubles (XGBoost 6.9% → 13.9%).

### Part 4: recall per attack mechanism, grouped folds

| Mechanism | Attacks | XGBoost recall (95% range) | Random Forest recall (95% range) |
|---|---:|---|---|
| introspection | 265 | 0.996 (0.979–0.999) | 0.992 (0.973–0.998) |
| probe | 103 | 0.981 (0.932–0.995) | 1.000 (0.964–1.000) |
| feature-abuse | 130 | 0.985 (0.946–0.996) | 0.992 (0.958–0.999) |
| direct-execution | 670 | 0.966 (0.949–0.977) | 0.970 (0.954–0.981) |
| enumeration | 107 | 0.832 (0.750–0.891) | 0.897 (0.825–0.942) |
| uncertain | 630 | 0.786 (0.752–0.816) | 0.811 (0.779–0.840) |

Mechanism labels are automatic and not reviewed by a person. 94% of `uncertain` rows are flagged for manual review in `Dataset/train/positives/positives.csv`.

## Other folders

| Folder | What it holds |
|---|---|
| [`deep_learning/`](deep_learning/) | RNN, LSTM and CNN-LSTM over 5 seeds (`dl_models.ipynb`, 30 September 2026) |
| [`earlier_analyses/`](earlier_analyses/) | Analyses run with separate scripts on 20–24 September 2026 (learning curve, v1 against v2 features, n-gram baseline, hard-negative errors), plus a full notebook run with v1 and v2 features. Their protocols are in that folder's README |
| [`superseded/`](superseded/) | Readings from earlier versions of the notebook. Kept for history; use the numbered folders instead |
