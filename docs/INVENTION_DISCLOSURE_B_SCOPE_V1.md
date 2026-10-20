# ScopeGuard invention disclosure response

19 October 2026. Response annex mapped to all ten questions in VIT IDF-B, Document 02-IPR-R003, Issue 2 / 01.02.2024. Research prototype implemented; patent novelty and inventive step remain unresolved. This annex preserves the original blank form. The 18 October draft describes an earlier proposal and is superseded for implementation status.

## 1. Title of the invention

Context-Consistent Scientific Claim Verification with Correlated Source Interpretations and Decision-Sufficient Clarification.

Working implementation name: ScopeGuard, an experimental extension to ClaimAudit. The title does not assert patentability.

## 2. Field / area of invention

Scientific document analysis, evidence-grounded natural-language systems, structured numerical verification and research-assistant software. The immediate use case is checking whether a generated scientific comparison combines measurements from incompatible experiments or alternative interpretations of table metadata.

## 3. Prior patents and publications from literature

| Prior art | Relevant established mechanism | Distinction to investigate |
| --- | --- | --- |
| RefChecker, 2024 [1] | Fine-grained claims and evidence verification | Preserve shared experimental context across predicates |
| Proof-Carrying Numbers, 2025 [2] | Source-referenced numerical verification | Joint context compatibility, not numerical matching alone |
| When Verification Fails, 2026 [3] | Failure on compound scientific constraints | Correlated source alternatives and exact binding analysis |
| EG-VAR, 2026 [4] | Tool-grounded proofs and evidence scope | Bounded alternative bundles and header clarification |
| Certain answers, 2016 [5] | Certainty over incomplete information | Application-specific implementation; foundations already known |
| AmbiFC, 2021 [6] | Ambiguous claims and evidence-based verdicts | Source metadata alternatives, not ambiguity alone |
| Claim Cards, 14 Oct 2026 [7] | Explicit scientific interpretations and verdict changes | All enumerated source bindings and decision-sufficient acquisition |
| US20260127386A1 [8] | Language-model constraint/theory solving | Narrow source-binding mechanism requires claim-level review |
| US20250077940A1 [9] | Verification and conditional answer output | Generic verification and retry are not claimed new |

These differences are hypotheses, not findings of novelty or non-infringement. Exact joins, dynamic programming, provenance and uncertainty reasoning are established. Search is preliminary and not a patent clearance opinion.

## 4. Summary and background of the invention

ClaimAudit already compares embeddings, NLI, and NLI combined with numerical/comparison checks. The remaining problem is evidence splicing: independently valid measurements can be combined into a claim that no single experiment supports. Ambiguous source metadata can also produce mutually exclusive interpretations that must not be pooled.

Example: configuration X reports 90% accuracy at 22 ms, while Y reports 80% accuracy at 2 ms. The claim that one configuration achieves at least 90% accuracy at at most 2 ms has no joint witness. Complete declared experimental coverage allows contradiction; partial evidence only permits an insufficient-evidence result.

The candidate contribution is a bounded verification workflow that retains correlated source alternatives, checks joint support across all admissible interpretations, merges decision-equivalent states, and identifies a source clarification sufficient to remove verdict ambiguity. Its distinctiveness over the cited work is unproven. The implemented result is an engineering proof of concept, not a new general reasoning algorithm.

## 5. Objectives of invention

- Detect cross-experiment and mutually exclusive evidence splicing.
- Avoid converting missing measurements into contradictions.
- Preserve uncertainty when plausible source interpretations produce different decisions.
- Reduce repeated computation for interpretations with identical satisfaction states.
- Identify a single obtainable metadata clarification that settles interpretation-dependent decisions.
- Produce reproducible records and a transparent researcher-facing demonstration.

## 6. Working principle in brief

A reviewer supplies numerical claim predicates, context IDs, source-linked facts and mutually exclusive alternative bundles. The system checks the whole conjunction in each interpretation through an exact state-merging algorithm. It returns supported, contradicted, insufficient or ambiguous, with incomplete on a state-budget limit. For ambiguity, it conditionally resolves each header and recommends the cheapest header whose every outcome settles the decision. A person reviews the source; the engine recomputes the result.

## 7. Description of the invention in detail

```text
Reviewed claim predicates + source-linked measurements
                         |
Explicit contexts + correlated alternative bundles
                         |
Per-context passing / failing predicate signatures
                         |
Exact combination and merging of identical states
                         |
Unanimous verdict OR interpretation-dependent ambiguity
                         |
Test each available single-header clarification
                         |
Human reviews source -> updated input -> recomputation
                         |
Replay record + representative bindings + input digest
```

