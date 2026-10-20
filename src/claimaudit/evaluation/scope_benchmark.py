"""Synthetic engineering benchmark, not a paper-derived validation dataset."""
from dataclasses import asdict
from itertools import product
import json
from pathlib import Path
from time import perf_counter
from decimal import Decimal
from claimaudit.verification.scope import Atom, Fact, Choice, Problem, audit, recommend_resolution, validate


def exhaustive(p):
    """Independent plain-loop reference; no DP signatures/decision helpers."""
    validate(p)
    counts = {}
    for choices in product(*(c.alternatives for c in p.choices)):
        facts = list(p.facts) + [f for bundle in choices for f in bundle]
        successes, failures = [], []
        for context in p.contexts:
            passed, failed = [], []
            for a in p.atoms:
                observations = [f for f in facts if (f.context, f.entity, f.metric, f.unit)
                                == (context, a.entity, a.metric, a.unit)]
                tests = []
                for f in observations:
                    x, y = Decimal(f.value), Decimal(a.value)
                    if a.operator == '==': ok = x == y
                    elif a.operator == '>=': ok = x >= y
                    elif a.operator == '<=': ok = x <= y
                    elif a.operator == '>': ok = x > y
                    else: ok = x < y
                    tests.append(ok)
                passed.append(bool(tests) and all(tests))
                failed.append(bool(tests) and not any(tests))
            successes.append(all(passed))
            failures.append(any(failed))
        status = 'supported' if any(successes) else ('contradicted' if p.closed_domain and all(failures) else 'insufficient')
        counts[status] = counts.get(status, 0) + 1
    return {'status': next(iter(counts)) if len(counts) == 1 else 'ambiguous', 'world_counts': counts}


def pooled_support(p, keep_context):
    """Deliberately lossy baselines: flatten mutually exclusive alternatives."""
    facts = p.facts + tuple(f for c in p.choices for alt in c.alternatives for f in alt)
    contexts = p.contexts if keep_context else ('*',)
    for ctx in contexts:
        passed = []
        for a in p.atoms:
            matches = []
            for f in facts:
                if (f.entity, f.metric, f.unit) != (a.entity, a.metric, a.unit): continue
                if keep_context and f.context != ctx: continue
                x, y = Decimal(f.value), Decimal(a.value)
                matches.append({'==': x == y, '>=': x >= y, '<=': x <= y, '>': x > y, '<': x < y}[a.operator])
            passed.append(any(matches))
        if all(passed): return True
    return False


def examples(n=50):
    for i in range(n):
        high, low = Decimal(90) + Decimal(i)/100, 2 + i % 3
        atoms = (Atom('Model A', 'accuracy', '%', '>=', str(high)), Atom('Model A', 'latency', 'ms', '<=', str(low)))
        def f(metric, value, ctx):
            return Fact('Model A', metric, '%' if metric == 'accuracy' else 'ms', str(value), ctx, f'synthetic:{i}/table/{ctx}/{metric}')
        good = (f('accuracy', high, 'X'), f('latency', low, 'X'))
        bad = (f('accuracy', high, 'X'), f('latency', low+20, 'X'), f('accuracy', high-10, 'Y'), f('latency', low, 'Y'))
        cases = [
            ('joint_support', 'supported', Problem(atoms, ('X','Y'), good)),
            ('cross_experiment_splice', 'contradicted', Problem(atoms, ('X','Y'), bad, closed_domain=True)),
            ('partial_evidence', 'insufficient', Problem(atoms, ('X','Y'), (good[0],))),
            ('header_ambiguity', 'ambiguous', Problem(atoms, ('X','Y'), choices=(Choice('Table 1 header', (good,bad)),), closed_domain=True)),
            ('exclusive_splice', 'contradicted', Problem(atoms, ('X',), choices=(Choice('Table 2 header', ((good[0], f('latency',low+20,'X')), (f('accuracy',high-10,'X'), good[1]))),), closed_domain=True)),
            ('invariant_support', 'supported', Problem(atoms, ('X','Y'), good, (Choice('Unrelated metadata', ((), (f('accuracy',high-10,'Y'),))),))),
        ]
        for family, gold, p in cases:
            yield {'id':f'{family}-{i:03}', 'family':family, 'expected':gold, 'problem':asdict(p)}, p


def main():
    root = Path(__file__).resolve().parents[3]
    output = root/'results/scope_v1'
    output.mkdir(parents=True, exist_ok=True)
    records, predictions = [], []
    for record, p in examples():
        records.append(record)
        start = perf_counter(); result = audit(p); dp_seconds = perf_counter()-start
        start = perf_counter(); reference = exhaustive(p); reference_seconds = perf_counter()-start
        if result['world_counts'] != reference['world_counts']:
            raise AssertionError(record['id'])
        predictions.append({'id':record['id'], 'expected':record['expected'], 'audit':result,
            'reference':reference, 'pooled_support':pooled_support(p, False),
            'flattened_join_support':pooled_support(p, True),
            'resolution':recommend_resolution(p), 'dp_seconds':dp_seconds, 'reference_seconds':reference_seconds})
    summary = {'dataset':'300 synthetic engineering cases; six parameterized families, no held-out study',
        'n':len(records), 'exact_reference_agreement':sum(r['audit']['world_counts']==r['reference']['world_counts'] for r in predictions),
        'expected_status_matches':sum(r['audit']['status']==r['expected'] for r in predictions),
        'binary_support_accuracy':{name:sum((r[name] if name != 'scope' else r['audit']['status']=='supported') == (r['expected']=='supported') for r in predictions)/len(records)
            for name in ('pooled_support','flattened_join_support','scope')},
        'timing_note':'Single local runs; timings recorded for diagnosis, not a speedup claim.'}
    # Scaling case: many alternatives yield identical decision signatures.
    _, base = next(examples(1))
    irrelevant = tuple(Choice(f'header-{i}', ((), (Fact('Other',f'metric{i}','count','1','X',f'synthetic:header{i}'),))) for i in range(20))
    scale = Problem(base.atoms, base.contexts, base.facts, irrelevant)
    summary['scaling_case'] = audit(scale)
    (root/'data/scope_v1/cases.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in records))
    (output/'predictions.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in predictions))
    (output/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__': main()
