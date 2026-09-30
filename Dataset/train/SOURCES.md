# Training set — sources and provenance

This file is the attribution ledger for the SSTI training corpus. It records where every
training payload came from, at which pinned revision, and what that provenance does and
does not prove. It replaces the former `Dataset/sources/` and `Dataset/review/` folders,
whose remaining historical material was archived on 19 September 2026 (see
`Dataset/_archive/dataset_history_2026-09-19.zip`).

Counts below are parsed data records, excluding headers, as of 19 September 2026.

## Current training corpus

| part | records | file |
|---|---:|---|
| positives (label = 1) | 1,905 | `positives/positives.csv` |
| benign (label = 0) | 2,001 | `benign/benign.csv` |
| combined | 3,906 | `combined/train_combined.csv` |
| combined + 17 features | 3,906 | `combined/train_features.csv` |

The corpus is no longer 1:1 balanced. It is roughly 49% positive / 51% benign, which is
why ROC-AUC and attack-class recall are the headline metrics rather than accuracy.

## Positive sources

Every positive record carries a single pinned `source_url`, populated for all 1,905 rows.
The URL has the form `https://github.com/<repo>/blob/<commit>/<file>`, so the repository,
the exact commit and the file path are all recoverable from it — which is why the separate
`source_repo`, `source_file` and `source_commit` columns were removed on 20 September 2026
as redundant. The tables below are derived from those URLs.

| source repository | records | pinned commit |
|---|---:|---|
| `payload-box/ssti-advanced-payload-list` | 1,441 | `957fb1fab4ded0f1f38e57f4e6c5b388698e501a` |
| `swisskyrepo/PayloadsAllTheThings` | 194 | `3ac27901c711bdf3f5b65a7b1d1820a1f65bd09a` |
| `danielmiessler/SecLists` | 29 | `d9458f277ed978a608ad165e5eb2fdb389e4c7ee` |
| `HackTricks-wiki/hacktricks` | 159 | `14f4a7d1b6d3534336d2a8740e3e893ffa38ea74` |
| `projectdiscovery/fuzzing-templates` | 17 | `5585787b43e6f7242fcbb706688f9528be63e29f` |
| `Hackmanit/template-injection-table` | 65 | `4be3ec7f8a7de162dd3bb340b54560938bfdfab2` |

### Per-file breakdown

**payload-box/ssti-advanced-payload-list** — engine-specific Burp Intruder payload lists.

| file | records |
|---|---:|
| `Intruder/ejs.txt` | 198 |
| `Intruder/smarty.txt` | 188 |
| `Intruder/erb-ruby.txt` | 182 |
| `Intruder/pug-jade.txt` | 169 |
| `Intruder/twig.txt` | 148 |
| `Intruder/thymeleaf.txt` | 144 |
| `Intruder/jinja2-flask.txt` | 118 |
| `Intruder/all-payloads.txt` | 111 |
| `Intruder/freemarker.txt` | 96 |
| `Intruder/velocity.txt` | 87 |

**swisskyrepo/PayloadsAllTheThings** — the `Server Side Template Injection/` section.

| file | records |
|---|---:|
| `Java.md` | 76 |
| `Python.md` | 48 |
| `PHP.md` | 34 |
| `JavaScript.md` | 20 |
| `Ruby.md` | 7 |
| `Elixir.md` | 5 |
| `Intruder/ssti.fuzz` | 4 |

**danielmiessler/SecLists** — template-engine fuzzing lists, added 19 September 2026.

| file | records |
|---|---:|
| `Fuzzing/template-engines-identification.txt` | 22 |
| `Fuzzing/template-engines-expression.txt` | 7 |

The SecLists contribution is mostly **polyglot engine-identification vectors** — strings
that wrap a template expression in surrounding text so the engine reveals itself by what
it renders. That shape is under-represented in the other two repositories, which is the
reason for including it.

**HackTricks-wiki/hacktricks** — the SSTI section of the wiki, added 19 September 2026.
Payloads were extracted from fenced and inline code spans in the SSTI pages.

| file | records |
|---|---:|
| `.../ssti-.../README.md` | 87 |
| `.../ssti-.../jinja2-ssti.md` | 60 |
| `.../ssti-.../el-expression-language.md` | 12 |

