# SSTI-ML-Detect

Detecting Server-Side Template Injection (SSTI) payloads with machine learning, evaluated with group-aware splits, hard negatives and a separate external test set.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/code%20license-MIT-green)
![Status](https://img.shields.io/badge/status-research%2Feducational-yellow)

---

## Overview

Server-Side Template Injection happens when user input reaches a template engine that evaluates it, which can lead to remote code execution. This project measures how well a classifier can tell SSTI payloads from benign input when the benign input includes real template code that looks a lot like an attack.

The repository holds a labelled dataset, two versions of a hand-built feature set, and notebooks that compare classical models (Random Forest, XGBoost and others), a character n-gram baseline and character-level neural networks.

This is the second version of the project. The first used 977 payloads and a single random split, so variants of one payload could land in both the training and the test data. That leakage makes its results unreliable, and this version replaces it.

## Dataset

Training and test data were collected separately, so the test set does not come from the same process as the training set. Every training positive has a `source_url` that points to a public file at a fixed commit. The benign class contains real template code from open-source projects, which means a payload cannot be recognised by its braces alone. Payloads that differ only in numbers or string values share a `base_id`, and every split keeps each group on one side.

| Set | Rows | Sources |
|---|---:|---|
| Training positives | 1,905 | [payload-box/ssti-advanced-payload-list](https://github.com/payload-box/ssti-advanced-payload-list) (1,441), [PayloadsAllTheThings](https://github.com/swisskyrepo/PayloadsAllTheThings) (194), [HackTricks](https://github.com/HackTricks-wiki/hacktricks) (159), [Hackmanit template-injection-table](https://github.com/Hackmanit/template-injection-table) (65), [SecLists](https://github.com/danielmiessler/SecLists) (29), [ProjectDiscovery fuzzing-templates](https://github.com/projectdiscovery/fuzzing-templates) (17) |
| Training benign | 2,001 | 787 template fragments (hard negatives) from [Sidekiq](https://github.com/sidekiq/sidekiq), [Symfony demo](https://github.com/symfony/demo), [Microblog](https://github.com/miguelgrinberg/microblog) and [Spring PetClinic](https://github.com/spring-projects/spring-petclinic); 1,214 normal web parameters from [HttpParamsDataset](https://github.com/Morzeux/HttpParamsDataset) |
| External test positives | 47 | Published write-ups, CVE proofs of concept, scanner templates, one HackerOne report and one CTF challenge, listed in [`Dataset/test_set/sources.md`](Dataset/test_set/sources.md) |
| External test benign | 500 | 143 template fragments and 357 normal parameters, from the same five sources as the training benign rows |

How the data was built and checked is described in [`Dataset/README.md`](Dataset/README.md). Known weaknesses are listed in [`Dataset/LIMITATIONS.md`](Dataset/LIMITATIONS.md), and per-file counts, pinned commits and licences are in [`Dataset/train/SOURCES.md`](Dataset/train/SOURCES.md).

## Features

Each payload is reduced to a short vector of counts and flags, such as delimiter counts, bracket depth, dangerous-name flags and method calls. Version 2 has 18 features and is the current set. Version 1 has 17 and is kept so earlier results can be reproduced. Files ending in `_v2.csv` use version 2. Definitions, and the reasons for each change from version 1, are in [`Dataset/DATASHEET.md`](Dataset/DATASHEET.md) section 7. The extractors are in [`Dataset/scripts/`](Dataset/scripts/), and `feature_audit.py` reproduces the evidence behind the changes.

## Results

All results use the grouped splits and the 47-positive external test set described above. Most come from five runs on one machine, so differences of a point or two between models are within run-to-run variation. The same model appears with different numbers in different tables because the tables use different splits, cutoffs and hyperparameters. The exact protocol for each table is in [`results/README.md`](results/README.md), and the raw numbers are in [`results/`](results/).

### 1. More training data no longer helps

XGBoost on the 17 version 1 features, trained on grouped subsamples of the training data:

| Training rows | Holdout AUC | External AUC |
|---:|---:|---:|
| 677 | 0.9438 | 0.9474 |
| 3,191 | 0.9661 | 0.9895 |

Going from 90% to 100% of the data changed holdout AUC by +0.0011 and external AUC by less than 0.0001.

### 2. The default cutoff gives low precision

At the default cutoff of 0.5, XGBoost reaches an external precision of 0.66. Choosing the cutoff from training data alone, by targeting a 5% false-alarm rate on out-of-fold benign scores from 5 grouped folds, raises precision to 0.84 and costs four more missed attacks.

| Model | Cutoff | Precision | Recall | F1 | False alarms | Missed attacks |
|---|---:|---:|---:|---:|---:|---:|
| XGBoost | 0.50 | 0.662 | 0.957 | 0.783 | 23 | 2 |
| XGBoost | 0.811 | 0.837 | 0.872 | 0.854 | 8 | 6 |
| Random Forest | 0.50 | 0.629 | 0.936 | 0.752 | 26 | 3 |
| Random Forest | 0.793 | 0.776 | 0.809 | 0.792 | 11 | 9 |

Single run with version 2 features. The code is in the last cells of [`model_evaluation/Model_evaluation.ipynb`](model_evaluation/Model_evaluation.ipynb).

### 3. Version 2 features give a small gain

Mean over 5 grouped splits, cutoff 0.5, external set:

| Model | Features | F1 | Precision | Recall |
|---|---|---:|---:|---:|
| XGBoost | v1 | 0.726 | 0.579 | 0.979 |
| XGBoost | v2 | 0.734 | 0.593 | 0.975 |
| Random Forest | v1 | 0.706 | 0.563 | 0.953 |
| Random Forest | v2 | 0.721 | 0.583 | 0.953 |

F1 rises by 0.008 for XGBoost and 0.015 for Random Forest, while the spread between splits is 3 to 8 points. The gain is consistent in direction but small, and it has not been shown to be real. External PR-AUC for Random Forest fell by 0.017.

### 4. The errors come from hard negatives

At cutoff 0.5 (XGBoost, version 1 features) all 23 external false positives were template fragments: 15 from Sidekiq, 4 from Microblog, 3 from PetClinic and 1 from Symfony demo. None of the 357 normal parameters was flagged. On attacks against hard negatives alone, AUC is 0.926 ± 0.009 over 5 grouped splits. More varied benign templates are the most likely way to reduce the remaining false alarms.

### 5. A character n-gram baseline is strong on in-distribution data

One grouped split:

| Model | Holdout AUC | External AUC | External PR-AUC |
|---|---:|---:|---:|
| 17 engineered features + XGBoost | 0.966 | 0.990 | 0.903 |
| Character 2-4-gram TF-IDF + logistic regression | 0.997 | 0.983 | 0.874 |

The n-gram model scores higher on the holdout and lower on the external set.

### 6. Character-level neural networks

An RNN, an LSTM and a CNN-LSTM read the raw payload characters ([`dl_models.ipynb`](model_evaluation/deep_learning/dl_models.ipynb)). The table shows mean ± standard deviation over 5 seeds, each with a different grouped split. The cutoff was chosen on validation rows only, at a 5% false-positive budget.

| Model | Holdout AUC | External AUC | External PR-AUC | External recall | External precision |
|---|---:|---:|---:|---:|---:|
| RNN | 0.960 ± 0.038 | 0.949 ± 0.049 | 0.796 ± 0.161 | 0.808 | 0.583 |
| LSTM | 0.957 ± 0.035 | 0.948 ± 0.015 | 0.844 ± 0.046 | 0.864 | 0.556 |
| CNN-LSTM | 0.979 ± 0.018 | 0.978 ± 0.011 | 0.880 ± 0.009 | 0.940 | 0.527 |

CNN-LSTM has the highest external AUC, ahead of the other two by more than the seed-to-seed spread. On the holdout the three models are within one standard deviation of each other. External precision is low at 0.53 to 0.58, because the cutoff picked on the validation rows lets through 6 to 8% of benign external rows instead of 5%. None of the three beats XGBoost on the engineered features, although the comparison is not exact because the splits and the cutoff procedure differ. A second run of the same code gave identical RNN results but an LSTM external AUC of 0.961, so differences of about 0.01 should be treated as noise.

## Usage

```bash
pip install -r requirements.txt
cd Dataset/scripts
python ssti_feature_extraction_v2.py   # rebuilds train_features_v2.csv and test_features_v2.csv
python feature_audit.py                # reproduces the feature analysis
```

Then open `model_evaluation/Model_evaluation.ipynb`. The `FEATURES_FILE` line in cell 4 switches between version 1 and version 2 features. The notebooks read local copies of the feature CSVs in `model_evaluation/` and check that they match the files in `Dataset/`. The neural network notebook is `model_evaluation/deep_learning/dl_models.ipynb`.

## License

| Component | License |
|---|---|
| Code (scripts and notebooks) | [MIT](LICENSE) |
| Dataset | Not covered by the MIT license and not yet cleared for redistribution |

The payloads come from 11 public repositories: seven under MIT, two under Apache-2.0, one under LGPL-3.0 (Sidekiq), and one (HackTricks) with custom terms that require attribution and ask for permission before commercial use. The licenses of the web pages behind the 47 test positives have not been checked. Read the licensing section of [`Dataset/train/SOURCES.md`](Dataset/train/SOURCES.md) before sharing or reusing any data file.

## Contact

Omar Walid Elhadidi, [omarwhadidi9@gmail.com](mailto:omarwhadidi9@gmail.com)
