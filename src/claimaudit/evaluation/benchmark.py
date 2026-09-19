"""Development calibration followed by a frozen grouped synthetic evaluation."""
import argparse
from collections import Counter
from dataclasses import asdict, replace
from datetime import datetime, timezone
from importlib.metadata import version
import json
from pathlib import Path
import platform
import time

from claimaudit.config import ExperimentConfig
from claimaudit.evaluation.dataset import load_dataset
from claimaudit.evaluation.metrics import binary_metrics, paired_group_bootstrap, select_threshold
from claimaudit.evaluation.splits import file_hash, load_splits, split_summary
from claimaudit.schemas import Verdict
from claimaudit.verification.structure import fuse_predictions


METHODS = ('embedding', 'nli', 'nli_numeric', 'nli_comparison', 'structure-aware')


def write_json(path: Path, value) -> None:
    with path.open('x', encoding='utf-8') as handle:
        json.dump(value, handle, indent=2, default=str, allow_nan=False)
        handle.write('\n')


def build_models(config):
    from transformers import set_seed
    from claimaudit.baselines.embedding import EmbeddingVerifier
    from claimaudit.baselines.nli import NLIVerifier
    set_seed(config.seed)
    models = {'embedding': EmbeddingVerifier(config.embedding), 'nli': NLIVerifier(config.nli)}
    metadata = {'embedding_max_length': models['embedding'].encoder.model.max_seq_length,
                'nli_max_length': models['nli'].backend.max_length,
                'nli_id2label': dict(enumerate(models['nli'].backend.labels)),
                'pair_order': ['evidence', 'claim']}
    return models, metadata


def score_rows(rows, models):
    inputs = [row.to_input() for row in rows]
    raw = {}
    for method, model in models.items():
        predictions = model.verify_many(inputs)
        if len(predictions) != len(rows) or any(p.score is None for p in predictions):
            raise ValueError(f'{method} did not return a score for every input')
        raw[method] = predictions
    return raw


def apply_threshold(predictions, threshold):
    return [replace(p, verdict=Verdict.SUPPORTED if p.score >= threshold else Verdict.NOT_SUPPORTED,
                    explanation=f'{p.score_type} {p.score:.6f}; development-selected support threshold >= {threshold:.17g}.')
            for p in predictions]


def variants(rows, raw, thresholds, config):
    output = {name: apply_threshold(raw[name], thresholds[name]['threshold']) for name in ('embedding', 'nli')}
    inputs = [row.to_input() for row in rows]
    for name, numeric, comparison in [('nli_numeric', True, False), ('nli_comparison', False, True),
                                      ('structure-aware', True, True)]:
        settings = replace(config.structure, numeric_checks=numeric, comparison_checks=comparison)
        output[name] = [replace(p, method=name) for p in fuse_predictions(inputs, output['nli'], settings)]
    return output


def structural_diagnostics(rows, predictions, baseline):
    gold = [row.gold_verdict for row in rows]
    counts = Counter(f'{check.name}:{check.status}' for p in predictions for check in p.checks)
    changed = [i for i, (p, b) in enumerate(zip(predictions, baseline)) if p.verdict != b.verdict]
    return {'check_counts': dict(counts),
            'any_conclusive_check_rate': sum(any(c.status in {'consistent', 'contradiction'} for c in p.checks)
                                             for p in predictions) / len(rows),
            'overrides': len(changed),
            'corrected_nli_errors': sum(predictions[i].verdict == gold[i] for i in changed),
            'introduced_errors': sum(predictions[i].verdict != gold[i] for i in changed)}


