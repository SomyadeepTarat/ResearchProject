# ScopeGuard: context-consistent scientific claim verification

Implemented 19 October 2026 in ClaimAudit. Research candidate, not confirmed patent novelty.

## Problem and use case

A scientific literature assistant says one configuration delivers 90% accuracy and 2 ms latency. The paper reports 90% with 22 ms in X, and 80% with 2 ms in Y. Both quoted numbers are real, but their conjunction is not supported by one experiment. Even joining on a context name is unsafe if two mutually exclusive interpretations of a table header are flattened into a single evidence table.

The extension answers: does the entire reviewed claim have a joint witness in every admissible interpretation of the source? Intended use: auditing model-comparison paragraphs, literature-review tables and RAG answers before they are presented to a researcher. The original embedding, NLI and numerical/comparison pipelines remain available. This is a separate structured-input experiment; it has not yet been integrated into automatic claim extraction or evaluated against NLI on matched new examples.

## Implemented semantics

Input contains exact decimal strings, explicit entity/metric/unit/context records with source locators, claim threshold predicates, and blocks of alternative record bundles. Exactly one alternative per block applies. Blocks are independent; correlated uncertainties MUST be represented together in a single block. Context IDs must encode all relevant conditions, such as dataset, split, hardware, batch size and model version. The engine cannot discover omitted conditions.

The supported claim grammar is existential: there is a declared context satisfying every predicate. Operators are ==, >=, <=, > and <. Units require exact agreement; there is no implicit conversion, rounding tolerance, statistics, ratio arithmetic, universal quantification or free-text parsing. Legitimate comparisons across two contexts are outside this grammar, not classified as splicing.

For each interpretation:

- Supported: one context has positive observations satisfying all predicates.
- Contradicted: the user explicitly declares an exhaustive context domain and every context has an observed failing predicate.
- Insufficient: neither condition holds. Missing records never count as negative observations.

Across interpretations, return the unanimous status or ambiguous when statuses differ. Incomplete means the state budget was exceeded, not that the claim failed. Conflicting measurements that could coexist are rejected as invalid input, including conflicts in irrelevant records; they are not silently reconciled. This conservative policy can reject a bundle containing some valid interpretations.

The quantifier order is FOR EVERY source interpretation, THERE EXISTS a supporting context. A different witness may support the claim in different interpretations. This does not establish one identical context as a witness across all interpretations.

## Exact computation and explanation

For each context, encode the predicates with passing and failing observations as two bit masks. Compute each whole alternative's signature, then combine it with the signatures from preceding blocks using bitwise OR. Merge identical signatures, summing multiplicities and retaining one representative binding. Identical signatures have identical future decisions because future transitions only OR the same new observations into them. Induction over blocks establishes equivalence to exhaustive enumeration under the input restrictions.

Worst-case growth remains exponential. With C contexts and A predicates, a coarse bound is 2^(2CA) signatures, also bounded by the number of worlds. A 100,000-state cap returns incomplete. Validation, record encoding and clarification analysis also cost time; the state cap is not a complete time/memory sandbox.

The audit records policy version, input SHA-256, outcome counts, representative source bindings and state widths. Counts are combinatorial multiplicities, not probabilities. verify_replay recomputes the output from structured input. This detects modification relative to the supplied record; it is not a cryptographic attestation, independent formal proof or authentication of the original paper.

For an ambiguous result, the acquisition policy tries every alternative of every header. It recommends the cheapest single header for which every possible resolution leaves a unanimous status. It cannot choose the correct interpretation, fetch documents, guarantee support rather than insufficiency, or optimize a sequence of acquisitions. If no single header suffices, it returns no recommendation. Costs are user-supplied positive integers, not measured retrieval times.

## Measured engineering results

Run: 19 October 2026, Python 3.12, local CPU. 300 generated examples comprise six families with 50 parameter variations each. They are not 300 independent experimental sources and have no held-out split. Gold statuses are author-assigned by construction.

| Method | Binary support accuracy | Interpretation |
| --- | --- | --- |
| Independent atomic number matching | 50.0% | Diagnostic baseline discards context and alternatives |
| Context join with flattened alternatives | 66.7% | Diagnostic baseline preserves context but loses exclusivity |
| Exhaustive interpretation verification | 100.0% | Strong reference with the same reviewed inputs |
| ScopeGuard signature merging | 100.0% | Matches the exact reference; no accuracy advantage over it |

