from collections import Counter
from dataclasses import asdict, replace
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from claimaudit.config import ExperimentConfig
from claimaudit.evaluation.benchmark import run_benchmark
from claimaudit.evaluation.dataset import load_dataset
from claimaudit.evaluation.metrics import binary_counts, binary_metrics, macro_from_counts, paired_group_bootstrap, select_threshold
from claimaudit.evaluation.splits import create_manifest, file_hash, load_splits
from claimaudit.evaluation.synthetic import generate_examples
from claimaudit.schemas import Example, Label, Prediction, Verdict

ROOT = Path(__file__).resolve().parents[1]
HAS_SKLEARN = importlib.util.find_spec('sklearn') is not None
HAS_MODELS = importlib.util.find_spec('sentence_transformers') is not None


def save_rows(path, rows):
    path.write_text(''.join(json.dumps(asdict(row), ensure_ascii=False) + '\n' for row in rows))


def example(index, label, group):
    return Example(str(index), str(index), 'source', 'claim', label, 'test', 'test', group)


class DatasetSplitTests(unittest.TestCase):
    def test_dataset_size_balance_and_reproducibility(self):
        rows = generate_examples()
        self.assertEqual(len(rows), 300)
        self.assertEqual(Counter(row.label for row in rows), {label: 75 for label in Label})
        self.assertEqual(len({row.source_id for row in rows}), 75)
        self.assertEqual(len({row.split_group for row in rows}), 15)
        self.assertEqual(len({(row.evidence, row.claim) for row in rows}), 300)
        self.assertEqual(rows, load_dataset(ROOT / 'data/controlled_v1/examples.jsonl'))
        self.assertEqual(rows, generate_examples())

    def test_whole_family_split(self):
        path = ROOT / 'data/controlled_v1/examples.jsonl'
        rows = load_dataset(path)
        splits = load_splits(rows, path, ROOT / 'data/controlled_v1/splits.json')
        self.assertEqual([len(splits[name]) for name in ('train', 'dev', 'test')], [180, 60, 60])
        group_sets = [{row.split_group for row in split} for split in splits.values()]
        self.assertEqual(sum(map(len, group_sets)), len(set.union(*group_sets)))
        for split in splits.values():
            self.assertEqual(len(set(Counter(row.label for row in split).values())), 1)

    def test_manifest_rejects_tampering_and_leakage(self):
        rows = generate_examples()
        with tempfile.TemporaryDirectory() as directory:
            data, manifest_path = Path(directory)/'data.jsonl', Path(directory)/'split.json'
            save_rows(data, rows)
            original = create_manifest(rows, data)
            variants = []
            wrong_hash = json.loads(json.dumps(original)); wrong_hash['dataset_sha256'] = 'wrong'; variants.append(wrong_hash)
            missing = json.loads(json.dumps(original)); missing['splits']['test'].pop(); variants.append(missing)
            duplicate = json.loads(json.dumps(original)); duplicate['splits']['test'].append(duplicate['splits']['test'][0]); variants.append(duplicate)
            overlap = json.loads(json.dumps(original))
            overlap['splits']['test'][0], overlap['splits']['dev'][0] = overlap['splits']['dev'][0], overlap['splits']['test'][0]
            lookup = {row.id: row for row in rows}
            overlap['groups'] = {name: sorted({lookup[i].split_group for i in ids}) for name, ids in overlap['splits'].items()}
            variants.append(overlap)
            for manifest in variants:
                manifest_path.write_text(json.dumps(manifest))
                with self.assertRaises(ValueError):
                    load_splits(rows, data, manifest_path)

    def test_same_evidence_cannot_cross_splits_under_new_source_ids(self):
        rows = generate_examples()
        with tempfile.TemporaryDirectory() as directory:
            data, manifest_path = Path(directory)/'data.jsonl', Path(directory)/'split.json'
            save_rows(data, rows)
            manifest = create_manifest(rows, data)
            lookup = {row.id: row for row in rows}
            a = lookup[manifest['splits']['dev'][0]]
            b = lookup[manifest['splits']['test'][0]]
            changed = [replace(row, evidence=a.evidence) if row.source_id==b.source_id else row for row in rows]
            save_rows(data, changed)
            manifest['dataset_sha256'] = file_hash(data)
            manifest_path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, 'leakage'):
                load_splits(changed, data, manifest_path)

    def test_source_group_consistency(self):
        rows = generate_examples()[:2]
        rows[1] = replace(rows[1], group_id='wrong')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'data.jsonl'
            save_rows(path, rows)
            with self.assertRaisesRegex(ValueError, 'inconsistent group'):
                load_dataset(path)

    def test_group_falls_back_to_source(self):
        row = example(1, Label.SUPPORTED, None)
        self.assertEqual(row.split_group, row.source_id)
        with self.assertRaises(ValueError):
            replace(row, group_id=' ')


