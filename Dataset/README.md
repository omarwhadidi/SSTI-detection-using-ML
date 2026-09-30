# SSTI dataset

Training data, external test data, and provenance for the SSTI detection work. The data was
built in two separate pipelines, one for training and one for the external test set, so that
the test material does not come from the same collection process as the training material.
Column definitions, pinned commits and per-file counts are in [DATASHEET.md](DATASHEET.md)
and [train/SOURCES.md](train/SOURCES.md).

## What to open

| What you need | Open this |
|---|---|
| Where the training payloads came from | [train/SOURCES.md](train/SOURCES.md) — positives *and* benign: repositories, pinned commits, per-file counts, licensing, and what the provenance does not prove |
| Where the test payloads came from | [test_set/sources.md](test_set/sources.md) |
| Full dataset explanation, sources, column meanings, and review status | [DATASHEET.md](DATASHEET.md) — checked 20 September 2026; section 9 lists verified checks and remaining limitations |
| How to gather training and test data for a new project | [HOW_TO_BUILD_A_DATASET.md](HOW_TO_BUILD_A_DATASET.md) |
| Dataset utilities | [scripts/](scripts/) |
| Earlier cleanup record | [CLEANUP_LOG.json](CLEANUP_LOG.json) |

## Main files

[train/](train/) has 3,906 rows and [test_set/](test_set/) has 547.

- Training — `train/combined/train_combined.csv` and `train/combined/train_features.csv`
- Test — `test_set/ssti_test_positives.jsonl`, `test_set/ssti_test_combined.csv`, and
  `test_set/features/test_features.csv`

Read multiline CSV records with a proper CSV reader, not by splitting on newlines.

## How the data was built

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

## Non-negotiables when using this data

- **Group on `base_id`.** Use `GroupShuffleSplit` or
  `StratifiedGroupKFold` in both the outer split and inner CV. Plain stratified splitting
  leaks structurally identical payloads across the boundary.
- **Fit every preprocessing step on training data only** — one scaler, one tokenizer, fitted
  once, applied to train, validation, and external test alike.
- **Keep the hard negatives in the benign set.** Dropping them makes the numbers meaningless.
- **ROC-AUC as headline, attack-class recall as the security-critical metric.** Never
  accuracy alone; the corpus is not balanced.
- **The test set is frozen.** No augmentation, no rebalancing, no re-selection.

## Review status

Automatic annotations are not final labels: all 1,905 positive mechanism annotations are
`auto_unreviewed`. A populated `source_url` is an attribution, not independent
verification. Row-level review flags live in `train/positives/positives.csv`
(`suspected_benign`, `review_notes`); treat them as review candidates, never as a deletion
rule. File consistency does not validate model results. Details are in
[DATASHEET.md](DATASHEET.md) section 9.
