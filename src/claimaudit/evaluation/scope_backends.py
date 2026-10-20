"""Actual solver adapters; none is presented as a novel algorithm.

Workload: initial status plus every single-choice outcome if initially ambiguous.
This gives each engine the same required output. SMT reuses one solver with scopes.
The rebuild BDD baseline intentionally recompiles; report it as an ablation, not
as the state of the art. ProbLog is a separate probabilistic-logic implementation.
"""
from dataclasses import replace
from decimal import Decimal
from itertools import combinations
from math import prod
from claimaudit.verification.scope import validate, audit
from claimaudit.verification.compiled_scope import CompiledScope, compiled_audit
from claimaudit.evaluation.scope_benchmark import exhaustive


def resolved(p,i,j):
    return replace(p,facts=p.facts+p.choices[i].alternatives[j],choices=p.choices[:i]+p.choices[i+1:])


def common_batch(p, fn):
    result=fn(p)
    if result['status']=='incomplete': return result
    result['resolution_table'] = [[fn(resolved(p,i,j))['status'] for j in range(len(c.alternatives))]
                                 for i,c in enumerate(p.choices)] if result['status']=='ambiguous' else []
    return result


def dp_batch(p):
    # Fixed before held-out results: 5,000 states. Capped outcomes remain explicit.
    return common_batch(p,lambda q:audit(q,max_states=5000))


def exhaustive_batch(p):
    if prod(len(c.alternatives) for c in p.choices)>4096:
        return {'status':'skipped','reason':'Predeclared exhaustive limit: 4096 worlds.'}
    return common_batch(p,exhaustive)


def bdd_rebuild_batch(p):
    def single(q):
        engine=CompiledScope(q)
        try: return engine.decide()
        finally: engine.close()
    result=common_batch(p,single)
    result['compilations']=1+sum(len(c.alternatives) for c in p.choices) if result['status']=='ambiguous' else 1
    return result


def z3_batch(p):
    """Independent SMT encoding using exact RealVal arithmetic and one-hot choices."""
    import z3
    validate(p)
    solver=z3.Solver(); solver.set(timeout=10000,random_seed=20261019)
    selected=[]; tagged=[(z3.BoolVal(True),f) for f in p.facts]
    for i,c in enumerate(p.choices):
        variables=[z3.Bool(f'choice_{i}_{j}') for j in range(len(c.alternatives))]
        solver.add(z3.PbEq([(v,1) for v in variables],1))
        selected.append(variables)
        tagged.extend((v,f) for v,alt in zip(variables,c.alternatives) for f in alt)
    support_contexts=[]; failure_contexts=[]
    for context in p.contexts:
        predicates=[]; failing=[]
        for a in p.atoms:
            yes=[]; no=[]
            for present,f in tagged:
                if (f.context,f.entity,f.metric,f.unit)!=(context,a.entity,a.metric,a.unit): continue
                x,y=z3.RealVal(format(Decimal(f.value),'f')),z3.RealVal(format(Decimal(a.value),'f'))
                test={'==':x==y,'>':x>y,'<':x<y,'>=':x>=y,'<=':x<=y}[a.operator]
                yes.append(z3.And(present,test)); no.append(z3.And(present,z3.Not(test)))
            predicates.append(z3.Or(yes)); failing.append(z3.Or(no))
        support_contexts.append(z3.And(predicates)); failure_contexts.append(z3.Or(failing))
    supported=z3.Or(support_contexts)
    contradicted=z3.And(z3.Not(supported),z3.And(failure_contexts)) if p.closed_domain else z3.BoolVal(False)
    formulas={'supported':supported,'contradicted':contradicted,'insufficient':z3.And(z3.Not(supported),z3.Not(contradicted))}
    calls=0
    def decide(extra=()):
        nonlocal calls
        possible=[]
        for status,formula in formulas.items():
            solver.push(); solver.add(formula,*extra); calls+=1
            outcome=solver.check(); solver.pop()
            if outcome==z3.unknown: return {'status':'incomplete','reason':'Z3 unknown or timeout.'}
            if outcome==z3.sat: possible.append(status)
        return {'status':possible[0] if len(possible)==1 else 'ambiguous','possible_statuses':sorted(possible)}
    result=decide()
    result['resolution_table']=[[decide((v,))['status'] for v in variables] for variables in selected] if result['status']=='ambiguous' else []
    result['solver_checks']=calls
    return result


