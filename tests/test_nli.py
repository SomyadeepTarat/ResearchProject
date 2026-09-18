from contextlib import nullcontext
from dataclasses import replace
import math
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from claimaudit.baselines.nli import NLIVerifier, TransformersNLIBackend, probabilities, resolve_labels
from claimaudit.config import NLIConfig, ExperimentConfig
from claimaudit.schemas import ClaimInput, Prediction, Verdict

ROOT = Path(__file__).resolve().parents[1]
CONFIG = NLIConfig('test/nli', 'a' * 40, 0.5)


class NLITests(unittest.TestCase):
    def test_mapping_uses_names_not_assumed_order(self):
        labels = resolve_labels({'2': 'NEUTRAL', '0': 'entailment', '1': 'contradiction'})
        scores = probabilities([1000, 999, 998], labels)
        self.assertAlmostEqual(sum(scores.values()), 1)
        self.assertGreater(scores['entailment'], scores['contradiction'])
        self.assertGreater(scores['contradiction'], scores['neutral'])

    def test_rejects_ambiguous_or_incomplete_mapping(self):
        for mapping in [{0: 'LABEL_0', 1: 'LABEL_1', 2: 'LABEL_2'},
                        {0: 'entailment', 1: 'entailment', 2: 'neutral'},
                        {1: 'entailment', 2: 'neutral', 3: 'contradiction'}, {0: None}]:
            with self.subTest(mapping=mapping), self.assertRaises(ValueError):
                resolve_labels(mapping)

    def test_bad_logits(self):
        for logits in [[1, 2], [1, math.inf, 0], [math.nan, 0, 1]]:
            with self.assertRaises(ValueError):
                probabilities(logits, ('entailment', 'neutral', 'contradiction'))

    def test_threshold_and_class_scores(self):
        backend = Mock()
        scores = [{'entailment': .5, 'neutral': .3, 'contradiction': .2},
                  {'entailment': .1, 'neutral': .2, 'contradiction': .7},
                  {'entailment': .1, 'neutral': .8, 'contradiction': .1}]
        backend.predict.return_value = scores
        inputs = [ClaimInput('source', str(i)) for i in range(3)]
        output = NLIVerifier(CONFIG, backend).verify_many(inputs)
        backend.predict.assert_called_once_with(inputs)
        self.assertEqual([p.verdict for p in output], [Verdict.SUPPORTED, Verdict.NOT_SUPPORTED, Verdict.NOT_SUPPORTED])
        self.assertEqual([p.class_scores for p in output], scores)
        self.assertEqual(output[0].score, .5)
        self.assertEqual(output[0].score_type, 'entailment_probability')

    def test_empty_single_and_wrong_count(self):
        backend = Mock()
        verifier = NLIVerifier(CONFIG, backend)
        self.assertEqual(verifier.verify_many([]), [])
        backend.predict.assert_not_called()
        backend.predict.return_value = [{'entailment': 1., 'neutral': 0., 'contradiction': 0.}]
        self.assertEqual(verifier.verify(ClaimInput('s', 'c')).verdict, Verdict.SUPPORTED)
        backend.predict.return_value = []
        with self.assertRaises(ValueError):
            verifier.verify(ClaimInput('s', 'c'))

    def test_invalid_scores_rejected(self):
        for scores in [{'entailment': 1}, {'entailment': .9, 'neutral': .9, 'contradiction': .9},
                       {'entailment': math.nan, 'neutral': 0, 'contradiction': 0},
                       {'entailment': -1, 'neutral': 1, 'contradiction': 1},
                       {'entailment': True, 'neutral': 0, 'contradiction': 0}]:
            backend = Mock()
            backend.predict.return_value = [scores]
            with self.assertRaises(ValueError):
                NLIVerifier(CONFIG, backend).verify(ClaimInput('s', 'c'))

    def test_config(self):
        for fields in [{'threshold': -.1}, {'threshold': math.nan}, {'threshold': 1.1},
                       {'revision': 'main'}, {'max_length': True}, {'max_length': 0},
                       {'batch_size': 0}, {'device': 'guess'}, {'local_files_only': 1}]:
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                replace(CONFIG, **fields)
        config = ExperimentConfig.load(ROOT / 'experiments/nli_smoke.toml')
        self.assertIsNone(config.embedding)
        self.assertEqual(config.nli.cache_dir, ROOT / '.cache/huggingface')

    def test_model_loader_revision_eval_and_roberta_capacity(self):
        library = Mock()
        model = library.AutoModelForSequenceClassification.from_pretrained.return_value
        model.config = SimpleNamespace(id2label={0: 'contradiction', 1: 'entailment', 2: 'neutral'},
                                       num_labels=3, max_position_embeddings=514,
                                       model_type='roberta', pad_token_id=1)
        library.AutoTokenizer.from_pretrained.return_value.model_max_length = 1000000
        with patch.dict('sys.modules', {'transformers': library, 'torch': Mock()}):
            backend = TransformersNLIBackend(replace(CONFIG, max_length=1024))
        self.assertEqual(backend.max_length, 512)
        self.assertEqual(backend.labels, ('contradiction', 'entailment', 'neutral'))
        model.to.assert_called_once_with('cpu')
        model.eval.assert_called_once()
        for loader in [library.AutoTokenizer, library.AutoModelForSequenceClassification]:
            loader.from_pretrained.assert_called_once_with(
                'test/nli', revision='a' * 40, cache_dir=str(CONFIG.cache_dir),
                local_files_only=False, trust_remote_code=False,
            )

    def make_backend(self):
        backend = TransformersNLIBackend.__new__(TransformersNLIBackend)
        backend.config = replace(CONFIG, batch_size=1)
        backend.max_length = 4
        backend.labels = ('contradiction', 'entailment', 'neutral')
        backend.torch = Mock()
        backend.torch.inference_mode.side_effect = nullcontext
        backend.tokenizer = Mock()
        backend.model = Mock()
        features = Mock()
        features.to.return_value = {'input_ids': 'tensor placeholder'}
        backend.tokenizer.pad.return_value = features
        backend.model.return_value.logits.detach.return_value.cpu.return_value.tolist.return_value = [[-1, 2, 0]]
        return backend

    def test_pair_order_batching_and_boundary(self):
        backend = self.make_backend()
        backend.tokenizer.return_value = {'input_ids': [[0, 1, 2, 3]]}
        result = backend.predict([ClaimInput('evidence one', 'claim one'), ClaimInput('evidence two', 'claim two')])
        self.assertEqual(len(result), 2)
        self.assertEqual(backend.model.call_count, 2)
        self.assertEqual(backend.torch.inference_mode.call_count, 2)
        self.assertEqual(backend.tokenizer.call_args_list[0].args, (['evidence one'], ['claim one']))
        self.assertEqual(backend.tokenizer.call_args_list[1].args, (['evidence two'], ['claim two']))
        self.assertFalse(backend.tokenizer.call_args.kwargs['truncation'])
        self.assertGreater(result[0]['entailment'], .8)

    def test_overlength_pair_rejected_before_model(self):
        backend = self.make_backend()
        backend.tokenizer.return_value = {'input_ids': [[0, 1, 2, 3, 4]]}
        with self.assertRaisesRegex(ValueError, 'no text was truncated'):
            backend.predict([ClaimInput('evidence', 'claim')])
        backend.model.assert_not_called()


if __name__ == '__main__':
    unittest.main()
