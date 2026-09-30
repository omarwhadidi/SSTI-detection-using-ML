# How to Build a Dataset for Web Vulnerabilities

**A beginner's guide, in the order you would do the work**  
Updated: **18 September 2026**

A **dataset** is a collection of examples arranged so that a person or computer can study them. For web security, an example might be a form value, a web request, or a piece of code.

Start with **Part 1** and follow the steps in order. **Part 2** lists datasets and benchmarks by vulnerability, such as SQL injection and XSS. The later parts explain record keeping and testing in more detail.

## Contents

- [Part 1. Build the dataset step by step](#part-1-build-the-dataset-step-by-step)
- [Part 2. Datasets and benchmarks by vulnerability](#part-2-datasets-and-benchmarks-by-vulnerability)
- [Part 3. Source records and review notes explained](#part-3-source-records-and-review-notes-explained)
- [Part 4. Understand the results](#part-4-understand-the-results)
- [Part 5. Final checklist](#part-5-final-checklist)

---

## Part 1. Build the dataset step by step

### Step 1. Decide what you want to detect

Start with one clear sentence.

**Example:** “I want to detect SQL injection attempts in values submitted through web forms.”

That sentence tells you what to collect and what the model should learn. A **model** is the program that learns patterns from examples and uses them to make predictions.

You might instead want to detect XSS, several attack types, or weaknesses in application code. Those are different tasks.

| Your goal | What you should collect |
|---|---|
| Detect suspicious form values | The actual values submitted |
| Detect attacks in web requests | Complete requests, including the relevant fields |
| Find SQL injection weaknesses in code | Code examples with evidence that they are vulnerable or safe |
| Detect unauthorized access | Requests plus information about the user, permissions, and resource owner |

**Important:** an attack attempt is something someone sends or does. A vulnerability is a weakness in the application. Detecting one does not automatically prove the other.

**What you should have when finished:** a one-sentence goal and a decision about what the model will receive.

### Step 2. Decide what one row means

A **row**, also called a **record**, should represent one example of the kind you chose.

For a form-value dataset, one row could be `O'Reilly`. For a request dataset, it could be the complete request containing that value.

Do not mix individual words, full requests, and entire code files in one input column without a clear reason. They contain different amounts of information.

Some problems need more than one request. For example, `GET /orders/123` might be legitimate for the order's owner and unauthorized for someone else. The request text alone does not tell you which.

**What you should have when finished:** a short definition such as “one row contains one submitted form value.”

### Step 3. Decide the labels

A **label** is the answer you attach to an example.

| Goal | Example labels |
|---|---|
| Attack or normal input | `attack`, `normal` |
| SQL injection specifically | `SQL_injection`, `not_SQL_injection` |
| Several attack types | `normal`, `SQL_injection`, `XSS`, `command_injection` |
| A weakness in code | `vulnerable`, `safe_for_this_weakness` |

For a beginner, use readable names first. If software later needs numbers, document the mapping, such as `0 = normal` and `1 = attack`.

Write a few rules explaining your labels:

- Do failed attack attempts count? Usually yes, if your task is detecting attempts.
- Are simple detection probes included?
- Can one request have more than one attack label?
- What evidence is enough to accept a label?
- What will you do with uncertain examples?

Keep uncertain examples in a review list. Do not guess just to fill every label.

**“Not SQL injection” does not mean “normal.”** The example could contain another attack.

**What you should have when finished:** a short label policy that another person could follow.

### Step 4. Choose sources and reserve material for testing

A **source** is where an example comes from. Training sources help the model learn; test sources help you measure what it learned.

- **Training:** collect varied attacks and realistic normal input.
- **Validation:** reserve part of the development data to choose settings.
- **Test:** reserve cases for a final assessment under a stated policy.

**How to read the tables:** these are broad directories of credible starting points, covering the main available source categories. No finite list can contain every trusted source, and a credible publisher does not make every copied string correct or independent. Check the specific record, source history, and reuse terms.

Both tables include attack and benign sources. The same resource may serve either role, but the examples and related groups used for final testing must be reserved according to your evaluation claim.

#### Table 1. Where to gather the training set

| Source and direct links | What you can collect | How to use it for training | What you must check |
|---|---|---|---|
| **T01. PayloadsAllTheThings** — [repository](https://github.com/swisskyrepo/PayloadsAllTheThings) | Examples across SQLi, XSS, command injection, SSRF, template injection, and other classes | Select relevant examples from the vulnerability folders | Preserve full blocks; separate inputs from outputs, safe examples, and explanations |
| **T02. payload-box** — [repositories](https://github.com/payload-box) | Dedicated attack lists, including [SQLi](https://github.com/payload-box/sql-injection-payload-list), [XSS](https://github.com/payload-box/xss-payload-list), and [SSTI](https://github.com/payload-box/ssti-advanced-payload-list) | Expand candidate input variety | Lists can repeat or lightly modify the same idea; review labels and related families |
| **T03. SecLists** — [repository](https://github.com/danielmiessler/SecLists) | Payloads and fuzzing/discovery wordlists | Use the folders that match your exact task | Usernames, filenames, and discovery words are not automatically attacks |
| **T04. FuzzDB** — [repository](https://github.com/fuzzdb-project/fuzzdb) | Attack patterns and discovery inputs | Add reviewed examples from relevant categories | Keep source path and version; inspect overlap with other collections |
| **T05. Teaching and reference material** — [PortSwigger Academy](https://portswigger.net/web-security), [OWASP WSTG](https://owasp.org/www-project-web-security-testing-guide/), [OWASP Cheat Sheets](https://cheatsheetseries.owasp.org/), [HackTricks](https://book.hacktricks.wiki/) | Explained attack examples, safe patterns, and application context | Understand labels before accepting the examples | Some snippets demonstrate defenses or incomplete steps; an educational example is not a production incident |
| **T06. Security-tool tests and plugins** — [sqlmap](https://github.com/sqlmapproject/sqlmap), [Commix](https://github.com/commixproject/commix), [Dalfox](https://github.com/hahwul/dalfox), [SSTImap](https://github.com/vladko312/SSTImap) | Tool-specific probes, test fixtures, and generation logic | Extract applicable inputs with the tool/version recorded | A generated input still needs context and validation; tools may cover more than one vulnerability class |
| **T07. Scanner templates** — [Nuclei templates](https://github.com/projectdiscovery/nuclei-templates) | Detection requests and CVE-related checks | Extract the actual injected value or request needed by your task | YAML configuration, response matchers, and template variables are not themselves payloads |
| **T08. Published input datasets** — [HttpParamsDataset](https://github.com/Morzeux/HttpParamsDataset), [CSIC description](https://petescully.co.uk/wp-content/uploads/2018/04/http_dataset_csic_2010.pdf), [ECML/PKDD paper](https://www.lirmm.fr/~poncelet/publications/papers/awt_raissi.pdf), [SR-BH data](https://doi.org/10.7910/DVN/OGOIXX) | Normal input and labeled attack/anomaly examples | Reuse a suitable development partition or compare to its original setup | Match input unit and label policy; track shared upstream sources and preserve any official comparison split |
| **T09. Code and application benchmarks** — [OWASP Benchmark](https://owasp.github.io/www-project-benchmark/), [NIST SARD](https://samate.nist.gov/SARD/test-suites) | Safe and vulnerable code/application cases | Use for code detection, or collect requests through a separately documented process | A vulnerable code file is not a ready-made attack string; keep related generated cases together |
| **T10. Controlled practice applications** — [Juice Shop](https://github.com/juice-shop/juice-shop), [WebGoat](https://github.com/WebGoat/WebGoat), [DVWA](https://github.com/digininja/DVWA), [crAPI](https://github.com/OWASP/crAPI), [Vulhub](https://github.com/vulhub/vulhub) | Attacks and normal actions in known environments | Collect controlled requests and record behavior | Record version, challenge, settings, roles, and sequence; do not describe lab traffic as production traffic |
| **T11. Research artifacts** — paper-linked author repositories, [Zenodo](https://zenodo.org/), [USENIX Security](https://www.usenix.org/conferences/byname/108), [ACM artifact guidance](https://www.acm.org/publications/policies/artifact-review-and-badging-current) | Authors' datasets, seeds, scripts, and test environments where released | Extend coverage and reproduce prior work | Follow the exact paper's artifact link; repository hosting or a paper alone does not verify every label |
| **T12. Original disclosures allocated to training** — [GitHub advisories](https://github.com/advisories), [GitHub Security Lab](https://securitylab.github.com/advisories/), vendor reports, disclosed bounty reports | Application-specific attacks with supporting context | Use cases explicitly assigned to development | Mark the related application/incident as used; do not later call copies or close variants independent test evidence |
| **T13. Maintainer regression tests and fixes** — affected projects' official repositories | Minimal reproductions, tests added with a patch, and safe comparison cases | Learn version-specific behaviors and difficult distinctions | A patch is not always a payload; source-code tests may require setup or objects absent from a string |
| **T14. Your own reviewed variations** | Encoded, formatted, or otherwise transformed versions of accepted examples | Fill a demonstrated gap after splitting original groups | Keep parent IDs, transformation rules, and validation; do not assume every edit preserves meaning |
| **T15. Normal-use traffic you are allowed to use** | Search values, forms, URLs, JSON/API requests, and ordinary workflows | Build the normal class from the intended application setting | Remove secrets before sharing; lack of a security alert does not prove the input is benign |
| **T16. Open-source applications and their normal tests** — for example [microblog](https://github.com/miguelgrinberg/microblog), [Symfony demo](https://github.com/symfony/demo), [Spring Petclinic](https://github.com/spring-projects/spring-petclinic) | Legitimate templates, form fixtures, paths, structured inputs, and safe code | Build normal input and hard negatives | Record exact file/commit and meaning; ordinary source code is not always representative user input |
| **T17. Normal subsets of public datasets** — CSIC, HttpParamsDataset, and other documented normal partitions | Benchmark-derived normal requests or values | Supplement benign diversity while keeping the origin explicit | Do not call them newly captured production traffic; avoid shared-record leakage into testing |
| **T18. Reviewed legitimate text and structured data** — application documentation, permitted comments, configuration/test fixtures | Quotes, HTML, code, Unicode, file paths, and other legitimate attack-like text | Challenge simplistic punctuation or keyword rules | Choose material plausible for the intended application; do not label out-of-scope attacks as ordinary benign input |

**Suggested order:** start with a relevant benchmark and a few well-documented lists, inspect a small batch, add realistic normal input, then expand missing coverage. More rows from one repeated family are less useful than reviewed examples covering a real gap.

#### Where the SSTI training set came from

**Training update found during test review:** current active training has 1,905 repository positives and 2,001 benign rows (3,906 total); the 366 legacy seed positives are archived. Positives were expanded from SecLists, HackTricks, Nuclei fuzzing-templates, and the TInjA table — see `train/SOURCES.md`. The evaluation training copy still has 4,002 rows. The detailed 2,001-positive provenance breakdown below describes the earlier training release; this test-only update did not modify training files.

The following counts were recomputed from the local files on **18 September 2026**. They describe this project's existing collection; they do not mean every source attribution has been independently verified.

**Positive training examples: 2,001**

- **1,441** attributed to [payload-box/ssti-advanced-payload-list](https://github.com/payload-box/ssti-advanced-payload-list).
- **194** attributed to [PayloadsAllTheThings](https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/Server%20Side%20Template%20Injection).
- **366** attributed to the local legacy seed, `original/ssti.txt`. Its original upstream sources remain unresolved.

All **1,905** positives have URL/file/commit fields. That means attribution fields exist; it does not yet prove membership in every cited snapshot. The current `is_augmentation=no` annotations mean no project-generated augmentation was recorded in this release, not that upstream payloads are unrelated.

**Benign training examples: 2,001**

- **1,214** from [Morzeux/HttpParamsDataset](https://github.com/Morzeux/HttpParamsDataset).
- **295** from [Sidekiq](https://github.com/sidekiq/sidekiq).
- **240** from [Symfony demo](https://github.com/symfony/demo).
- **134** from [microblog](https://github.com/miguelgrinberg/microblog).
- **118** from [Spring Petclinic](https://github.com/spring-projects/spring-petclinic).

The four application repositories contribute **787 template fragments**; the remaining **1,214** are benchmark-derived parameters.

Local evidence: positive annotations (`train/positives/positives.csv` — the enriched file was merged into it), [benign records](train/benign/benign.csv), and [benign collection notes](train/SOURCES.md#benign-sources).

#### Table 2. Where to gather the test set

For your desired real-world evaluation, start with original disclosures that document an actual application weakness. Use scanner, benchmark, and lab material as clearly named additional test categories. Do not give a source a stronger evidence label merely because it mentions a CVE.

| Source and direct links | What you can collect | Best test role | What you must check |
|---|---|---|---|
| **E01. CVE records** — [CVE.org](https://www.cve.org/) | Vulnerability identifiers and references to original reports | Find documented cases and deduplicate incident IDs | A CVE entry may contain no usable payload; follow the original reference |
| **E02. NVD** — [vulnerability search](https://nvd.nist.gov/vuln/search) | CVE descriptions, weakness mappings, affected-product information, and references | Broaden discovery and cross-check identifiers | Do not count the NVD page and original advisory as different incidents; weakness labels can be broad |
| **E03. Maintainer security advisories** — [GitHub Advisory Database](https://github.com/advisories) and the project's `security/advisories` pages | Maintainer-hosted descriptions, reproductions, affected versions, and fixes | Strong starting point for documented application cases | Distinguish original maintainer reports from mirrored summaries and generic dependency entries |
| **E04. Vendor security advisories** — [Apache](https://www.apache.org/security/), [Atlassian](https://www.atlassian.com/trust/security/advisories), [Spring](https://spring.io/security), affected vendors' own sites | Confirmed product weaknesses and patch information | Validate product/version and attach the authoritative advisory | Some advisories intentionally omit PoCs; record a lead rather than inventing a payload |
| **E05. HackerOne disclosures** — [Hacktivity](https://hackerone.com/hacktivity/overview) | Public reports, impact discussion, and occasionally exact requests | Report-associated examples with explicit program and report ID | Confirm the report is readable and the behavior is server-side; unresolved or private reports are not verified evidence |
| **E06. Bugcrowd disclosures** — [CrowdStream](https://bugcrowd.com/crowdstream) | Public disclosure activity and report links where provided | Locate original bounty reports | Public activity cards may not expose technical evidence; count only reviewed report content |
| **E07. Other coordinated-disclosure platforms** — [huntr](https://huntr.com/), [Intigriti](https://www.intigriti.com/), [YesWeHack](https://www.yeswehack.com/) | Public technical reports or original researcher disclosures, where available | Additional documented cases | A tutorial on a bounty company's blog is not automatically a disclosed bounty report |
| **E08. GitHub Security Lab** — [advisories](https://securitylab.github.com/advisories/) | Original coordinated disclosures, vulnerable code paths, and PoCs | Application-specific cases with technical context | Match the actual mechanism; expression injection or CI workflow injection may fall outside your chosen scope |
| **E09. Original research teams** — [PortSwigger Research](https://portswigger.net/research), [Sonar](https://www.sonarsource.com/blog/), [elttam](https://www.elttam.com/resources), [Check Point Research](https://research.checkpoint.com/), [Doyensec](https://blog.doyensec.com/), [NCC Group](https://research.nccgroup.com/), [Wordfence](https://www.wordfence.com/threat-intel/vulnerabilities), [Snyk research/advisories](https://security.snyk.io/) | Original disclosures and detailed analysis | Add evidence and mechanisms missing from short vendor notices | Identify the original case and distinguish it from educational examples or quoted upstream work |
| **E10. Coordinated-disclosure databases** — [CERT/CC notes](https://kb.cert.org/vuls/), [Zero Day Initiative](https://www.zerodayinitiative.com/advisories/published/) | Coordinated reports and vendor references | Find additional products and validate disclosure history | Public records often lack the exact input; keep those as leads |
| **E11. Exploit archives** — [Exploit-DB](https://www.exploit-db.com/) | Public reproductions with author and vulnerability references | Secondary reproduction evidence, cross-checked against the original case | Submission or archive inclusion is not proof of successful execution or correct labeling |
| **E12. Researcher-owned PoC repositories** | Code linked from an original report or advisory | Extract documented attack input with setup context | Prefer an attributable original repository and fixed commit; a random CVE-named repository is not sufficient |
| **E13. CVE reproduction projects** — [Vulhub](https://github.com/vulhub/vulhub), [Metasploit modules](https://github.com/rapid7/metasploit-framework) | Reproducible environments and application-specific checks | A separate reproduced-vulnerability category | Preserve the CVE, module/path, version, and prerequisites; lab reproduction is not an observed production attack |
| **E14. CVE scanner templates** — [Nuclei](https://github.com/projectdiscovery/nuclei-templates) | Versioned request patterns and response checks | A separate scanner-derived challenge category | A scanner template may reuse a training-list payload; a matcher or harmless probe does not prove full exploitation |
| **E15. Held-out published benchmarks** — the matching resources in Part 2 | Labeled examples under an existing evaluation procedure | Compare results with prior work or test transfer to another collection | Trace common upstream sources and preserve official splits for comparable results |
| **E16. Original papers and released research artifacts** | Documented evaluation cases and generated stress tests | Additional research or robustness comparisons | Record whether cases are collected, generated, or reconstructed; do not count them as incident evidence without support |
| **E17. Authorized operational captures** | Actual attack attempts and normal requests from application logs, WAF logs, honeypots, or incident-response work | Evidence of observed inputs in a defined environment | Alerts are not ground truth; retain collection dates, labeling method, repeated-session links, and privacy handling |
| **E18. Reserved normal-use data and OSS sources** | Normal requests or legitimate code/templates from applications, files, sessions, or dates excluded from development | Estimate false alarms on genuinely held-out normal behavior | Record the exact holdout boundary; different rows in a shared file may be strongly related |
| **E19. Reserved labs and CTFs** — [PortSwigger labs](https://portswigger.net/web-security/all-labs), [OWASP application directory](https://vwad.owasp.org/), original challenge repositories | Controlled difficult cases and known behaviors | A separate lab/CTF challenge set | Do not label them production incidents; reserve their solutions and variants from training |

**Suggested order for your test expansion:** original maintainer/vendor and bounty disclosures first; original technical research next; CVE-linked reproduction artifacts after that. Use scanner, benchmark, and lab examples as separate supporting evaluations. A CVE identifier strengthens traceability, not automatic independence or payload validity.

#### Where the current SSTI test set came from

The active set contains **47 positive examples and 500 benign examples**, for **547 total records**. The following table counts retained positive rows across 22 source pages. It includes the nine approved additions; six related-injection inputs are preserved separately. See the scope review (archived in `_archive/dataset_history_2026-09-19.zip`, path `review/TEST_SCOPE_REVIEW_2026-09-18.md`).

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

Evidence categories count records, not independent vulnerabilities. Existing source-type annotations remain provisional.

**Benign test examples: 500**

- **357** from [HttpParamsDataset](https://github.com/Morzeux/HttpParamsDataset).
- **89** from [Sidekiq](https://github.com/sidekiq/sidekiq).
- **25** from [microblog](https://github.com/miguelgrinberg/microblog).
- **19** from [Symfony demo](https://github.com/symfony/demo).
- **10** from [Spring Petclinic](https://github.com/spring-projects/spring-petclinic).

That is **143 template fragments plus 357 benchmark-derived parameters**. All five benign source repositories also occur in training. File/session independence needs per-record evidence; it cannot be inferred from separate CSV filenames.

Thirteen positives have known training-family relationships (seven earlier flags plus six new comparisons). Zero exact or conservative normalized duplicates remain, but the other 34 positives are not certified unseen families.

Local evidence: [retained positive records](test_set/ssti_test_positives_enriched.csv), [benign records](test_set/test_benign.csv), and [source notes](test_set/sources.md).

**New collection work:** see the SSTI expansion research report (archived in `_archive/dataset_history_2026-09-19.zip`, path `research/ssti_test_expansion_2026-09-18/SSTI_TEST_EXPANSION_RESEARCH.md`). Nine of the 14 captured candidates have now been admitted after source/scope and duplicate review; five remain outside the active set. The admission ledger (archived in `_archive/dataset_history_2026-09-19.zip`, path `review/test_scope_review_2026-09-18.json`) records the decisions. Original research files preserve their collection-time status.

**What you should have when finished with this step:** a development-source list, a reserved test-source plan, and a place to record candidate evidence. Continue with Step 5 below.

### Step 5. Set up a simple collection file

You can start with a table. You do not need a complicated database.

Use these columns initially:

| Column | Meaning |
|---|---|
| `record_id` | A permanent ID, such as `WEB-0001` |
| `input` | The exact value, request, or code |
| `label` | The proposed answer |
| `source` | Source name and URL or local file |
| `source_location` | Where the example appears inside that source |
| `review_status` | `unreviewed`, `needs_review`, or `accepted` |
| `notes` | Why you chose the label and anything uncertain |

Keep a separate untouched copy of the source material when permitted.

This source history is called **provenance**. You are recording where an example came from and what happened to it. [Part 3](#part-3-source-records-and-review-notes-explained) explains how to expand these simple notes when the collection grows.

**What you should have when finished:** an empty collection table and a place to save originals.

### Step 6. Collect a small first batch of attacks and normal examples

Before collecting thousands of rows, try a small batch—for example, ten attack candidates and ten normal examples. This is a practice batch to test your process, not a target size for a research paper.

For each example:

1. Copy the correct input.
2. Record its source and exact location.
3. Add the proposed label.
4. Leave its review status as `unreviewed`.
5. Save enough context to understand it later.

Read the surrounding explanation. Do not accidentally copy a response, command prompt, or incomplete code fragment as the attack input.

Also collect **benign** examples. “Benign” means legitimate or non-malicious under your label policy.

Include some **hard negatives**: normal examples that look suspicious.

| Normal example | Why it helps |
|---|---|
| A name such as `O'Reilly` | Teaches that a quote alone does not mean SQL injection |
| A programming question containing HTML | Teaches that HTML text is not always an XSS attempt |
| A legitimate path in an allowed file operation | Teaches that a path alone does not mean path traversal |
| Normal JSON with punctuation and Unicode | Prevents special characters from becoming an easy attack clue |

Choose examples that make sense for the intended application. A coding forum and a payment form have different normal input.

**Exception:** some anomaly-detection methods learn only normal behavior. An **anomaly** is something unusual, not necessarily malicious. The attack-and-normal recipe here is for ordinary supervised classification, where the model learns from labeled examples.

**What you should have when finished:** a small collection containing both classes and source notes.

### Step 7. Review the examples before expanding

For each row, ask:

1. Did I copy the example correctly?
2. Does the surrounding context support my label?
3. Is this a complete example of the kind my model will receive?
4. Is it actually an attack input, ordinary input, or something else?
5. Is any important context missing?

Record your decision and a short reason. Add your name or reviewer ID and the date.

**Checking the source, checking the label, and running the example are different activities.** A correctly copied example can still have an uncertain label. A failed local reproduction does not automatically make an attack attempt normal.

If the first batch contains extraction mistakes, fix the collection method before scaling up.

**What you should have when finished:** reviewed examples, a list of uncertain cases, and a collection method you understand.

### Step 8. Expand, then check duplicates and related examples

Now collect more examples using the same method.

Aim for variety in attack methods, applications, input styles, and normal behavior. There is no universal number of rows that makes a dataset good enough for a paper.

Check for:

- **Exact duplicates:** identical inputs.
- **Near duplicates:** small changes to the same input.
- **Related examples:** cases from the same original attack, report, session, or generated parent.
- **Conflicting labels:** the same input labeled differently in different places.

Keep the original collection history even when the final model file uses only one copy.

Give closely related examples a shared **group ID**. This will help you keep them together in the next step.

Do not put every SQL injection example into one group. An attack class is broad; a group normally represents a closer relationship.

**What you should have when finished:** a reviewed collection with duplicates documented and related cases linked.

### Step 9. Divide the data into training, validation, and test sets

Keep related examples together when your evaluation requires independent cases.

For example, an original input and five lightly edited versions should not be spread between training and a test intended to measure performance on new examples.

| Relationship | How to handle it |
|---|---|
| An original and its generated variations | Keep them in the same group |
| Requests from one attack sequence | Keep them together when they depend on one another |
| Examples from the same application | Hold the whole application out if claiming performance on unseen applications |
| The same broad attack type | It can normally appear in both training and test |

There is no required split percentage. A ratio such as 70/15/15 is only a possible starting point; group sizes and the number of examples in each class matter more.

Save the record IDs assigned to each set. Do not rely only on a random seed or on the current row order.

If you are comparing against a published benchmark, preserve its official split for that comparison. Report any new split as a separate experiment.

**What you should have when finished:** three clearly defined sets with saved membership and checked overlap.

### Step 10. Add extra training examples only if needed

Creating variations of existing examples is called **augmentation**.

Use it only after splitting the original data. Keep the original record ID as the new example's `parent_id`, and explain the change.

Check that a change still makes sense. Different encoding, spacing, or punctuation does not always preserve behavior.

Generated examples stay in the training part for ordinary model development. A separately named generated challenge set is also valid, but it is not a collection of independent real-world incidents.

If you use cross-validation, apply the same rule within each round's training portion.

**What you should have when finished:** optional extra training rows with clear parent links and reviewed labels.

### Step 11. Check and save the finished dataset

Before training, check that:

- Every accepted row has an ID, input, label, and source.
- All examples use the intended input format.
- Uncertain rows are handled according to your policy.
- The saved split memberships are correct.
- Exporting and loading the files preserves the inputs.
- Line breaks, quotes, Unicode, and backslashes survive unchanged.
- Private information and secrets are handled before sharing.

A **CSV** is a table file. A proper CSV reader understands quoted fields and line breaks inside values. Counting physical lines is not always the same as counting records.

For complex requests, **JSONL** is another useful format: each line stores one structured record. A JSON reader restores line breaks encoded inside a value.

A simple folder layout could be:

```text
dataset/
  raw/             untouched sources or permitted source copies
  reviewed/        accepted examples
  metadata/        sources, review notes, and related-example links
  splits/          IDs in training, validation, and test
  scripts/         steps used to create exports
  README.md        what the dataset contains and how to use it
  LABEL_POLICY.md  what the labels mean
  CHANGES.md       changes between versions
  MANIFEST.json    filenames, record counts, and file fingerprints
```

A **manifest** is a file inventory. A **file hash** is a fingerprint that helps identify changes. These are explained further in Part 3.

Check reuse terms before redistributing source material; public availability alone is not permission to republish it. See the [Creative Commons guidance](https://creativecommons.org/faq/).

**What you should have when finished:** a saved, versioned dataset that another person could understand.

### Step 12. Train, adjust, and evaluate—in that order

The dataset is now prepared. Model work comes next:

1. Learn from the training data.
2. Use validation data to choose settings and the alarm threshold.
3. Fix those choices.
4. Evaluate on the test data.
5. Report correct detections, missed attacks, and false alarms.

A **threshold** is the score at which the model raises an alarm.

Do not use source names, reviewer notes, or labels as input clues. Do not learn preprocessing from the test data. **Preprocessing** means preparing inputs for the model, such as turning text into numerical features.

If you repeatedly change the model after seeing the test results, that test has become part of development. A new untouched test is needed for a fresh final assessment.

[Part 4](#part-4-understand-the-results) explains the main measurements.

---

## Part 2. Datasets and benchmarks by vulnerability

### 2.1 How to read this section

The resources below are organized around **SQL injection, XSS, command injection, and other vulnerability types**.

There are three different resource types:

| Type | What you get | Best use |
|---|---|---|
| **Input dataset** | Labeled strings or requests | Training or evaluating attack-input classifiers |
| **Code/application benchmark** | Known safe and vulnerable cases, often with expected answers | Testing whether a tool finds weaknesses |
| **Practice lab** | A deliberately vulnerable application or lesson | Understanding behavior and collecting controlled examples |

A **benchmark** is a defined test with a way to score results. A payload collection or practice lab is not automatically a benchmark.

The list contains established resources and useful starting points, not a popularity ranking. For some vulnerabilities, the resources checked here are labs rather than a suitable ready-made labeled dataset. Their presence does not mean no other datasets exist.

### 2.2 SQL injection — SQLi

SQL injection concerns attacker-controlled input changing a database query. Begin with the [PortSwigger explanation](https://portswigger.net/web-security/sql-injection) if the vulnerability itself is new to you.

| Resource | Type | What to inspect |
|---|---|---|
| [HttpParamsDataset](https://github.com/Morzeux/HttpParamsDataset) | Input dataset | `sqli` and `norm` examples; its source list and split files |
| [ECML/PKDD 2007](https://www.lirmm.fr/~poncelet/publications/papers/awt_raissi.pdf) | Request benchmark | SQL injection labels, request fields, and target context |
| [SR-BH 2020](https://doi.org/10.7910/DVN/OGOIXX) | Request dataset | SQL injection category and the labeling method in the [authors' paper](https://reunir.unir.net/bitstream/handle/123456789/14058/new_multi-label_dataset.pdf?isAllowed=y&sequence=2) |
| [OWASP Benchmark](https://owasp.github.io/www-project-benchmark/) | Code/application benchmark | SQL injection cases and their expected results |
| [NIST PHP XSS/SQLi suite](https://samate.nist.gov/SARD/test-suites/114) | Code benchmark | PHP cases and their weakness labels |
| [PortSwigger SQLi labs](https://portswigger.net/web-security/sql-injection) | Practice labs | Database context, the submitted input, and observed behavior |

**Suggested starting point:** HttpParamsDataset for a small input-classification project; OWASP Benchmark for finding vulnerable code or testing scanners.

**Collection detail:** preserve database and query context when available. A quote in a person's name is not automatically an attack.

### 2.3 Cross-site scripting — XSS

XSS involves attacker-controlled content executing script in another user's browser. Different browser and page contexts matter. See the [PortSwigger explanation](https://portswigger.net/web-security/cross-site-scripting).

| Resource | Type | What to inspect |
|---|---|---|
| [HttpParamsDataset](https://github.com/Morzeux/HttpParamsDataset) | Input dataset | `xss` examples, normal values, and collection sources |
| [ECML/PKDD 2007](https://www.lirmm.fr/~poncelet/publications/papers/awt_raissi.pdf) | Request benchmark | XSS class and attack location within the request |
| [OWASP Benchmark](https://owasp.github.io/www-project-benchmark/) | Code/application benchmark | XSS cases and expected findings |
| [NIST PHP XSS/SQLi suite](https://samate.nist.gov/SARD/test-suites/114) | Code benchmark | XSS code cases and supporting metadata |
| [PortSwigger XSS labs](https://portswigger.net/web-security/cross-site-scripting) | Practice labs | Reflected, stored, and browser-side examples and their contexts |

**Suggested starting point:** compare normal HTML-containing input with reviewed attack input. Use a code benchmark if the goal is to find weaknesses in code.

**Collection detail:** record whether you are studying reflected, stored, or DOM-based XSS. A server request alone may not show all browser-side behavior.

### 2.4 OS command injection

This occurs when application input changes a command executed by the operating system. See the [PortSwigger explanation](https://portswigger.net/web-security/os-command-injection).

| Resource | Type | What to inspect |
|---|---|---|
| [HttpParamsDataset](https://github.com/Morzeux/HttpParamsDataset) | Input dataset | `cmdi` examples and normal values |
| [SR-BH 2020 paper and data reference](https://reunir.unir.net/bitstream/handle/123456789/14058/new_multi-label_dataset.pdf?isAllowed=y&sequence=2) | Request dataset | OS command injection category and label origins |
| [OWASP Benchmark](https://owasp.github.io/www-project-benchmark/) | Code/application benchmark | Command injection cases and expected results |
| [PortSwigger command injection labs](https://portswigger.net/web-security/os-command-injection) | Practice labs | Application behavior and operating-system assumptions |

**Collection detail:** record the operating system and command context where known. The same text may behave differently on different systems.

### 2.5 Path traversal

Path traversal lets input reach files outside an intended location. See the [PortSwigger explanation](https://portswigger.net/web-security/file-path-traversal).

| Resource | Type | What to inspect |
|---|---|---|
| [HttpParamsDataset](https://github.com/Morzeux/HttpParamsDataset) | Input dataset | `path-traversal` examples and legitimate path values |
| [ECML/PKDD 2007](https://www.lirmm.fr/~poncelet/publications/papers/awt_raissi.pdf) | Request benchmark | Path traversal class and target context |
| [SR-BH 2020](https://doi.org/10.7910/DVN/OGOIXX) | Request dataset | Path traversal labels |
| [OWASP Benchmark](https://owasp.github.io/www-project-benchmark/) | Code/application benchmark | Path traversal cases and expected findings |
| [PortSwigger path traversal labs](https://portswigger.net/web-security/file-path-traversal) | Practice labs | Intended file location and actual file-access behavior |

**Collection detail:** include legitimate paths as well as attacks. A path is meaningful only in relation to what the application allows.

### 2.6 LDAP and XPath injection

These attacks change queries used by directory services or XML processing.

| Resource | Type | What to inspect |
|---|---|---|
| [ECML/PKDD 2007](https://www.lirmm.fr/~poncelet/publications/papers/awt_raissi.pdf) | Request benchmark | Separate LDAP and XPath classes, plus context fields |
| [OWASP Benchmark](https://owasp.github.io/www-project-benchmark/) | Code/application benchmark | Separate LDAP and XPath test categories |

**Collection detail:** keep the query language and application context. Similar punctuation across query languages does not make the attacks interchangeable.

### 2.7 SSRF and XXE

**SSRF**, or server-side request forgery, involves making a server send an unintended request. **XXE**, or XML external entity injection, abuses how an application processes external entities in XML.

| Vulnerability | Starting resource | Type | What the record needs |
|---|---|---|---|
| SSRF | [PortSwigger SSRF labs](https://portswigger.net/web-security/ssrf) | Practice labs | Submitted input, server behavior, and what destination was allowed |
| XXE | [PortSwigger XXE labs](https://portswigger.net/web-security/xxe) | Practice labs | XML input, parser conditions, and evidence of the behavior |
| Either, where a matching case exists | [Vulhub](https://github.com/vulhub/vulhub) | Vulnerability reproduction environments | Exact application version, case reference, and setup |

**Collection detail:** a URL alone does not establish SSRF, and unusual XML alone does not prove an XXE vulnerability. Keep evidence of how the application handled the input.

These are starting points for controlled collection, not claims of an already labeled, independent test corpus.

### 2.8 CSRF, access control, and authentication

These problems often need user and application context rather than a suspicious-looking payload.

| Vulnerability | Starting resource | What you need to record |
|---|---|---|
| **CSRF:** a user's browser is induced to perform an unwanted action | [PortSwigger CSRF labs](https://portswigger.net/web-security/csrf) | The request, browser/session conditions, and protection checks |
| **Access control / IDOR:** a user can access an object or action they should not | [PortSwigger access-control labs](https://portswigger.net/web-security/access-control), [OWASP crAPI](https://github.com/OWASP/crAPI) | User identity or role, ownership, permissions, and outcome |
| **Authentication:** a problem with verifying who a user is | [PortSwigger authentication labs](https://portswigger.net/web-security/authentication) | Relevant request sequence, account state, and result |

These links are **practice applications or labs**, not ready-made labeled input datasets.

For example, an order number can be normal for one user and unauthorized for another. Do not try to infer that distinction from the number alone.

### 2.9 Broad resources covering several vulnerabilities

| Resource | Why inspect it? | Important limit |
|---|---|---|
| [HTTP CSIC 2010 description](https://petescully.co.uk/wp-content/uploads/2018/04/http_dataset_csic_2010.pdf) | Historical generated HTTP traffic, including SQLi and XSS among other anomalies | “Anomalous” includes accidental invalid requests; it is not a precise attack-type label for every record |
| [OWASP Juice Shop](https://github.com/juice-shop/juice-shop) | Understand several web weaknesses in one application | Record the exact challenge and application version |
| [OWASP WebGoat](https://github.com/WebGoat/WebGoat) | Follow guided vulnerability lessons | Lessons need a defined collection and scoring method before becoming your dataset |
| [DVWA](https://github.com/digininja/DVWA) | Study controlled web vulnerabilities | Record the version and difficulty setting |
| [WAVSEP](https://github.com/sectooladdict/wavsep) | Inspect a legacy scanner-evaluation collection | Check its case coverage and environment before using it |
| [NIST SARD / Juliet](https://samate.nist.gov/SARD/test-suites) | Find code tests for particular weakness types | Select web-relevant cases; the whole collection is not web-specific |

**WIVET and network intrusion datasets are not the first choices for this guide's purpose.** [WIVET](https://github.com/bedirhan/wivet) measures discovery of web inputs. [CICIDS2017](https://www.unb.ca/cic/datasets/ids-2017.html) includes web attacks within broader network traffic; its flow-feature tables are not raw payload datasets.

### 2.10 What to check before using a benchmark

Open the documentation and a few records, then answer:

1. Is each example a value, request, code case, or multi-step test?
2. Does it contain the vulnerability type I need?
3. Are labels per example, or are attack types mentioned only in a general description?
4. Are there normal or safe examples?
5. Were examples captured, generated, or copied from other collections?
6. Is there an official split or scoring method?
7. Can I obtain the exact version and reuse it under its terms?

**Do not merge collections just because their labels sound similar.** In particular, HttpParamsDataset's documentation identifies CSIC as its benign source. Using one for training and the other for testing does not automatically create an independent comparison.

**What was checked:** the resource descriptions and vulnerability mappings above were checked against original papers and official documentation. The review supports keeping normal examples, recording context, tracing shared sources, and matching the test to the task. It also shows that normal-only training and controlled synthetic tests can be valid for the right experiment.

**Access limits:** the original CSIC site was unavailable, so a preserved copy of its description is linked. The ECML paper was readable, although the old challenge site timed out. The SR-BH data page required browser verification; its paper was readable. Downloaded record counts and every individual label have not been independently audited here.

---

## Part 3. Source records and review notes explained

### 3.1 What does provenance mean?

**Provenance means the history of an example: where you got it and what happened to it.**

Think of it as keeping a receipt plus a short notebook entry.

A payload and a label are not enough if you later need to answer:

- Where exactly did I find this?
- Was it copied as-is or changed?
- Why did I call it an attack?
- Has anyone checked it?
- Is it a variation of another example?
- Can another researcher find the same source?

You do not need to fill dozens of columns on the first day. Start with a small record and add detail when it matters.

### 3.2 What to record for each example

| Field | Plain-English meaning | Example |
|---|---|---|
| `record_id` | A permanent name for this example | `WEB-0001` |
| `input` | The exact text, request, or code being classified | A captured request |
| `label` | Your current answer | `normal` or `SQL_injection` |
| `source_id` | Which source record it belongs to | `SRC-001` |
| `source_locator` | Where inside that source it came from | File path and case ID, report section, or request number |
| `collected_at` | When you collected it | `2026-09-18` |
| `label_origin` | Who or what supplied the initial label | `source_author`, `tool`, or `our_reviewer` |
| `label_reason` | Why the label makes sense | “Ordinary author search; confirmed in the normal-use scenario” |
| `review_status` | Whether the label has been checked | `unreviewed`, `needs_review`, or `accepted` |
| `reviewer` | Who made the review decision | A name or stable reviewer ID |
| `reviewed_at` | When that decision was made | A date, or `not_reviewed` |
| `review_notes` | Important context or unresolved questions | “Quote belongs to a person's name” |

An ID should not change when rows are sorted. Spreadsheet row 57 is not a reliable permanent identifier.

“Accepted” should mean accepted under your written policy. It is not a promise that every label is beyond doubt.

### 3.3 What to record for each source

If 500 examples came from the same repository version, you can put shared details in a separate **source table**. Each example points to it using `source_id`.

If the same example appears in several sources, keep all source references, even if you keep only one copy for training. Two websites containing the same example do not make it two independent examples.

| Source field | What it means |
|---|---|
| `source_id` | A stable name such as `SRC-001` |
| `source_name` | Dataset, repository, report, or local experiment name |
| `source_url` | The original page or download address, when available |
| `source_version` | The release, Git commit, or saved-page version you used |
| `source_type` | Published dataset, incident report, lab, tool output, or another defined category |
| `saved_copy` | Where you stored a permitted local copy |
| `file_sha256` | A fingerprint used to detect changes to the saved file |
| `license_or_terms` | The relevant reuse terms, or `not_checked` |

A **Git commit** identifies a repository snapshot. A link to its current main page can change tomorrow; a commit-specific link is more precise.

A **SHA-256 hash** is a file fingerprint. It helps show that two copies are the same. It does not prove that a label is correct, that the source is trustworthy, or that reuse is permitted.

If you downloaded the repository today, do not call today's commit the original collection version unless you have evidence that it was the version used then.

A report may have no Git commit. In that case, record the URL, date, section, and a saved copy if permitted. Use `not_applicable` where a field genuinely does not apply.

Use `unknown` when the information is missing, `not_checked` when you have not investigated it, and `not_applicable` when it does not apply. These mean different things; an empty cell does not explain which one you intended.

### 3.4 A complete fictional example

The following is a teaching example, **not a real dataset record or evidence of an actual experiment**.

**Source record:**

```text
source_id: SRC-DEMO
source_name: Our local practice shop
source_type: controlled_lab
source_version: practice-version-1
source_url: not_applicable
saved_copy: raw/practice-shop/normal-requests.jsonl
license_or_terms: not_checked
```

**Example record:**

```text
record_id: WEB-0001
input: GET /search?author=O%27Reilly HTTP/1.1
label: normal
source_id: SRC-DEMO
source_locator: request_id=12
collected_at: 2026-09-18
label_origin: our_reviewer
label_reason: A user searched for an author's name.
review_status: accepted
reviewer: reviewer_1
reviewed_at: 2026-09-18
review_notes: The quote is part of the name, not an injection attempt.
```

This record lets you return to request 12 and see why it was included. The word `normal` alone would not tell you that.

The HTTP status code is not enough to establish the label: both attacks and ordinary requests can receive an error or a successful response.

### 3.5 Three different checks

These checks answer different questions. Do not combine them into one vague “verified” flag.

| Check | Question | Possible status |
|---|---|---|
| **Source match** | Did we copy the correct example from the recorded location? | `not_checked`, `matched`, `mismatch` |
| **Label review** | Does the source context support our label? | `unreviewed`, `needs_review`, `accepted`, `excluded` |
| **Behavior test** | Did we run it in a suitable test environment, and what happened? | `not_tested`, `reproduced`, `not_reproduced` |

An example can match its source and still have an uncertain label.

An attack attempt can be accepted from good report evidence without being reproduced locally. Keep `not_tested` honest. A failed local test also does not automatically make an attack normal; the application version or conditions may differ.

### 3.6 How to record related examples

| Field | What it tells you | Example |
|---|---|---|
| `parent_id` | Which existing example was changed to make this one | `WEB-0001` |
| `is_generated` | Whether you created this example rather than copying it directly | `yes` |
| `change_description` | Exactly what you changed | “Created a different URL-encoded representation” |
| `family_id` | A reviewed group of closely related cases | `FAMILY-014` |
| `split_group_id` | Examples that must stay together when dividing the data | `GROUP-014` |
| `application_id` / `incident_id` | The shared application or report | An application name or report ID |

A family is more specific than a broad class such as “all XSS.” Define what counts as closely related for your task.

An automatic **skeleton** replaces changing parts of an input with placeholders to find similar patterns. It can help suggest families, but it can make mistakes. A matching skeleton is a review clue, not a final decision.

For a generated child of `WEB-0001`, keep a new record ID, point to `WEB-0001` as its parent, describe the change, and keep parent and child in the same split group. Check that the change preserves the intended label.

### 3.7 How to review an example manually

1. Open the recorded source and find the exact example.
2. Compare the saved input with the source, including line breaks and encoding.
3. Read the surrounding explanation, not just the example itself.
4. Decide whether the label fits your policy.
5. Record the decision, your name or reviewer ID, the date, and a short reason.
6. If unsure, use `needs_review` and explain what information is missing.
7. If a label changes later, keep a short change history with the old label and reason.

For a large collection, automatic checks and sampling can help. Report how many records were checked and how they were selected; do not describe a small sample review as verification of the whole dataset.

**Keep these notes for research, not as clues for the classifier.** A source filename such as `attacks.txt`, a review decision, or a label explanation could reveal the answer. Usually the model should receive the intended input only.

---

## Part 4. Understand the results

### 4.1 Start with four counts

Suppose the model calls an example an attack or normal.

| Actual example | Model's answer | Name |
|---|---|---|
| Attack | Attack | True positive: correct detection |
| Attack | Normal | False negative: missed attack |
| Normal | Attack | False positive: false alarm |
| Normal | Normal | True negative: correct normal decision |

Always keep these raw counts. They make percentages easier to understand and check.

### 4.2 Understand the main percentages

**Fictional example:** a test contains 100 attacks and 900 normal examples. The model finds 80 attacks and wrongly flags 18 normal examples.

| Measure | Question it answers | Result in this example |
|---|---|---|
| Recall | How many actual attacks were found? | 80 / 100 = **80%** |
| False-positive rate | How many normal examples caused an alarm? | 18 / 900 = **2%** |
| Precision | How many raised alarms were correct? | 80 / 98 = **about 81.6%** |
| Accuracy | How many total decisions were correct? | (80 + 882) / 1,000 = **96.2%** |

This example shows why accuracy alone can hide missed attacks.

Precision also depends on how common attacks are. A result from a balanced research dataset is not automatically the result you would get on ordinary traffic.

### 4.3 More advanced measures can wait

Once the basic counts are clear:

- **F1** combines precision and recall.
- **PR-AUC or average precision** summarizes precision and recall across score thresholds. State which calculation you use.
- **ROC-AUC** summarizes how well scores rank attacks above normal examples.
- A **confidence interval** is an uncertainty range around an estimate.

For several vulnerability classes, report results for each class. Small classes can perform poorly even when the overall result looks good.

If many examples are closely related, account for those groups when estimating uncertainty. Repeated variants do not provide as much independent evidence as unrelated cases.

### 4.4 Avoid accidental shortcuts

**Data leakage** means the model gets information it should not have during a fair test.

Common examples:

- A filename or metadata column reveals the label.
- A near-copy of a test example appears in training.
- Preprocessing learns from the complete dataset before splitting.
- A response field is used to claim detection before the server has responded.
- Labels from a security tool are treated as fully independent truth when testing that same tool.

Use training data to fit learned preprocessing and apply the same fitted process to validation/test data. If using **cross-validation**, which repeats training and validation across several divisions, respect the same boundaries in every round.

These recommendations are supported by [scikit-learn's leakage guidance](https://scikit-learn.org/stable/common_pitfalls.html) and [grouped cross-validation documentation](https://scikit-learn.org/stable/modules/cross_validation.html).

---

## Part 5. Final checklist

### Before collecting

- [ ] I can describe the task in one sentence.
- [ ] I know what one row represents.
- [ ] I have written the label meanings.
- [ ] I have selected relevant sources.
- [ ] I know what I want the final test to demonstrate.

### While collecting and reviewing

- [ ] Every example has a stable ID and source location.
- [ ] I have kept an original copy or a reliable source reference.
- [ ] I record review decisions and uncertainty.
- [ ] Normal examples reflect the intended application.
- [ ] Duplicates, copied sources, and related examples are documented.

### Before model training

- [ ] Training, validation, and test membership is saved.
- [ ] Related examples stay together where required.
- [ ] Generated examples have parent links.
- [ ] Inputs survive export and reload without unwanted changes.
- [ ] The model cannot read labels or revealing review metadata.

### Before reporting or sharing

- [ ] I report missed attacks and false alarms, not just accuracy.
- [ ] I state the test size, class mix, and limitations.
- [ ] I name the dataset version and explain changes.
- [ ] Source references and reuse terms are recorded.
- [ ] Another person could understand how the dataset was built.

---

**Review scope:** this is a general guide based on the linked documentation and papers, reviewed on 18 September 2026. It does not claim that all listed data were downloaded or that every benchmark was executed.
