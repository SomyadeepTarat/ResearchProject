from dataclasses import replace
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from claimaudit.baselines.embedding import EmbeddingVerifier, SentenceTransformerEncoder, cosine_similarity
from claimaudit.config import EmbeddingConfig, ExperimentConfig
from claimaudit.schemas import ClaimInput, Prediction, Verdict

ROOT = Path(__file__).resolve().parents[1]
CONFIG = EmbeddingConfig('test/model', 'a' * 40, 0.75)


class EmbeddingTests(unittest.TestCase):
    def test_cosine_geometry(self):
        for left, right, expected in [([2, 0], [7, 0], 1), ([1, 0], [0, 1], 0),
                                       ([1, 0], [-1, 0], -1), ([3, 4], [1, 0], .6)]:
            self.assertAlmostEqual(cosine_similarity(left, right), expected)

    def test_invalid_vectors(self):
        for left, right in [([], []), ([0, 0], [1, 2]), ([1], [1, 2]),
                            ([math.nan], [1]), ([math.inf], [1])]:
            with self.subTest(left=left), self.assertRaises(ValueError):
                cosine_similarity(left, right)

    def test_batch_order_deduplication_and_threshold_boundary(self):
        encoder = Mock()
        encoder.encode.return_value = [[1, 0], [1, 0], [0, 1], [-1, 0]]
        verifier = EmbeddingVerifier(replace(CONFIG, threshold=0), encoder)
        rows = verifier.verify_many([ClaimInput('evidence', 'same'), ClaimInput('evidence', 'orthogonal'),
                                     ClaimInput('evidence', 'opposite')])
        encoder.encode.assert_called_once_with(['evidence', 'same', 'orthogonal', 'opposite'])
        self.assertEqual([p.score for p in rows], [1, 0, -1])
        self.assertEqual([p.verdict for p in rows], [Verdict.SUPPORTED, Verdict.SUPPORTED, Verdict.NOT_SUPPORTED])
        self.assertTrue(all(p.score_type == 'cosine_similarity' for p in rows))

    def test_single_and_empty(self):
        encoder = Mock()
        verifier = EmbeddingVerifier(CONFIG, encoder)
        self.assertEqual(verifier.verify_many([]), [])
        encoder.encode.assert_not_called()
        encoder.encode.return_value = [[1, 0]]
        self.assertEqual(verifier.verify(ClaimInput('same', 'same')).score, 1)

    def test_bad_encoder_count(self):
        encoder = Mock()
        encoder.encode.return_value = []
        with self.assertRaises(ValueError):
            EmbeddingVerifier(CONFIG, encoder).verify(ClaimInput('source', 'claim'))

    def test_config_validation(self):
        for kwargs in [{'threshold': math.nan}, {'threshold': True}, {'threshold': 1.1},
                       {'revision': 'main'}, {'batch_size': 0}, {'batch_size': True},
                       {'local_files_only': 'false'}, {'device': 'guess'}]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                replace(CONFIG, **kwargs)
        config = ExperimentConfig.load(ROOT / 'experiments/embedding_smoke.toml')
        self.assertEqual(config.embedding.cache_dir, ROOT / '.cache/huggingface')

    def test_token_limit_rejects_before_encode(self):
        adapter = SentenceTransformerEncoder.__new__(SentenceTransformerEncoder)
        adapter.config = CONFIG
        adapter.model = Mock(max_seq_length=3)
        adapter.model.tokenizer.return_value = {'input_ids': [[1, 2, 3, 4]]}
        with self.assertRaisesRegex(ValueError, 'no text was truncated'):
            adapter.encode(['too long'])
        adapter.model.encode.assert_not_called()
        adapter.model.tokenizer.return_value = {'input_ids': [[1, 2, 3]]}
        adapter.encode(['fits exactly'])
        adapter.model.encode.assert_called_once()

    def test_loader_uses_pinned_revision_and_cache(self):
        fake_library = Mock()
        with patch.dict(sys.modules, {'sentence_transformers': fake_library}):
            adapter = SentenceTransformerEncoder(CONFIG)
        fake_library.SentenceTransformer.assert_called_once_with(
            CONFIG.model_id, revision=CONFIG.revision, device='cpu',
            cache_folder=str(CONFIG.cache_dir), local_files_only=False, trust_remote_code=False,
        )
        adapter.model.eval.assert_called_once()

    def test_score_contract(self):
        for kwargs in [{'score': .5}, {'score_type': 'cosine_similarity'},
                       {'score': math.nan, 'score_type': 'cosine_similarity'}]:
            with self.assertRaises(ValueError):
                Prediction('embedding', Verdict.SUPPORTED, 'reason', **kwargs)

    def test_output_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'result.json'
            output.write_text('keep')
            result = subprocess.run([sys.executable, '-m', 'claimaudit.cli', '--method', 'embedding',
                                     '--config', str(ROOT / 'experiments/embedding_smoke.toml'),
                                     '--output', str(output)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn('already exists', result.stderr)
            self.assertEqual(output.read_text(), 'keep')


if __name__ == '__main__':
    unittest.main()
