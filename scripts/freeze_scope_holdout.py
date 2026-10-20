"""Freeze reserved inputs before compiling the new engine; no scope_v1 generator.

Annotations for paper cases are manually specified here by the coding assistant,
not independent human labels. Generated topology labels come from the pre-existing
exhaustive reference. This is a reserved test, not a blinded external evaluation.
"""
from dataclasses import asdict
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import random
from claimaudit.verification.scope import Atom, Fact, Choice, Problem
from claimaudit.evaluation.scope_benchmark import exhaustive

ROOT = Path(__file__).resolve().parents[1]
SEED = 20261019


def build():
    rng = random.Random(SEED)
    records = []
    # New sparse multi-context, three-way source-block topologies, not the six
    # accuracy/latency templates used to design ScopeGuard v1.
    for case in range(24):
        contexts = tuple(f'lab-{i}' for i in range(rng.randint(2,4)))
        atoms = tuple(Atom('specimen', f'assay-{i}', 'unit', rng.choice(['==','<','>','<=','>=']), '0') for i in range(rng.randint(3,5)))
        slots = [(c,a.metric) for c in contexts for a in atoms]
        rng.shuffle(slots)
        blocks = [[] for _ in range(rng.randint(3,5))]
        for i, slot in enumerate(slots): blocks[i % len(blocks)].append(slot)
        choices = []
        for b, owned in enumerate(blocks):
            alternatives = []
            for alt in range(3):
                alternatives.append(tuple(Fact('specimen',m,'unit',str(rng.choice([-1,0,1])),c,f'synthetic-topology:{case}/{b}/{alt}/{c}/{m}') for c,m in owned if rng.random() > .15))
            choices.append(Choice(f'plate-map-{b}', tuple(alternatives), rng.randint(1,5)))
        p = Problem(atoms, contexts, choices=tuple(choices), closed_domain=case%2==0)
        records.append({'id':f'topology-{case:02}', 'split':'heldout_topology', 'source':'synthetic sparse 3-way topology',
            'annotation':'pre-existing exhaustive oracle; not independent human gold', 'expected':exhaustive(p)['status'], 'problem':asdict(p)})
    # Directly transcribed complete rows; claims scoped to exactly these rows.
    def paper(prefix, title, url, table, entity, rows, metrics, claims, note):
        contexts = tuple(f'{prefix}:{row}' for row in rows)
        facts = tuple(Fact(entity,metric,unit,value,f'{prefix}:{row}',f'{url}#{table};row={row};column={metric}')
                      for row, values in rows.items() for (metric,unit),value in zip(metrics,values))
        for i,(predicates,expected,rationale) in enumerate(claims):
            atoms = tuple(Atom(entity,*predicate) for predicate in predicates)
            p=Problem(atoms,contexts,facts,closed_domain=True)
            records.append({'id':f'{prefix}-{i}', 'split':'heldout_paper', 'source':title,'url':url,'table':table,
                'annotation':'assistant manually transcribed; independent human review outstanding',
                'scope_note':note, 'claim':'Among only the listed configurations there exists one satisfying: '+ '; '.join(f'{a.metric} {a.operator} {a.value} {a.unit}' for a in atoms),
                'rationale':rationale, 'expected':expected, 'problem':asdict(p)})
    paper('transformer','Attention Is All You Need','https://arxiv.org/pdf/1706.03762','Table3-page9','Transformer',
        {'base':('4.92','25.8','65'),'big':('4.33','26.4','213')},
        [('PPL','per-wordpiece'),('BLEU','score'),('parameters','million')], [
        ([('PPL','per-wordpiece','==','4.92'),('BLEU','score','==','25.8'),('parameters','million','==','65')],'supported','Base row supplies all three.'),
        ([('BLEU','score','>=','26.4'),('parameters','million','<=','65')],'contradicted','Big BLEU cannot be combined with base parameter count.'),
        ([('PPL','per-wordpiece','<=','4.33'),('parameters','million','==','213')],'supported','Big row jointly satisfies both.'),
        ([('BLEU','score','>','26.4')],'contradicted','Strict boundary exceeds both listed scores.'),
        ([('BLEU','score','>=','25.8'),('training_energy','kWh','<','100')],'insufficient','Neither row supplies energy; no observed failing condition in every row.'),
        ([('PPL','per-wordpiece','==','4.33'),('BLEU','score','==','25.8')],'contradicted','These exact values belong to different rows.')],
        'Only base and big rows of Table 3, English-to-German newstest2013 development; NOT Table 2 test BLEU. Printed perplexity is per wordpiece. Other ablations are outside the claim domain.')
    paper('resnet','Deep Residual Learning for Image Recognition','https://arxiv.org/pdf/1512.03385','Table6-page7','ResNet',
        {'20':('8.75','0.27'),'56':('6.97','0.85'),'1202':('7.93','19.4')},
        [('error','percent'),('parameters','million')],[
        ([('error','percent','<=','6.97'),('parameters','million','<=','0.85')],'supported','56-layer row meets both.'),
        ([('error','percent','==','6.97'),('parameters','million','==','0.27')],'contradicted','56-layer error spliced with 20-layer parameter count.'),
        ([('error','percent','==','7.93'),('parameters','million','==','19.4')],'supported','1202-layer row meets both.'),
        ([('error','percent','<','6.97')],'contradicted','None of these three rows clears the strict bound; no claim about omitted 110-layer row.'),
        ([('error','percent','<=','9'),('latency','ms','<=','1')],'insufficient','Latency is unreported in these records.'),
        ([('error','percent','==','8.75'),('parameters','million','==','19.4')],'contradicted','20-layer error spliced with 1202-layer parameter count.')],
        'Only 20, 56 and 1202-layer rows of Table 6; CIFAR-10 test with augmentation. Excludes the 110-layer best/mean statistic to avoid a statistic-type ambiguity.')
    return records


if __name__ == '__main__':
    path=ROOT/'data/scope_v2/heldout.jsonl'
    payload=''.join(json.dumps(r,sort_keys=True)+'\n' for r in build())
    if path.exists() and path.read_text()!=payload:
        raise SystemExit('Refusing to overwrite a changed frozen dataset.')
    path.write_text(payload)
    freeze=ROOT/'data/scope_v2/freeze.json'
    if not freeze.exists():
        freeze.write_text(json.dumps({'frozen_at':datetime.now(timezone.utc).isoformat(),'seed':SEED,
            'input_sha256':sha256(payload.encode()).hexdigest(), 'records':36,
            'procedure':'Frozen before new backend implementation/evaluation. No tuning against this set. Same assistant authors and annotates; not a blinded independent holdout.'},indent=2)+'\n')
    print(freeze.read_text())