ScopeGuard matches all 300 intended four-way statuses and all exhaustive outcome counts. The tests also compare 200 seeded random problems against an independently written exhaustive implementation. A constructed stress case with 20 irrelevant binary choices represents 1,048,576 worlds with one signature per layer and 40 transitions. This demonstrates a favorable case, not a general runtime speedup. Per-case local timings are recorded without a speedup claim. Existing ClaimAudit NLI metrics are not evidence for this extension.

## Novelty assessment

The research hypothesis is that explicitly preserving correlated source interpretations prevents evidence-splicing errors, while merging equivalent satisfaction states reduces repeated reasoning and decision-sufficient clarification avoids irrelevant source inspection. This combination and its empirical value need evaluation; no claim of first invention is justified.

Known overlap includes claim decomposition (RefChecker), numerical provenance (Proof-Carrying Numbers), compound-constraint errors (When Verification Fails), formal evidence scope (EG-VAR), certain answers in incomplete databases, and ambiguous fact-checking (AmbiFC). Dynamic programming and exact joins are established algorithms. A new name or their combination is not itself proof of inventive step.

The 14 October 2026 paper Same Claim, Different Interpretations explicitly records claim interpretations and studies changes to verification decisions. Our bounded source-alternative representation and exhaustive decision-sufficient header selection differ operationally from its Claim Cards, but this is a proposed distinction, not a legal novelty conclusion. It must be included in further comparison.

US20260127386A1 describes language-model theory solvers; generic joint constraints are not a defensible broad claim. US20250077940A1 describes answer verification and conditional output. Search coverage is incomplete: patent families, prosecution, non-English material and unpublished applications were not exhaustively examined. No freedom-to-operate opinion is provided.

## Journal validation protocol (not yet performed)

1. Collect a licensed paper-derived corpus from at least 30 independent papers, preserving table crops, captions, headers and exact source offsets. Stratify by explicit context, missing context, correlated ambiguity and genuine cross-context comparison.
2. Use two independent annotators and adjudication. Record claim quantifier, context equality, completeness declarations, all defensible interpretations, rationale and disagreements. Review automatic extraction separately from verification.
3. Freeze train/dev/test splits by paper; keep perturbation siblings together. Freeze rules on development papers before opening test labels.
4. Compare the existing embedding/NLI/hybrid methods, exact context joins, exhaustive reasoning and a documented strong LLM verifier on equivalent source information. Separate oracle-reviewed input from end-to-end extracted input.
5. Report support precision/recall, four-way confusion, abstention coverage, ambiguity detection, false support on splices, and paper-clustered confidence intervals. Include well-formed legitimate comparisons as negative controls.
6. Measure exact agreement and runtime/memory across increasing relevant uncertainty, not only irrelevant choices. Compare clarification against cheapest-first and random acquisition; report actual reading/token cost and unresolved rate.
7. Publish failures and scope restrictions. A method paper needs evidence beyond this synthetic demonstration; neither acceptance nor a patent can be inferred from passing tests.

## Reproduction

From /Users/somyadeeptarat/Desktop/Claim:

```bash
.venv/bin/python -m unittest discover -s tests -q
.venv/bin/python -m claimaudit.evaluation.scope_benchmark
.venv/bin/python -m streamlit run app/streamlit_app.py
```

Choose Scope audit (experimental). Inspect all six scenarios, switch the reviewed header interpretation, and download the replay record. Benchmark output is in results/scope_v1; the dataset is data/scope_v1/cases.jsonl. These outputs are distinct from results/controlled_v1.

## Sources

- RefChecker: https://arxiv.org/abs/2405.14486
- Proof-Carrying Numbers: https://arxiv.org/abs/2509.06902
- When Verification Fails: https://arxiv.org/abs/2604.10990
- EG-VAR: https://arxiv.org/abs/2607.12650
- Certain answers as objects and knowledge: https://homepages.inf.ed.ac.uk/libkin/papers/aij.pdf
- AmbiFC: https://arxiv.org/abs/2104.00640
- Same Claim, Different Interpretations: https://arxiv.org/abs/2610.20457
- Language model theory solvers: https://patents.google.com/patent/US20260127386A1/en
- Answer verification: https://patents.google.com/patent/US20250077940A1/en
- Indian Patent Office basics: https://ipindia.gov.in/basics-of-patents

Search update: 19 October 2026. Queries included claim verification plus possible worlds, header ambiguity, evidence context and patents. The earlier 18 October assessment is historical; this document supersedes its implementation status, not its prior-art cautions.
