# Limitations

This is the single list of limitations for the SSTI dataset and the results built on it. Read it before citing any number from the repository.

## Labels

- **No payload was executed.** A positive label states what its source claims. It does not confirm that the payload works in any engine or version.
- **Annotations are automatic.** `engine`, `language` and `mechanism` were assigned by rules and have not been reviewed by a person. All 1,905 `mechanism` values are `auto_unreviewed`, and 630 of them are `uncertain`. Do not use an automatic flag as a rule for deleting or relabelling rows: an earlier automatic pass wrongly removed genuine probes and had to be reversed.
- **Review flags are open.** 884 training rows are flagged for review of their extraction or type, and 4 are flagged `suspected_benign`. These flags overlap, so they should not be added together as a count of faulty rows.
- **One label conflict.** The string `{% endif %}` appears with both labels.
- **Provenance is attribution, not verification.** A populated `source_url` records where a string came from. Rows are whitespace-normalised, so they are not byte-for-byte copies of their sources.

## Training data

- **Benign hard negatives come from four projects**, one per template engine (Sidekiq, Symfony demo, Microblog, Spring PetClinic). This is the most likely reason for the remaining false alarms, and more projects would be the main way to reduce them.
- **Normal parameters are not new traffic.** The 1,214 benign parameters come from an existing public benchmark.
- **The class mix is roughly 49% positive and 51% benign**, which does not reflect real traffic. Report ROC-AUC, PR-AUC and attack-class recall rather than accuracy, and choose thresholds with the base rate in mind.
- **`base_id` is a rough grouping key.** It masks digits and quoted strings, so it groups payloads that differ only in those, but it cannot relate attacks written in different ways.
- **366 earlier seed payloads were removed** because they had no traceable upstream source.

## External test set

- **It is not fully independent of the training data.** Test and training benign rows come from the same repositories and the same parameter dataset, and 13 of the 47 test positives have a recorded relationship to a training payload family. Training additions were checked against the test set by exact string and by `base_id`, which reduces leakage but does not remove it.
- **It has been inspected during development**, so it should not be treated as untouched.
- **Only 47 positives.** One payload is 2.13 points of recall, and a recall near 0.95 has a 95% interval of about ±6 points. Differences smaller than that cannot be resolved.
- **The evidence behind the positives is weak.** 34 of the 47 come from security write-ups, which describe a technique and not necessarily an observed attack. None was executed.

## Features and evaluation

- **Two features are shape proxies.** `payload_length` and `special_char_ratio` alone reach an external AUC of 0.953. They separate template-shaped strings from plain parameters more than they separate attacks from hard negatives.
- **The first cells of `Model_evaluation.ipynb` use a random, ungrouped split**, kept as the original baseline. The grouped results are in the later cells and in the README.
- **Results are provisional.** Differences between models are often smaller than the seed-to-seed variation.
- **There is no adversarial evaluation** against an attacker who knows the features.

## Reproducibility

- The collection scripts in `scripts/` are partly historical. There is no single command that rebuilds the release.
- The data has not been cleared for redistribution. See the licensing section of [train/SOURCES.md](train/SOURCES.md).

The review status of individual rows is tracked in [DATASHEET.md](DATASHEET.md) section 9.
