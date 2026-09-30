"""Repair positive test serialization and record a reversible, validated release inventory.

Run with --prepare before editing documentation, --repair to refresh CSV/TSV,
and --finalize after documentation edits. No training or label changes occur.
"""
import argparse
import collections
import csv
import hashlib
import importlib.util
import json
import math
import shutil
import sys
import unicodedata
import zipfile
from urllib.parse import unquote
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKUP = ROOT / 'Dataset/review/repair_sessions/serialization_repair/backups'
BEFORE = BACKUP.parent / 'before.json'
MANIFEST = ROOT / 'Dataset/review/repair_sessions/serialization_repair/release_manifest.json'
DATA_TARGETS = ['Dataset/test_set/ssti_test_positives.csv',
                'Dataset/test_set/ssti_test_positives.tsv']
DOC_TARGETS = ['Dataset/DATASHEET.md', 'Dataset/train/README.md',
               'Dataset/test_set/sources.md', 'Dataset/train/SOURCES.md',
               'Dataset/review/history/MANIFEST_and_CORRECTIONS.md', 'model Evaluation/RESULTS_SUMMARY.md']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(rel):
    path = ROOT / rel
    with path.open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle, delimiter='\t' if path.suffix == '.tsv' else ',', strict=True)
        fields = reader.fieldnames
        rows = list(reader)
    assert fields and all(None not in row and all(v is not None for v in row.values()) for row in rows), rel
    return fields, rows


def read_jsonl(rel):
    return [json.loads(line) for line in (ROOT / rel).read_text(encoding='utf-8').splitlines() if line.strip()]


def tracked_files():
    paths = list((ROOT / 'Dataset').rglob('*'))
    paths += [(ROOT / 'model Evaluation' / name) for name in
              ['train_features.csv', 'test_features.csv', 'Model_evaluation.ipynb', 'RESULTS_SUMMARY.md']]
    return sorted(p for p in paths if p.is_file() and '_archive' not in p.parts
                  and '__pycache__' not in p.parts and p != MANIFEST)


def identity(rows):
    return [(r['payload'], str(r['label'])) for r in rows]


def prepare():
    if BEFORE.exists():
        raise RuntimeError(f'Existing backup session: {BEFORE}. Do not overwrite it.')
    BACKUP.mkdir(parents=True, exist_ok=False)
    state = {p.relative_to(ROOT).as_posix(): digest(p) for p in tracked_files()}
    for rel in DATA_TARGETS + DOC_TARGETS:
        target = BACKUP / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, target)
    BEFORE.write_text(json.dumps(state, indent=2) + '\n', encoding='utf-8')
    print(f'Backed up {len(DATA_TARGETS + DOC_TARGETS)} affected files; inventoried {len(state)} files.')


def repair():
    before = json.loads(BEFORE.read_text(encoding='utf-8'))
    canonical = read_jsonl('Dataset/test_set/ssti_test_positives.jsonl')
    enriched = read_jsonl('Dataset/test_set/ssti_test_positives_enriched.jsonl')
    assert len(canonical) == 44 and identity(canonical) == identity(enriched)
    for rel in DATA_TARGETS:
        path = ROOT / rel
        assert digest(path) == before[rel], f'{rel} changed since backup'
        fields, old = read_csv(rel)
        assert len(old) == len(canonical)
        # Metadata and order are retained. Only the five audited escaped-newline
        # representations may change; never globally decode payload escapes.
        changed = []
        for index, (a, b) in enumerate(zip(old, canonical), start=2):
            assert all(a[k] == str(b[k]) for k in fields if k != 'payload')
            if a['payload'] != b['payload']:
                assert a['payload'] == b['payload'].replace('\n', '\\n')
                changed.append(index)
        assert changed == [40, 41, 42, 43, 44], (rel, changed)
        temporary = path.with_suffix(path.suffix + '.repair-tmp')
        assert not temporary.exists()
        with temporary.open('w', encoding='utf-8', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=fields,
                                    delimiter='\t' if path.suffix == '.tsv' else ',',
                                    lineterminator='\n')
            writer.writeheader()
            writer.writerows({k: row[k] for k in fields} for row in canonical)
        temporary.replace(path)
        assert identity(read_csv(rel)[1]) == identity(canonical)
        print(f'{rel}: repaired records {changed}; 44 records preserved.')


