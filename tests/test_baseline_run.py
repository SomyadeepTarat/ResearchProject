from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from claimaudit.evaluation.baseline_run import run_baseline
from claimaudit.schemas import Prediction, Verdict

ROOT = Path(__file__).resolve().parents[1]


class BaselineRunTests(unittest.TestCase):
    def test_all_methods_preserve_row_order_and_hide_gold(self):
        for method, config_name, constructor in [
            ('embedding', 'embedding_smoke.toml', 'EmbeddingVerifier'),
            ('nli', 'nli_smoke.toml', 'NLIVerifier'),
            ('structure-aware', 'structure_smoke.toml', 'StructureAwareVerifier'),
        ]:
            with self.subTest(method=method):
                verifier = Mock()
                verifier.verify_many.return_value = [Prediction(method, Verdict.NOT_SUPPORTED, 'stub') for _ in range(12)]
                verifier.encoder.model.max_seq_length = 256
                verifier.backend.max_length = 512
                verifier.backend.labels = ('contradiction', 'entailment', 'neutral')
                verifier.nli.backend = verifier.backend
                torch = Mock()
                torch.get_num_threads.return_value = 1
                transformers = Mock()
                with patch.dict('sys.modules', {'torch': torch, 'transformers': transformers}), patch(
                    f'claimaudit.evaluation.baseline_run.{constructor}', return_value=verifier
                ):
                    report = run_baseline(ROOT / 'experiments' / config_name, method)
                inputs = verifier.verify_many.call_args.args[0]
                self.assertTrue(all(set(vars(item)) == {'evidence', 'claim'} for item in inputs))
                self.assertEqual(len(report['predictions']), 12)
                self.assertEqual(report['predictions'][0]['id'], 'accuracy-1')
                self.assertEqual(report['predictions'][0]['gold_label'], 'supported')
                self.assertEqual(report['method'], method)
                self.assertEqual(len(report['dataset']['sha256']), 64)
                self.assertNotIn('metrics', report)
                transformers.set_seed.assert_called_once_with(42)
                if method != 'embedding':
                    self.assertEqual(report['runtime']['pair_order'], ['evidence', 'claim'])

    def test_missing_configuration_and_unknown_method(self):
        for method in ('nli', 'embedding', 'structure-aware', 'unknown'):
            with self.subTest(method=method), self.assertRaises(ValueError):
                run_baseline(ROOT / 'experiments/smoke.toml', method)


if __name__ == '__main__':
    unittest.main()
