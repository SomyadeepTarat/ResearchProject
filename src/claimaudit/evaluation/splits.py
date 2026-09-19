"""Freeze and validate whole-group splits; reject missing IDs and leakage."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
from claimaudit.schemas import Example


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def create_manifest(rows: list[Example], path: Path, seed: int = 42) -> dict:
    groups = sorted({row.split_group for row in rows})
    if len(groups) < 5:
        raise ValueError('At least five independent groups are required for three splits')
    random.Random(seed).shuffle(groups)
    n_dev = max(1, len(groups) // 5)
    n_test = max(1, len(groups) // 5)
    split_groups = {'train': groups[:-(n_dev+n_test)], 'dev': groups[-(n_dev+n_test):-n_test], 'test': groups[-n_test:]}
    return {'schema_version': 1, 'seed': seed, 'dataset_sha256': file_hash(path),
            'grouping': 'group_id when provided, otherwise source_id',
            'splits': {name: sorted(row.id for row in rows if row.split_group in selected)
                       for name, selected in split_groups.items()},
            'groups': {name: sorted(selected) for name, selected in split_groups.items()}}


def load_splits(rows: list[Example], dataset: Path, manifest_path: Path) -> dict[str, list[Example]]:
    manifest = json.loads(manifest_path.read_text())
    if manifest.get('schema_version') != 1 or manifest.get('dataset_sha256') != file_hash(dataset):
        raise ValueError('Split manifest version or dataset hash mismatch')
    splits = manifest.get('splits')
    if not isinstance(splits, dict) or set(splits) != {'train', 'dev', 'test'}:
        raise ValueError('Manifest must define train, dev, test')
    all_ids = []
    for ids in splits.values():
        if not isinstance(ids, list) or not ids or any(not isinstance(item, str) for item in ids):
            raise ValueError('Each split must be a nonempty list of IDs')
        all_ids.extend(ids)
    if len(set(all_ids)) != len(all_ids) or set(all_ids) != {row.id for row in rows}:
        raise ValueError('Splits must cover each dataset ID exactly once')
    lookup = {row.id: row for row in rows}
    output = {name: [lookup[item] for item in ids] for name, ids in splits.items()}
    owner = {}
    for name, split_rows in output.items():
        for row in split_rows:
            for key in [('group', row.split_group), ('source', row.source_id),
                        ('evidence', ' '.join(row.evidence.casefold().split()))]:
                if key in owner and owner[key] != name:
                    raise ValueError(f'Cross-split leakage: {key[0]}')
                owner[key] = name
        declared = manifest.get('groups', {}).get(name)
        if declared != sorted({row.split_group for row in split_rows}):
            raise ValueError('Manifest group listing does not match split IDs')
        if len({row.gold_verdict for row in split_rows}) != 2:
            raise ValueError(f'{name} must contain both binary gold classes')
    return output


def split_summary(splits: dict[str, list[Example]]) -> dict:
    return {name: {'examples': len(rows), 'sources': len({r.source_id for r in rows}),
                   'groups': sorted({r.split_group for r in rows}),
                   'labels': dict(Counter(row.label.value for row in rows))}
            for name, rows in splits.items()}