def validate_test():
    """Validate this test release without repairing or assuming a training schema."""
    canonical = read_jsonl('Dataset/test_set/ssti_test_positives.jsonl')
    enriched = read_csv('Dataset/test_set/ssti_test_positives_enriched.csv')[1]
    assert identity(enriched) == identity(canonical)
    assert len({r['record_id'] for r in enriched}) == len(canonical)
    assert all(r['scope'] == 'template_ssti' for r in enriched)
    for raw, annotation in zip(canonical, enriched):
        assert all(annotation[k] == str(v) for k, v in raw.items()), 'Raw/enriched metadata mismatch'
    restored_csv = ROOT / 'Dataset/test_set/ssti_test_positives.csv'
    if restored_csv.exists():
        assert read_csv('Dataset/test_set/ssti_test_positives.csv')[1] == [
            {k: str(v) for k, v in row.items()} for row in canonical
        ], 'Positive CSV differs from canonical JSONL'
    combined = read_csv('Dataset/test_set/ssti_test_combined.csv')[1]
    benign = read_csv('Dataset/test_set/test_benign.csv')[1]
    assert identity(combined) == identity(canonical) + identity(benign)
    assert [r['source'] for r in combined[:len(canonical)]] == [r['source_url'] for r in canonical]
    def duplicate_key(payload):
        return unicodedata.normalize('NFC', unquote(payload)).replace('\r\n', '\n').replace('\r', '\n').strip()
    keys = {duplicate_key(r['payload']) for r in combined}
    assert len(keys) == len({r['payload'] for r in combined}) == len(combined)
    train_path = 'Dataset/train/combined/train_combined.csv'
    if not (ROOT / train_path).exists():
        train_path = 'Dataset/train/combined/train_combined_nofeatures.csv'
    # Only payload and label are needed for this cross-set check. The externally
    # changed training CSV has short metadata rows; report them without rewriting it.
    with (ROOT / train_path).open(encoding='utf-8-sig', newline='') as handle:
        train = list(csv.DictReader(handle, strict=True))
    assert all(r.get('payload') is not None and r.get('label') in ('0', '1') and None not in r for r in train)
    malformed_training_metadata = sum(any(v is None for v in r.values()) for r in train)
    eval_train = read_csv('model Evaluation/train_features.csv')[1]
    for training in (train, eval_train):
        assert not keys.intersection(duplicate_key(r['payload']) for r in training)
    spec = importlib.util.spec_from_file_location('features', ROOT / 'Dataset/scripts/ssti_feature_extraction.py')
    extractor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(extractor)
    for rel in ['Dataset/test_set/features/test_features.csv', 'model Evaluation/test_features.csv']:
        features = read_csv(rel)[1]
        assert identity(features) == identity(combined), rel
        for feature, row in zip(features, combined):
            expected = extractor.extract_features(row['payload'])
            assert all(math.isclose(float(feature[k]), float(v), rel_tol=0, abs_tol=1e-6)
                       for k, v in expected.items()), rel
    assert (ROOT / 'Dataset/test_set/features/test_features.csv').read_bytes() == (ROOT / 'model Evaluation/test_features.csv').read_bytes()
    # The research snapshot was subsequently consolidated into the history ZIP.
    # Its old protection hashes describe that release, not today's training files.
    candidate_path = ROOT / 'Dataset/research/ssti_test_expansion_2026-09-18/candidate_payloads.jsonl'
    if candidate_path.exists():
        candidate_text = candidate_path.read_text(encoding='utf-8')
    else:
        with zipfile.ZipFile(ROOT / 'Dataset/_archive/dataset_history_2026-09-19.zip') as history:
            candidate_text = history.read('research/ssti_test_expansion_2026-09-18/candidate_payloads.jsonl').decode('utf-8')
    candidate_rows = [json.loads(line) for line in candidate_text.splitlines() if line.strip()]
    candidates = {r['candidate_id']: r for r in candidate_rows}
    for row in enriched:
        if row['candidate_id']:
            candidate = candidates[row['candidate_id']]
            assert row['payload'] == candidate['payload'] and row['source_url'] == candidate['source_url']
    return {'test_release_checks': 'passed', 'test_positives': len(canonical),
            'test_benign': len(benign), 'test_combined': len(combined),
            'multiline_positive_records': sum('\n' in r['payload'] for r in canonical),
            'test_exact_and_normalized_duplicates': 0, 'duplicates_against_both_training_versions': 0,
            'test_feature_copies': 'byte-identical; 17 features recomputed and checked',
            'source_capture_alignment': 'passed against original research records', 'payloads_executed': False,
            'active_training_rows': len(train), 'evaluation_training_rows': len(eval_train),
            'training_rows_with_missing_trailing_metadata_fields': malformed_training_metadata,
            'training_status': 'WARNING: evaluation training copy is stale; not modified' if identity(train) != identity(eval_train) else 'payloads/labels aligned',
            'semantic_limitations': 'Source/scope review only; legacy runtime validity and human review remain pending'}


