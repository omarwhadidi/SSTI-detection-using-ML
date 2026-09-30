# Training data (SSTI detection)

Training corpus for SSTI payload classification. Full provenance is in
[SOURCES.md](SOURCES.md). The external challenge set is in `../test_set/`, where known
skeleton and near-family overlaps are flagged. This corpus does **not** establish source or
semantic-family independence from the test set.

## Files

| file | records | what |
|---|---:|---|
| `positives/positives.csv` | 1,905 | positive payloads with engine/language, grouping key, provenance URL, and review flags |
| `positives/positives.txt` | 1,905 | the same payload strings, one per line |
| `benign/benign.csv` | 2,001 | benign payloads: `payload`, `label`(=0), `kind`, `source`, `engine`, `base_id` |
| `benign/benign.txt` | 2,001 | the same benign strings, one per line |
| `combined/train_combined.csv` | 3,906 | canonical positives + benign with unified columns |
| `combined/train_features.csv` | 3,906 | the same records plus the 17 deterministic features |

## Columns

`label` is 1 for an SSTI payload and 0 for benign. `engine` and `language` are automatic
annotations with a separate `engine_confidence`; `language` is `unknown` where the
heuristic could not decide, rather than guessed. `source_url` is the attribution ledger —
one pinned GitHub blob URL per row, populated for all 1,905 positives, from which the
repository, commit and file path can all be read.

The positives file carries 10 columns, in this order: `payload`, `base_id`, `language`,
`engine`, `label`, `engine_confidence`, `mechanism`, `suspected_benign`, `review_notes`,
`source_url`. Nine earlier columns were dropped as redundant across two passes on
20 September 2026 (see `SOURCES.md` for the full list). The three `positives_added_from_*`
transparency exports were retired the same day — their rows were already inside
`positives.csv`; they add nothing and are archived, not deleted.

`base_id` is the automatic
structural skeleton of a payload, with digits and quoted strings masked and whitespace
stripped. **This is the grouping key.** There are 1,283 distinct positive skeletons and
1,432 distinct benign ones. Group on it in the outer split and in inner CV. It prevents
shared stored skeletons from straddling the split; it does not catch every semantic-family
overlap.

`mechanism`, `suspected_benign`, and `review_notes` are review metadata. They are not
model inputs and need not become numeric features. Every `mechanism` value is automatic and
unreviewed.

## Notes

**Class balance.** 1,905 positive against 2,001 benign, roughly 49/51. Report ROC-AUC and attack-class recall, not accuracy.

**Features are derived, never edited.** `combined/train_features.csv` is generated from `combined/train_combined.csv` with `../scripts/ssti_feature_extraction.py` (`train_features_v2.csv` uses `../scripts/ssti_feature_extraction_v2.py`). Regenerate after any payload, label, or grouping change. Metadata-only edits (review flags, annotations) do not require regeneration.

**Benign composition.** 787 hard negatives (real template expressions from four open-source projects) and 1,214 benchmark-derived HTTP parameters. See [SOURCES.md](SOURCES.md#benign-sources).

Limitations of this data, including unreviewed annotations and the shared repositories between train and test, are listed in [../LIMITATIONS.md](../LIMITATIONS.md).
