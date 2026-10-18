# ClaimAudit: novelty assessment and research decision

Assessment date: 18 October 2026. Scope: scientific-claim verification, not financial fraud. This is a preliminary public-source technical assessment, not a patentability, infringement or freedom-to-operate opinion.

## Decision

**No candidate has yet passed the user's novelty condition for implementation as a patent-oriented extension.** The existing ClaimAudit remains a useful research prototype. Its current numerical/comparison checks should not be described as a proven patentable invention. No new verification algorithm was implemented in this assessment. A more specific candidate is defined below for further search and evaluation, but adding a new name or combining known techniques does not establish an inventive step.

The working repository is `/Users/somyadeeptarat/Desktop/Claim`. The restored repository's existing 69 tests passed on 18 October 2026. All six artifacts listed in `results/controlled_v1/complete.json` passed SHA-256 verification. These checks verify existing software/artifact integrity, not novelty or new model performance.

## What the existing method actually establishes

ClaimAudit compares an embedding baseline, NLI, and NLI with entity/metric/unit-aligned numerical and comparison checks. The structural layer only vetoes NLI support; it does not recover supported claims rejected by NLI. Its grammar abstains on unmodeled context and many complex scientific statements. Gold labels are unavailable at inference.

The recorded 60-case synthetic test evaluation has binary macro-F1 0.540 (embedding), 0.635 (NLI), and 0.700 (full hybrid). Four numerical errors were corrected; comparison checks added no correction. Support recall remained 0.333 and the paired improvement interval included zero. The 300-example dataset is synthetic; only three test families are independent clusters. These results motivate research but establish neither general scientific-paper accuracy nor novelty. This assessment did not rerun inference or modify those results.

## Ideas screened out as broad novelty claims

| Idea | Why it is not a sufficient novelty claim |
| --- | --- |
| Decompose answers into claims, verify with evidence | RefChecker and RT4CHART already cover fine-grained evidence-grounded verification [P1, P5]. |
| Check numbers, units, rounding and tolerances; issue a certificate | Proof-Carrying Numbers already specifies mechanical numeric policies and verified presentation [P2]. |
| Check every constraint in a compound scientific claim | Compositionally infeasible claim checking is explicitly studied in [P3]. |
| Use an LLM with a logical solver | Patent publication [P7] contains relevant independent claims; a solver wrapper is not enough. |
| Emit proof-backed decisions with source scope and abstention | EG-VAR is close prior art [P4]. Its advertised guarantees must still be read within its assumptions. |
| Test all possible evidence interpretations | Certain-answer semantics for incomplete databases is established [P9]. |
| Retrieve a minimal supporting set | Minimal evidence groups are already studied [P6]. |
| Change metrics, improve F1, or create another benchmark | Useful experimental work, but those changes alone do not establish a patentable technical invention. |

## Candidate for further investigation

**Scope-consistent evidence binding with ambiguity-directed source expansion.**

The use case is auditing AI-written research comparisons that combine measurements from incompatible settings: different datasets, experimental runs, hardware, populations, checkpoints, denominators or measurement definitions. A citation and individually correct values may still fail to support their claimed conjunction.

Illustrative complete table (not an experimental result):

| Model | Experiment | Accuracy | Latency |
| --- | --- | --- | --- |
| A | X | 90% | 20 ms |
| A | Y | 80% | 2 ms |

Claim: "In a single evaluated configuration, A achieved at least 90% accuracy and latency at most 2 ms."

Independent checks can find 90% and 2 ms. A joint check must bind both measurements to the same configuration: neither X nor Y satisfies both. If the table is explicitly complete for the cited configurations, that existential claim is contradicted within that scope. If only excerpts are supplied, the absence of a matching row means insufficient evidence, not proof that no such configuration exists. A claim explicitly comparing different configurations must be permitted to bind different contexts.

The narrower candidate is the operational interaction between binding disagreement, targeted retrieval of missing scope metadata, and dependency-aware revalidation. It is a research hypothesis, **not** an established inventive distinction. Relational joins, possible worlds, query planning, counterexamples, caches, and active information acquisition are individually known; their straightforward combination may be obvious.

### Concrete proposed operation