Input values use exact decimal strings and exact units. Each claim asserts that one listed context meets all threshold predicates. Exactly one alternative in each block applies; correlated uncertainties must reside in the same block. The current implementation does not extract these records from arbitrary PDFs or support universal claims, cross-context comparisons, statistical significance or implicit unit conversion.

A state holds passing and failing predicate masks for each context. Combining facts is bitwise union; merging identical masks preserves all future decisions. The engine counts merged interpretations and retains representative bindings. Counts are not probabilities. Worst-case state growth remains exponential, and exceeding the configured cap produces no substantive verdict.

Contradiction requires an explicit exhaustive-domain declaration and an observed failing condition in every context. Potentially coexisting conflicting measurements are rejected as invalid input. The replay digest identifies the structured input; it does not prove source authenticity or constitute a formal proof certificate.

Clarification costs are declared positive integers. The implemented acquisition policy selects a cheapest sufficient single clarification; it is not an optimal multi-step policy. Retrieval, automatic header interpretation and incremental dependency invalidation are not implemented.

## 8. Experimental validation results

Measured locally on 19 October 2026. The new dataset has 300 synthetic cases from six parameterized families. It is a controlled engineering check, with no independent annotation or held-out paper evaluation.

| Method | Support accuracy | Qualification |
| --- | --- | --- |
| Atomic matching | 50.0% | Discards context |
| Flattened context join | 66.7% | Discards alternative exclusivity |
| Exhaustive verifier | 100.0% | Strong exact reference |
| ScopeGuard | 100.0% | Same correctness as exact reference |

All 300 intended four-way statuses and exhaustive outcome counts agree. A further 200 seeded random problems are checked against an independently implemented exhaustive reference in tests. A favorable stress example represents 1,048,576 interpretations with one signature per layer and 40 transitions; this is not a general speedup measurement.

Tests cover decimal equality, units, missing evidence, conflicting records, resource-limit abstention, replay modification detection, representative bindings, clarification selection and all six interactive scenarios. The validation manifest and reproducible commands are saved with the project. No new embedding/NLI accuracy comparison is claimed from this structured-input experiment.

Real-paper annotation, extraction-quality measurement, paper-level test splits, strong language-model comparison, adverse scaling cases and acquisition-cost evaluation remain necessary for a journal submission.

## 9. What aspects of the invention need protection?

Candidate for professional assessment: the specific sequence of correlated source-binding representation, exact joint-support evaluation, verdict-equivalent state merging, and decision-sufficient metadata clarification for scientific document verification. Any proposed claim must identify a technical distinction over existing uncertain-database reasoning, Claim Cards, numerical verification and solver-assisted systems.

Do not claim ownership of embeddings, NLI, generic numerical checks, all-world reasoning, dynamic programming, evidence provenance, clarification generally or cryptographic hashes. No claim set is proposed as filing-ready. Novelty, inventive step, industrial applicability and software eligibility require separate assessment; a completed disclosure is not patent approval.

The implemented prototype and its reproducible artifacts can support an institutional IP-cell discussion. Patentability remains unresolved rather than positively established by this search.

## 10. Technology readiness level

Suggested self-assessment: TRL 3, experimental proof of concept. A bounded engine, synthetic verification suite and interactive local demo exist. It has not been validated on independently annotated real scientific papers or in an operational research workflow. TRL 4 or higher is not justified by the current evidence.

## References

[1] RefChecker: https://arxiv.org/abs/2405.14486

[2] Proof-Carrying Numbers: https://arxiv.org/abs/2509.06902

[3] When Verification Fails: https://arxiv.org/abs/2604.10990

[4] EG-VAR: https://arxiv.org/abs/2607.12650

[5] Certain answers as objects and knowledge: https://homepages.inf.ed.ac.uk/libkin/papers/aij.pdf

[6] AmbiFC: https://arxiv.org/abs/2104.00640

[7] Same Claim, Different Interpretations: https://arxiv.org/abs/2610.20457

[8] Language model theory solvers: https://patents.google.com/patent/US20260127386A1/en

[9] Verification and conditional output: https://patents.google.com/patent/US20250077940A1/en

[10] Indian Patent Office, patent basics: https://ipindia.gov.in/basics-of-patents