def report_markdown(summary):
    total = sum(split['examples'] for split in summary['splits'].values())
    fmt = lambda value: 'n/a' if value is None else f'{value:.3f}'
    lines = ['# Controlled synthetic evaluation', '',
             '**Exploratory results, not a real-paper benchmark.** Labels come from author-defined templates and have not been independently reviewed. No model weights were trained.', '',
             f'The dataset has {total} examples. Training examples are reserved and unused. Thresholds were selected on development data and written before test inference. All variants share the same NLI scores and threshold; parser rules and tolerances were not tuned on this evaluation.', '',
             f'Test examples: {summary["splits"]["test"]["examples"]}. Independent test template families: {len(summary["splits"]["test"]["groups"])}.', '',
             '| Method | Macro-F1 | 95% group bootstrap interval | Support precision | Support recall | Supported false rejection |',
             '| --- | ---: | --- | ---: | ---: | ---: |']
    for name, metrics in summary['test_metrics'].items():
        low, high = summary['bootstrap']['macro_f1_intervals'][name]
        lines.append(f'| {name} | {metrics["macro_f1"]:.3f} | [{low:.3f}, {high:.3f}] | {metrics["support_precision"]:.3f} | {metrics["support_recall"]:.3f} | {metrics["supported_false_rejection_rate"]:.3f} |')
    lines += ['', 'Intervals resample whole template families and pair the same draws across methods. With few independent test families, they are descriptive and cannot establish statistical significance or generalization to scientific papers.', '',
              '## Thresholds', '']
    for method, calibration in summary['thresholds'].items():
        lines.append(f'- {method}: {calibration["threshold"]:.8f}; development macro-F1 {calibration["macro_f1"]:.3f}.')
    lines += ['', '## Error-type detection recall', '',
              '| Method | Numerical contradiction | Comparison contradiction | Unsupported |', '| --- | ---: | ---: | ---: |']
    for method, metrics in summary['test_metrics'].items():
        recalls = metrics['error_type_detection_recall']
        lines.append(f'| {method} | {fmt(recalls["numeric_contradiction"])} | {fmt(recalls["comparison_contradiction"])} | {fmt(recalls["unsupported"])} |')
    lines += ['', '## Structural effects relative to NLI', '',
              '| Variant | Conclusive check coverage | Overrides | Corrected errors | Introduced errors |',
              '| --- | ---: | ---: | ---: | ---: |']
    for name, diagnostic in summary['structural_diagnostics'].items():
        lines.append(f'| {name} | {diagnostic["any_conclusive_check_rate"]:.3f} | {diagnostic["overrides"]} | {diagnostic["corrected_nli_errors"]} | {diagnostic["introduced_errors"]} |')
    delta = summary['test_metrics']['structure-aware']['macro_f1'] - summary['test_metrics']['nli']['macro_f1']
    low, high = summary['bootstrap']['paired_macro_f1_delta_vs_nli']['structure-aware']
    lines += ['', f'Full-hybrid minus NLI macro-F1: {delta:+.3f}; paired group bootstrap interval [{low:+.3f}, {high:+.3f}]. This is an observed result on this synthetic split, not proof of a research hypothesis.', '',
              '## Audit and limitations', '',
              '- `protocol.json` records hashes, source snapshots by hash, configuration, environment, and frozen split assignments.',
              '- `calibration.json` records development IDs and every threshold candidate before test inference.',
              '- `predictions.jsonl` contains every development/test score, verdict, and structural explanation; `failures.jsonl` contains all test mistakes across methods.',
              '- `summary.json` includes confusion matrices (rows=gold, columns=prediction; order not_supported, supported), per-family metrics, diagnostic coverage, and paired intervals.',
              '- Templates are controlled, classes are balanced by construction, and unsupported wording can be a cue. These are not independently sampled scientific claims.',
              '- Families are separated within this dataset, but some grammar forms were used in earlier smoke tests and parser development. This is not a parser-unseen challenge set.',
              '- The test set has now been inspected. Future method changes need a new untouched evaluation set or explicitly labeled exploratory reuse.',
              '- Obtain independently reviewed, paper-derived examples and more independent documents before making a publishable generalization claim.', '']
    return '\n'.join(lines)


