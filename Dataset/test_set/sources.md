# Sources — current SSTI test subset

**47 positives across 22 source pages; 500 benign inputs; 547 total records.** Updated 18 September 2026.

## Scope and review

The scope review and admission decisions were archived on 2026-09-19 to
`../_archive/dataset_history_2026-09-19.zip` (`review/TEST_SCOPE_REVIEW_2026-09-18.md`). Source-documented template inputs include probes and information disclosure, not only RCE. Earlier XSS stages are context, not active positive rows. Six related-injection inputs are preserved outside the active set in the review ledger.

## Retained positive sources

| Retained source page | Positive rows |
|---|---:|
| [hackerone.com/reports/125980](https://hackerone.com/reports/125980) | 1 |
| [routezero.security/2025/02/17/proving-grounds-practice-cve-2024-56145-walkthrough/](https://routezero.security/2025/02/17/proving-grounds-practice-cve-2024-56145-walkthrough/) | 2 |
| [onsecurity.io/article/server-side-template-injection-with-jinja2/](https://onsecurity.io/article/server-side-template-injection-with-jinja2/) | 6 |
| [0x1.gitlab.io/web-security/Server-Side-Template-Injection/](https://0x1.gitlab.io/web-security/Server-Side-Template-Injection/) | 12 |
| [www.intigriti.com/researchers/blog/hacking-tools/exploiting-server-side-template-injection-ssti](https://www.intigriti.com/researchers/blog/hacking-tools/exploiting-server-side-template-injection-ssti) | 4 |
| [www.yeswehack.com/learn-bug-bounty/server-side-template-injection-exploitation](https://www.yeswehack.com/learn-bug-bounty/server-side-template-injection-exploitation) | 5 |
| [dev.to/roxdavirox/ssti-in-apis-when-json-parameters-reach-template-engines-and-become-rce-339n](https://dev.to/roxdavirox/ssti-in-apis-when-json-parameters-reach-template-engines-and-become-rce-339n) | 1 |
| [dev.to/roxdavirox/server-side-template-injection-how-to-identify-the-engine-and-escalate-to-rce-386b](https://dev.to/roxdavirox/server-side-template-injection-how-to-identify-the-engine-and-escalate-to-rce-386b) | 1 |
| [projectdiscovery.io/blog/crafting-dast-nuclei-templates-for-oob-template-engines-injection-a-practical-guide](https://projectdiscovery.io/blog/crafting-dast-nuclei-templates-for-oob-template-engines-injection-a-practical-guide) | 1 |
| [github.com/geeknik/the-nuclei-templates/blob/main/node-nunjucks-ssti.yaml](https://github.com/geeknik/the-nuclei-templates/blob/main/node-nunjucks-ssti.yaml) | 1 |
| [7rocky.github.io/en/htb/nunchucks/](https://7rocky.github.io/en/htb/nunchucks/) | 1 |
| [onsecurity.io/article/go-ssti-method-research/](https://onsecurity.io/article/go-ssti-method-research/) | 2 |
| [tarq.net/posts/handlebars-4-1-2-command-execution/](https://tarq.net/posts/handlebars-4-1-2-command-execution/) | 1 |
| [github.com/open-metadata/OpenMetadata/security/advisories/GHSA-5f29-2333-h9c7](https://github.com/open-metadata/OpenMetadata/security/advisories/GHSA-5f29-2333-h9c7) | 1 |
| [github.com/jumpserver/jumpserver/security/advisories/GHSA-qx8h-rx2j-j5wc](https://github.com/jumpserver/jumpserver/security/advisories/GHSA-qx8h-rx2j-j5wc) | 1 |
| [github.com/getgrav/grav/security/advisories/GHSA-c9gp-64c4-2rrh](https://github.com/getgrav/grav/security/advisories/GHSA-c9gp-64c4-2rrh) | 1 |
| [github.com/cachethq/cachet/security/advisories/GHSA-hv79-p62r-wg3p](https://github.com/cachethq/cachet/security/advisories/GHSA-hv79-p62r-wg3p) | 1 |
| [github.com/jupyter-server/enterprise_gateway/security/advisories/GHSA-f49j-v924-fx9w](https://github.com/jupyter-server/enterprise_gateway/security/advisories/GHSA-f49j-v924-fx9w) | 1 |
| [github.com/knadh/listmonk/security/advisories/GHSA-jc7g-x28f-3v3h](https://github.com/knadh/listmonk/security/advisories/GHSA-jc7g-x28f-3v3h) | 1 |
| [sec.stealthcopter.com/wpml-rce-via-twig-ssti/](https://sec.stealthcopter.com/wpml-rce-via-twig-ssti/) | 1 |
| [www.sonarsource.com/blog/it-s-a-snmp-trap-gaining-code-execution-on-librenms/](https://www.sonarsource.com/blog/it-s-a-snmp-trap-gaining-code-execution-on-librenms/) | 1 |
| [portswigger.net/research/server-side-template-injection](https://portswigger.net/research/server-side-template-injection) | 1 |

## Evidence and independence

Evidence annotations: HackerOne=1, CVE_PoC=9, security_writeup=34, scanner_template=2, CTF=1. Tier annotations: A=10, C=35, B=2. These count rows, not independent incidents; older categories still need source-type review.

13 positives have known training-family relationships. Zero exact/transport-normalized string duplicates does not establish family independence. Six newly flagged comparisons include training IDs in the enriched records; original seven flags retain their earlier annotations.

## Benign sources

The 500 unchanged benign rows contain 143 template fragments (89 Sidekiq, 25 microblog, 19 Symfony demo, 10 Spring Petclinic) and 357 HttpParamsDataset parameters. See [benign source references](../train/SOURCES.md#benign-sources). Train/test share repositories; file separation is not independently established without per-record paths.

## Files to use

| File | Purpose |
|---|---|
| [ssti_test_positives.jsonl](ssti_test_positives.jsonl) | Canonical 47 positive inputs, with engine, context and source URL. Preserves multiline strings. |
| [ssti_test_positives.csv](ssti_test_positives.csv) | Restored basic CSV export of the same 47 positives: payload, engine, tier, context, source URL and label. |
| [ssti_test_positives_enriched.csv](ssti_test_positives_enriched.csv) | The same positives with stable IDs, source details, review notes and family flags. Best for manual review. |
| [test_benign.csv](test_benign.csv) | The 500 benign inputs with their source metadata. |
| [ssti_test_combined.csv](ssti_test_combined.csv) | All 547 examples, ready for loading: positives followed by benign inputs. |
| [features/test_features.csv](features/test_features.csv) | The 17 computed features used by evaluation, plus `base_id` for group-aware analysis. |
| [sources.md](sources.md) | This source catalog and file guide. |

## Cleanup and validation

Four redundant exports were previously removed after checking all fields. The basic positive CSV has now been restored at the user's request; the TSV, enriched positive JSONL and benign TXT remain removed. No examples, labels, provenance or feature values were changed. Their hashes and replacement files are recorded in [the cleanup log](../CLEANUP_LOG.json).

Read CSV with a CSV parser because some fields contain actual newlines. Run
`../scripts/reconcile_dataset_exports.py --validate --test-only` for current checks.
The validator reads the retained files and original research evidence from the history ZIP.
Historical collection/admission scripts describe earlier layouts and must not rebuild this release.

The evaluation-folder test-feature copy is kept for compatibility and matches the canonical file.
Source attribution is recorded per row; public availability alone is not permission to redistribute.
