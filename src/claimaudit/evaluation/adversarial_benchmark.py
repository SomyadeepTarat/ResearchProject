"""Reproducible reserved evaluation and adverse scaling, isolated per engine/case.

No tuning, rounding, extrapolation or claims of patent novelty. Median of three
raw ns samples, including construction, validation and conditional queries. Imports
and process startup excluded. Peak RSS includes Python and imported libraries.
"""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
from hashlib import sha256
from importlib.metadata import version
import json
import os
from pathlib import Path
import platform
import random
import resource
import statistics
import subprocess
import sys
from time import perf_counter_ns
from claimaudit.verification.scope import Atom,Fact,Choice,Problem,from_dict
from claimaudit.evaluation.scope_backends import BACKENDS

ROOT=Path(__file__).resolve().parents[3]
SEED=20261019


def scaling_cases():
    for n in (6,10,12,16):
        # Each choice independently changes one required predicate: every full
        # signature is different. This intentionally defeats v1 state merging.
        atoms=tuple(Atom('a',str(i),'u','==','1') for i in range(n))
        choices=tuple(Choice(str(i),((Fact('a',str(i),'u','1','x','synthetic'),),(Fact('a',str(i),'u','0','x','synthetic'),))) for i in range(n))
        p=Problem(atoms,('x',),choices=choices,closed_domain=True)
        yield {'id':f'adverse-{n}','split':'scaling_adverse','expected':'ambiguous','problem':asdict(p)}
        # Favorable control: choices all refer to unqueried measurements.
        p=Problem((Atom('a','target','u','==','1'),),('x',),(Fact('a','target','u','1','x','synthetic'),),
                  tuple(Choice(str(i),((),(Fact('other',str(i),'u','1','x','synthetic'),))) for i in range(n)))
        yield {'id':f'favorable-{n}','split':'scaling_favorable','expected':'supported','problem':asdict(p)}


def worker(engine, repeats):
    # Load heavy engine libraries before the stopwatch, equally documented.
    if engine=='z3': import z3
    elif engine=='problog':
        import problog, pysdd.sdd
    elif engine in ('compiled_reuse','bdd_rebuild'): import dd.autoref
    payload=sys.stdin.read(); problem=from_dict(json.loads(payload))
    samples=[]; result=None
    for _ in range(repeats):
        start=perf_counter_ns(); actual=BACKENDS[engine](problem); samples.append(perf_counter_ns()-start)
        if result is not None and actual!=result: raise AssertionError('Nondeterministic semantic output.')
        result=actual
    rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print(json.dumps({'result':result,'elapsed_ns':samples,'median_ns':statistics.median(samples),
                      'peak_rss_bytes':rss if sys.platform=='darwin' else rss*1024}))