1. Build reviewed evidence records with document/version, source span, entity, metric, value/unit and context identifiers. Preserve alternatives for genuinely ambiguous header or footnote bindings. Missing fields are unknown, not wildcards that permit arbitrary joins.
2. Translate a claim into atomic predicates plus explicit shared-context constraints. Require a reviewed structured input initially. Do not claim automatic PDF or language interpretation is solved.
3. Enumerate consistent bindings within a bounded evidence bundle, or use a constraint solver. Separate binding uncertainty from measurement uncertainty. A confidence interval is not a hard bound on the true parameter; rounded values require an explicit rounding policy.
4. For each admissible interpretation, assess the whole proposition. A support decision requires evidence for every predicate under its proper quantifier and scope. Refutation requires explicit incompatible facts or a justified completeness declaration. Other cases remain insufficient or ambiguous. An inconsistent evidence bundle gets its own conflict status rather than logical explosion.
5. If interpretations yield different outcomes, identify their differing context attributes and point to an obtainable header, caption, methods passage or footnote that could settle those attributes. Do not ask for evidence that cannot distinguish the outcomes. Use a bounded, declared acquisition budget; do not invent outcome probabilities.
6. After acquiring that actual source fragment, validate the binding update and recompute affected claims. Track dependencies on both existing records and candidate-selection predicates, so a newly inserted conflicting record cannot leave a stale support decision. Fall back to complete recomputation when dependency coverage is uncertain.
7. Record witnesses, unresolved bindings, source offsets, policies, and versions for replay. A hash detects changes relative to a trusted digest; it does not establish source truth or semantic extraction correctness.

### Candidate technical effect to measure

At equal false-support risk and supported-case coverage, does targeted scope resolution read fewer source tokens or invoke fewer model calls than full-context verification? Does dependency-aware revalidation reduce repeated work without any divergence from full recomputation after additions, corrections or deletions? No such benefit has been measured yet.

## Prior-art table

