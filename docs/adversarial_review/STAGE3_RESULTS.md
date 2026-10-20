# Stage 3 - Measured research evaluation

Completed 20 October 2026 (India). This extension applies known BDD compilation and restriction. It is NOT a newly established invention. Stage 2 rejected all three novelty candidates before implementation. The code is useful for reproducible research on context-preserving numerical verification.

## Protocol and checkpoints

E0: 90 unit/integration tests passed in the complete suite. This includes seven new backend tests covering exact rational probabilities, mixed statuses, independent encodings, randomized development inputs, source restrictions and a rare supported world (1/4096). A development-only 20-choice ProbLog conditional-query test was stopped because it was too slow; it was replaced by a bounded 12-choice single-query unit test before reserved evaluation. No reserved cases were removed.

E1: 36 inputs were frozen before new backend evaluation: 24 sparse three-way topologies, plus 12 manually transcribed claims from two real paper tables. The topology family differs from the original six development templates. Gold for synthetic inputs comes from the pre-existing exhaustive oracle. Paper annotation is by the assistant with visual source checks, not independent human review. The same assistant designed both the method and evaluation; this is an internal reserved set, not a blinded external benchmark. Source extraction accuracy is not measured.

All six engines completed and matched all 36 labels. Initial and every single-choice conditional status matched exhaustive outputs where exhaustive ran; disagreements recorded: 0. Agreement checks implementations of a shared policy; it does not validate the policy as scientific truth or establish generalization to arbitrary papers.

E2: Every case ran in an isolated process with three repetitions; reported time is the exact integer median in nanoseconds. Times include validation, construction/compilation, the initial status and all single-choice conditional statuses when ambiguous. Imports and process startup are excluded. The compiled implementation additionally computes its clarification recommendation; some conditional work is repeated there. No model generation ran concurrently with solver timing. Engine order is shuffled with seed 20261019. Raw samples, all inputs, code hashes and package versions are saved. No extrapolation or rounded speedup is reported.

Real baselines: ProbLog 2.3.0 with PySDD 1.0.6 evaluates annotated-disjunction possible worlds using exact rational weights; Z3 4.15.4.0 uses one-hot categorical variables, exact numerical comparisons and incremental satisfiability checks; the existing exhaustive engine enumerates worlds. Scope DP is the original signature-merging implementation. BDD rebuild is a controlled ablation, not an independent state-of-the-art baseline. Compiled reuse uses dd 0.6.0. Uniform ProbLog priors are counting weights, not calibrated confidence. The ProbLog adapter rebuilds each conditional problem; a tuned incremental ProbLog integration could change the comparison. Library-language overhead also differs.

### Reserved topology inputs (24)

| Engine | Correct / completed / total | Sum of case median times (ns) | Max process RSS (bytes) |
| --- | --- | --- | --- |
| scope_dp | 24 / 24 / 24 | 26714833 | 24608768 |
| bdd_rebuild | 24 / 24 / 24 | 104202459 | 38715392 |
| compiled_reuse | 24 / 24 / 24 | 24968876 | 39370752 |
| z3 | 24 / 24 / 24 | 124363956 | 53886976 |
| problog | 24 / 24 / 24 | 2516006750 | 198213632 |
| exhaustive | 24 / 24 / 24 | 107458539 | 24264704 |

The sum of medians is 24968876 ns for compiled reuse versus 104202459 ns for BDD rebuild, 26714833 ns for original DP, 124363956 ns for Z3, 2516006750 ns for this ProbLog adapter and 107458539 ns for exhaustive evaluation. This is an aggregate of individual medians, not an end-to-end elapsed time. No confidence interval or statistical significance is claimed. Generic BDD operations (P04/P06/P16) already explain the reuse mechanism; measured reduction does not rescue novelty.

### Reserved real-paper fixtures (12)

| Engine | Correct / completed / total | Sum of case median times (ns) | Max process RSS (bytes) |
| --- | --- | --- | --- |
| scope_dp | 12 / 12 / 12 | 433207 | 24150016 |
| bdd_rebuild | 12 / 12 / 12 | 889793 | 39141376 |
| compiled_reuse | 12 / 12 / 12 | 914541 | 38977536 |
| z3 | 12 / 12 / 12 | 10831750 | 53641216 |
| problog | 12 / 12 / 12 | 93755334 | 194035712 |
| exhaustive | 12 / 12 / 12 | 147417 | 23904256 |

These fixtures contain no alternative source interpretations. Reuse offers no repeated-query advantage: its 914541 ns aggregate exceeds exhaustive's 147417 ns, original DP's 433207 ns and BDD rebuild's 889793 ns. Perfect correctness on 12 hand-selected, structured fixtures is not evidence of end-to-end PDF verification accuracy.

### Adverse signature-state growth (4)