def problog_program(p):
    """Ground categorical choices; literal strings never contain source/user text."""
    validate(p)
    lines=[]; tagged=[('true',f) for f in p.facts]
    for i,c in enumerate(p.choices):
        n=len(c.alternatives)
        lines.append('; '.join(f'1/{n}::choice({i},{j})' for j in range(n))+'.')
        tagged.extend((f'choice({i},{j})',f) for j,alt in enumerate(c.alternatives) for f in alt)
    for ci,context in enumerate(p.contexts):
        for ai,a in enumerate(p.atoms):
            for prefix in ('pass','fail'):
                lines.append(f'{prefix}({ci},{ai}) :- fail.')
            for present,f in tagged:
                if (f.context,f.entity,f.metric,f.unit)!=(context,a.entity,a.metric,a.unit): continue
                x,y=Decimal(f.value),Decimal(a.value)
                ok={'==':x==y,'>':x>y,'<':x<y,'>=':x>=y,'<=':x<=y}[a.operator]
                lines.append(f'{"pass" if ok else "fail"}({ci},{ai}) :- {present}.')
            lines.append(f'bad({ci}) :- fail({ci},{ai}).')
        lines.append('supported :- '+', '.join(f'pass({ci},{ai})' for ai in range(len(p.atoms)))+'.')
    if p.closed_domain:
        lines.append('contradicted :- \\+ supported, '+', '.join(f'bad({ci})' for ci in range(len(p.contexts)))+'.')
    else: lines.append('contradicted :- fail.')
    lines.append('insufficient :- \\+ supported, \\+ contradicted.')
    lines.extend('query('+s+').' for s in ('supported','contradicted','insufficient'))
    return '\n'.join(lines)


def problog_batch(p, conditional=True):
    from problog import get_evaluatable
    from problog.program import PrologString
    from problog.evaluator import Semiring
    from fractions import Fraction

    class Rational(Semiring):
        # Exact rational endpoints: no floating epsilon can hide rare worlds.
        def plus(self,a,b): return a+b
        def times(self,a,b): return a*b
        def negate(self,a): return 1-a
        def is_one(self,a): return a==1
        def one(self): return Fraction(1)
        def zero(self): return Fraction(0)
        def value(self,a): return Fraction(str(a))
        def pos_value(self,a,key=None):
            # ProbLog arithmetic terms must be evaluated exactly, not float().
            if getattr(a,'functor',None)=='/': return Fraction(str(a.args[0]))/Fraction(str(a.args[1]))
            return Fraction(str(a))
        def neg_value(self,a,key=None): return 1-self.pos_value(a,key)
        def normalize(self,a,z): return a/z
        def result(self,a,formula=None): return a
        def is_dsp(self): return True
    def single(q):
        values=get_evaluatable(name='sdd').create_from(PrologString(problog_program(q))).evaluate(semiring=Rational())
        probs={str(k):v for k,v in values.items()}
        possible=sorted(k for k,v in probs.items() if v>0)
        return {'status':possible[0] if len(possible)==1 else 'ambiguous','possible_statuses':possible,
                'uniform_world_fractions':{k:str(v) for k,v in probs.items()}}
    return common_batch(p,single) if conditional else single(p)


BACKENDS={'scope_dp':dp_batch,'bdd_rebuild':bdd_rebuild_batch,'compiled_reuse':compiled_audit,
          'z3':z3_batch,'problog':problog_batch,'exhaustive':exhaustive_batch}