**projectdiscovery/fuzzing-templates** — Nuclei SSTI/CSTI fuzzing templates, added 19
September 2026.

| file | records |
|---|---:|
| `ssti/reflection-ssti.yaml` | 16 |
| `csti/angular-client-side-template-injection.yaml` | 1 |

Because HackTricks is a prose wiki rather than a flat payload list, its extraction is
noisier than the other sources: all 176 rows from these two repositories carry
`review_notes = manual_review_pending`, and 91 of them received a `mechanism = uncertain`
label the automatic heuristic could not resolve. Treat this batch as review candidates
until spot-checked in source context, not as verified payloads.

**Hackmanit/template-injection-table** — the TInjA project's engine-identification table,
added 19 September 2026. Probe strings were extracted from the table's data file (`engines.js`).

| file | records |
|---|---:|
| `engines.js` | 65 |

These are polyglot / engine-fingerprinting probes, so nearly all are labelled
`mechanism = probe`; they carry `manual_review_pending` like the other extracted batches.

### Language and engine distribution

Language is derived from the source file or the delimiter syntax, not from execution.

| language | records |
|---|---:|
| java | 459 |
| javascript | 388 |
| php | 370 |
| python | 286 |
| ruby | 245 |
| multi | 120 |
| unknown | 32 |
| elixir | 5 |

`multi` means the payload uses a delimiter shared by several engines and the source file
did not disambiguate. `unknown` means the heuristic could not decide — it is recorded as
unknown deliberately rather than guessed.

The ten most frequent engine labels are unknown (426), EJS (198), ERB (193), Smarty (188),
Jinja2 (178), Pug/Jade (169), Twig (148), Thymeleaf (144), FreeMarker (96), Velocity (87).
The large `unknown` bucket is mostly `Intruder/all-payloads.txt`, the SecLists files, and
the HackTricks README, which are not organised by engine.

## Removed material — sources-only policy

An earlier version of this corpus held 2,001 positives. 366 of those were **local seed
payloads** with no traceable upstream source. They were removed so that every training
positive can be pointed at a public file at a pinned commit. The removed rows are kept at
`_archive/positives_removed_localseed.csv`; they are not part of any active export.

Successive states are preserved under `_archive/` for rollback: `*_pre_seclists.*`
(1,635 positives), `*_pre_hacktricks.*` (1,664), `*_pre_tinja.*` (1,840). Each addition batch
was also exported separately for transparency at the time
(`positives_added_from_seclists.csv`, `_hacktricks_fuzzingtemplates.csv`, `_tinja.csv`).
Those three exports were retired on 20 September 2026: every payload and `base_id` in each
was already present in `positives.csv`, so they held no data that the single file didn't
already have. They are kept at `_archive/` (unchanged) for provenance; `positives/` now
holds exactly one file, `positives.csv`.

## Collection and deduplication rules

