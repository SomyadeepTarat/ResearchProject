from dataclasses import replace
import math
from pathlib import Path
import unittest
from unittest.mock import Mock

from claimaudit.config import ExperimentConfig, NLIConfig, StructureConfig
from claimaudit.schemas import ClaimInput, Prediction, StructuralCheck, Verdict
from claimaudit.verification.checks import check_structure
from claimaudit.verification.structure import StructureAwareVerifier

ROOT = Path(__file__).resolve().parents[1]
CONFIG = StructureConfig()
NLI_CONFIG = NLIConfig('test/nli', 'a' * 40, .5)


def check(evidence, claim, name, config=CONFIG):
    return next(item for item in check_structure(ClaimInput(evidence, claim), config) if item.name == name)


class StructureTests(unittest.TestCase):
    def test_numerical_alignment_not_number_presence(self):
        evidence = 'Model Alpha achieved 84.2% accuracy, exceeding Model Beta at 81.4%.'
        result = check(evidence, 'Model Alpha achieved 81.4% accuracy.', 'numeric')
        self.assertEqual(result.status, 'contradiction')
        self.assertEqual(result.evidence_spans, (evidence,))
        self.assertEqual(check(evidence, 'Model Beta achieved 81.4% accuracy.', 'numeric').status, 'consistent')
        self.assertEqual(check(evidence, 'Model Gamma achieved 81.4% accuracy.', 'numeric').status, 'abstain')
        self.assertEqual(check(evidence, 'Model Alpha achieved 81.4% recall.', 'numeric').status, 'abstain')

    def test_unit_equivalence(self):
        cases = [
            ('BERT achieved 84.2% accuracy.', 'BERT had accuracy of 0.842.'),
            ('BERT achieved 84.2 percent precision.', 'BERT achieved 84.20% precision.'),
            ('System X had latency of 12 ms.', 'System X had latency of 0.012 seconds.'),
            ('System X had runtime of 500 microseconds.', 'System X had runtime of 0.5 ms.'),
            ('System X had memory usage of 1 GB.', 'System X had memory of 1000 MB.'),
            ('System X had memory of 1 GiB.', 'System X had memory of 1024 MiB.'),
            ('The trial enrolled 1,200 participants.', 'The trial enrolled 1200 participants.'),
            ('System X had throughput of 120 samples/s.', 'System X had throughput of 120.0 samples/s.'),
        ]
        for evidence, claim in cases:
            with self.subTest(evidence=evidence):
                self.assertEqual(check(evidence, claim, 'numeric').status, 'consistent')
        self.assertEqual(check('System X had memory of 1 GB.', 'System X had memory of 1 GiB.', 'numeric').status, 'contradiction')

    def test_wrong_or_missing_unit_abstains(self):
        for claim in ['System X had latency of 12.', 'System X had latency of 12 MB.',
                      'System X had mean latency of 12 ms.']:
            self.assertEqual(check('System X had latency of 12 ms.', claim, 'numeric').status, 'abstain')

    def test_partition_count_and_direction(self):
        evidence = 'The trial enrolled 120 participants: 70 in group X and 50 in group Y.'
        self.assertEqual(check(evidence, 'Group Y included 70 participants.', 'numeric').status, 'contradiction')
        self.assertEqual(check(evidence, 'The trial enrolled 150 participants.', 'numeric').status, 'contradiction')
        self.assertEqual(check(evidence, 'Group X had more participants than group Y.', 'comparison').status, 'consistent')
        self.assertEqual(check(evidence, 'Group Y had more participants than group X.', 'comparison').status, 'contradiction')

    def test_counts_require_exact_equality_even_at_large_scale(self):
        self.assertEqual(check('The trial enrolled 1000000 participants.',
                               'The trial enrolled 1000001 participants.', 'numeric').status, 'contradiction')
        evidence = 'Group X included 1000000 participants. Group Y included 1000001 participants.'
        self.assertEqual(check(evidence, 'Group Y had more participants than group X.', 'comparison').status, 'consistent')

    def test_reversed_entity_order(self):
        evidence = 'Model Alpha had higher accuracy than Model Beta.'
        cases = [('Model Beta had lower accuracy than Model Alpha.', 'consistent'),
                 ('Model Beta had higher accuracy than Model Alpha.', 'contradiction'),
                 ('Model Alpha had lower accuracy than Model Beta.', 'contradiction'),
                 ('Model Alpha had higher recall than Model Beta.', 'abstain'),
                 ('Model Gamma had higher accuracy than Model Beta.', 'abstain')]
        for claim, expected in cases:
            self.assertEqual(check(evidence, claim, 'comparison').status, expected)

    def test_lower_is_better_and_numeric_direction(self):
        evidence = 'System Fast had a latency of 12 ms, lower than System Slow at 20 ms.'
        cases = [('System Fast had lower latency than System Slow.', 'consistent'),
                 ('System Fast had higher latency than System Slow.', 'contradiction'),
                 ('System Fast outperformed System Slow in latency.', 'consistent'),
                 ('System Slow outperformed System Fast in latency.', 'contradiction')]
        for claim, expected in cases:
            self.assertEqual(check(evidence, claim, 'comparison').status, expected)

    def test_comparison_from_two_quantities_and_units(self):
        evidence = 'System Alpha had latency of 0.01 s. System Beta had latency of 20 ms.'
        self.assertEqual(check(evidence, 'System Alpha had higher latency than System Beta.', 'comparison').status, 'contradiction')
        self.assertEqual(check(evidence, 'System Beta had higher latency than System Alpha.', 'comparison').status, 'consistent')

    def test_equal_and_near_equal_values(self):
        evidence = 'Model A achieved 80% accuracy. Model B achieved 80.00% accuracy.'
        self.assertEqual(check(evidence, 'Model A had higher accuracy than Model B.', 'comparison').status, 'contradiction')
        self.assertEqual(check(evidence, 'Model A had the same accuracy as Model B.', 'comparison').status, 'consistent')
        near = 'Model A achieved 80% accuracy. Model B achieved 80.000001% accuracy.'
        self.assertEqual(check(near, 'Model B had higher accuracy than Model A.', 'comparison').status, 'abstain')
        config = replace(CONFIG, relative_tolerance=0, absolute_tolerance=0)
        self.assertEqual(check(near, 'Model B had higher accuracy than Model A.', 'comparison', config).status, 'consistent')

    def test_negation_qualifiers_context_and_intervals_abstain(self):
        evidence = 'Model A achieved 80% accuracy.'
        claims = ['Model A did not achieve 90% accuracy.', 'Model A never achieved 90% accuracy.',
                  'Model A achieved approximately 90% accuracy.', 'Model A achieved at least 90% accuracy.',
                  'Model A achieved 90% accuracy on Dataset Z.', 'Model A achieved 90% accuracy in 2025.',
                  'Model A achieved 90 +/- 2% accuracy.', 'Model A achieved 80–90% accuracy.',
                  'Model A achieved 90% accuracy and 70% recall.', 'It achieved 90% accuracy.',
                  'Model A achieved -90% accuracy.', 'Model A achieved 90% accuracy...', 'Model A achieved 90% accuracy?']
        for claim in claims:
            with self.subTest(claim=claim):
                self.assertTrue(all(item.status == 'abstain' for item in check_structure(ClaimInput(evidence, claim), CONFIG)))
                self.assertTrue(all(item.status == 'abstain' for item in check_structure(ClaimInput(claim, evidence), CONFIG)))
        context = 'The results are hypothetical. Model A achieved 80% accuracy.'
        self.assertEqual(check(context, 'Model A achieved 90% accuracy.', 'numeric').status, 'abstain')

    def test_conflicting_or_incomplete_evidence_abstains(self):
        cases = [
            'Model A achieved 80% accuracy. Model A achieved 90% accuracy.',
            'Model A achieved 80% accuracy, exceeding Model B at 90%.',
            'The trial enrolled 120 participants: 70 in group X and 60 in group Y.',
            'Model A had higher accuracy than Model B. Model B had higher accuracy than Model A.',
            'Model A achieved 80% accuracy. Model B achieved 90% accuracy. Model A had higher accuracy than Model B.',
        ]
        for evidence in cases:
            with self.subTest(evidence=evidence):
                self.assertEqual(check(evidence, 'Model A achieved 95% accuracy.', 'numeric').status, 'abstain')

    def test_only_fully_atomic_claims_are_checked(self):
        evidence = 'Model A achieved 80% accuracy. Model B achieved 70% accuracy.'
        claim = 'Model A achieved 90% accuracy. Model B achieved 70% accuracy.'
        self.assertTrue(all(x.status == 'abstain' for x in check_structure(ClaimInput(evidence, claim), CONFIG)))

    def test_ablation_switches(self):
        numeric = ClaimInput('Model A achieved 80% accuracy.', 'Model A achieved 90% accuracy.')
        relation = ClaimInput('Model A had higher accuracy than Model B.', 'Model A had lower accuracy than Model B.')
        for enabled in (False, True):
            checks = check_structure(numeric, replace(CONFIG, numeric_checks=enabled))
            self.assertEqual(checks[0].status, 'contradiction' if enabled else 'disabled')
            checks = check_structure(relation, replace(CONFIG, comparison_checks=enabled))
            self.assertEqual(checks[1].status, 'contradiction' if enabled else 'disabled')

    def test_hybrid_overrides_only_contradictions_and_retains_scores(self):
        nli = Mock()
        supported = Prediction('nli', Verdict.SUPPORTED, 'stub', .9, 'entailment_probability',
                               {'entailment': .9, 'neutral': .05, 'contradiction': .05})
        inputs = [ClaimInput('Model A achieved 80% accuracy.', 'Model A achieved 90% accuracy.'),
                  ClaimInput('Model A achieved 80% accuracy.', 'Model A achieved 80% accuracy.'),
                  ClaimInput('Unparsed source.', 'Unparsed claim.')]
        nli.verify_many.return_value = [supported] * 3
        output = StructureAwareVerifier(NLI_CONFIG, CONFIG, nli).verify_many(inputs)
        nli.verify_many.assert_called_once_with(inputs)
        self.assertEqual([p.verdict for p in output], [Verdict.NOT_SUPPORTED, Verdict.SUPPORTED, Verdict.SUPPORTED])
        for item in output:
            self.assertEqual(item.base_verdict, Verdict.SUPPORTED)
            self.assertEqual(item.score, .9)
            self.assertEqual(item.score_type, 'nli_entailment_probability')
            self.assertEqual(item.class_scores, supported.class_scores)
        self.assertEqual(output[0].checks[0].status, 'contradiction')

    def test_consistent_check_cannot_promote_nli_rejection(self):
        nli = Mock()
        nli.verify_many.return_value = [Prediction('nli', Verdict.NOT_SUPPORTED, 'stub')]
        verifier = StructureAwareVerifier(NLI_CONFIG, CONFIG, nli)
        result = verifier.verify(ClaimInput('BERT achieved 80% accuracy.', 'BERT achieved 80% accuracy.'))
        self.assertEqual(result.verdict, Verdict.NOT_SUPPORTED)
        self.assertEqual(result.checks[0].status, 'consistent')

    def test_both_disabled_exactly_preserve_nli_decision(self):
        nli = Mock()
        nli.verify_many.return_value = [Prediction('nli', Verdict.SUPPORTED, 'stub')]
        verifier = StructureAwareVerifier(NLI_CONFIG, StructureConfig(False, False), nli)
        result = verifier.verify(ClaimInput('BERT achieved 80% accuracy.', 'BERT achieved 90% accuracy.'))
        self.assertEqual(result.verdict, result.base_verdict)
        self.assertTrue(all(c.status == 'disabled' for c in result.checks))

    def test_empty_and_wrong_count(self):
        nli = Mock()
        verifier = StructureAwareVerifier(NLI_CONFIG, CONFIG, nli)
        self.assertEqual(verifier.verify_many([]), [])
        nli.verify_many.assert_not_called()
        nli.verify_many.return_value = []
        with self.assertRaises(ValueError):
            verifier.verify(ClaimInput('s', 'c'))

    def test_configuration_and_schema_validation(self):
        config = ExperimentConfig.load(ROOT / 'experiments/structure_smoke.toml')
        self.assertEqual(config.structure, CONFIG)
        self.assertIsNotNone(config.nli)
        for fields in [{'numeric_checks': 1}, {'comparison_checks': 'true'},
                       {'absolute_tolerance': -1}, {'relative_tolerance': math.nan}]:
            with self.assertRaises(ValueError):
                replace(CONFIG, **fields)
        for status in ['contradiction', 'consistent', 'unknown']:
            with self.assertRaises(ValueError):
                StructuralCheck('numeric', status, 'Missing evidence spans')


if __name__ == '__main__':
    unittest.main()