| ID and source | Verified overlap | Consequence for the candidate |
| --- | --- | --- |
| P1. [RefChecker, 2024](https://arxiv.org/abs/2405.14486) | Claim-triplet extraction and reference-based fine-grained checking. | Atomic claims and explanations are not new; compare against context-preserving decomposition. |
| P2. [Proof-Carrying Numbers, 8 September 2025](https://arxiv.org/abs/2509.06902) | Numeric spans bound to structured claims; unit normalization, equality, rounding, aliases and qualified tolerance checks. | Do not claim numerical verification, provenance tokens or a verified badge as new. |
| P3. [When Verification Fails, 13 April 2026](https://arxiv.org/abs/2604.10990) | Studies failure to enforce all constraints in compositionally infeasible scientific claims. | A compound-claim benchmark alone is not enough; scope binding must show a distinct mechanism and benefit. |
| P4. [EG-VAR, 14 July 2026](https://arxiv.org/abs/2607.12650) | Tool-attested, kernel-checked empirical reasoning with declared source scope, proof obligations and abstention. | Close overlap with formal sidecars/certificates. Full comparison of ambiguity and source-lift handling is essential. |
| P5. [RT4CHART, March 2026; revised July 2026](https://arxiv.org/abs/2603.27752) | Claim decomposition, local-to-global context verification and evidence/answer spans. | Hierarchical verification and span-level diagnostics are established. |
| P6. [Minimal Evidence Group Identification, 2024 preprint](https://arxiv.org/abs/2404.15588) | Identifies sets of evidence that jointly support claims. | Minimal evidence selection is established; distinguish metadata disambiguation from supporting-set selection. |
| P7. [US20260127386A1, published 7 May 2026](https://patents.google.com/patent/US20260127386A1/en) | Independent claim 1 uses an LLM to derive constraint representations, joint satisfiability and a generated response; claims 2-3 specify SMT. Independent claim 5 concerns conditional statements and language-model output. | Solver-assisted reasoning is close prior art. Compare every essential claim element; this table does not establish avoidance or non-infringement. |
| P8. [US20250077940A1, published 6 March 2025](https://patents.google.com/patent/US20250077940A1/en) | Independent claim 1 covers model interrogation with a positive/negative verification prompt and conditional output; claims 5-6 add iterative improvement. | Generic verify-then-output and retry loops are not a safe novelty basis. |
| P9. [Certain answers as objects and knowledge, Artificial Intelligence, 2016](https://doi.org/10.1016/j.artint.2015.11.004) | Query answering under incomplete information; answers across possible interpretations. | Universal interpretation checking is a known foundation, not a new algorithm by itself. |
| P10. [Towards Robust Numerical Claim Verification, September 2026](https://arxiv.org/abs/2610.00689) | Adversarial fine-tuning on numerical perturbations. | Numerical sensitivity training and synthetic perturbations require differentiation too. |

Search also surfaced EP4372660A1; inspection showed employment/data-assertion verification rather than scientific numeric hallucination checking. It is not treated as a close comparator merely because its title says "Verifying data". Third-party patent legal-status labels were not treated as legal conclusions.

## Search scope and remaining uncertainty

Public web searches covered numeric hallucination, rounding, counterfactual claim verification, scope/context binding, formal constraint solvers, proof-carrying outputs, evidence groups and incomplete-database certain answers. Primary publication abstracts/full text and the relevant published patent claim sections above were inspected. This is not an exhaustive patent search. No private paper or user document was uploaded to a search service.

Further searches must include schema/column disambiguation, provenance-aware joins, active schema matching, query-driven document expansion, incremental view maintenance and semantic cache invalidation. Review cited/citing documents, patent families, priority/publication chronology, prosecution history and equivalent claims across jurisdictions. A phrase search yielding no exact match is not novelty clearance. Unpublished applications and unindexed material remain unknown.

India is a provisional jurisdiction assumption, not a confirmed filing instruction. [IP India](https://ipindia.gov.in/basics-of-patents) requires novelty, inventive step, industrial applicability and exclusion review. [Section 3(k)](https://ipindia.gov.in/acts/patent-act-1970/section-3) is relevant to mathematical/business methods, algorithms and computer programs per se. Assess the actual technical contribution using the [current official CRI guidance](https://ipindia.gov.in/resource/patents-resources-guidelines); a generic computer or higher accuracy alone does not settle eligibility. Human inventorship, ownership and earlier disclosure dates require actual contributor records and professional review.

## Proposed experiment before any superiority claim

Create a new document-level split, with independent annotation of the full claim, source spans, scope bindings, completeness and ambiguity. Keep the old inspected synthetic set as regression material. Include correct multi-setting comparisons so the method cannot win merely by rejecting every compound claim.

Compare: original NLI; original hybrid; atom-wise verification; deterministic exact-context joins; full-context verification; candidate binding analysis without source expansion; candidate plus budgeted expansion. Use equal evidence and model backbones where applicable. Compare expansion with random available fragments, nearest-context fragments and generic uncertainty-driven acquisition at equal budgets. A simple join is a particularly important baseline.

Include same values across different datasets, hardware/run mismatches, omitted headers, contradictory corrections, legitimate cross-study comparisons, missing context, correlated evidence, interval/rounding ambiguity and fully supported claims. Separate structured-input evaluation from automatic extraction evaluation. Do not turn missing evidence into a contradiction label.

Measure false-support rate, support recall, macro-F1 under a stated label mapping, abstention/coverage curves, scope-binding accuracy, source tokens and model calls per resolved claim, and p50/p95 latency. Bootstrap at paper level. Verify cached and fully recomputed outputs are identical under new matching records, corrections and deletions. Report extraction failures and query failures, not just successful cases.

Pre-register a practical cost-reduction target and acceptable false-support/coverage margins with the intended user before held-out evaluation. These are not fixed here because no deployment budget or risk tolerance was supplied. Reject the extra mechanism if exact-context joins plus ordinary retrieval perform as well.

## Gate status and implementation boundary

| Gate | Current status |
| --- | --- |
| Concrete use case and executable design specification | Defined as a proposal |
| Current ClaimAudit software and historical artifact integrity | Verified; 69 tests pass |
| New method experimentally validated | Not implemented; no new results |
| Improvement over strong/simple baselines | Not demonstrated |
| Novelty / inventive step | Unresolved; material close prior art |
| India eligibility / freedom to operate | Not determined |
| User's novelty-conditioned implementation gate | Not passed |

No deployment, patent filing, public publication or external submission is authorized or performed by this work. The disclosure draft is a discussion document for the institution's IP cell, not a declaration that the candidate is novel. If the user later chooses an exploratory research implementation irrespective of patent clearance, build it in a separate experimental module with these baselines and limitations preserved.