def validate():
    if not (ROOT / 'Dataset/train/combined/train_combined_nofeatures.csv').exists():
        raise RuntimeError('Training schema changed externally. Use --validate --test-only for the current test release; resolve the stale evaluation training copy separately.')
    train = read_csv('Dataset/train/combined/train_combined_nofeatures.csv')[1]
    positive = [r for r in train if r['label'] == '1']
    benign = [r for r in train if r['label'] == '0']
    assert len(train) == 4002 and len(positive) == len(benign) == 2001
    assert read_csv('Dataset/train/positives/positives.csv')[1] == positive
    assert (ROOT / 'Dataset/train/positives/positives.txt').read_text(encoding='utf-8').splitlines() == [r['payload'] for r in positive]
    enrichment = read_csv('Dataset/train/positives/positives_enriched.csv')[1]
    assert identity(enrichment) == identity(positive)
    assert len({r['record_id'] for r in enrichment}) == 2001
    assert all(a['skeleton_id'] == b['base_id'] for a, b in zip(enrichment, positive))
    canonical = read_jsonl('Dataset/test_set/ssti_test_positives.jsonl')
    for rel in DATA_TARGETS + ['Dataset/test_set/ssti_test_positives_enriched.csv']:
        assert identity(read_csv(rel)[1]) == identity(canonical), rel
    test_enriched = read_jsonl('Dataset/test_set/ssti_test_positives_enriched.jsonl')
    assert identity(test_enriched) == identity(canonical)
    assert len({r['record_id'] for r in test_enriched}) == len(canonical)
    for a, b in zip(read_csv('Dataset/test_set/ssti_test_positives_enriched.csv')[1], test_enriched):
        assert a == {k: str(v) for k, v in b.items()}
    combined = read_csv('Dataset/test_set/ssti_test_combined.csv')[1]
    assert len(combined) == len(canonical) + len(read_csv('Dataset/test_set/test_benign.csv')[1])
    # Conservative duplicate screen only; never rewrite source payload strings.
    def duplicate_key(payload):
        return unicodedata.normalize('NFC', unquote(payload)).replace('\r\n', '\n').replace('\r', '\n').strip()
    raw_keys = [r['payload'] for r in combined]
    test_keys = [duplicate_key(p) for p in raw_keys]
    assert len(set(raw_keys)) == len(combined), 'Exact duplicate test payloads'
    assert len(set(test_keys)) == len(combined), 'Transport-normalized duplicate test payloads'
    assert not set(test_keys).intersection(duplicate_key(r['payload']) for r in train), 'Test/train payload overlap'
    assert identity([r for r in combined if r['label'] == '1']) == identity(canonical)
    assert identity([r for r in combined if r['label'] == '0']) == identity(read_csv('Dataset/test_set/test_benign.csv')[1])
    spec = importlib.util.spec_from_file_location('features', ROOT / 'Dataset/scripts/ssti_feature_extraction.py')
    extractor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(extractor)
    for rel, source in [('Dataset/train/combined/train_features.csv', train),
                        ('model Evaluation/train_features.csv', train),
                        ('Dataset/test_set/features/test_features.csv', combined),
                        ('model Evaluation/test_features.csv', combined)]:
        features = read_csv(rel)[1]
        assert identity(features) == identity(source), rel
        for a, b in zip(features, source):
            if 'base_id' in b:
                assert a['base_id'] == b['base_id']
            expected = extractor.extract_features(b['payload'])
            assert all(math.isclose(float(a[k]), float(v), rel_tol=0, abs_tol=1e-6) for k, v in expected.items()), rel
    return {
        'strict_parsing_and_export_reconciliation': 'passed',
        'all_four_feature_exports_recomputed_and_verified': 'passed',
        'training_rows': 4002, 'training_positive_rows': 2001, 'test_rows': len(combined),
        'test_positive_rows': len(canonical), 'test_multiline_positive_rows': sum('\n' in r['payload'] for r in canonical),
        'exact_and_transport_normalized_test_duplicates': 0,
        'transport_normalized_test_train_duplicates': 0,
        'training_annotation_url_rows': sum(bool(r['source_url']) for r in enrichment),
        'training_annotation_commit_rows': sum(bool(r['source_commit']) for r in enrichment),
        'test_evidence_types_as_annotated': dict(collections.Counter(r['evidence_type'] for r in test_enriched)),
        'overlap_flag_union_count': sum(r['related_train_family'] == 'yes' or r['near_train_family'] in ('yes', 'exact') for r in test_enriched),
        'source_url_content_and_historical_commit_verification': 'not performed; populated metadata is not source validation',
        'semantic_label_review': 'See test scope review ledger; training annotations and full execution validation remain pending',
    }


