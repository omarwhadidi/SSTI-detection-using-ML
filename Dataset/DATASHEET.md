# SSTI Dataset — What It Contains and How It Was Built

**Checked against the local files: 20 September 2026**  
**Owner:** Omar · Iowa State University master's creative component  
**Status:** The files agree with each other. Some labels and source details still need review.

> **Start here:** This document explains the current training and test data, where the examples came from, how they were collected, and what every column means. Counts below are parsed records, not lines in a text editor. This check did not change any payload, label, or feature value.

## Contents

1. [What this dataset is for](#1-what-this-dataset-is-for)
2. [What is in it today](#2-what-is-in-it-today)
3. [How the training set was built](#3-how-the-training-set-was-built)
4. [How the test set was built](#4-how-the-test-set-was-built)
5. [Which files to use](#5-which-files-to-use)
6. [What the columns mean](#6-what-the-columns-mean)
7. [What the 17 number features mean](#7-what-the-17-number-features-mean)
8. [Duplicates, groups, and fair testing](#8-duplicates-groups-and-fair-testing)
9. [What has been checked and what still needs work](#9-what-has-been-checked-and-what-still-needs-work)
10. [Source records, sharing, and future updates](#10-source-records-sharing-and-future-updates)

## 1. What this dataset is for

Server-Side Template Injection, or **SSTI**, can happen when a website treats a user's input as template instructions. A template engine is the software that fills values into a page or other text.

The project studies whether a machine-learning model can identify SSTI-like input strings.

| Word | Simple meaning |
|---|---|
| Example or record | One saved input string and its information. |
| Payload | The input text being studied. The column also holds harmless inputs. |
| Positive, label `1` | An input collected as an SSTI attack or probe candidate. Some still need review. |
| Benign, label `0` | An input collected from a source of normal examples. |
| Probe | A small test intended to reveal whether a template expression is evaluated. It does not have to run a system command. |
| Training set | Examples used to teach the model and choose its settings. |
| Test set | Examples saved separately to measure the finished model. |
| Feature | A number calculated from the text, such as its length. |
| Metadata | Information for people, such as the source URL, engine, or review notes. |

**One record is usually an input value or template fragment. It is not a complete web request, vulnerable application, or confirmed security incident.** The same expression can be normal inside an application's own template and suspicious when submitted by a user. The string alone cannot prove intent or that an application is vulnerable.

## 2. What is in it today

| Set | Positive candidates | Benign examples | Total |
|---|---:|---:|---:|
| Training | 1,905 | 2,001 | **3,906** |
| Test | 47 | 500 | **547** |
| **Both sets** | **1,952** | **2,501** | **4,453** |

The training data is about 49% positive and 51% benign. The test data has many more benign examples than positives. A model predicting every test record as benign would already score about **91.4% accuracy**, so accuracy alone is not enough.

The feature files contain **17 calculated numbers** for each record, together with `payload`, `base_id`, and `label`.

## 3. How the training set was built

### 3.1 Gather positive candidates from public sources

The current positive file records six repositories. These counts were checked directly in `positives.csv`.

| Source | Records | Material collected |
|---|---:|---|
| [payload-box SSTI list](https://github.com/payload-box/ssti-advanced-payload-list) | 1,441 | Engine-specific payload lists in `Intruder/`, including EJS, Smarty, ERB, Pug/Jade, Twig, Thymeleaf, Jinja2, FreeMarker, and Velocity. |
| [PayloadsAllTheThings](https://github.com/swisskyrepo/PayloadsAllTheThings) | 194 | Examples from the Server Side Template Injection pages and `Intruder/ssti.fuzz`. |
| [SecLists](https://github.com/danielmiessler/SecLists) | 29 | `Fuzzing/template-engines-identification.txt` and `Fuzzing/template-engines-expression.txt`. |
| [HackTricks](https://github.com/HackTricks-wiki/hacktricks) | 159 | Code examples from SSTI, Jinja2, and expression-language pages. |
| [ProjectDiscovery fuzzing templates](https://github.com/projectdiscovery/fuzzing-templates) | 17 | 16 records attributed to `ssti/reflection-ssti.yaml`, and one to a client-side Angular template-injection file. **This batch needs review for scope and extraction errors.** |
| [Hackmanit template-injection table](https://github.com/Hackmanit/template-injection-table) | 65 | Engine-identification probes extracted from `engines.js`; related to the TInjA project. |
| **Total** | **1,905** | |

All 1,905 records have repository, file, commit, and URL fields filled in. A **commit** identifies a saved version of a repository. The exact commits and per-file counts are in [Training sources](train/SOURCES.md#positive-sources). Filled fields establish attribution; each payload still needs to be checked against its cited file where this has not been done.

### 3.2 Extract, clean, and keep records of additions

The collection notes describe extracting strings from lists, Markdown code examples, scanner templates, and the engine table. Whitespace was normalized and repeated strings were removed before merging additions. Whitespace normalization changes the representation, so these records should not all be described as exact copies of the original bytes.

Recorded development of the positive set:

| Step | Change | Positive records after the step |
|---|---|---:|
| Earlier collection | 1,635 repository examples plus 366 local seed examples | 2,001 |
| Remove untraceable local seeds from active data | Preserve the 366 removed records in the archive | 1,635 |
| Add SecLists | 29 retained additions | 1,664 |
| Add HackTricks and ProjectDiscovery | 159 + 17 retained additions | 1,840 |
| Add the Hackmanit engine table | 65 retained additions | **1,905** |

The three `positives_added_from_*.csv` files that recorded these additions have been retired
(20 September 2026): every payload and `base_id` in each was verified already present in
`positives.csv`, so they were pure redundancy, not separate data. `train/positives/` now holds one CSV.

Every current positive is unaugmented sourced material — no generated variant is recorded
for any row. This used to be visible as `is_augmentation=no` on every row; that constant
column was dropped in the same pass (see §6.2). It does not mean every upstream repository
string is original or unrelated to other strings. The earlier local seed collection is
archived, not included in today's training set.

### 3.3 Gather benign examples

There are two kinds of benign input:

- **Hard negatives:** normal template fragments. They resemble attacks, so the model must learn more than just the presence of braces.
- **Normal parameters:** ordinary web input values taken from the benign class of HttpParamsDataset. They are benchmark-derived examples, not newly captured production traffic.

| Source | Type | Engine | Training records | Test records |
|---|---|---|---:|---:|
| [Sidekiq](https://github.com/sidekiq/sidekiq) | Template fragments | ERB | 295 | 89 |
| [Symfony demo](https://github.com/symfony/demo) | Template fragments | Twig | 240 | 19 |
| [Microblog](https://github.com/miguelgrinberg/microblog) | Template fragments | Jinja2 | 134 | 25 |
| [Spring Petclinic](https://github.com/spring-projects/spring-petclinic) | Template fragments | Thymeleaf | 118 | 10 |
| [HttpParamsDataset](https://github.com/Morzeux/HttpParamsDataset) | Normal parameters | Not assigned | 1,214 | 357 |
| **Total** | | | **2,001** | **500** |

The recorded template extraction searched for expressions inside delimiters such as `{{...}}`, `{%...%}`, `<%...%>`, `${...}`, and `[[...]]`. It collapsed whitespace, kept strings between 3 and 200 characters with at least one letter, and removed repeated normalized strings. Normal parameters came from the `payload` field of records labelled `norm` in HttpParamsDataset.

Collection notes describe an 85/15 split by template source file and use of the parameter dataset's own train/test files. **The benign records do not retain individual source-file paths, so that file separation cannot currently be verified.** Both sets use the same five repositories.

### 3.4 Add labels, group keys, and features

The positive and benign records were combined, with positives first. The grouping key is `base_id` in the positives file and in the combined file alike. The feature extractor calculates the 17 numbers from each string. Full source and review information stays in the detailed positive and benign files.

## 4. How the test set was built

### 4.1 Gather source-documented examples separately

The test positives were collected from reports, advisories, examples in security articles, scanner material, and a challenge writeup. The retained file has **47 positives from 22 distinct source URLs**. A URL can supply several payloads, and several sources can explain the same technique.

| Recorded evidence type | Records | What it means |
|---|---:|---|
| `security_writeup` | 34 | A security article or researcher explanation. This does not necessarily describe an observed attack. |
| `CVE_PoC` | 9 | An example linked to a CVE or advisory proof of concept. |
| `HackerOne` | 1 | An example attributed to a HackerOne report. |
| `scanner_template` | 2 | An example attributed to scanner material. |
| `CTF` | 1 | An example from a deliberately vulnerable challenge. |
| **Total** | **47** | Categories are saved annotations, not counts of independently verified incidents. |

The full, clickable page-by-page list and counts are in [Test sources](test_set/sources.md#retained-positive-sources). It includes HackerOne, OnSecurity, Intigriti, YesWeHack, PortSwigger, GitHub advisories, and other cited articles.

### 4.2 Keep the template input and its source context

The current release contains 38 records marked `verbatim` and nine marked `source_value_extracted`. The latter were taken from code blocks or values inside JSON/YAML examples; their notes describe any wrapper removal or decoding.

The September scope review removed six related expression/compiler-option injection cases from active use and added nine source-documented candidates. Removed cases and decisions remain in the history ZIP. Stable test IDs were retained, so gaps in IDs are expected; the highest ID is not the record count.

All 47 are currently tagged `scope=template_ssti`. This is a review decision about their intended category. It is not runtime proof. Every test positive currently says `execution_status=not_executed` and `human_review_status=pending`.

### 4.3 Add the 500 benign inputs and export

The test benign examples contain 143 template fragments and 357 normal parameters from the sources in section 3.3. Positives and benign inputs are combined into 547 records, then the same 17 features used for training are calculated.

The main saved positive text is [ssti_test_positives.jsonl](test_set/ssti_test_positives.jsonl). JSONL stores one JSON object per record. It preserves characters and line breaks inside strings. The basic CSV contains the same six fields; the enriched CSV adds source and review information.

**Eight positive payloads contain actual line breaks.** Always use a CSV reader. Counting lines or splitting the file at every newline will give wrong counts and can break the payloads.

## 5. Which files to use

### 5.1 Training files

| File | Records | Purpose |
|---|---:|---|
| [positives.csv](train/positives/positives.csv) | 1,905 | Main positive records, with source details and review flags. Start here to review positives. |
| [positives.txt](train/positives/positives.txt) | 1,905 | Text-only convenience copy. It loses labels and source information. |
| [benign.csv](train/benign/benign.csv) | 2,001 | Main benign records and their source categories. |
| [benign.txt](train/benign/benign.txt) | 2,001 | Text-only convenience copy. |
| [train_combined.csv](train/combined/train_combined.csv) | 3,906 | Positive and benign text with selected metadata. |
| [train_features.csv](train/combined/train_features.csv) | 3,906 | Model-ready numeric features, label, payload, and grouping key. |

### 5.2 Test files

| File | Records | Purpose |
|---|---:|---|
| [ssti_test_positives.jsonl](test_set/ssti_test_positives.jsonl) | 47 | Main positive text and basic source information; preserves multiline payloads. |
| [ssti_test_positives.csv](test_set/ssti_test_positives.csv) | 47 | Basic CSV copy of the same positives. |
| [ssti_test_positives_enriched.csv](test_set/ssti_test_positives_enriched.csv) | 47 | Detailed source, scope, and review fields. Start here to review test positives. |
| [test_benign.csv](test_set/test_benign.csv) | 500 | Main test benign records. |
| [ssti_test_combined.csv](test_set/ssti_test_combined.csv) | 547 | Positive and benign text, with label and source. |
| [test_features.csv](test_set/features/test_features.csv) | 547 | Same 17 features as training, plus label, payload, and grouping key. |

### 5.3 Documentation, scripts, and archives

| Item | Purpose |
|---|---|
| [README.md](README.md) | Quick entry point and file links. |
| [HOW_TO_BUILD_A_DATASET.md](HOW_TO_BUILD_A_DATASET.md) | General guide to building web-vulnerability datasets and comparing benchmarks. |
| [train/README.md](train/README.md), [train/SOURCES.md](train/SOURCES.md), [test_set/sources.md](test_set/sources.md) | More training details and the source catalogs. |
| [CLEANUP_LOG.json](CLEANUP_LOG.json) | Historical record of cleanup actions. Old counts describe those actions, not today's dataset. |
| [scripts/README.md](scripts/README.md) | Which utilities are current and which are historical. |
| `scripts/ssti_feature_extraction.py` | Current definitions of the 17 features. |
| `scripts/reconcile_dataset_exports.py` | Consistency checker and separate repair modes. Only its test-only validation was used for this documentation check. |
| `scripts/extract_to_csv.py` | Text-to-feature utility. Its line-based input is unsuitable for multiline test positives. |
| `scripts/admit_ssti_test_candidates.py`, `scripts/dedup_merge.py`, `scripts/legacy/` | Earlier admission, collection, or grouping logic. Some paths are old and some construction logic is missing. These are not a complete current rebuild pipeline. |

## 6. What the columns mean

### 6.1 Basic columns used across files

| Column | Meaning |
|---|---|
| `payload` | Exact string saved in this file. It may be malicious, a probe, or benign. |
| `label` | Saved target class: `1` positive candidate, `0` benign-source example. |
| `engine` | Template engine associated with the example, such as Jinja2 or Twig. It may be inferred. A blank engine for a normal parameter means none was assigned. |
| `language` | Associated programming language, such as Python or Java. `multi` means several may apply; `unknown` means it was not determined. |
| `base_id` | Text-based grouping key used to keep structurally similar examples together during model evaluation. It is not a unique record ID. |
| `source` | Source description. Benign files use repository tags such as `github:symfony/demo`; the test combined file also uses this field for positive source attribution. |
| `kind` | Benign category: `hard-negative` for template fragments, `normal-param` for normal web values. |

### 6.2 Training positive and addition-file columns

`positives.csv` has the following 10-column layout, in this column order: `payload`,
`base_id`, `language`, `engine`, `label`, `engine_confidence`, `mechanism`,
`suspected_benign`, `review_notes`, `source_url`. The basic fields above also apply.

| Column | Meaning |
|---|---|
| `engine_confidence` | Automatic confidence category: `high` or `low`. This is not a measured probability or proof of execution. |
| `base_id` | The grouping key: the payload's structural skeleton with digits and quoted strings masked and whitespace stripped. The same name is used in every combined and feature export. Group on it when splitting. |
| `mechanism` | Automatic description of the apparent behavior: `probe`, `direct-execution`, `introspection` (inspect objects), `enumeration` (list available objects), `feature-abuse`, or `uncertain`. Every value is automatic and unreviewed. |
| `suspected_benign` | `yes` flags a possible normal example for review. `no` does not mean it was verified as an attack. |
| `review_notes` | Notes about unresolved questions. `manual_review_pending` means someone still needs to inspect the row. |
| `source_url` | The single attribution field: a GitHub blob link of the form `https://github.com/<repo>/blob/<commit>/<file>`, so repository, commit and file path are all readable from it. It is not necessarily the original collection revision. |

Nine columns have been removed from the original 19, in two passes on 20 September 2026.
First: `record_id` and `orig_record_id` (row position identifies the row); `source_repo`,
`source_file` and `source_commit` (all contained in `source_url`); `payload_type_auto` (it
tracked `mechanism` closely enough to be a second name for the same judgement); and
`augmentation_note` and `mechanism_review_status`, which held one identical value on every
row. That last fact — that no mechanism annotation has been human-reviewed — is now stated
in prose here and in `train/SOURCES.md` rather than repeated 1,905 times in a column.
Second: `is_augmentation`, which also held one value (`no`) on every row — the file
currently contains no augmented rows at all, so the flag was pure documentation, not data.
If augmentation is applied later, track lineage through `base_id` rather than reviving this
column. `label` is kept despite being constant (`1`) in this file, for schema consistency
with `benign.csv` (constant `0`) — both are concatenated by row into `train_combined.csv`,
where the column carries real information. The positives file previously called the
grouping key `skeleton_id`; it is `base_id` everywhere now.

The training combined file keeps only: `payload`, `label`, `engine`, `language`, `base_id`, `mechanism`, and `source_url`. Consult the original positive/benign files for the information omitted from this smaller export.

### 6.3 Test positive columns

The basic CSV and JSONL have six fields: `payload`, `engine`, `tier`, `context`, `source_url`, and `label`. The enriched CSV has 22 fields, including these and the extra fields below.

| Column | Meaning |
|---|---|
| `record_id` | Stable test identifier, such as `TEST-053`. IDs have gaps after exclusions. |
| `scope` | Assigned vulnerability scope. All current values are `template_ssti`. |
| `tier` | Older source-evidence grouping: current A rows are CVE/HackerOne, B rows scanner material, C rows writeups/CTF. It is not a severity or validation score. Use `evidence_type` for the clearer description. |
| `evidence_type` | The recorded kind of source, as listed in section 4.1. |
| `context` | Explanation of how the input appeared or was used in its source. |
| `source_url` | Page or file credited for the input. |
| `related_train_family` | `yes` means a relationship to training examples was recorded. `no` means no relationship was recorded in this field. |
| `near_train_family` | `exact` means an exact stored skeleton relationship, not identical raw text. `yes` means a recorded nearby family relationship. `no` does not certify independence. |
| `capture_status` | `verbatim` records a direct-copy claim; `source_value_extracted` records extraction of a value from source material. |
| `candidate_id` | Identifier used during candidate collection, when available. |
| `identifiers` | Associated CVE, advisory, or other identifiers, when saved. A blank cell means none was recorded here. |
| `source_locator` | Where to find the example on the page, such as a heading or code block. |
| `extraction_method` | What was extracted or decoded, such as a JSON string or YAML value. Blank older entries mean the method was not saved in this field. |
| `scope_review_status` | Recorded assistant review of scope, or source and scope. This is separate from human review. |
| `execution_status` | Whether the payload was run for validation. All current values are `not_executed`. |
| `human_review_status` | Human-review state. All current values are `pending`. |
| `review_notes` | Source, interpretation, and unresolved-review notes. |
| `related_train_ids` | Training IDs associated with a family comparison. Older notes may refer to earlier IDs; trace through the recorded history. |
| `family_review_notes` | Explanation of why examples appear related. |

The test combined file contains only `payload`, `label`, and `source`. Unlike the training combined file, it has **no `base_id` column**. The test feature file does contain `base_id`.

## 7. What the 17 number features mean

These definitions follow the current [feature code](scripts/ssti_feature_extraction.py). They are pattern counts and flags, not proof that an attack works.

| Feature | Value | What the code measures |
|---|---|---|
| `payload_length` | Integer | Number of characters in the saved string. |
| `special_char_ratio` | 0–1 | Characters that are neither letters/digits nor whitespace, divided by total length; rounded to six decimals. Empty input gives 0. |
| `count_double_brace` | Count | Occurrences of the opening `{{`. |
| `count_dollar_brace` | Count | Occurrences of `${`. |
| `count_hash_brace` | Count | Matches for `#{`, `#set`, `#foreach`, and `#if`. |
| `count_percent_brace` | Count | Matches for `%{`. Despite its name, it does not count `{%`. |
| `count_erb` | Count | Matches for `<%`, `%>`, `<#`, and `<@`. It can count both opening and closing markers. |
| `delimiter_family_count` | 0–5 | Number of the code's five marker groups found. This is not the number of actual template engines. |
| `max_bracket_depth` | Integer | Highest nesting counter for round, square, and curly brackets. The counter does not check that bracket types match. |
| `has_dunder_chain` | 0 or 1 | Presence of a listed Python double-underscore name, such as `__class__`. A single match is enough; a full chain is not required. |
| `has_exec_tokens` | 0 or 1 | Presence of a listed execution-related pattern, such as `popen`, `ProcessBuilder`, or a shell path. |
| `has_java_reflection` | 0 or 1 | Presence of a listed Java object/reflection pattern, such as `getClass` or `getMethod`. |
| `has_flask_objects` | 0 or 1 | Presence of a listed name such as `request`, `config`, `cycler`, or `self`. These can also occur in normal templates. |
| `has_arithmetic_operation` | 0 or 1 | A number/operator/number pattern inside recognized template interiors. If none are captured, it scans the whole string, so non-template text can also match. |
| `has_string_operation` | 0 or 1 | A listed string-operation pattern, including `~`, some quoted concatenations, or calls such as `.join()` and `.replace()`. |
| `count_method_calls` | Count | Matches shaped like a dot, a name, and an opening parenthesis, such as `.get(`. |
| `count_dots` | Count | Every literal `.` character. |

Both feature files have the same 20 columns: `payload`, `base_id`, these 17 features, and `label`. The CSVs store the raw calculated numbers. Scaling, when needed by a model, happens later in the evaluation pipeline.

Only the 17 feature columns go into the current numeric model. `label` is the answer to predict, and `base_id` controls grouping. IDs, source URLs, engine annotations, and review decisions must not accidentally become prediction inputs.

## 8. Duplicates, groups, and fair testing

### 8.1 Different meanings of “the same”

| Check | Example meaning |
|---|---|
| Exact duplicate | Identical saved string. |
| Normalized duplicate | Strings become equal under a specified cleanup rule, such as transport decoding. Different normalizers can give different answers. |
| Same skeleton | Strings have the same stored structural pattern after masking variable text. |
| Related attack family | Different-looking strings use the same underlying technique. This may require a person's judgment. |

Historical skeleton logic repeatedly URL-decodes, lowercases, masks quoted strings and digits, and removes whitespace. Stored keys are a rough grouping tool; they are not proven engine-aware families. There are **1,283 stored positive skeletons** and **1,432 stored benign keys** in training. Do not add these counts and call the result independent attack families.

For example, two arithmetic probes that differ only in numbers should generally stay in the same development group. Grouping limits memorization of small variants. It cannot catch every relationship between attacks written in different ways.

### 8.2 Current overlap findings

- No repeated exact payloads were found within each separate positive or benign file.
- **One training string occurs in both classes:** `{% endif %}`, positive ID `POS-1805`, also appears in the benign file. Its conflicting labels remain unresolved.
- The current test validator found no exact or conservatively normalized test duplicates and no such matches against the active or evaluation training files.
- **13 of the 47 test positives have recorded training-family relationships.** This is the union of `related_train_family=yes` and `near_train_family` equal to `yes` or `exact`; do not add the fields' separate counts because they overlap.
- The other 34 test positives are unflagged, not certified as independent families.
- Benign train and test share repositories. There is no demonstrated benign repository holdout.

### 8.3 How to use the sets fairly

Use grouped splits within training when selecting settings. Keep matching `base_id` values together, including during cross-validation. Fit any scaler or learned text representation using only the training portion of each split, then reuse it on that split's validation data.

Use the fixed test set after choosing model settings. Report results for all 47 positives and, where useful, the 34 currently unflagged positives as a clearly labelled subset. Explain that this smaller subset is not proof of unseen attack families.

Report attack recall, precision, F1, false positives, and the actual confusion-matrix counts. One missed test positive changes recall by about **2.13 percentage points**, so this small set cannot support very precise estimates. Earlier test inspection and repeated dataset changes must also be disclosed; the set has already been used during development review.

## 9. What has been checked and what still needs work

### 9.1 File checks completed on 20 September 2026

| Check | Result |
|---|---|
| Training record counts and source totals | Confirmed against the CSVs. |
| Training positive/benign records versus combined and feature exports | Payloads, labels, order, and stored group keys agree. |
| Feature calculation | All 17 values recomputed for all 3,906 training and 547 test records; no mismatches found within the checked numeric tolerance. |
| Test serialization and source-capture alignment | Existing test-only validator passed against the saved historical evidence. This is not a fresh audit of every website. |
| Evaluation feature copies | `model_evaluation/train_features.csv` and `model_evaluation/test_features.csv` are byte-identical to the current Dataset feature files. The old 4,002-row warning is obsolete. |
| Positive training attribution fields | All 1,905 rows have the four source fields filled in. |
| Payload execution or model retraining | Not performed in this documentation check. |

### 9.2 Review work still needed

| Finding | Why it matters | Next step |
|---|---|---|
| One exact positive/benign label conflict | Identical inputs have different answers. | Review both source contexts and apply a consistent labelling policy. |
| 884 training rows contain `manual_review_pending` | Extraction or payload type is unresolved. | Inspect each flagged row in its source context. |
| Four training rows have `suspected_benign=yes` | They may be normal examples. | Review them; do not delete based only on this automatic flag. |
| All 1,905 mechanism annotations are `auto_unreviewed` | Descriptive labels were assigned automatically. | Review before presenting mechanism-level results as verified. |
| 630 mechanisms are `uncertain`; 205 automatic payload types are blank | The current metadata is incomplete. | Fill values only when supported by evidence. |
| ProjectDiscovery batch includes scanner expressions/placeholders and one CSTI-source row | Scanner construction code and client-side examples may not be actual SSTI inputs. | Check each row against its file and the project's scope. |
| All 47 test positives are not executed and await human review | Source documentation does not prove behavior in a particular engine/version. | Review sources and, for runtime claims, validate in controlled matching environments. |
| Benign records lack per-example source-file paths | Recorded file separation cannot be audited. | Recover paths and locations where possible. |
| Original collectors are incomplete or assume older layouts | A new researcher cannot rebuild the release with one reliable command. | Preserve the current data and complete a separate reproducible build process. |

The 884 pending rows consist of 643 earlier review flags, 176 HackTricks/ProjectDiscovery additions, and 65 Hackmanit probes. The four suspected-benign rows are a separate flag that may overlap other review categories. Counts of different flags should not be summed into one number of faulty rows.

Old evaluation results remain historical until their model code, preprocessing, split procedure, and input version are checked together. Matching feature copies fixes the stale-file description; it does not establish that the previous scaling defect, model execution, or cross-validation has been corrected.

### 9.3 Claims to avoid

- Do not call this the first SSTI dataset or detector. Earlier work on SSTI exists and should be cited.
- Do not call the whole test set CVE/HackerOne data or independently observed incidents. Most records are tagged as writeup-derived.
- Do not equate no exact duplicates with no related attack families.
- Do not describe all labels as human-reviewed or all payloads as successfully executed.
- Do not treat a high score on 47 positives as proof of production performance.

## 10. Source records, sharing, and future updates

### 10.1 What “keep provenance” means

**Provenance means keeping the history of where an example came from.** Another person should be able to find the source, understand what you copied, and see what changed.

For each example, keep its ID, original text, source link, file/section location, saved source version, extraction steps, and review decision. The current training positives have file/commit attribution; newer test records have extraction fields; benign records retain less detail.

A useful review note explains the decision, for example: “The source shows this as normal template syntax; human review pending.” A later review should record who checked it, when, what evidence was used, and the decision. These are recommended future records, not fields that already exist everywhere.

**Blank means not recorded.** A populated source URL means a source was cited. Neither a blank flag nor a present URL proves that the payload was independently verified.

### 10.2 Source permissions and distribution status

The folder combines material from multiple repositories and websites. Existing source notes list licenses and unresolved checks in [Training sources — Licensing](train/SOURCES.md#licensing). Those license statements were not re-verified during this local documentation audit.

The project has not established one blanket redistribution permission covering every record. Public availability and attribution alone do not establish that permission. Keep source-specific terms and notices with the release, and resolve the pending checks before claiming that the whole dataset has a particular license. The earlier CC BY 4.0 suggestion is a proposal, not a confirmed license for all underlying material.

### 10.3 Updating the dataset without losing its history

1. Keep the existing record ID and source history when reviewing a row.
2. Record whether you changed only metadata or changed the payload, label, or group key.
3. If payloads, labels, or groups change, rebuild the affected combined/feature exports and check all copies. Pure review-note changes do not change the 17 feature values, although metadata copies may need refreshing.
4. Compare new training candidates with the held-out test data under documented duplicate and grouping rules. This avoids direct reuse but does not prove independent sources or families.
5. Update counts, source summaries, review totals, and the file manifest. Preserve historical logs as history rather than replacing their earlier facts.
6. Record the dataset version used for every model run. Keep train/test data and all archives clearly separated.

**This revision updates documentation and inventory. It does not resolve pending labels, add examples, or establish new model results.**