def run(output,repeats):
    output.mkdir(parents=True,exist_ok=True)
    data=ROOT/'data/scope_v2/heldout.jsonl'
    freeze=json.loads((data.parent/'freeze.json').read_text())
    if sha256(data.read_bytes()).hexdigest()!=freeze['input_sha256']: raise ValueError('Frozen inputs changed.')
    records=[json.loads(line) for line in data.read_text().splitlines()]+list(scaling_cases())
    (output/'inputs.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in records))
    metadata={'started_at':datetime.now(timezone.utc).isoformat(),'seed':SEED,'repeats':repeats,
              'python':platform.python_version(),'platform':platform.platform(),'machine':platform.machine(),
              'packages':{p:version(p) for p in ('dd','z3-solver','problog','pysdd')},
              'heldout_sha256':freeze['input_sha256'],'benchmark_inputs_sha256':sha256((output/'inputs.jsonl').read_bytes()).hexdigest(),
              'protocol':'Time includes validation, compilation, initial decision and all single-choice conditional decisions for ambiguous cases. Imports excluded. RSS is whole isolated process peak including imports, not incremental algorithm allocation.',
              'limits':{'scope_dp_states':5000,'exhaustive_worlds':4096,'z3_check_timeout_ms':10000,'worker_timeout_seconds':45},
              'llm':{'status':'separate_experiment','reason':'Local Ollama comparison is excluded from solver timings; see the separate LLM report.'}}
    rows=[]; rng=random.Random(SEED)
    for idx,record in enumerate(records):
        names=list(BACKENDS); rng.shuffle(names)
        for name in names:
            payload=json.dumps(record['problem'],sort_keys=True)
            row={'id':record['id'],'split':record['split'],'expected':record['expected'],'engine':name,
                 'input_sha256':sha256(payload.encode()).hexdigest()}
            try:
                proc=subprocess.run([sys.executable,'-m',__name__ if __name__!='__main__' else 'claimaudit.evaluation.adversarial_benchmark','--worker',name,'--repeats',str(repeats)],input=payload,text=True,capture_output=True,timeout=45,check=False,
                                    env={**os.environ,'PYTHONHASHSEED':str(SEED),'OMP_NUM_THREADS':'1'})
                if proc.returncode: row.update({'result':{'status':'error'},'stderr':proc.stderr,'returncode':proc.returncode})
                else:
                    row.update(json.loads(proc.stdout))
                    if proc.stderr: row['stderr']=proc.stderr
            except subprocess.TimeoutExpired:
                row['result']={'status':'timeout','reason':'45 second worker cap; no timing or memory inferred.'}
            rows.append(row)
            with (output/'measurements.jsonl').open('a') as f: f.write(json.dumps(row)+'\n')
        print(f"{idx+1}/{len(records)} {record['id']}",flush=True)
    summary={}
    for split in sorted({r['split'] for r in rows}):
        summary[split]={}
        for name in BACKENDS:
            group=[r for r in rows if r['split']==split and r['engine']==name]
            complete=[r for r in group if r['result']['status'] in ('supported','contradicted','insufficient','ambiguous')]
            summary[split][name]={'correct':sum(r['result']['status']==r['expected'] for r in complete),'completed':len(complete),'total':len(group),
                                 'noncompleted':{s:sum(r['result']['status']==s for r in group) for s in ('incomplete','skipped','timeout','error')},
                                 'sum_median_ns_completed':sum(r['median_ns'] for r in complete),'max_peak_rss_bytes':max((r.get('peak_rss_bytes',0) for r in group),default=0)}
    disagreements=[]
    for record in records:
        group=[r for r in rows if r['id']==record['id'] and r['result']['status'] in ('supported','contradicted','insufficient','ambiguous')]
        ref=next((r for r in group if r['engine']=='exhaustive'),None)
        if ref:
            for r in group:
                if r['result']['status']!=ref['result']['status'] or r['result'].get('resolution_table')!=ref['result'].get('resolution_table'):
                    disagreements.append({'id':record['id'],'engine':r['engine']})
    metadata.update({'finished_at':datetime.now(timezone.utc).isoformat(),'summary':summary,'exhaustive_disagreements':disagreements})
    paths=['src/claimaudit/verification/scope.py','src/claimaudit/verification/compiled_scope.py','src/claimaudit/evaluation/scope_backends.py','src/claimaudit/evaluation/adversarial_benchmark.py','src/claimaudit/evaluation/scope_benchmark.py','scripts/freeze_scope_holdout.py']
    metadata['source_sha256']={p:sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}
    metadata['measurements_sha256']=sha256((output/'measurements.jsonl').read_bytes()).hexdigest()
    (output/'summary.json').write_text(json.dumps(metadata,indent=2)+'\n')


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--worker',choices=list(BACKENDS)); parser.add_argument('--repeats',type=int,default=3)
    parser.add_argument('--output',type=Path,default=ROOT/'results/adversarial_v2')
    args=parser.parse_args()
    if args.repeats<1 or args.repeats%2!=1: parser.error('Use a positive odd repeat count for integer median ns.')
    if args.worker: worker(args.worker,args.repeats)
    else:
        if (args.output/'measurements.jsonl').exists(): parser.error('Choose a fresh output folder; prior measurements are never appended or replaced.')
        run(args.output,args.repeats)


if __name__=='__main__': main()