def finalize():
    checks = validate()
    before = json.loads(BEFORE.read_text(encoding='utf-8'))
    after = {p.relative_to(ROOT).as_posix(): digest(p) for p in tracked_files()}
    changed = [r for r in before if before[r] != after.get(r)]
    assert set(changed) <= set(DATA_TARGETS + DOC_TARGETS), changed
    inventory = {}
    for rel, value in after.items():
        p = ROOT / rel
        entry = {'sha256': value, 'bytes': p.stat().st_size}
        if p.suffix in ('.csv', '.tsv', '.jsonl'):
            try:
                entry['records'] = len(read_jsonl(rel) if p.suffix == '.jsonl' else read_csv(rel)[1])
                with p.open(encoding='utf-8-sig', newline='') as handle:
                    entry['physical_lines_including_header_if_present'] = sum(1 for _ in handle)
            except (csv.Error, AssertionError, ValueError) as exc:
                entry['parse_error'] = str(exc)
        inventory[rel] = entry
    result = {
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'scope': 'Two test serialization exports and documentation only; no relabeling or model changes.',
        'backup_directory': BACKUP.relative_to(ROOT).as_posix(),
        'changed_files': [{'path': r, 'before_sha256': before[r], 'after_sha256': after[r],
                           'backup': (BACKUP / r).relative_to(ROOT).as_posix()} for r in changed],
        'new_files': sorted(set(after) - set(before)),
        'validation': checks,
        'inventory': inventory,
        'inventory_note': 'Archives and caches excluded. This JSON manifest excludes itself to avoid a self-referential hash. Documentation, source JSONL, training exports, feature copies and notebook are tracked.',
    }
    MANIFEST.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'validation': checks, 'changed_files': changed}, indent=2))


if __name__ == '__main__':
    sys.dont_write_bytecode = True
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare', action='store_true')
    mode.add_argument('--repair', action='store_true')
    mode.add_argument('--finalize', action='store_true')
    mode.add_argument('--validate', action='store_true', help='Read-only validation of current data exports')
    parser.add_argument('--test-only', action='store_true', help='Validate current test exports and screen against both training versions without changing them')
    args = parser.parse_args()
    if args.validate:
        print(json.dumps(validate_test() if args.test_only else validate(), indent=2))
    elif args.prepare:
        prepare()
    elif args.repair:
        repair()
    else:
        finalize()
