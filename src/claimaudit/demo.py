"""UI-independent demo services. Saved result browsing does not import model libraries."""
from dataclasses import asdict, replace
from datetime import datetime, timezone
import json
from pathlib import Path
from threading import RLock

from claimaudit.config import ExperimentConfig
from claimaudit.schemas import ClaimInput, Verdict
from claimaudit.verification.structure import fuse_predictions

METHOD_LABELS = {'embedding': 'Embedding similarity', 'nli': 'NLI',
                 'nli_numeric': 'NLI + numbers', 'nli_comparison': 'NLI + comparisons',
                 'structure-aware': 'Structure-aware'}
REQUIRED_ARTIFACTS = {'protocol.json', 'calibration.json', 'predictions.jsonl',
                      'failures.jsonl', 'summary.json', 'report.md'}


def load_run(directory: Path) -> dict:
    """Validate completed artifact bytes before displaying any recorded result."""
    marker = json.loads((directory / 'complete.json').read_text())
    if not isinstance(marker, dict):
        raise ValueError('Invalid completion marker')
    if marker.get('status') != 'complete' or set(marker.get('artifacts', {})) != REQUIRED_ARTIFACTS:
        raise ValueError('This directory is not a complete evaluation run')
    # Read once, then verify and decode those same bytes (avoid a read/hash race).
    import hashlib
    content = {}
    for name in sorted(REQUIRED_ARTIFACTS):
        raw = (directory / name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != marker['artifacts'][name]:
            raise ValueError(f'Artifact integrity check failed: {name}')
        content[name] = raw.decode('utf-8')
    run = {name.removesuffix('.json'): json.loads(content[name])
           for name in ('protocol.json', 'calibration.json', 'summary.json')}
    run['records'] = [json.loads(line) for line in content['predictions.jsonl'].splitlines()]
    run['report'] = content['report.md']
    if len({row['id'] for row in run['records']}) != len(run['records']):
        raise ValueError('Saved prediction IDs are not unique')
    return run


def calibration_thresholds(run: dict, config: ExperimentConfig) -> tuple[float, float]:
    """Never silently apply a calibration from different model revisions/settings."""
    stored = run['protocol']['config']
    fields = ('model_id', 'revision', 'device')
    for name in ('embedding', 'nli'):
        current = getattr(config, name)
        if current is None or any(getattr(current, field) != stored[name][field] for field in fields):
            raise ValueError('Saved calibration belongs to different model settings')
    if config.nli.max_length != stored['nli']['max_length']:
        raise ValueError('Saved calibration uses a different NLI token limit')
    embedding = run['calibration']['thresholds']['embedding']['threshold']
    nli = run['calibration']['thresholds']['nli']['threshold']
    replace(config.embedding, threshold=embedding)
    replace(config.nli, threshold=nli)
    return embedding, nli


def filter_records(records: list[dict], *, split='test', method='structure-aware',
                   errors_only=False, label=None, group=None) -> list[dict]:
    if method not in METHOD_LABELS:
        raise ValueError('Unknown verification method')
    result = []
    for row in records:
        if row['split'] != split or (label and row['label'] != label) or (group and row['group_id'] != group):
            continue
        gold = 'supported' if row['label'] == 'supported' else 'not_supported'
        if errors_only and row['methods'][method]['verdict'] == gold:
            continue
        result.append(row)
    return result


class DemoEngine:
    """Serialize access to globally cached model resources; never cache user text."""
    def __init__(self, config: ExperimentConfig, embedding, nli) -> None:
        self.config, self.embedding, self.nli = config, embedding, nli
        self.lock = RLock()

    @classmethod
    def load(cls, config: ExperimentConfig, offline: bool = True):
        from claimaudit.baselines.embedding import EmbeddingVerifier
        from claimaudit.baselines.nli import NLIVerifier
        if config.embedding is None or config.nli is None or config.structure is None:
            raise ValueError('Demo requires embedding, NLI, and structure configuration')
        configured = replace(config, embedding=replace(config.embedding, local_files_only=offline),
                             nli=replace(config.nli, local_files_only=offline))
        return cls(configured, EmbeddingVerifier(configured.embedding), NLIVerifier(configured.nli))

    def verify(self, evidence: str, claim: str, embedding_threshold: float, nli_threshold: float,
               *, numeric: bool = True, comparison: bool = True) -> dict:
        item = ClaimInput(evidence.strip(), claim.strip())
        if max(len(item.evidence), len(item.claim)) > 20000:
            raise ValueError('Please keep each text under 20,000 characters; model token limits also apply.')
        replace(self.config.embedding, threshold=embedding_threshold)
        replace(self.config.nli, threshold=nli_threshold)
        structure = replace(self.config.structure, numeric_checks=numeric, comparison_checks=comparison)
        with self.lock:
            embedding, nli = self.embedding.verify(item), self.nli.verify(item)
        retuned = []
        for prediction, threshold in ((embedding, embedding_threshold), (nli, nli_threshold)):
            if prediction.score is None:
                raise ValueError('Model did not return a score')
            retuned.append(replace(prediction,
                verdict=Verdict.SUPPORTED if prediction.score >= threshold else Verdict.NOT_SUPPORTED,
                explanation=f'{prediction.score_type} {prediction.score:.6f}; support threshold >= {threshold:.8f}.'))
        hybrid = fuse_predictions([item], [retuned[1]], structure)[0]
        return {'purpose': 'interactive_diagnostic_not_benchmark',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'input': asdict(item), 'thresholds': {'embedding': embedding_threshold, 'nli': nli_threshold},
                'structure': asdict(structure),
                'models': {name: {'model_id': getattr(self.config, name).model_id,
                                  'revision': getattr(self.config, name).revision,
                                  'device': getattr(self.config, name).device} for name in ('embedding','nli')},
                'predictions': {name: asdict(prediction) for name, prediction in
                                zip(('embedding','nli','structure-aware'), (*retuned, hybrid))}}
