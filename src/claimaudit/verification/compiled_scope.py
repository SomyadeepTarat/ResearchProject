"""Known-method extension: compile source-world lineage once, then cofactor.

This is an application of established BDD operations, NOT a novelty claim.
Dependency: dd==0.6.0 (optional research extra). No model inference or text parsing.
"""
from fractions import Fraction
from functools import reduce
from operator import and_, or_

from claimaudit.verification.scope import validate


class CompiledScope:
    def __init__(self, problem):
        from dd.autoref import BDD
        validate(problem)
        self.problem = problem
        self.bdd = b = BDD()
        self.names = [[f'b{i}a{j}' for j in range(len(c.alternatives))] for i,c in enumerate(problem.choices)]
        names = [n for group in self.names for n in group]
        if names: b.declare(*names)
        conjunction = lambda xs: reduce(and_, xs, b.true)
        disjunction = lambda xs: reduce(or_, xs, b.false)
        valid = b.true
        tagged = [(b.true, f) for f in problem.facts]
        for group, choice in zip(self.names, problem.choices):
            variables = [b.var(n) for n in group]
            valid &= disjunction(variables)
            for j, v in enumerate(variables):
                for w in variables[j+1:]: valid &= ~(v & w)
            tagged.extend((v,f) for v,alt in zip(variables,choice.alternatives) for f in alt)
        supported_contexts, failed_contexts = [], []
        for context in problem.contexts:
            passes, failures = [], []
            for atom in problem.atoms:
                yes, no = [], []
                for present, fact in tagged:
                    if (fact.context,fact.entity,fact.metric,fact.unit) != (context,atom.entity,atom.metric,atom.unit):
                        continue
                    x,y=Fraction(fact.value),Fraction(atom.value)
                    ok={'==':x==y,'>':x>y,'<':x<y,'>=':x>=y,'<=':x<=y}[atom.operator]
                    (yes if ok else no).append(present)
                passes.append(disjunction(yes)); failures.append(disjunction(no))
            supported_contexts.append(conjunction(passes))
            failed_contexts.append(disjunction(failures))
        supported = disjunction(supported_contexts)
        contradicted = ~supported & conjunction(failed_contexts) if problem.closed_domain else b.false
        self.roots = {'supported': valid & supported,
                      'contradicted': valid & contradicted,
                      'insufficient': valid & ~supported & ~contradicted}
        # Release temporary references before reporting live manager size.
        self.valid = valid

    def decide(self, resolutions=None):
        assignment = {}
        for i,j in (resolutions or {}).items():
            if type(i) is not int or type(j) is not int or not 0<=i<len(self.names) or not 0<=j<len(self.names[i]):
                raise ValueError('Invalid source-choice resolution.')
            assignment.update({name:k==j for k,name in enumerate(self.names[i])})
        possible = sorted(status for status,root in self.roots.items()
                          if self.bdd.let(assignment,root) != self.bdd.false)
        if not possible:
            raise ValueError('No admissible source world remains.')
        return {'status':possible[0] if len(possible)==1 else 'ambiguous', 'possible_statuses':possible}

    def resolution_table(self):
        return [[self.decide({i:j})['status'] for j in range(len(c.alternatives))]
                for i,c in enumerate(self.problem.choices)]

    def recommend(self):
        if self.decide()['status'] != 'ambiguous': return None
        candidates=[]
        for i,outcomes in enumerate(self.resolution_table()):
            if all(s!='ambiguous' for s in outcomes):
                c=self.problem.choices[i]
                candidates.append({'choice_index':i,'source_locator':c.locator,'cost':c.cost,'conditional_statuses':outcomes})
        return min(candidates,key=lambda c:(c['cost'],c['choice_index'])) if candidates else None

    def close(self):
        # Explicit lifetime prevents dd.autoref shutdown diagnostics from live roots.
        self.roots.clear()
        self.valid=None
        self.bdd.collect_garbage()


def compiled_audit(problem):
    engine=CompiledScope(problem)
    try:
        result=engine.decide()
        result['resolution_table']=engine.resolution_table() if result['status']=='ambiguous' else []
        result['recommendation']=engine.recommend()
        engine.bdd.collect_garbage()
        result['bdd_live_nodes']=len(engine.bdd)
        result['compilations']=1
        return result
    finally:
        engine.close()
