"""Build disclosure text directly from saved measurements; never invent results."""
from pathlib import Path
import json
import re
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'docs/adversarial_review'
S=json.loads((ROOT/'results/adversarial_v2/summary.json').read_text())
R=[json.loads(l) for l in (ROOT/'results/adversarial_v2/measurements.jsonl').read_text().splitlines()]
L=ROOT/'results/ollama_scope_v2/summary.json'
llm=json.loads(L.read_text()) if L.exists() else None
llm_rows=[json.loads(l) for l in (L.parent/'responses.jsonl').read_text().splitlines()] if llm else []
llm_table='\n'.join(['| Fixture | Expected | Output | Stop reason |','| --- | --- | --- | --- |']+[f"| {r['id']} | {r['expected']} | {r['predicted']} | {r.get('response',{}).get('done_reason','error')} |" for r in llm_rows]) if llm else ''

def table(split):
    lines=['| Engine | Correct / completed / total | Sum of case median times (ns) | Max process RSS (bytes) |','| --- | --- | --- | --- |']
    for name,x in S['summary'][split].items():
        lines.append(f"| {name} | {x['correct']} / {x['completed']} / {x['total']} | {x['sum_median_ns_completed']} | {x['max_peak_rss_bytes']} |")
    return '\n'.join(lines)