def run_benchmark(config_path: Path, output_dir: Path) -> dict:
    config = ExperimentConfig.load(config_path)
    if any(value is None for value in (config.embedding, config.nli, config.structure, config.evaluation)):
        raise ValueError('Evaluation requires [embedding], [nli], [structure], and [evaluation] tables')
    if not config.structure.numeric_checks or not config.structure.comparison_checks:
        raise ValueError('Evaluation config must enable both checks; runner generates all ablations explicitly')
    rows = load_dataset(config.dataset)
    splits = load_splits(rows, config.dataset, config.evaluation.manifest)
    if len({row.split_group for row in splits['test']}) < 2:
        raise ValueError('Test evaluation requires at least two independent groups')
    output_dir.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[3]
    paths = [config_path.resolve(), config.dataset, config.evaluation.manifest, root / 'uv.lock',
             *sorted((root / 'src/claimaudit').rglob('*.py'))]
    hashes = {str(path): file_hash(path) for path in paths}
    protocol = {'created_at': datetime.now(timezone.utc).isoformat(), 'purpose': 'controlled_synthetic_evaluation',
                'annotation_status': 'author_rules_not_independently_reviewed',
                'config': asdict(config), 'hashes': hashes, 'splits': split_summary(splits),
                'manifest': json.loads(config.evaluation.manifest.read_text()),
                'python': platform.python_version(), 'platform': platform.platform(),
                'packages': {name: version(name) for name in ('claimaudit', 'torch', 'transformers', 'sentence-transformers', 'scikit-learn', 'numpy', 'huggingface-hub')},
                'calibration_objective': 'binary_macro_f1',
                'bootstrap_unit': 'split_group', 'train_usage': 'reserved; no training or tuning',
                'test_policy': 'score only after calibration artifact has been written',
                'structural_policy': 'frozen grammar and tolerances; shared NLI calibration for all ablations'}
    write_json(output_dir / 'protocol.json', protocol)
    start = time.perf_counter()
    print('Loading pinned models.', flush=True)
    models, model_metadata = build_models(config)
    print('Scoring development pairs and selecting thresholds.', flush=True)
    dev_raw = score_rows(splits['dev'], models)
    gold = [row.gold_verdict == Verdict.SUPPORTED for row in splits['dev']]
    thresholds = {}
    for name, lower, default in [('embedding', -1, config.embedding.threshold), ('nli', 0, config.nli.threshold)]:
        thresholds[name] = select_threshold([p.score for p in dev_raw[name]], gold, lower=lower, upper=1,
                                            default=default, split_name='dev')
    calibration = {'development_ids': [row.id for row in splits['dev']], 'thresholds': thresholds,
                   'dataset_sha256': file_hash(config.dataset), 'manifest_sha256': file_hash(config.evaluation.manifest)}
    write_json(output_dir / 'calibration.json', calibration)
    print('Calibration saved. Scoring frozen test pairs.', flush=True)
    test_raw = score_rows(splits['test'], models)
    dev = variants(splits['dev'], dev_raw, thresholds, config)
    test = variants(splits['test'], test_raw, thresholds, config)
    boolean = {method: [p.verdict == Verdict.SUPPORTED for p in predictions] for method, predictions in test.items()}
    summary = {'purpose': protocol['purpose'], 'splits': protocol['splits'], 'thresholds': thresholds,
               'test_metrics': {method: binary_metrics(splits['test'], predictions) for method, predictions in boolean.items()},
               'dev_metrics': {method: binary_metrics(splits['dev'], [p.verdict == Verdict.SUPPORTED for p in predictions]) for method, predictions in dev.items()},
               'structural_diagnostics': {method: structural_diagnostics(splits['test'], test[method], test['nli'])
                                          for method in METHODS[2:]},
               'bootstrap': paired_group_bootstrap(splits['test'], boolean, config.evaluation.bootstrap_samples, config.seed),
               'model_metadata': model_metadata, 'elapsed_seconds_including_model_load': time.perf_counter() - start}
    summary['per_test_group'] = {}
    for group in sorted({row.split_group for row in splits['test']}):
        indices = [i for i, row in enumerate(splits['test']) if row.split_group == group]
        summary['per_test_group'][group] = {method: binary_metrics([splits['test'][i] for i in indices],
                                                                  [predictions[i] for i in indices]) for method, predictions in boolean.items()}
    if any(file_hash(Path(path)) != digest for path, digest in hashes.items()):
        raise ValueError('Source, configuration, dataset, or split manifest changed during evaluation')
    with (output_dir / 'predictions.jsonl').open('x', encoding='utf-8') as handle:
        for split_name, predictions in [('dev', dev), ('test', test)]:
            for index, row in enumerate(splits[split_name]):
                record = {**asdict(row), 'split': split_name, 'methods': {method: asdict(values[index]) for method, values in predictions.items()}}
                handle.write(json.dumps(record, default=str, allow_nan=False) + '\n')
    with (output_dir / 'failures.jsonl').open('x', encoding='utf-8') as handle:
        for index, row in enumerate(splits['test']):
            for method, values in test.items():
                if values[index].verdict != row.gold_verdict:
                    handle.write(json.dumps({**asdict(row), 'method': method, 'prediction': asdict(values[index])}, default=str, allow_nan=False) + '\n')
    write_json(output_dir / 'summary.json', summary)
    with (output_dir / 'report.md').open('x', encoding='utf-8') as handle:
        handle.write(report_markdown(summary))
    write_json(output_dir / 'complete.json', {'status': 'complete', 'artifacts': {
        path.name: file_hash(path) for path in sorted(output_dir.iterdir()) if path.is_file()}})
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    try:
        summary = run_benchmark(args.config, args.output_dir)
    except (OSError, ValueError, TypeError, RuntimeError, ImportError) as exc:
        parser.error(str(exc))
    print(json.dumps({'status': 'complete', 'test_examples': summary['splits']['test']['examples'],
                      'report': str(args.output_dir / 'report.md')}, indent=2))


if __name__ == '__main__':
    main()
