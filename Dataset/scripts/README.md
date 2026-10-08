# Dataset utilities

`admit_ssti_test_candidates.py` records the historical 18 September test update. Its inputs and ledger now belong to the archived layout; do not rerun it on the current release. Use the current validator below.

## Current feature and consistency utilities

- `ssti_feature_extraction_v3.py`: the current feature set (22 features). Run it to rebuild `model_evaluation/full_DS_v3.csv`, which the evaluation notebook reads.
- `ssti_feature_extraction_v2.py`: version 2 (18 features), imported by version 3.
- `ssti_feature_extraction.py`: version 1 (17 features), imported by version 2 and used to validate the dataset exports.
- `extract_to_csv.py`: text-to-feature export utility. A one-payload-per-line text file is not appropriate for multiline payloads.
- `reconcile_dataset_exports.py --validate --test-only`: checks current test exports and both test-feature copies, screening against both training versions without modifying them. Full historical validation assumes the old training schema. Its repair modes are separate and should only be used for a deliberate new repair session.

## Historical collection logic

`legacy/` contains earlier collection/build scripts and an alternate feature implementation. They have old path assumptions, incomplete construction steps, or old selection behavior; they are not a complete reproducible release pipeline. The relocated test builder must not overwrite the frozen test data.

`dedup_merge.py` remains here because the research builder reads its normalization/skeleton functions without executing the collection script. Its old main workflow has container-specific paths; do not run it as a current dataset builder.

Historical audit/repair scripts and their reports were retired on 2026-09-19 and are not
part of this repository. No model algorithms were changed by this cleanup.
