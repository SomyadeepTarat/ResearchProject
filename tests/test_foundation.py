import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from claimaudit.config import ExperimentConfig
from claimaudit.evaluation.dataset import load_dataset
from claimaudit.schemas import ClaimInput, Label, Prediction, Verdict

ROOT = Path(__file__).resolve().parents[1]


class FoundationTests(unittest.TestCase):
    def test_smoke_balance_and_no_gold_leak(self):
        rows = load_dataset(ROOT / 'data/smoke.jsonl')
        self.assertEqual(len(rows), 12)
        for label in Label:
            self.assertEqual(sum(row.label == label for row in rows), 3)
        for row in rows:
            self.assertEqual(set(vars(row.to_input())), {'evidence', 'claim'})
            self.assertEqual(row.gold_verdict == Verdict.SUPPORTED, row.label == Label.SUPPORTED)

    def test_invalid_datasets(self):
        valid = json.loads((ROOT / 'data/smoke.jsonl').read_text().splitlines()[0])
        cases = ['', '\n', '[]\n', '{oops}\n', json.dumps({**valid, 'label': 'unknown'}),
                 json.dumps({**valid, 'claim': ' '}), json.dumps({**valid, 'extra': 1}),
                 json.dumps(valid) + '\n' + json.dumps(valid),
                 json.dumps(valid) + '\n' + json.dumps({**valid, 'id': 'new', 'evidence': 'different'})]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'bad.jsonl'
            for content in cases:
                with self.subTest(content=content):
                    path.write_text(content)
                    with self.assertRaisesRegex(ValueError, 'bad.jsonl'):
                        load_dataset(path)

    def test_config_relative_to_file(self):
        config = ExperimentConfig.load(ROOT / 'experiments/smoke.toml')
        self.assertEqual(config.dataset, ROOT / 'data/smoke.jsonl')
        self.assertEqual(config.seed, 42)

    def test_invalid_config(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'config.toml'
            for content in ['dataset = "x"\nseed = true', 'dataset = "x"\nseed = -1',
                            'dataset = "x"\nunknown = 1', 'seed = 42']:
                path.write_text(content)
                with self.assertRaises(ValueError):
                    ExperimentConfig.load(path)

    def test_prediction_and_input_validation(self):
        with self.assertRaises(ValueError):
            ClaimInput('', 'claim')
        with self.assertRaises(ValueError):
            Prediction('baseline', 'unknown', 'reason')

    def test_cli_from_other_directory(self):
        result = subprocess.run([sys.executable, '-m', 'claimaudit.cli', '--config',
                                 str(ROOT / 'experiments/smoke.toml')], cwd='/private/tmp',
                                capture_output=True, text=True, check=True)
        report = json.loads(result.stdout)
        self.assertEqual(report['examples'], 12)
        self.assertFalse(report['models_run'])

    def test_cli_bad_config_fails(self):
        result = subprocess.run([sys.executable, '-m', 'claimaudit.cli', '--config',
                                 '/nonexistent/claimaudit.toml'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn('error:', result.stderr)


if __name__ == '__main__':
    unittest.main()