Collection notes describe extraction from source files, whitespace normalization, and
exact-string deduplication before merging. Normalization changes the saved representation;
do not describe all rows as byte-for-byte source copies. No row in `positives.csv`
is a generated evasion variant — the current positive set is entirely sourced material,
none of it augmented; this was `is_augmentation = no` on all 1,905 rows before that
constant column was dropped on 20 September 2026 (see Pending review work). Additions were deduplicated against **both** the existing training corpus **and
the frozen test set**: any candidate matching a test payload by exact string, or sharing a
test payload's `base_id`, was dropped according to the collection notes (3 such
collisions were recorded in the 2026-09-19 batch). These checks do not establish an
independent test distribution or catch every related family. See the current overlap
findings in [the datasheet](../DATASHEET.md#8-duplicates-groups-and-fair-testing).

`base_id` is the structural skeleton of a payload with digits and quoted strings masked
and whitespace stripped. There are **1,283 distinct positive skeletons** across 1,905
payloads. This is the grouping key: use it for `GroupShuffleSplit` / `StratifiedGroupKFold`
in both the outer split and inner CV, so that variants of one payload never straddle
train and test. Plain stratified splitting on this corpus leaks.

## Benign sources

The benign class is drawn from public repositories and benchmark data, in two kinds.

**Hard negatives** are legitimate template expressions extracted from real open-source
template files. They are the difficult negatives — syntactically they look exactly like
the positives. They do not establish that a string-only model can infer whether an
expression is used maliciously, which is a genuine limitation of the whole framing.

**Normal parameters** are public-benchmark HTTP parameter values. The source dataset
traces its benign examples to CSIC2010. Do not describe these as newly captured
production traffic.

| kind | train | test |
|---|---:|---:|
| hard negatives (template expressions) | 787 | 143 |
| normal HTTP parameters | 1,214 | 357 |
| **total** | **2,001** | **500** |

### Sources and pinned commits (collected 2026-09-15)

| repository | engine | train records | commit |
|---|---|---:|---|
| `sidekiq/sidekiq` | ERB | 295 | `bdc197a9bc1590bcae2f9c06805df0f9583cd1b7` |
| `symfony/demo` | Twig | 240 | `920d86dc809f837543cb519d3df5b364a2c36577` |
| `miguelgrinberg/microblog` | Jinja2 | 134 | `a975ef64864354867c88e0ed3a17ba7d17dca752` |
| `spring-projects/spring-petclinic` | Thymeleaf | 118 | `818c4136ea971c21674525f9053de0d9c7ad8cfe` |
| `Morzeux/HttpParamsDataset` | — (params) | 1,214 | `926670a710283f87c05b554680facf3f9530548c` |

The 143 test hard negatives break down as 89 Sidekiq, 25 microblog, 19 Symfony demo, and
10 Spring Petclinic.

### Extraction rules (reproducible)

Template expressions were matched by delimiter regex across the template files:
`{{...}}`, `{%...%}`, `<%=...%>` / `<%...%>`, `[[...]]`, `[(...)]`, `${...}`, `*{...}`,
`#{...}`, `@{...}`. Whitespace was collapsed, length was restricted to 3–200 characters,
and a match had to contain at least one letter, which drops empty delimiters like `{{ }}`.
Results were deduplicated after normalisation.

Normal parameters are the `payload` column of rows labelled `norm` in the source dataset.

There are 1,432 distinct benign skeletons (`base_id`) across the 2,001 train records.

### Recorded split procedure and its verification limits

Collection notes describe an 85/15 split by template source file, and use of the source
dataset's own train/test parameter split (`payload_train.csv` versus `payload_test.csv`)
followed by deduplication. Both are *recorded procedure, not verified outcome*:

- **Per-record source paths were not retained**, so file-level disjointness cannot
  currently be independently verified. Restore those paths from collection evidence before
  claiming it as checked.
- **Train and test share repositories**, including Sidekiq, and share the same
  HTTP-parameter dataset. No repository holdout is established on the benign side.
- Deduplication checks are string diagnostics. They do not certify semantic or family
  independence.

### Balance note

Earlier documentation described the benign set as balanced 1:1 against 2,001 positives.
That is now stale — the positive count is 1,905 after the sources-only cleanup and the
SecLists additions. Nothing about the benign data itself changed; only the ratio did.

## What this provenance does not prove

These are the limits a reviewer will push on, so they are recorded here rather than in a
footnote:

- **A populated URL is an attribution, not a verification.** The `source_url` fields point
  at pinned files, but each payload has not been individually re-confirmed to occur in the
  cited snapshot. That check is outstanding.
- **A pinned commit is not the original collection revision.** The commits are the
  revisions the files were read at; they should not be described as the state of the
  repository at the moment of first collection unless that is separately evidenced.
- **Train and test share benign repositories.** Both draw on the same four template repos
  (including Sidekiq) and the same HTTP-parameter dataset. No repository holdout exists on
  the benign side, so benign independence between train and test is not established.
- **Skeleton grouping is structural, not semantic.** Grouping on `base_id` prevents
  shared stored skeletons from straddling the split. It does not prevent two payloads that
  exploit the same underlying mechanism through different syntax from landing on opposite
  sides.
- **Engine, language, and mechanism labels are automatic.** All 1,905 rows are
  automatic and unreviewed. They are usable as descriptive metadata and
  for stratification diagnostics; they are not human-verified ground truth.

## Pending review work

The positives file was reduced from 19 columns to 11 on 20 September 2026, then to
10 on the same day in a second pass. First pass removed as redundant: `record_id` and
`orig_record_id` (row position is the identifier), `source_repo` / `source_file` /
`source_commit` (all recoverable from `source_url`), `payload_type_auto` (it tracked
`mechanism` closely enough to be a second name for it), and two columns that held the same
value on every row — `augmentation_note` and `mechanism_review_status`. Second pass dropped
`is_augmentation`, which also held one value (`no`) on all 1,905 rows — the entire file is
currently un-augmented sourced material, so the flag carried no information; if augmentation
is applied to positives in the future, lineage between an original and its augmented variant
belongs to `base_id`, not a boolean column, so `is_augmentation` is not expected to come
back. `label` stays even though it is constant (`1`) here — it is kept for schema
consistency with `benign.csv` (constant `0`), since both files get concatenated by row into
`train_combined.csv` where the column is not constant. The grouping key, previously
`skeleton_id` here and `base_id` everywhere else, is now `base_id` in every file.

**All mechanism annotations remain automatic and unreviewed.** That fact used to live in
the `mechanism_review_status` column; it is recorded here instead, because a column that
holds one value on all 1,905 rows is documentation, not data.

The current schema, in column order, is `payload`, `base_id`, `language`, `engine`,
`label`, `engine_confidence`, `mechanism`, `suspected_benign`, `review_notes`,
`source_url`.

Row-level review flags live inside `positives/positives.csv` rather than in separate
files:

- `suspected_benign = yes` — 4 rows whose payloads may be ordinary template usage rather
  than attacks. Review each in its source context. Do not delete them automatically; an
  earlier automatic pass wrongly removed genuine probes and had to be reversed.
- `review_notes` contains `manual_review_pending` for 884 rows: 643 carried over from the
  September 2026 review list, plus 176 HackTricks / fuzzing-templates additions and 65
  TInjA-table probes whose extraction needs source-context confirmation. These are review
  candidates with unresolved payload-type questions, not confirmed mislabels.

Both flags are metadata. Changing them does not require recomputing features. Changing a
payload, label, or grouping key does — regenerate `combined/train_features.csv` with
`../scripts/ssti_feature_extraction.py` after any such change, and never edit a feature
export by hand.

## Licensing

Each source repository carries its own licence and they differ. Verify before any public
redistribution; the `source_repo` / `source_file` / `source_commit` / `source_url` columns
on the positives and the `source` column on the benign records are the attribution ledger
for that purpose.

| source | role | licence |
|---|---|---|
| `swisskyrepo/PayloadsAllTheThings` | train positives | MIT |
| `payload-box/ssti-advanced-payload-list` | train positives | MIT |
| `danielmiessler/SecLists` | train positives | MIT *(not yet re-verified from LICENSE)* |
| `HackTricks-wiki/hacktricks` | train positives | *(wiki — verify licence before release)* |
| `projectdiscovery/fuzzing-templates` | train positives | MIT *(not yet re-verified)* |
| `Hackmanit/template-injection-table` | train positives | Apache-2.0 (keep NOTICE) |
| `miguelgrinberg/microblog` | benign hard negatives | MIT |
| `symfony/demo` | benign hard negatives | MIT |
| `spring-projects/spring-petclinic` | benign hard negatives | Apache-2.0 (keep NOTICE) |
| `sidekiq/sidekiq` | benign hard negatives | **LGPL-3.0 — see caution** |
| `Morzeux/HttpParamsDataset` | benign parameters | MIT |

**Caution — Sidekiq (LGPL-3.0).** The extracted items are short, functional template
expressions, likely below the threshold of copyrightability, but LGPL is copyleft. Before
public release either document that short-snippet rationale and keep attribution, or
re-harvest the ERB hard negatives from a permissively licensed Rails/ERB project and drop
the 295 Sidekiq-derived rows. The second option keeps the dataset uniformly permissive and
is the safer choice for release.

CC BY 4.0 was proposed for a future release, but is not a confirmed license covering all
underlying records. The license names and Sidekiq discussion above are historical source
notes, not a completed permissions review. Resolve source-specific terms before making
blanket redistribution claims; attribution alone does not establish permission.