class CalibrationTests(unittest.TestCase):
    def test_threshold_uses_greater_equal_and_development_only(self):
        result = select_threshold([.8,.7,.3,.2], [True,True,False,False], lower=0, upper=1, default=.75, split_name='dev')
        self.assertEqual(result['threshold'], .7)
        self.assertEqual(result['macro_f1'], 1)
        with self.assertRaisesRegex(ValueError, 'development'):
            select_threshold([.8,.2], [True,False], lower=0, upper=1, default=.5, split_name='test')

    def test_ties_are_deterministic_and_inputs_validated(self):
        kwargs = dict(lower=-1, upper=1, default=.75, split_name='dev')
        result = select_threshold([.9,.1], [True,False], **kwargs)
        self.assertEqual(result['threshold'], .75)
        self.assertEqual(result, select_threshold([.9,.1], [True,False], **kwargs))
        for scores, gold in [([float('nan'),.1],[True,False]), ([.9],[True]), ([.8,.2],[True]), ([2,.1],[True,False])]:
            with self.assertRaises(ValueError):
                select_threshold(scores, gold, **kwargs)

    def test_binary_count_validation(self):
        self.assertEqual(binary_counts([False,False,True,True], [False,True,False,True]), [1,1,1,1])
        self.assertEqual(macro_from_counts([1,1,1,1]), .5)
        for gold, pred in [([],[]), ([True],[True,False]), ([1],[True])]:
            with self.assertRaises(ValueError):
                binary_counts(gold, pred)


@unittest.skipUnless(HAS_SKLEARN, 'Install --extra evaluation to test scikit-learn metrics')
class MetricTests(unittest.TestCase):
    def setUp(self):
        self.rows = [example(0, Label.NUMERIC_CONTRADICTION, 'g1'), example(1, Label.UNSUPPORTED, 'g2'),
                     example(2, Label.SUPPORTED, 'g1'), example(3, Label.SUPPORTED, 'g2')]

    def test_metrics_against_hand_computed_confusion(self):
        metrics = binary_metrics(self.rows, [False,True,False,True])
        self.assertEqual(metrics['confusion_matrix'], [[1,1],[1,1]])
        for key in ('accuracy','macro_f1','support_precision','support_recall','support_f1','supported_false_rejection_rate'):
            self.assertEqual(metrics[key], .5)
        self.assertEqual(metrics['error_type_detection_recall']['numeric_contradiction'], 1)
        self.assertEqual(metrics['error_type_detection_recall']['unsupported'], 0)
        self.assertIsNone(metrics['error_type_detection_recall']['comparison_contradiction'])
        self.assertEqual(binary_metrics(self.rows, [False]*4)['support_precision'], 0)

    def test_bootstrap_is_paired_and_reproducible(self):
        methods = {'nli': [False,True,False,True], 'structure-aware': [False,True,False,True]}
        report = paired_group_bootstrap(self.rows, methods, 100, 42)
        self.assertEqual(report['independent_groups'], 2)
        self.assertEqual(report['paired_macro_f1_delta_vs_nli']['structure-aware'], [0,0])
        self.assertEqual(report, paired_group_bootstrap(self.rows, methods, 100, 42))
        self.assertEqual(report, paired_group_bootstrap(list(reversed(self.rows)),
                         {name:list(reversed(values)) for name,values in methods.items()},100,42))
        with self.assertRaises(ValueError):
            paired_group_bootstrap([replace(row,group_id='one') for row in self.rows],methods,100,42)


@unittest.skipUnless(HAS_SKLEARN and HAS_MODELS, 'Install models and evaluation extras for workflow integration')
class WorkflowTests(unittest.TestCase):
    def test_calibration_saved_before_test_and_test_labels_cannot_tune_thresholds(self):
        base_config = ExperimentConfig.load(ROOT / 'experiments/controlled.toml')
        rows = generate_examples()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dataset, manifest_path = root/'data.jsonl', root/'splits.json'
            save_rows(dataset, rows)
            manifest = create_manifest(rows, dataset)
            manifest_path.write_text(json.dumps(manifest))
            config = replace(base_config, dataset=dataset, evaluation=replace(base_config.evaluation, manifest=manifest_path, bootstrap_samples=10))
            calibrations = []
            for run in range(2):
                if run:
                    test_ids=set(manifest['splits']['test'])
                    swap={Label.SUPPORTED:Label.NUMERIC_CONTRADICTION, Label.NUMERIC_CONTRADICTION:Label.SUPPORTED}
                    changed=[replace(row,label=swap.get(row.label,row.label)) if row.id in test_ids else row for row in rows]
                    save_rows(dataset,changed)
                    manifest['dataset_sha256']=file_hash(dataset)
                    manifest_path.write_text(json.dumps(manifest))
                output = root/f'run{run}'
                models = {}
                for name in ('embedding','nli'):
                    model = Mock()
                    calls=[]
                    def predict(inputs, name=name, calls=calls):
                        if calls:
                            self.assertTrue((output/'calibration.json').exists())
                        calls.append(inputs)
                        self.assertTrue(all(set(vars(item))=={'evidence','claim'} for item in inputs))
                        return [Prediction(name,Verdict.SUPPORTED,'stub',.9,'test_score',
                                {'entailment':.9,'neutral':.05,'contradiction':.05} if name=='nli' else None) for _ in inputs]
                    model.verify_many.side_effect=predict
                    models[name]=model
                with patch('claimaudit.evaluation.benchmark.ExperimentConfig.load', return_value=config), patch(
                    'claimaudit.evaluation.benchmark.build_models', return_value=(models, {'test_double':True})
                ):
                    run_benchmark(ROOT/'experiments/controlled.toml',output)
                calibrations.append(json.loads((output/'calibration.json').read_text())['thresholds'])
                self.assertTrue((output/'complete.json').exists())
                self.assertEqual(len((output/'predictions.jsonl').read_text().splitlines()),120)
                with patch('claimaudit.evaluation.benchmark.ExperimentConfig.load', return_value=config), self.assertRaises(FileExistsError):
                    run_benchmark(ROOT/'experiments/controlled.toml',output)
            self.assertEqual(calibrations[0],calibrations[1])


if __name__ == '__main__':
    unittest.main()
