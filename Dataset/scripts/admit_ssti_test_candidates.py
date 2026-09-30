"""One-time, guarded 2026-09-18 test-scope update. Never execute payload strings.

Run --apply to migrate the original 44-positive release. A completed admission
ledger blocks reruns. Current consistency checks: reconcile_dataset_exports.py --validate --test-only.
"""
import argparse
import collections
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import unicodedata
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'Dataset'
TEST = DATA / 'test_set'
RESEARCH = DATA / 'research/ssti_test_expansion_2026-09-18'
LEDGER = DATA / 'review/test_scope_review_2026-09-18.json'
REPORT = DATA / 'review/TEST_SCOPE_REVIEW_2026-09-18.md'
EXCLUDED = {
    'TEST-002': 'OGNL expression injection; outside this template-expression subset.',
    'TEST-003': 'OGNL invocation of a FreeMarker utility class, not a FreeMarker template expression; original engine label was misleading.',
    'TEST-004': 'Spring SpEL expression injection; outside this template-expression subset.',
    'TEST-007': 'EJS compiler-option injection. Commonly called SSTI in advisories, but separated from this narrower template-expression subset. Not XSS.',
    'TEST-016': 'Java EL expression injection; insufficient template-engine context for this narrower subset.',
    'TEST-038': 'EJS compiler-option injection. Commonly called SSTI; separated by input type, not relabeled as XSS or benign.',
}
ADMITTED = ['PAYLOAD-002', 'PAYLOAD-003', 'PAYLOAD-004', 'PAYLOAD-005',
            'PAYLOAD-007', 'PAYLOAD-009', 'PAYLOAD-018', 'PAYLOAD-021', 'PAYLOAD-024']
HELD = {
    'PAYLOAD-001': 'Exact duplicate of active training POS-1478 (original ID POS-1844).',
    'PAYLOAD-006': 'Published demonstration uses JMS; a corresponding web input path is not established.',
    'PAYLOAD-008': 'Library-level reproduction; a concrete exposed web input path is not established.',
    'PAYLOAD-012': 'Model-file metadata ingestion; held outside this web-form/API/template-editing subset.',
    'PAYLOAD-022': 'XWiki macro/Groovy evaluation; held outside the narrower template-expression subset.',
}
FAMILIES = {
    'PAYLOAD-002': ('POS-1039', 'FreeMarker Execute/new command-execution mechanism; original training ID POS-1405'),
    'PAYLOAD-003': ('POS-1478', 'Jinja globals/builtins import chain; bracket/dot variant; original training ID POS-1844'),
    'PAYLOAD-005': ('POS-1300', 'Twig sort/system mechanism; also related to TEST-005; original training ID POS-1666'),
    'PAYLOAD-007': ('POS-0494', 'Generic template arithmetic probe also contained in a training polyglot; original legacy POS-0003 is now archived'),
    'PAYLOAD-018': ('POS-0494', 'Generic arithmetic probe across engines also contained in a training polyglot; wrapper does not establish a new family'),
    'PAYLOAD-024': ('POS-1044', 'FreeMarker Execute/new mechanism; also related to new OpenMetadata case; original training ID POS-1410'),
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def csv_read(path):
    with path.open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle, strict=True)
        return reader.fieldnames, list(reader)


def jsonl_read(path):
    return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines() if s.strip()]


def text_write(path, content):
    temporary = path.with_name(path.name + '.admission-tmp')
    assert not temporary.exists(), temporary
    temporary.write_text(content, encoding='utf-8', newline='\n')
    temporary.replace(path)


def csv_write(path, fields, rows, delimiter=','):
    temporary = path.with_name(path.name + '.admission-tmp')
    assert not temporary.exists(), temporary
    with temporary.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter=delimiter, lineterminator='\n')
        writer.writeheader()
        writer.writerows({k: r[k] for k in fields} for r in rows)
    temporary.replace(path)


def jsonl_write(path, rows):
    text_write(path, ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows))


def key(payload):
    return unicodedata.normalize('NFC', unquote(payload)).replace('\r\n', '\n').replace('\r', '\n').strip()


