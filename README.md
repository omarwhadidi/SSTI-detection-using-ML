# SSTI-ML-Detect

**Machine learning detection of Server-Side Template Injection (SSTI) payloads, evaluated with group-aware splits, hard negatives, and an independent external test set.**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/code%20license-MIT-green)
![Status](https://img.shields.io/badge/status-research%2Feducational-yellow)

---

## Overview

Server-Side Template Injection lets an attacker inject template syntax that the server's template engine then evaluates, often escalating to remote code execution. This project asks whether a classifier trained on interpretable features of a payload string can separate SSTI payloads from benign input, including benign template code that looks like an attack.

This is the second version of the project. The first version used 977 hand-assembled payloads and a single random split, which let variants of the same payload land on both sides of the split. It is preserved in [`legacy_977_row_version/`](legacy_977_row_version/) for history and **its results should not be cited**. This version replaces it.

## Dataset construction

The data was built in two separate pipelines, one for training and one for the external test set, so that the test material does not come from the same collection process as the training material. This section summarises the process. Column definitions, exact commits and per-file counts are in [`Dataset/DATASHEET.md`](Dataset/DATASHEET.md) and [`Dataset/train/SOURCES.md`](Dataset/train/SOURCES.md).

### Design principles

- **Traceable positives.** Every training positive carries a `source_url` pointing at a public file at a pinned commit. An earlier version of the corpus held 366 locally written seed payloads with no upstream source; they were removed so that every positive can be traced.
- **Hard negatives.** A benign set of plain web parameters would make the task trivial, because anything containing template braces would be an attack. The benign class therefore includes real template fragments that share delimiters with attacks.
- **Group-aware evaluation.** Near-identical payloads are given the same `base_id`, and all splits keep each group on one side.
- **A separate, frozen test set.** Training additions were checked against it before merging (see below).

### At a glance

| | rows | notes |
|---|---:|---|
| Training positives | 1,905 | six public sources; 1,283 distinct structural skeletons (`base_id`) |
| Training benign | 2,001 | 787 hard negatives from four projects, 1,214 normal parameters |
| External test positives | 47 | 22 distinct source documents |
| External test benign | 500 | 143 template fragments, 357 normal parameters |

### Training positives

| source | rows | material |
|---|---:|---|
| payload-box `ssti-advanced-payload-list` | 1,441 | engine-specific lists (EJS, Smarty, ERB, Pug, Twig, Thymeleaf, Jinja2, FreeMarker, Velocity) |
| PayloadsAllTheThings | 194 | SSTI pages and `Intruder/ssti.fuzz` |
| HackTricks | 159 | code examples from SSTI, Jinja2 and expression-language pages |
| Hackmanit `template-injection-table` | 65 | engine-identification probes from `engines.js` |
| SecLists | 29 | template-engine identification and expression lists |
| ProjectDiscovery `fuzzing-templates` | 17 | scanner templates (flagged for scope review) |

Strings were extracted from payload lists, Markdown code blocks, scanner templates and the engine table, whitespace was normalised, and exact duplicates were removed before each merge. Because of the normalisation, rows are not byte-for-byte copies of their sources. Each batch of additions was deduplicated against the existing training corpus and against the frozen test set, by exact string and by `base_id`, and any candidate matching a test payload was dropped. This reduces leakage; it does not establish that the test set is independent of the training families.

### Training benign

| source | type | engine | rows |
|---|---|---|---:|
| Sidekiq | template fragments | ERB | 295 |
| Symfony demo | template fragments | Twig | 240 |
| Microblog | template fragments | Jinja2 | 134 |
| Spring PetClinic | template fragments | Thymeleaf | 118 |
| HttpParamsDataset (benign class) | normal web parameters | none | 1,214 |

Template fragments were extracted from the projects' template files by matching expressions inside delimiters (`{{...}}`, `{%...%}`, `<%...%>`, `${...}`), collapsing whitespace, keeping strings of 3 to 200 characters that contain at least one letter, and removing repeats. Normal parameters come from the `norm` records of an existing public benchmark, not from newly captured traffic.

### External test set

The 47 test positives were collected separately from reports, advisories, security articles, scanner material and one challenge write-up.

| recorded evidence type | rows |
|---|---:|
| security write-up | 34 |
| CVE proof of concept | 9 |
| scanner template | 2 |
| HackerOne report | 1 |
| CTF challenge | 1 |

These are saved annotations, not independently verified incidents: a write-up describes a technique, not necessarily an observed attack. A scope review removed six related cases (expression or compiler-option injection) and added nine template-injection candidates. The 500 test benign rows come from the same five sources as the training benign rows, with no overlap at the string level.

### Grouping

`base_id` is a payload's structural skeleton: digits and quoted strings are masked, text is lowercased and whitespace removed. Two arithmetic probes that differ only in their numbers therefore share a group. It is a rough grouping tool, not a proven attack-family label, and it cannot relate two attacks written in different ways.

### Checks performed

Record counts and source totals were confirmed against the files; the training positives and benign rows match the combined and feature files in payload, label, order and `base_id`; all feature values were recomputed for every training and test row with no mismatches; and every positive has its source fields filled in.

### Known issues in the data

- No payload was executed. Labels state the source's claim, not a confirmed exploit.
- `engine`, `language` and `mechanism` are assigned automatically and are not human-reviewed. 630 of the 1,905 mechanism labels are `uncertain`.
- 884 training rows are flagged for review of their extraction or type, and 4 are flagged as possibly benign.
- One string (`{% endif %}`) appears with both labels.
- 13 of the 47 test positives have a recorded relationship to a training payload family, and training and test benign rows share repositories, so the test set is not independent of the training data. Only 47 test positives also means recall estimates are coarse: one payload is 2.13 points.
- The test set has been inspected during development, so it should not be treated as untouched.
- Collection scripts in `Dataset/scripts/` are partly historical; there is no single command that rebuilds the release.

## Features

Version 1 has 17 features (lexical, structural, semantic); version 2 has 18. Files ending `_v2.csv` use version 2. Columns starting with `v2_` are new or redefined; all other columns are computed exactly as in version 1.

| Change in v2 | Why |
|---|---|
| removed `count_percent_brace` | fired on 2 of 3,906 rows |
| `count_erb` → `v2_count_erb_open` | version 1 counted opening and closing tags, so ERB scored double |
| `has_arithmetic_operation` → `v2_has_arithmetic_probe` | version 1 missed probes with a quoted operand |
| added `v2_call_inside_delim`, `v2_max_attr_chain_len` | behaviour features that still separate attacks from hard negatives |

Definitions and rationale: [`Dataset/scripts/ssti_feature_extraction.py`](Dataset/scripts/ssti_feature_extraction.py) and [`..._v2.py`](Dataset/scripts/ssti_feature_extraction_v2.py). Evidence for each change: [`Dataset/scripts/feature_audit.py`](Dataset/scripts/feature_audit.py).

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

## Limitations

- **The external test set is not fully independent.** Its benign rows come partly from the same four open-source projects as the training hard negatives, and 13 of its 47 positives have a recorded relationship to a training payload family (see [Known issues in the data](#known-issues-in-the-data)).
- **Only 47 external positives.** A recall near 0.95 has a 95% interval of about ±6 points, so differences smaller than that cannot be resolved.
- **Hard negatives come from four projects**, one per template engine, which is the most likely reason for the remaining false alarms.
- **Labels and annotations are automatic.** `engine`, `language` and `mechanism` are not human-reviewed; nothing was executed to confirm a payload works.
- **Two feature columns are shape proxies.** `payload_length` and `special_char_ratio` alone reach external AUC 0.953; they separate template-shaped strings from plain parameters more than attacks from hard negatives.
- **The first cells of `Model_evaluation.ipynb` use a random, ungrouped split** (kept as the original baseline). The grouped readings are in the cells after it and in the last two sections.
- No adversarial evaluation against an attacker who knows the features.

## Layout

```
Dataset/
  DATASHEET.md, README.md      dataset documentation
  train/                       positives/, benign/, combined/ (incl. *_features.csv), SOURCES.md
  test_set/                    external test data, features/, sources.md
  scripts/                     feature extractors (v1, v2), feature_audit.py, older utilities
model_evaluation/
  Model_evaluation.ipynb       7 classical models, grouped evaluation, threshold selection
  deep_learning/dl_models.ipynb  RNN / LSTM / CNN-LSTM, 5-split rerun
  *.csv                        local copies the notebooks read (byte-identical to Dataset/)
legacy_977_row_version/        first version, superseded
```

The notebooks find `Dataset/` by walking up from their own folder, and compare their local CSV copies with the originals, which is why the copies are kept.

## Usage

```bash
pip install -r requirements.txt
cd Dataset/scripts
python ssti_feature_extraction_v2.py      # rebuilds train_features_v2.csv and test_features_v2.csv
python feature_audit.py                    # reproduces the feature analysis
```

Then open `model_evaluation/Model_evaluation.ipynb`. Cell 4 has a `FEATURES_FILE` line that switches between v1 and v2 features.

## Licence

Code: MIT, see [LICENSE](LICENSE).

**Data is not covered by that licence and has not been cleared for redistribution.** Payloads come from repositories with different licences (MIT, Apache-2.0, LGPL-3.0, and one wiki whose licence is unverified). See the Licensing section of [`Dataset/train/SOURCES.md`](Dataset/train/SOURCES.md) before sharing or reusing any data file.

## Contact

Omar Walid Elhadidi, [omarwhadidi9@gmail.com](mailto:omarwhadidi9@gmail.com)

Built as part of a Master of Science in Cyber Security creative component, Iowa State University.