llm_text=(f"E4: Local Ollama qwen3:4b (4B, Q4_K_M), one zero-shot prompt, seed 20261019, temperature 0, thinking enabled, 2048 generated-token cap, 8192 context cap. Correct {llm['correct']}/{llm['total']}; false supports {llm['false_support']}; invalid/error outputs {llm['invalid_or_error']}. Full requests, responses, timing/token metadata, model digest and protocol are saved. This is NOT a strong/frontier-model test; its results cannot be generalized to stronger models. No prompt tuning or retries were used. Invalid outputs count as incorrect under this fixed budget, not as demonstrated semantic errors or evidence splicing." if llm else 'E4: Local Ollama comparison is pending. No model-performance conclusion is reported.')
report=f'''# Stage 3 - Measured research evaluation

Completed 20 October 2026 (India). This extension applies known BDD compilation and restriction. It is NOT a newly established invention. Stage 2 rejected all three novelty candidates before implementation. The code is useful for reproducible research on context-preserving numerical verification.

## Protocol and checkpoints

E0: 90 unit/integration tests passed in the complete suite. This includes seven new backend tests covering exact rational probabilities, mixed statuses, independent encodings, randomized development inputs, source restrictions and a rare supported world (1/4096). A development-only 20-choice ProbLog conditional-query test was stopped because it was too slow; it was replaced by a bounded 12-choice single-query unit test before reserved evaluation. No reserved cases were removed.

E1: 36 inputs were frozen before new backend evaluation: 24 sparse three-way topologies, plus 12 manually transcribed claims from two real paper tables. The topology family differs from the original six development templates. Gold for synthetic inputs comes from the pre-existing exhaustive oracle. Paper annotation is by the assistant with visual source checks, not independent human review. The same assistant designed both the method and evaluation; this is an internal reserved set, not a blinded external benchmark. Source extraction accuracy is not measured.

All six engines completed and matched all 36 labels. Initial and every single-choice conditional status matched exhaustive outputs where exhaustive ran; disagreements recorded: {len(S['exhaustive_disagreements'])}. Agreement checks implementations of a shared policy; it does not validate the policy as scientific truth or establish generalization to arbitrary papers.

E2: Every case ran in an isolated process with three repetitions; reported time is the exact integer median in nanoseconds. Times include validation, construction/compilation, the initial status and all single-choice conditional statuses when ambiguous. Imports and process startup are excluded. The compiled implementation additionally computes its clarification recommendation; some conditional work is repeated there. No model generation ran concurrently with solver timing. Engine order is shuffled with seed 20261019. Raw samples, all inputs, code hashes and package versions are saved. No extrapolation or rounded speedup is reported.

Real baselines: ProbLog 2.3.0 with PySDD 1.0.6 evaluates annotated-disjunction possible worlds using exact rational weights; Z3 4.15.4.0 uses one-hot categorical variables, exact numerical comparisons and incremental satisfiability checks; the existing exhaustive engine enumerates worlds. Scope DP is the original signature-merging implementation. BDD rebuild is a controlled ablation, not an independent state-of-the-art baseline. Compiled reuse uses dd 0.6.0. Uniform ProbLog priors are counting weights, not calibrated confidence. The ProbLog adapter rebuilds each conditional problem; a tuned incremental ProbLog integration could change the comparison. Library-language overhead also differs.

### Reserved topology inputs (24)

{table('heldout_topology')}

The sum of medians is 24968876 ns for compiled reuse versus 104202459 ns for BDD rebuild, 26714833 ns for original DP, 124363956 ns for Z3, 2516006750 ns for this ProbLog adapter and 107458539 ns for exhaustive evaluation. This is an aggregate of individual medians, not an end-to-end elapsed time. No confidence interval or statistical significance is claimed. Generic BDD operations (P04/P06/P16) already explain the reuse mechanism; measured reduction does not rescue novelty.

### Reserved real-paper fixtures (12)

{table('heldout_paper')}

These fixtures contain no alternative source interpretations. Reuse offers no repeated-query advantage: its 914541 ns aggregate exceeds exhaustive's 147417 ns, original DP's 433207 ns and BDD rebuild's 889793 ns. Perfect correctness on 12 hand-selected, structured fixtures is not evidence of end-to-end PDF verification accuracy.

### Adverse signature-state growth (4)

{table('scaling_adverse')}

E3: At 6, 10, 12 and 16 independent binary choices, every full pass/fail signature differs, so original DP cannot merge those states. At 16 choices it returns incomplete under the 5000-state cap. Exhaustive returns skipped under the 4096-world cap, on both adverse-16 and favorable-16; skipped is not a correctness result or measured runtime of verification. All other engines completed, including ProbLog: there were zero worker timeouts and zero errors in this final run. ProbLog adverse-16 median was 12451630959 ns. The initial slow development test must not be mislabeled as a benchmark timeout.

These inputs defeat the original DP compression but have simple Boolean structure; they are not worst cases for BDD size. This experiment does not demonstrate immunity to exponential BDD growth. Broader variable-order and hard Boolean-lineage benchmarks remain missing.

### Favorable irrelevant-choice controls (4)

{table('scaling_favorable')}

Original DP is faster on each favorable control. For favorable-16 it takes 113292 ns versus compiled reuse 1384083 ns. This is a measured case where compiling and preserving choices costs more than direct signature merging.

Peak RSS includes interpreter, imported libraries and retained memory across repetitions within one worker. Compiled reuse's topology peak (39370752 bytes) exceeds BDD rebuild (38715392 bytes) and original DP (24608768 bytes). No memory improvement is established. These process peaks are not allocator-level algorithm measurements.

## Optional local model

{llm_text}

{llm_table}

The paper subset has four supported, six contradicted and two insufficient examples; all are supplied as structured facts and predicates with explicit semantics. It does not test free-form extraction or ambiguous paper layouts. False-support count includes all unsupported predictions labeled supported; it must not automatically be called an evidence-splicing rate without reviewing each response. A strong LLM comparison and independently annotated larger benchmark remain open.

## Reproduction

Run from /Users/somyadeeptarat/Desktop/Claim:

```bash
uv sync --frozen --all-extras
uv run --all-extras python -m unittest discover -s tests -q
uv run --extra research python -m claimaudit.evaluation.adversarial_benchmark --output results/adversarial_reproduction
uv run --extra research python scripts/evaluate_local_scope_llm.py --url http://127.0.0.1:11434 --model qwen3:4b --output results/ollama_reproduction
python scripts/build_adversarial_report.py
uv run --with reportlab python scripts/render_adversarial_disclosure.py
```

Use fresh output directories: benchmark and LLM scripts refuse to overwrite measurements. To execute the complete existing application tests, also install the app/models extras if they are not already installed; see pyproject.toml. Solver experiments use Python {S['python']} on {S['platform']}. Local timing will vary. The Ollama model must already be installed; no download is performed by the script.

Frozen input SHA-256: {S['heldout_sha256']}

Full benchmark input SHA-256: {S['benchmark_inputs_sha256']}

Measurement JSONL SHA-256: {S['measurements_sha256']}

All numeric tables are generated from results/adversarial_v2/summary.json. Raw per-case observations are in measurements.jsonl. A preserved copy of the measurement files accompanies this report for audit. No publication, deployment, filing or public release was performed.
'''
if llm and llm['false_support']==0:
    report=report.replace('The paper subset has four supported', 'No false-support verdict was observed in this run. The targeted evidence-splicing error was therefore not demonstrated for this model under this protocol; invalid outputs are a different failure.\n\nThe paper subset has four supported')