def main():
    if LEDGER.exists():
        raise RuntimeError('Admission already recorded. Do not overwrite the review history.')
    before = {str(p.relative_to(ROOT)).replace('\\', '/'): digest(p)
              for folder in [DATA, ROOT / 'model Evaluation']
              for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    protected = {p: h for p, h in before.items()
                 if p.startswith('Dataset/train/') or p.startswith('Dataset/test_set/test_benign')
                 or (p.startswith('model Evaluation/') and p not in
                     ['model Evaluation/test_features.csv', 'model Evaluation/RESULTS_SUMMARY.md'])}
    canonical = jsonl_read(TEST / 'ssti_test_positives.jsonl')
    original = jsonl_read(TEST / 'ssti_test_positives_enriched.jsonl')
    candidates = {r['candidate_id']: r for r in jsonl_read(RESEARCH / 'candidate_payloads.jsonl')}
    assert len(canonical) == len(original) == 44
    assert [r['record_id'] for r in original] == [f'TEST-{i:03}' for i in range(1, 45)]
    assert [r['payload'] for r in canonical] == [r['payload'] for r in original]
    assert set(ADMITTED) | set(HELD) == set(candidates)
    raw_fields, _ = csv_read(TEST / 'ssti_test_positives.csv')
    enriched_fields = list(original[0]) + ['candidate_id', 'identifiers', 'source_locator',
        'extraction_method', 'scope_review_status', 'execution_status', 'human_review_status',
        'review_notes', 'related_train_ids', 'family_review_notes']
    old_combined = csv_read(TEST / 'ssti_test_combined.csv')[1]
    benign = [r for r in old_combined if r['label'] == '0']
    assert len(benign) == 500
    new_raw, new_enriched = [], []
    excluded = []
    for raw, enriched in zip(canonical, original):
        rid = enriched['record_id']
        if rid in EXCLUDED:
            excluded.append({'record_id': rid, 'reason': EXCLUDED[rid], 'canonical_record': raw,
                             'enriched_record': enriched})
            continue
        new_raw.append(raw.copy())
        row = {k: enriched.get(k, '') for k in enriched_fields}
        row.update(scope='template_ssti', scope_review_status='assistant_scope_review',
                   execution_status='not_executed', human_review_status='pending',
                   review_notes='Template-language input retained after scope screening. Original verbatim/source annotation was not independently reverified for every legacy row.')
        if rid == 'TEST-022':
            row['review_notes'] += ' FreeMarker ?new requires TemplateModel classes; the ProcessBuilder example is an attack-attempt string, not established working RCE. Execution validity needs review.'
        if rid in ('TEST-006', 'TEST-009', 'TEST-019', 'TEST-024', 'TEST-030', 'TEST-032'):
            row['review_notes'] += ' Probe/enumeration/fragment; do not count as demonstrated command execution.'
        new_enriched.append(row)
    for number, cid in enumerate(ADMITTED, start=45):
        c = candidates[cid]
        raw = dict(payload=c['payload'], engine=c['engine'], tier='A' if c['identifiers'] else 'C',
                   context=c['context_and_prerequisites'], source_url=c['source_url'], label=1)
        new_raw.append(raw)
        row = {k: '' for k in enriched_fields}
        row.update(raw)
        row.update(record_id=f'TEST-{number:03}', scope='template_ssti',
                   evidence_type='CVE_PoC' if c['identifiers'] else 'security_writeup',
                   related_train_family='yes' if cid in FAMILIES else 'no',
                   near_train_family='yes' if cid in FAMILIES else 'no',
                   capture_status='source_value_extracted', candidate_id=cid,
                   identifiers='; '.join(c['identifiers']), source_locator=c['source_locator'],
                   extraction_method=c['extraction_method'], scope_review_status='assistant_source_and_scope_review',
                   execution_status='not_executed', human_review_status='pending',
                   review_notes=c['review_notes'],
                   related_train_ids=FAMILIES.get(cid, ('', ''))[0],
                   family_review_notes=FAMILIES.get(cid, ('', 'No specific family match established; not a certification of independence.'))[1])
        new_enriched.append(row)
    combined = [dict(payload=r['payload'], label=1, source=r['source_url']) for r in new_raw] + benign
    train = csv_read(DATA / 'train/combined/train_combined.csv')[1]
    evaluation_train = csv_read(ROOT / 'model Evaluation/train_features.csv')[1]
    assert len(train) == 3636 and len(evaluation_train) == 4002
    assert len(combined) == 547 and len(new_raw) == 47
    assert len({r['payload'] for r in combined}) == len({key(r['payload']) for r in combined}) == len(combined)
    assert not {key(r['payload']) for r in combined}.intersection(key(r['payload']) for r in train)
    assert not {key(r['payload']) for r in combined}.intersection(key(r['payload']) for r in evaluation_train)
    spec = importlib.util.spec_from_file_location('extractor', DATA / 'scripts/ssti_feature_extraction.py')
    extractor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(extractor)
    feature_fields = csv_read(TEST / 'features/test_features.csv')[0]
    features = [dict(payload=r['payload'], **extractor.extract_features(r['payload']), label=r['label']) for r in combined]
    # All candidate checks and feature calculations complete before any data write.
    jsonl_write(TEST / 'ssti_test_positives.jsonl', new_raw)
    jsonl_write(TEST / 'ssti_test_positives_enriched.jsonl', new_enriched)
    csv_write(TEST / 'ssti_test_positives.csv', raw_fields, new_raw)
    csv_write(TEST / 'ssti_test_positives.tsv', raw_fields, new_raw, '\t')
    csv_write(TEST / 'ssti_test_positives_enriched.csv', enriched_fields, new_enriched)
    csv_write(TEST / 'ssti_test_combined.csv', ['payload', 'label', 'source'], combined)
    csv_write(TEST / 'features/test_features.csv', feature_fields, features)
    (ROOT / 'model Evaluation/test_features.csv').write_bytes((TEST / 'features/test_features.csv').read_bytes())
    assert all(digest(ROOT / p) == h for p, h in protected.items())
    evidence = dict(collections.Counter(r['evidence_type'] for r in new_enriched))
    tiers = dict(collections.Counter(r['tier'] for r in new_enriched))
    source_counts = collections.Counter(r['source_url'] for r in new_raw)
    flags = [r['record_id'] for r in new_enriched if r['related_train_family'] == 'yes' or r['near_train_family'] in ('yes', 'exact')]
    ledger = dict(date='2026-09-18', scope='Web-facing template-expression subset, including probes, information disclosure and server-side stages of chains; distinct expression languages and compiler-option injection are held separately.',
        before_counts=dict(positives=44, benign=500, combined=544),
        training_snapshot=dict(active_rows=len(train), active_positive_rows=1635,
            evaluation_copy_rows=len(evaluation_train), evaluation_copy_positive_rows=2001,
            note='Training was changed externally before this migration. Both versions screened; neither modified here. Seven original family flags are historical and require remapping.'),
        after_counts=dict(positives=47, benign=500, combined=547),
        excluded_original_records=excluded,
        added_records=[dict(record_id=r['record_id'], candidate_id=r['candidate_id'], source_url=r['source_url'], payload_sha256_utf8=hashlib.sha256(r['payload'].encode()).hexdigest()) for r in new_enriched if r['candidate_id']],
        candidate_dispositions={cid: dict(decision='admitted' if cid in ADMITTED else 'held', reason='Documented web-facing SSTI input; context and family limitations retained.' if cid in ADMITTED else HELD[cid]) for cid in candidates},
        evidence_counts=evidence, tier_counts=tiers, family_flag_ids=flags,
        duplicate_check=dict(exact_test_duplicates=0, normalized_test_duplicates=0, normalized_test_train_duplicates=0,
            normalization='Single URL percent decode, Unicode NFC, CRLF/CR to LF, outer whitespace strip; case, internal whitespace and literal escapes preserved. Used for checks only.'),
        limitations=['No payload execution or model rerun.', 'Legacy source-content and runtime-validity review is incomplete.', 'Training scope was not narrowed; compare scope-matched subsets before claiming strict SSTI performance.', 'Known family relations are flagged; distinct strings are not necessarily independent attacks.'],
        before_sha256=before, protected_sha256=protected, protected_files_unchanged=True)
    text_write(LEDGER, json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
    source_table = '| Retained source page | Positive rows |\n|---|---:|\n' + ''.join(
        f'| [{urlparse(url).netloc}{urlparse(url).path}]({url}) | {count} |\n' for url, count in source_counts.items())
    added_table = '| New ID | Product | Engine | Evidence |\n|---|---|---|---|\n' + ''.join(
        f'| {r["record_id"]} | {candidates[r["candidate_id"]]["product"]} | {r["engine"]} | [Source]({r["source_url"]}) |\n' for r in new_enriched if r['candidate_id'])
    report = '# Test-set scope review and additions — 18 September 2026\n\n'
    report += '## Result\n\n**47 positive examples + 500 unchanged benign examples = 547 rows.** Nine new source-documented inputs were added; six earlier related-injection rows were moved out of the active subset. All 38 retained positive strings are unchanged.\n\n'
    report += '## What counts here\n\nThe active positive subset uses server-side template expressions or directives supplied through web forms, APIs, uploaded application manifests or template-editing interfaces. It includes detection probes, information disclosure, sandbox escapes and command-execution attempts. It is not restricted to HTTP query parameters or successful RCE. A template in an attack chain is included only as the server-side stage; standalone browser XSS is excluded. No standalone XSS payloads were identified in the original positives during this review.\n\n'
    report += 'EJS option injection is often called SSTI in the literature. Its separation here is a narrower input-scope decision, not a claim that those advisories are wrong or that those rows are XSS. Training still contains broader collected examples: this scope mismatch must be acknowledged or resolved in future training review.\n\n'
    report += '## Added inputs\n\n' + added_table
    report += '\nThe LibreNMS and Alfresco inputs contain only the server-side template stage; their sources describe earlier XSS and permission prerequisites. Jupyter and WPML are arithmetic probes; listmonk demonstrates information disclosure. Source excerpts are preserved as captured, including multiline formatting and placeholders. Inputs were not executed.\n\n'
    report += '## Earlier rows separated from the active subset\n\n| ID | Reason |\n|---|---|\n' + ''.join(f'| {rid} | {reason} |\n' for rid, reason in EXCLUDED.items())
    report += '\nTheir complete original canonical and enriched records are preserved in [the JSON review ledger](test_scope_review_2026-09-18.json). They were not relabeled benign. Existing IDs were retained; new IDs start at TEST-045.\n\n'
    report += '## Research inputs held back\n\n| Candidate | Product | Reason |\n|---|---|---|\n' + ''.join(f'| {cid} | {candidates[cid]["product"]} | {reason} |\n' for cid, reason in HELD.items())
    report += '\n## Duplicate checks and remaining review\n\nZero exact or conservatively normalized duplicate payloads occur in the 547-row combined set. The same normalization found zero matching payloads against both the current 3,636-row training set and the older 4,002-row evaluation training copy. This includes positive-versus-benign comparisons. Normalization decodes URL percent escapes once, applies Unicode NFC, normalizes line endings and strips outer whitespace for comparison only. Stored payloads were not normalized.\n\n'
    report += f'**{len(flags)} positives have known related-training-family flags:** ' + ', '.join(flags) + '. The other rows are not certified unseen families. Changed command arguments, whitespace, wrappers or access syntax do not establish a new attack family. See enriched metadata for the six new family comparisons.\n\n'
    report += 'This is a source-and-scope review, not a runtime test or completed human label audit. In particular, TEST-022 remains an attack-attempt string whose claimed FreeMarker execution requires review; several legacy probes require application context. Existing model scores were not rerun and do not describe this release.\n\n'
    report += '**Separate training issue found:** active training now contains 1,635 positives + 2,001 benign = 3,636, but the evaluation training copy still contains 4,002 rows. Both were left unchanged. Synchronize them deliberately before evaluation. Seven original family flags refer to the earlier training release; six new comparisons use current IDs. This review does not certify a scope-matched training dataset.\n\n'
    report += '## Updated files\n\nPositive JSONL/CSV/TSV, enriched JSONL/CSV, combined CSV and both test-feature copies were rebuilt in the existing locations. The original 500 benign rows, training files, feature definitions and algorithm notebooks are unchanged. [Current inventory](../FILE_MANIFEST.json) records the resulting file hashes. Original research JSONL files retain their collection-time candidate status; this review ledger records the subsequent admission decision.\n'
    text_write(REPORT, report)
    text_write(TEST / 'sources.md', '# Sources — current SSTI test subset\n\n'
        + f'**47 positives across {len(source_counts)} source pages; 500 benign inputs; 547 total records.** Updated 18 September 2026.\n\n'
        + '## Scope and review\n\nSee the [scope review and admission decisions](../review/TEST_SCOPE_REVIEW_2026-09-18.md). Source-documented template inputs include probes and information disclosure, not only RCE. Earlier XSS stages are context, not active positive rows. Six related-injection inputs are preserved outside the active set in the review ledger.\n\n'
        + '## Retained positive sources\n\n' + source_table
        + '\n## Evidence and independence\n\nEvidence annotations: ' + ', '.join(f'{k}={v}' for k, v in evidence.items()) + '. Tier annotations: ' + ', '.join(f'{k}={v}' for k, v in tiers.items()) + '. These count rows, not independent incidents; older categories still need source-type review.\n\n'
        + f'{len(flags)} positives have known training-family relationships. Zero exact/transport-normalized string duplicates does not establish family independence. Six newly flagged comparisons include training IDs in the enriched records; original seven flags retain their earlier annotations.\n\n'
        + '## Benign sources\n\nThe 500 unchanged benign rows contain 143 template fragments (89 Sidekiq, 25 microblog, 19 Symfony demo, 10 Spring Petclinic) and 357 HttpParamsDataset parameters. See [benign source references](../train/SOURCES.md#benign-sources). Train/test share repositories; file separation is not independently established without per-record paths.\n\n'
        + '## Loading and reproduction\n\nUse `ssti_test_positives.jsonl` as the lossless positive source; enriched files carry source locators, extraction methods and review status. CSV/TSV fields quote actual embedded newlines: count parsed records, not physical lines. Combined positives precede unchanged benign rows. Both test-feature files have the original 17 numeric feature columns. Run `../scripts/reconcile_dataset_exports.py --validate --test-only` for consistency checks. Do not rerun historical collectors over this release. Source attribution is recorded per row; public availability alone is not permission to redistribute.\n')
    readme = DATA / 'README.md'
    s = readme.read_text(encoding='utf-8').replace('44 positives + 500 benign = **544**', '47 positives + 500 benign = **547**').replace('24 cases/leads and 14 candidate inputs, not yet admitted', '24 cases/leads and 14 captured inputs; 9 now admitted, 5 held back')
    s = s.replace('2,001 positives + 2,001 benign = **4,002**', '1,635 positives + 2,001 benign = **3,636**')
    s = s.replace('train/combined/train_combined_nofeatures.csv', 'train/combined/train_combined.csv')
    s = s.replace('They match the canonical feature files here.', 'The test copy matches the current canonical test features. The training copy is stale (4,002 rows versus 3,636 in active training); it was not changed in this test-only update.')
    s = s.replace('## What still needs review', '## Latest test update\n\n[Scope review and additions](review/TEST_SCOPE_REVIEW_2026-09-18.md): nine new inputs admitted, six related-injection rows preserved outside the active subset. No standalone XSS inputs were identified in the original positive set. Exact and conservative normalized duplicate checks passed across test and training.\n\n## What still needs review')
    text_write(readme, s)
    guide = DATA / 'HOW_TO_BUILD_A_DATASET.md'
    s = guide.read_text(encoding='utf-8')
    s = s.replace('#### Where the current SSTI training set came from', '#### Where the SSTI training set came from\n\n**Training update found during test review:** current active training has 1,635 repository positives and 2,001 benign rows (3,636 total); the 366 legacy seed positives are archived. The evaluation training copy still has 4,002 rows. The detailed 2,001-positive provenance breakdown below describes the earlier training release; this test-only update did not modify training files.')
    start = s.index('The active set contains **44 positive examples')
    end = s.index('**Benign test examples: 500**', start)
    s = s[:start] + f'The active set contains **47 positive examples and 500 benign examples**, for **547 total records**. The following table counts retained positive rows across {len(source_counts)} source pages. It includes the nine approved additions; six related-injection inputs are preserved separately. See the [scope review](review/TEST_SCOPE_REVIEW_2026-09-18.md).\n\n' + source_table + '\nEvidence categories count records, not independent vulnerabilities. Existing source-type annotations remain provisional.\n\n' + s[end:]
    s = s.replace('Four automatic skeleton matches and three additional near matches are flagged among the positives. They are not seven identical raw strings, and the other 37 rows are not certified unseen families.', 'Thirteen positives have known training-family relationships (seven earlier flags plus six new comparisons). Zero exact or conservative normalized duplicates remain, but the other 34 positives are not certified unseen families.')
    s = s.replace('Research candidates stay separate from the active test files until the specific proposed additions and their overlap have been reviewed.', 'Nine of the 14 captured candidates have now been admitted after source/scope and duplicate review; five remain outside the active set. The [admission ledger](review/test_scope_review_2026-09-18.json) records the decisions. Original research files preserve their collection-time status.')
    text_write(guide, s)
    datasheet = DATA / 'DATASHEET.md'
    s = datasheet.read_text(encoding='utf-8')
    s = s.replace('4,002 rows — 2,001 SSTI positives (1,296 unique structural skeletons)', '3,636 rows — 1,635 repository SSTI positives').replace('  Balanced 1:1.', '  No longer balanced 1:1. The evaluation training copy still has 4,002 rows; resolve this separately before rerunning models.')
    s = s.replace('and 366 to the local legacy seed.', 'and 366 to the local legacy seed in the earlier release. Those 366 seed rows are now archived outside active training.')
    s = s.replace('All 2,001 mechanism annotations remain', 'Active training mechanism annotations remain')
    s = s.replace('Feature values and payload/label alignment were checked for all four active\n  train/test feature exports. This validates serialization and computation, not labels.', 'Both current test-feature copies were recomputed and checked for alignment.\n  Training files were left unchanged; their evaluation copy is stale. Test checks\n  validate serialization and computation, not runtime behavior or label correctness.')
    start = s.index('- **External challenge set:**')
    end = s.index('- **Labels.**', start)
    s = s[:start] + '- **External challenge set:** 547 rows — 47 positive examples and 500 benign inputs.\n  The active scope is template-expression inputs in web-facing workflows; six related\n  expression/compiler-option injection rows are preserved in the review ledger.\n  Nine source-documented candidates were added. Evidence annotations: ' + ', '.join(f'{k}={v}' for k, v in evidence.items()) + '.\n  These count records, not verified independent incidents. See the [scope review](review/TEST_SCOPE_REVIEW_2026-09-18.md).\n' + s[end:]
    s = s.replace('External annotations flag four skeleton matches and three leading-`1` near matches.\n  Zero exact raw positive-string matches is not a claim of seven exact duplicates\n  or of complete independence among the remaining cases.', 'External annotations flag 13 known related-training-family examples: seven original\n  flags and six new comparisons. No exact or conservatively normalized duplicates\n  were found within test or against training; unflagged rows are not certified independent.')
    s = s.replace('small (44 attacks)', 'small (47 positive examples)').replace('newlines in five records', 'newlines in eight records')
    s = s.replace('- Training enrichment has URL/file/commit fields', '- New positive annotations include source locators, extraction methods and permission\n  context. Source review was performed without executing inputs; human review remains\n  pending. Training retains its earlier broader scope and was not filtered in this update.\n- Training enrichment has URL/file/commit fields')
    text_write(datasheet, s)
    for path, note in [
        (DATA / 'review/README.md', 'Current test decisions: [scope review](TEST_SCOPE_REVIEW_2026-09-18.md) and [lossless review ledger](test_scope_review_2026-09-18.json). Nine inputs admitted; six old related-injection rows separated.\n\n'),
        (DATA / 'scripts/README.md', '`admit_ssti_test_candidates.py --apply` records the guarded, one-time 18 September test update. Its existing review ledger prevents accidental reruns; use the validator to check the current release.\n\n'),
        (RESEARCH / 'SSTI_TEST_EXPANSION_RESEARCH.md', '**Subsequent admission update:** nine of the 14 captured inputs are now active; five are held back. This report and its candidate JSONL describe the original collection snapshot. See the [current decisions](../../review/TEST_SCOPE_REVIEW_2026-09-18.md) and [ledger](../../review/test_scope_review_2026-09-18.json). Do not rerun the historical research builder over this annotated report.\n\n'),
        (ROOT / 'model Evaluation/RESULTS_SUMMARY.md', '**Test release changed on 18 September 2026:** current files contain 47 positives + 500 benign = 547 rows. Active training separately changed to 3,636 rows; this folder still has the older 4,002-row training copy. The saved scores and dataset description below refer to the earlier 44-positive release; they have not been recomputed. See the [test review](../Dataset/review/TEST_SCOPE_REVIEW_2026-09-18.md).\n\n')]:
        content = path.read_text(encoding='utf-8')
        first, rest = content.split('\n', 1)
        text_write(path, first + '\n\n' + note + rest.lstrip('\n'))
    assert all(digest(ROOT / p) == h for p, h in protected.items())
    print(json.dumps(dict(after_counts=ledger['after_counts'], evidence=evidence, tiers=tiers,
                         source_pages=len(source_counts), family_flags=len(flags), protected_files=len(protected)), indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', required=True)
    parser.parse_args()
    main()
