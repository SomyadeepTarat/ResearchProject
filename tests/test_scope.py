from dataclasses import replace
import random
import unittest
from claimaudit.verification.scope import Atom, Fact, Choice, Problem, audit, recommend_resolution, from_dict, verify_replay
from claimaudit.evaluation.scope_benchmark import examples, exhaustive


class ScopeTests(unittest.TestCase):
    def test_named_cases(self):
        for record, p in examples(3):
            with self.subTest(record['id']):
                self.assertEqual(audit(p)['status'], record['expected'])
                self.assertEqual(audit(p)['world_counts'], exhaustive(p)['world_counts'])
                self.assertEqual(from_dict(record['problem']), p)

    def test_random_exhaustive_equivalence(self):
        rng = random.Random(42)
        for _ in range(200):
            atoms = tuple(Atom('A',f'm{i}','u',rng.choice(['==','>=','<=','>','<']),'5') for i in range(3))
            choices = []
            for i in range(3):
                alternatives = tuple(tuple(Fact('A',f'm{i}','u',str(rng.randrange(10)),c,f'source-{i}-{j}-{c}') for c in ('X','Y') if rng.random()<.8) for j in range(3))
                choices.append(Choice(f'header{i}', alternatives))
            p = Problem(atoms, ('X','Y'), choices=tuple(choices), closed_domain=rng.choice([True,False]))
            self.assertEqual(audit(p)['world_counts'], exhaustive(p)['world_counts'])

    def test_replay_detects_changed_input_and_output(self):
        record, p = next(examples(1))
        replay = {'input':record['problem'], 'result':audit(p)}
        self.assertTrue(verify_replay(replay))
        replay['result']['status'] = 'contradicted'
        self.assertFalse(verify_replay(replay))
        replay['result'] = audit(p)
        replay['input']['facts'][0]['value'] = '91'
        self.assertFalse(verify_replay(replay))

    def test_resolution_ignores_unrelated_header(self):
        p = list(examples(1))[3][1]
        p = replace(p, choices=(Choice('unrelated', ((), ()), 1), replace(p.choices[0], cost=2)))
        self.assertEqual(recommend_resolution(p)['source_locator'], 'Table 1 header')

    def test_representative_bindings_replay(self):
        for _, p in examples(1):
            for status, indices in audit(p)['representative_bindings'].items():
                facts = p.facts + tuple(f for c,i in zip(p.choices, indices) for f in c.alternatives[i])
                self.assertEqual(exhaustive(replace(p, facts=facts, choices=()))['status'], status)

    def test_cap_abstains(self):
        p = list(examples(1))[3][1]
        self.assertEqual(audit(p, max_states=1)['status'], 'incomplete')

    def test_resolution_has_conditional_outcomes(self):
        p = list(examples(1))[3][1]
        result = recommend_resolution(p)
        self.assertEqual(result['conditional_statuses'], ['supported','contradicted'])
        self.assertEqual(result['source_locator'], 'Table 1 header')

    def test_no_closed_world_rejection_without_declaration(self):
        p = list(examples(1))[1][1]
        self.assertEqual(audit(replace(p, closed_domain=False))['status'], 'insufficient')

    def test_missing_context_rejected(self):
        p = list(examples(1))[0][1]
        with self.assertRaises(ValueError): audit(replace(p, contexts=('Y',)))

    def test_conflict_rejected(self):
        p = list(examples(1))[0][1]
        with self.assertRaises(ValueError):
            audit(replace(p, facts=p.facts+(replace(p.facts[0], value='-1'),)))

    def test_nonfinite_rejected(self):
        p = list(examples(1))[0][1]
        for value in ('NaN','Infinity','-Infinity'):
            with self.assertRaises(ValueError): audit(replace(p, atoms=(replace(p.atoms[0],value=value),)))

    def test_exact_decimal_and_unit_mismatch(self):
        p = Problem((Atom('A','m','ms','==','0.10'),), ('X',), (Fact('A','m','ms','0.1','X','table1'),))
        self.assertEqual(audit(p)['status'],'supported')
        self.assertEqual(audit(replace(p, atoms=(replace(p.atoms[0],unit='s'),)))['status'],'insufficient')

    def test_irrelevant_alternatives_merge(self):
        p = list(examples(1))[0][1]
        p = replace(p, choices=tuple(Choice(str(i),((),())) for i in range(30)))
        r = audit(p)
        self.assertEqual(r['worlds'],2**30)
        self.assertEqual(max(r['state_widths']),1)
        self.assertEqual(r['world_counts'],{'supported':2**30})

class ScopeDemoTests(unittest.TestCase):
    def test_all_scenarios_and_resolution(self):
        from pathlib import Path
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app/streamlit_app.py')).run()
        app.sidebar.radio[0].set_value('Scope audit (experimental)').run()
        for record, _ in examples(1):
            next(s for s in app.selectbox if s.label=='Scenario').set_value(record['family']).run()
            self.assertEqual(len(app.exception), 0)
            self.assertEqual(app.metric[2].value, record['expected'].capitalize())
            if record['family']=='header_ambiguity':
                next(s for s in app.selectbox if s.label=='Reviewed interpretation').set_value(1).run()
                self.assertIn('contradicted', app.success[0].value)

if __name__ == '__main__': unittest.main()

