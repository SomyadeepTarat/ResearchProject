from dataclasses import replace
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import random
import unittest
from claimaudit.verification.scope import Atom, Fact, Choice, Problem, recommend_resolution
from claimaudit.verification.compiled_scope import CompiledScope
from claimaudit.evaluation.scope_benchmark import examples, exhaustive
from claimaudit.evaluation.scope_backends import BACKENDS, problog_batch, resolved


class SolverTests(unittest.TestCase):
    def test_original_development_cases_all_engines(self):
        for record,p in examples(1):
            reference=BACKENDS['exhaustive'](p)
            for name,fn in BACKENDS.items():
                with self.subTest(record=record['id'],engine=name):
                    result=fn(p)
                    self.assertEqual(result['status'],reference['status'])
                    self.assertEqual(result['resolution_table'],reference['resolution_table'])

    def test_exact_thirds_and_all_three_outcomes(self):
        p=Problem((Atom('A','m','u','==','1'),),('X',),choices=(Choice('h',((Fact('A','m','u','1','X','s'),),(Fact('A','m','u','0','X','s'),),())),),closed_domain=True)
        result=problog_batch(p)
        self.assertEqual(set(result['uniform_world_fractions'].values()),{'1/3'})
        self.assertEqual(result['resolution_table'],[['supported','contradicted','insufficient']])
        for fn in BACKENDS.values(): self.assertEqual(fn(p)['status'],'ambiguous')

    def test_seeded_development_differential(self):
        rng=random.Random(77)
        for trial in range(12):
            atoms=tuple(Atom('a',str(i),'u',rng.choice(['==','<','>','<=','>=']),'-0.1') for i in range(2))
            choices=tuple(Choice(str(i),tuple(tuple(Fact('a',str(i),'u',rng.choice(['-0.10','-1','1']),c,'fixture') for c in ('x','y') if rng.random()<.9) for _ in range(2))) for i in range(2))
            p=Problem(atoms,('x','y'),choices=choices,closed_domain=trial%2==0)
            ref=BACKENDS['exhaustive'](p)
            for name,fn in BACKENDS.items():
                with self.subTest(trial=trial,engine=name):
                    actual=fn(p)
                    self.assertEqual(actual['status'],ref['status'])
                    self.assertEqual(actual['resolution_table'],ref['resolution_table'])
            counts=exhaustive(p)['world_counts']
            probabilities=problog_batch(p)['uniform_world_fractions']
            self.assertEqual({s:Fraction(v) for s,v in probabilities.items()}, {s:Fraction(counts.get(s,0),4) for s in probabilities})

    def test_multiple_resolutions_and_bad_indices(self):
        p=list(examples(1))[3][1]
        engine=CompiledScope(p)
        try:
            self.assertEqual(engine.decide({0:0})['status'],'supported')
            self.assertEqual(engine.decide({0:1})['status'],'contradicted')
            self.assertEqual(engine.recommend(),recommend_resolution(p))
            with self.assertRaises(ValueError): engine.decide({0:3})
            with self.assertRaises(ValueError): engine.decide({True:0})
        finally: engine.close()

    def test_support_can_have_different_witnesses(self):
        p=Problem((Atom('A','m','u','==','1'),),('x','y'),choices=(Choice('h',((Fact('A','m','u','1','x','s'),),(Fact('A','m','u','1','y','s'),))),))
        for fn in BACKENDS.values(): self.assertEqual(fn(p)['status'],'supported')

    def test_rare_world_not_rounded_away(self):
        atoms=tuple(Atom('a',str(i),'u','==','1') for i in range(12))
        choices=tuple(Choice(str(i),((Fact('a',str(i),'u','1','x','s'),),(Fact('a',str(i),'u','0','x','s'),))) for i in range(12))
        p=Problem(atoms,('x',),choices=choices,closed_domain=True)
        r=problog_batch(p,conditional=False)
        self.assertEqual(Fraction(r['uniform_world_fractions']['supported']),Fraction(1,2**12))
        self.assertEqual(r['status'],'ambiguous')
        self.assertEqual(BACKENDS['z3'](p)['status'],'ambiguous')

    def test_freeze_digest(self):
        root=Path(__file__).resolve().parents[1]/'data/scope_v2'
        self.assertEqual(sha256((root/'heldout.jsonl').read_bytes()).hexdigest(),json.loads((root/'freeze.json').read_text())['input_sha256'])


if __name__=='__main__': unittest.main()