(D/'STAGE3_RESULTS.md').write_text(report)
# A complete table of verified sources, preserving stated limitations.
prior=(D/'STAGE1_PRIOR_ART.md').read_text()
entries=re.findall(r'### (P\d+).*?\n\n(.*?)(?=\n### |\n## |\Z)',prior,re.S)
headers=re.findall(r'### (P\d+) [—-] (.*?)\n',prior)
titles=dict(headers)
prior_table=['| Source / date / URL | Coverage and remaining limits |','| --- | --- |']
for pid,body in entries:
    paragraphs=body.strip().split('\n\n')
    prior_table.append('| '+pid+' - '+titles[pid]+'<br>'+paragraphs[0].replace('\n',' ')+' | '+' '.join(paragraphs[1:]).replace('\n',' ')+' |')
form=f'''# Invention Disclosure Format (IDF)-B - completed research response

Document No. 02-IPR-R003 | Issue No/Date 2/01.02.2024 | Amd. No/Date 0/00.00.0000

Prepared 20 October 2026. Expanded layout preserves the blank form's ten questions, order and numbering. The original blank is unchanged. This response supersedes the earlier ScopeGuard annex's unresolved novelty framing. No defensible novelty has been established; this is a research-paper-only recommendation, not an assertion of patentability. Investigator identity, ownership and signatures are not invented.

## 1. Title of the invention:

ClaimAudit / ScopeGuard: Reusable Source-Interpretation Verification for Numerical Scientific Claims (research prototype using established methods).

## 2. Field /Area of invention:

Computer-assisted scientific claim verification; uncertain relational data; knowledge compilation; numerical predicate verification; reproducible evaluation of context-consistent evidence. Intended use: review a compound numerical assertion against a finite set of scientific table configurations and explicitly represented alternative source interpretations. Financial fraud is outside this project.

## 3. Prior Patents and Publications from literature (provide a table summarizing the prior art)

The following sources were opened during Stage 1 on 19 October 2026. Dates are publication/submission dates where verified. A missing feature means it was not established in the inspected material, not that the entire source legally excludes it. Abstract-only and date limitations are stated. The full search-query record and excluded URLs are in STAGE1_PRIOR_ART.md.

{chr(10).join(prior_table)}

Legal context: L01, official Guidelines for Examination of Computer Related Inventions (CRIs), 2025, sections 3.5/4.5 and separate novelty/inventive-step discussion: https://ipindia.gov.in/storage/uploads/docs-operator/7fdd559b-1ff8-4a87-8c36-033e7356b39b.pdf . L02, official PIB release, 29 July 2025: https://www.pib.gov.in/PressReleasePage.aspx?PRID=2149719 . Technical measurements do not by themselves establish eligibility, novelty or inventive step under Section 3(k).

## 4. Summary and background of the invention (Address the gap / Novelty)

Scientific claims may combine valid numbers taken from incompatible experimental configurations. ScopeGuard represents each admissible metadata interpretation explicitly and evaluates whether all numerical conditions can hold in one configuration. It distinguishes supported, contradicted, insufficient and ambiguous outcomes under a declared finite-domain policy. Its new code compiles this policy once into a BDD and uses restrictions to evaluate possible header clarifications.

Stage 1 found the core mechanisms already covered by P01-P08/P16, and close claim-verification applications in P09-P15/P18-P22. P18 is particularly close to the combined use case: relational numerical claims, probabilistic ambiguity, context and feedback. Stage 2 rejected three candidate novelty claims. No affirmative claim of novelty is made in this completed form.

The remaining research gap is empirical: under which structured-input conditions does reusable compilation reduce clarification cost, and when do simpler methods win? E1-E3 in Question 8 establish a limited measured engineering effect, not a technical feature absent from P04/P06/P16. Neither scientific terminology nor exact implementation differences establish patent novelty. The proposed journal contribution is a candid comparative study, benchmark and failure analysis; publication acceptance is unproven.

## 5. Objective(s) of Invention

Preserve experimental context across compound numerical conditions; expose verdict changes across admissible interpretations; reuse a compiled relation for conditional clarification queries; compare exact backends and document computation and memory costs; retain adverse cases and abstentions. These are research/engineering objectives, not statements that their underlying mechanisms are new.

## 6. Working principle of the invent (in brief)

Input consists of reviewed facts, numerical predicates, a finite set of contexts and mutually exclusive alternative fact groups. One Boolean selector represents each alternative; exactly-one constraints define admissible worlds. For each context and predicate the engine computes whether an observed value passes or fails. A world is supported when some single context satisfies every predicate. It is contradicted only when the declared domain is closed and every context has an observed violation. Otherwise it is insufficient. If different worlds yield different statuses, the overall answer is ambiguous. The compiled BDD shares these formulas; fixing a source-choice selector answers a proposed clarification without rebuilding the entire representation. A cheapest single clarification is suggested only if all its outcomes remove ambiguity; it is not a multi-step optimal policy.

## 7. Description of the invention in detail (Include drawing and or photograph as needed)

[DIAGRAM]

The pipeline is: manually reviewed source/table facts and predicates -> categorical source alternatives and context keys -> Boolean lineage with exactly-one constraints -> reusable BDD -> current verdict and conditional outcomes. Parallel adapters encode the same policy in ProbLog/PySDD and Z3, while exhaustive enumeration provides a small-instance oracle. These engines evaluate the same structured input; the diagram does not imply an automatic PDF extraction system.

Facts retain entity, metric, unit, exact numeric value, context and source locator. Input validation rejects conflicting values that can coexist at the same key. Numerical comparisons use exact decimal/rational values, not embedding thresholds. Choices are independent across blocks and mutually exclusive within each block; more general cross-block correlations are unsupported. Closed-domain contradiction applies only to the listed contexts. The paper fixtures deliberately limit that domain to selected rows.

Implementation: src/claimaudit/verification/compiled_scope.py contains reusable BDD compilation; src/claimaudit/evaluation/scope_backends.py contains the actual ProbLog, Z3, DP, rebuild and exhaustive adapters; src/claimaudit/evaluation/adversarial_benchmark.py isolates workers and records raw samples. tests/test_scope_backends.py tests equality across independently expressed engines. scripts/evaluate_local_scope_llm.py saves the optional local-model requests and responses. Exact paths and commands are preserved in CHANGESET.md and STAGE3_RESULTS.md.

Limits: no extraction recall evaluation, no guarantee that all plausible interpretations were captured, no calibrated probabilities, no arbitrary natural-language entailment, no automatic unit conversion, no optimum multi-step clarification plan, and no general polynomial complexity. BDD size may grow exponentially and depends on variable ordering. This extension does not replace the existing embedding/NLI project components; it evaluates an explicit structured subproblem.

## 8. Experimental validation results:

E0: 90 tests passed. E1: all six engines matched 36/36 reserved input labels; there were zero discrepancies in initial and single-choice conditional statuses against exhaustive verification where exhaustive completed. The 24 topology inputs use an existing exhaustive oracle; 12 paper-table fixtures were assistant-annotated from Attention Is All You Need, Table 3, and Deep Residual Learning for Image Recognition, Table 6. Independent human annotation remains absent.

E2 - reserved topology cost, exact integer nanoseconds and bytes:

{table('heldout_topology')}

Times are sums of per-case medians from three isolated-process repetitions, including validation/compilation and all conditional queries; imports/startup are excluded. Compiled reuse reduced this aggregate relative to rebuilding, but this follows known BDD operations (P04/P06/P16). Its peak RSS is higher than rebuilding and original DP; no memory-saving claim survives.

E2 - paper fixtures, where repeated-query reuse has no advantage:

{table('heldout_paper')}

E3: Four adverse cases have 6, 10, 12 and 16 independent binary choices with distinct signatures. At 16, original DP was incomplete at its 5000-state cap and exhaustive was skipped above 4096 worlds. Compiled reuse, BDD rebuild, Z3 and ProbLog completed all four. Their adverse-16 median times were respectively 4464791, 60532125, 11274125 and 12451630959 ns. There were no final-run worker timeouts or errors. Favorable-16 also skipped exhaustive under the same cap; original DP took 113292 ns versus compiled reuse 1384083 ns. These adverse cases defeat DP merging, not BDD worst-case complexity. No result is extrapolated to larger instances.

{llm_text}

Paper claims are authored fixtures rather than claims of errors in the original papers. Local-model false supports, if present, require response-level analysis before attributing them to splicing. Strong-LLM comparison, larger independent annotation and relevant-environment validation remain missing. Neither this experiment nor the sources support a patentability conclusion.

Reproducibility: seed 20261019; Python {S['python']}; dd 0.6.0; Z3 4.15.4.0; ProbLog 2.3.0; PySDD 1.0.6. Frozen input SHA-256: {S['heldout_sha256']}. Raw solver samples, limits, hashes and all local-model responses are saved with the code. STAGE3_RESULTS.md contains commands and interpretation; no rounding or fabricated results were used.

## 9. What aspect(s) of the invention need(s) protection?

No presently demonstrated technical aspect is recommended as an established patent-novel claim. Candidates for professional assessment only: (i) the exact source-interpretation policy and its implementation boundary, assessed against P01-P08/P12/P18 and E1; (ii) the particular compile/restrict integration, assessed against P04/P06/P16 and E2-E3. Both failed this preliminary novelty screening. They are listed to make the assessment boundary explicit, not as proposed patent claims. A professional may assess claim scope, ownership and any additional unpublished technical material; none is presumed here.

Must NOT be claimed as new: BID/x-tuples, possible-world/certain-answer semantics, equivalent-state merging, BDD restriction, generic query-guided or budgeted cleaning, claim decomposition, numerical provenance, ambiguity reporting, general solver-assisted verification, generic explanation/gating, or the evidence-splicing failure mode. The ScopeGuard name and a measured speed difference do not establish invention. Copyright/licensing and dataset documentation are separate issues and do not cure the absence of patent novelty.

Open risks: some exact publication dates are unverified; certain sources were inspected only at abstract level; failed URLs were excluded rather than fabricated. Patent search used Google Patents and did not exhaust InPASS, PATENTSCOPE, Espacenet, families, claims, prosecution histories, non-English documents or unpublished applications. Independent annotation, strong-model evidence, extraction robustness and BDD-hard cases remain missing. Consult the institutional IP cell/professional about disclosure timing before any public manuscript, repository or demonstration; prior public disclosures by others or the user have not been audited. No public release or patent filing was performed in this task.

## 10. What is Technology readiness level of your invention? (Tick the appropriate TRL)

[TRL_CHECKBOXES]

TRL 3 - Experimental proof of concept. Selected because executable algorithms, cross-engine checks and limited controlled experiments exist. No real-environment validation is available. TRL 4-9 are not claimed; the existence of a demonstration UI does not establish operational readiness.
'''
if llm and llm['false_support']==0:
    form=form.replace('Local-model false supports, if present, require response-level analysis before attributing them to splicing.', 'No false-support verdict occurred in this run; the targeted splicing error was not demonstrated. Invalid responses are a separate budget/format failure.')
(D/'STAGE4_COMPLETED_IDF_B.md').write_text(form)
# Preserve raw measured evidence with the review, independent of ignored results folders.
for name in ('summary.json','measurements.jsonl'):
    (D/('solver_'+name)).write_bytes((ROOT/'results/adversarial_v2'/name).read_bytes())
if llm:
    for name in ('summary.json','protocol.json','responses.jsonl'):
        (D/('ollama_'+name)).write_bytes((ROOT/'results/ollama_scope_v2'/name).read_bytes())
print('Generated Stage 3 and Stage 4 text; LLM complete:',bool(llm))