| Engine | Correct / completed / total | Sum of case median times (ns) | Max process RSS (bytes) |
| --- | --- | --- | --- |
| scope_dp | 3 / 3 / 4 | 97678416 | 27000832 |
| bdd_rebuild | 4 / 4 / 4 | 105881209 | 39305216 |
| compiled_reuse | 4 / 4 / 4 | 10091499 | 39550976 |
| z3 | 4 / 4 / 4 | 28861249 | 54214656 |
| problog | 4 / 4 / 4 | 14324801085 | 249069568 |
| exhaustive | 3 / 3 / 4 | 622475833 | 24313856 |

E3: At 6, 10, 12 and 16 independent binary choices, every full pass/fail signature differs, so original DP cannot merge those states. At 16 choices it returns incomplete under the 5000-state cap. Exhaustive returns skipped under the 4096-world cap, on both adverse-16 and favorable-16; skipped is not a correctness result or measured runtime of verification. All other engines completed, including ProbLog: there were zero worker timeouts and zero errors in this final run. ProbLog adverse-16 median was 12451630959 ns. The initial slow development test must not be mislabeled as a benchmark timeout.

These inputs defeat the original DP compression but have simple Boolean structure; they are not worst cases for BDD size. This experiment does not demonstrate immunity to exponential BDD growth. Broader variable-order and hard Boolean-lineage benchmarks remain missing.

### Favorable irrelevant-choice controls (4)

| Engine | Correct / completed / total | Sum of case median times (ns) | Max process RSS (bytes) |
| --- | --- | --- | --- |
| scope_dp | 4 / 4 / 4 | 334334 | 23773184 |
| bdd_rebuild | 4 / 4 / 4 | 3271167 | 38862848 |
| compiled_reuse | 4 / 4 / 4 | 3137209 | 39321600 |
| z3 | 4 / 4 / 4 | 4377250 | 53297152 |
| problog | 4 / 4 / 4 | 31037291 | 193839104 |
| exhaustive | 3 / 3 / 4 | 6310208 | 24363008 |

Original DP is faster on each favorable control. For favorable-16 it takes 113292 ns versus compiled reuse 1384083 ns. This is a measured case where compiling and preserving choices costs more than direct signature merging.

Peak RSS includes interpreter, imported libraries and retained memory across repetitions within one worker. Compiled reuse's topology peak (39370752 bytes) exceeds BDD rebuild (38715392 bytes) and original DP (24608768 bytes). No memory improvement is established. These process peaks are not allocator-level algorithm measurements.

## Optional local model

E4: Local Ollama qwen3:4b (4B, Q4_K_M), one zero-shot prompt, seed 20261019, temperature 0, thinking enabled, 2048 generated-token cap, 8192 context cap. Correct 8/12; false supports 0; invalid/error outputs 4. Full requests, responses, timing/token metadata, model digest and protocol are saved. This is NOT a strong/frontier-model test; its results cannot be generalized to stronger models. No prompt tuning or retries were used. Invalid outputs count as incorrect under this fixed budget, not as demonstrated semantic errors or evidence splicing.

| Fixture | Expected | Output | Stop reason |
| --- | --- | --- | --- |
| transformer-0 | supported | supported | stop |
| transformer-1 | contradicted | contradicted | stop |
| transformer-2 | supported | supported | stop |
| transformer-3 | contradicted | contradicted | stop |
| transformer-4 | insufficient | invalid | length |
| transformer-5 | contradicted | invalid | length |
| resnet-0 | supported | supported | stop |
| resnet-1 | contradicted | invalid | length |
| resnet-2 | supported | supported | stop |
| resnet-3 | contradicted | contradicted | stop |
| resnet-4 | insufficient | invalid | length |
| resnet-5 | contradicted | contradicted | stop |

No false-support verdict was observed in this run. The targeted evidence-splicing error was therefore not demonstrated for this model under this protocol; invalid outputs are a different failure.

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

Use fresh output directories: benchmark and LLM scripts refuse to overwrite measurements. To execute the complete existing application tests, also install the app/models extras if they are not already installed; see pyproject.toml. Solver experiments use Python 3.12.11 on macOS-15.7.4-arm64-arm-64bit. Local timing will vary. The Ollama model must already be installed; no download is performed by the script.

Frozen input SHA-256: 02e1ded15415be7e90f95bc28da336cf6f7567e55fd69526bef3f35da60528c4

Full benchmark input SHA-256: 1911fd611ca7a226c6f7c74b6e3e92eb49e684a7add5f9555075fd09cf98d61e

Measurement JSONL SHA-256: bd9070d5d2f0d73779a8933ced994e5da0fefbca0f93799906b01f72bc105d4e

All numeric tables are generated from results/adversarial_v2/summary.json. Raw per-case observations are in measurements.jsonl. A preserved copy of the measurement files accompanies this report for audit. No publication, deployment, filing or public release was performed.
