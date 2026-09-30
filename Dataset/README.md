# SSTI dataset — start here

Active dataset, collection guidance, and provenance for the SSTI detection work. Folder
consolidation on **19 September 2026** removed the `research/`, `review/`, and `sources/`
folders; their contents were archived verbatim and the information worth keeping was moved
into the live dataset. No active payload, label, feature, or evaluation algorithm changed.

## What to open

| What you need | Open this |
|---|---|
| Where the training payloads came from | [train/SOURCES.md](train/SOURCES.md) — positives *and* benign: repositories, pinned commits, per-file counts, licensing, and what the provenance does not prove |
| Where the test payloads came from | [test_set/sources.md](test_set/sources.md) |
| Full dataset explanation, sources, column meanings, and review status | [DATASHEET.md](DATASHEET.md) — checked 20 September 2026; section 9 lists verified checks and remaining limitations |
| How to gather training and test data for a new project | [HOW_TO_BUILD_A_DATASET.md](HOW_TO_BUILD_A_DATASET.md) |
| Dataset utilities | [scripts/](scripts/) |
| Earlier cleanup record | [CLEANUP_LOG.json](CLEANUP_LOG.json) |

## Current data

| split | positives | benign | total |
|---|---:|---:|---:|
| [train/](train/) | 1,905 | 2,001 | **3,906** |
| [test_set/](test_set/) | 47 | 500 | **547** |

Main files:

- Training — `train/combined/train_combined.csv` and `train/combined/train_features.csv`
- Test — `test_set/ssti_test_positives.jsonl`, `test_set/ssti_test_combined.csv`, and
  `test_set/features/test_features.csv`

Read multiline CSV records with a proper CSV reader, not by splitting on newlines.

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

## What still needs review

Automatic annotations are not final labels — all 1,905 positive mechanism annotations are
`auto_unreviewed`. A populated `source_url` is an attribution, not independent
verification. Row-level review flags live in `train/positives/positives.csv`
(`suspected_benign`, `review_notes`); treat them as review candidates, never as a deletion
rule. Both evaluation feature copies now match the active dataset. Historical model
scores still need a separate pipeline and run review; file consistency alone does not
validate model results. Details are in [DATASHEET.md](DATASHEET.md) section 9.
