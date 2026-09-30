# SSTI-ML-Detect

**Machine learning detection of Server-Side Template Injection (SSTI) payloads, evaluated with group-aware splits, hard negatives, and an independent external test set.**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/code%20license-MIT-green)
![Status](https://img.shields.io/badge/status-research%2Feducational-yellow)

---

## Overview

Server-Side Template Injection lets an attacker inject template syntax that the server's template engine then evaluates, often escalating to remote code execution. This project asks whether a classifier trained on interpretable features of a payload string can separate SSTI payloads from benign input, including benign template code that looks like an attack.

This is the second version of the project. The first version used 977 hand-assembled payloads and a single random split, which let variants of the same payload land on both sides of the split. Its results should not be cited; this version replaces it.

## Dataset

The data was built in two separate pipelines, one for training and one for the external test set, so the test material does not come from the same collection process as the training material. Every training positive carries a `source_url` pinned to a public file at a specific commit, and the benign class includes real template code that shares delimiters with attacks, so it cannot be separated by the presence of braces alone. Near-identical payloads share a `base_id`, and all splits keep each group on one side.

| set | rows | sources |
|---|---:|---|
| Training positives | 1,905 | [payload-box/ssti-advanced-payload-list](https://github.com/payload-box/ssti-advanced-payload-list) (1,441), [PayloadsAllTheThings](https://github.com/swisskyrepo/PayloadsAllTheThings) (194), [HackTricks](https://github.com/HackTricks-wiki/hacktricks) (159), [Hackmanit template-injection-table](https://github.com/Hackmanit/template-injection-table) (65), [SecLists](https://github.com/danielmiessler/SecLists) (29), [ProjectDiscovery fuzzing-templates](https://github.com/projectdiscovery/fuzzing-templates) (17) |
| Training benign | 2,001 | 787 template fragments (hard negatives) from [Sidekiq](https://github.com/sidekiq/sidekiq), [Symfony demo](https://github.com/symfony/demo), [Microblog](https://github.com/miguelgrinberg/microblog) and [Spring PetClinic](https://github.com/spring-projects/spring-petclinic); 1,214 normal web parameters from [HttpParamsDataset](https://github.com/Morzeux/HttpParamsDataset) |
| External test positives | 47 | Published write-ups, CVE proofs of concept, scanner templates, one HackerOne report and one CTF challenge, listed in [`Dataset/test_set/sources.md`](Dataset/test_set/sources.md) |
| External test benign | 500 | 143 template fragments and 357 normal parameters, from the same five sources as the training benign rows |

Construction steps, grouping and checks are in [`Dataset/README.md`](Dataset/README.md), and the limitations of the data and results are in [`Dataset/LIMITATIONS.md`](Dataset/LIMITATIONS.md). Per-file counts, pinned commits and licences are in [`Dataset/train/SOURCES.md`](Dataset/train/SOURCES.md).

## Features

Each payload is turned into a short vector of interpretable counts and flags (delimiter counts, bracket depth, dangerous-name flags, method calls). Version 2 has 18 features and is the current set; version 1 has 17 and is kept so earlier results can be reproduced. Files ending `_v2.csv` use version 2. The full list of definitions, and what changed from version 1 and why, is in [`Dataset/DATASHEET.md`](Dataset/DATASHEET.md) section 7. The extractors are in [`Dataset/scripts/`](Dataset/scripts/), and `feature_audit.py` reproduces the evidence for each change.

## Results

**These numbers are provisional.** They come from repeated runs of the code in this repository on one machine, several with only 5 random splits, and the external set has just 47 positives. Re-run the notebooks before quoting anything.

**1. More positives have stopped helping.** XGBoost on the 17 features, grouped subsamples of the training data:

| training rows | holdout AUC | external AUC |
|---:|---:|---:|
| 677 | 0.9438 | 0.9474 |
| 3,191 | 0.9661 | 0.9895 |

Going from 90% to 100% of the data moved holdout AUC by +0.0011 and external AUC by +0.0000.

**2. At threshold 0.5, precision on the external set is poor.** Choosing the threshold from training data only (5-fold grouped out-of-fold scores, targeting a 5% false-alarm rate on benign rows) and applying it once to the external set:

| model | cutoff | precision | recall | F1 | false alarms | missed attacks |
|---|---:|---:|---:|---:|---:|---:|
| XGBoost | 0.50 | 0.662 | 0.957 | 0.783 | 23 | 2 |
| XGBoost | 0.811 | 0.837 | 0.872 | 0.854 | 8 | 6 |
| Random Forest | 0.50 | 0.629 | 0.936 | 0.752 | 26 | 3 |
| Random Forest | 0.793 | 0.776 | 0.809 | 0.792 | 11 | 9 |

The cost of the higher threshold is more missed attacks. One run each, v2 features. See the last cells of [`model_evaluation/Model_evaluation.ipynb`](model_evaluation/Model_evaluation.ipynb).

**3. Version 2 features help a little.** Mean over 5 grouped splits, threshold 0.5, external set:

| model | features | F1 | precision | recall |
|---|---|---:|---:|---:|
| XGBoost | v1 | 0.726 | 0.579 | 0.979 |
| XGBoost | v2 | 0.734 | 0.593 | 0.975 |
| Random Forest | v1 | 0.706 | 0.563 | 0.953 |
| Random Forest | v2 | 0.721 | 0.583 | 0.953 |

The gains are 1 to 2 points while split-to-split spread is 3 to 8 points, so this is a small consistent improvement, not a demonstrated one. Random Forest's external PR-AUC fell by 0.017.

**4. The errors are all on hard negatives.** At threshold 0.5 (XGBoost, v1 features) all 23 external false positives were template fragments (Sidekiq 15, Microblog 4, PetClinic 3, Symfony 1); none of the 357 normal parameters were flagged. Attacks versus hard negatives only, grouped, 5 splits: AUC 0.926 ± 0.009.

**5. A plain character n-gram baseline is strong in-distribution.** One grouped split:

| model | holdout AUC | external AUC | external PR-AUC |
|---|---:|---:|---:|
| 17 engineered features + XGBoost | 0.966 | 0.990 | 0.903 |
| character 2-4-gram TF-IDF + logistic regression | 0.997 | 0.983 | 0.874 |

Character-level neural models (RNN, LSTM, CNN-LSTM in [`model_evaluation/deep_learning/dl_models.ipynb`](model_evaluation/deep_learning/dl_models.ipynb), 5 splits) follow the same pattern: holdout AUC 0.960 to 0.981, external AUC 0.949 to 0.981, with standard deviations of 0.005 to 0.049 that are as large as the gaps between the three architectures.

## Usage

```bash
pip install -r requirements.txt
cd Dataset/scripts
python ssti_feature_extraction_v2.py      # rebuilds train_features_v2.csv and test_features_v2.csv
python feature_audit.py                    # reproduces the feature analysis
```

Then open `model_evaluation/Model_evaluation.ipynb`. Cell 4 has a `FEATURES_FILE` line that switches between v1 and v2 features. The notebooks read local copies of the feature CSVs in `model_evaluation/` and check that they match the files in `Dataset/`; the deep-learning notebook is `model_evaluation/deep_learning/dl_models.ipynb`.

## Licence

Code: MIT, see [LICENSE](LICENSE).

**Data is not covered by that licence and has not been cleared for redistribution.** Payloads come from repositories with different licences (MIT, Apache-2.0, LGPL-3.0, and one wiki whose licence is unverified). See the Licensing section of [`Dataset/train/SOURCES.md`](Dataset/train/SOURCES.md) before sharing or reusing any data file.

## Contact

Omar Walid Elhadidi, [omarwhadidi9@gmail.com](mailto:omarwhadidi9@gmail.com)
