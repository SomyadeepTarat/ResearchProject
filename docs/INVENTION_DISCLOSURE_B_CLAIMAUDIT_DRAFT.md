# Invention Disclosure Format B - ClaimAudit research draft

18 October 2026. Prepared against the ten questions in VIT document 02-IPR-R003, Issue 2 / 01.02.2024. For technical/IP-cell discussion only. The new candidate is a proposal: novelty is unresolved and implementation has not passed the user's novelty condition. The existing ClaimAudit prototype is distinguished from the proposed extension throughout.

## 1. Title of the invention

Scope-Consistent Scientific Claim Verification with Ambiguity-Directed Source Expansion.

This is a working research title, not a claim of granted or established patentability.

## 2. Field / area of invention

Natural language processing, evidence-grounded scientific summarization, document information extraction, constrained claim verification and retrieval systems. Intended users include researchers auditing AI-written comparisons of models, methods or experiments. The system checks whether supplied sources support a claim; it does not certify that a paper's findings are scientifically true.

## 3. Prior patents and publications from literature

| Prior art | Established overlap | Candidate distinction requiring assessment |
| --- | --- | --- |
| RefChecker (2024), P1 | Fine-grained reference-based claim checking | Shared experiment bindings, not claim decomposition alone |
| Proof-Carrying Numbers (2025), P2 | Numeric policies, claim references and verified output | Joint context consistency and missing-context resolution, not numerical certificates |
| When Verification Fails (2026), P3 | Compound scientific constraints and compositional errors | Operational binding diagnosis and source-expansion policy, not simply checking every clause |
| EG-VAR (2026), P4 | Source scope, formal proofs, tool evidence and abstention | Close overlap; ambiguity-directed acquisition/revalidation must be compared in detail |
| RT4CHART (2026), P5 | Local/global verification and evidence spans | Context-binding ambiguity, not hierarchical verification itself |
| Minimal Evidence Group Identification (2024), P6 | Joint supporting evidence sets | Resolve a missing context binding rather than simply find a supporting set |
| US20260127386A1 (2026), P7 | LLM constraint representations, joint satisfiability and generated output | The proposed source-binding operation needs element-by-element claim assessment |
| US20250077940A1 (2025), P8 | Verification prompts, conditional output and iterative improvement | Generic verification/retry is already disclosed |
| Certain answers as objects and knowledge (2016), P9 | Query certainty under incomplete information | All-interpretation reasoning is an established foundation |
| Towards Robust Numerical Claim Verification (2026), P10 | Training on numerical counterfactual perturbations | Numerical robustness training alone is not the proposed distinction |

Full titles, links and search limits appear in the references and companion novelty assessment. The differences above are hypotheses to investigate, not assertions of novelty, validity or freedom to operate.

## 4. Summary and background of the invention

The existing ClaimAudit evaluates evidence-claim pairs with embeddings, NLI, and NLI plus numerical/comparison checks. It handles limited explicit grammar and does not represent experimental context as a first-class binding. The proposed extension addresses evidence splicing: individually supported facts can be assembled into a compound statement that no single claimed experimental setting supports.

For example, Model A achieves 90% accuracy and 20 ms latency in configuration X, but 80% accuracy and 2 ms in configuration Y. A claim that one configuration achieves at least 90% accuracy and at most 2 ms cannot be justified by independently matching the two desirable numbers. A complete table refutes that claim within the table's declared domain; partial evidence only fails to support it.

The candidate mechanism preserves shared-context constraints, distinguishes alternative evidence bindings, requests an actual source fragment that could resolve verdict-changing ambiguity, and revalidates affected claims after the binding changes. A possible technical benefit is lower evidence-processing cost at equal verification quality. That benefit has not been measured. Known work already covers many constituents, and the novelty/inventive-step requirement is currently unresolved.

## 5. Objectives of invention

- Prevent support decisions based on incompatible experiment, dataset, hardware, population, denominator or version bindings.
- Preserve legitimate comparisons across settings when that is what the claim actually asserts.
- Distinguish numerical contradiction, missing evidence, context ambiguity and conflicting evidence.
- Resolve only uncertainty that obtainable source information can settle, under an explicit acquisition budget.
- Keep updated decisions reproducible and equivalent to full recomputation after evidence changes.
- Test the proposed benefit against simple exact-context joins and stronger verification baselines.

## 6. Working principle in brief

Represent evidence as source-linked measurements with explicit context. Represent the claim as predicates plus context-equality or context-difference requirements. Assess the complete proposition under each admissible evidence binding. If bindings lead to different conclusions, identify the metadata disagreement and retrieve a relevant header, caption, footnote or methods fragment. Validate the resulting binding update and recompute dependent decisions. Return a supported, contradicted, insufficient, ambiguous or evidence-conflict status with an auditable rationale. These statuses are proposed for the extension; the existing shared evaluation remains binary.

## 7. Detailed description and drawing

Proposed architecture:

```text
Claim + cited source bundle
           |
Reviewed claim predicates + source-linked evidence records
           |
Context constraints and admissible binding alternatives
           |
Joint numerical/context verification
       /                    \
Stable decision        Verdict-changing ambiguity
       |                    |
Evidence record        Select obtainable scope fragment
       |                    |
       +---------- Updated binding + revalidation
```

An evidence record would contain document ID and version, exact span or table-cell locator, entity, metric, value, unit and experiment-context attributes. Source bindings are not inferred from matching numbers alone. An initial prototype should use human-reviewed structured records to isolate reasoning from extraction errors. Later automatic extraction must be evaluated separately.

Let W be a bounded set of admissible interpretations of the supplied evidence. Let V(w,c) evaluate the entire claim c within interpretation w, preserving its quantifiers and context relationships. Support requires every admissible interpretation to establish the claim. Refutation requires each interpretation to establish its negation with explicit conflicting evidence or an appropriate completeness assertion. Unknown cases remain insufficient; materially different outcomes across bindings are reported as ambiguous. W being empty indicates conflicting constraints, not proof of arbitrary statements. Resource exhaustion must return an explicit unresolved status.

For the example in section 4, the claim contains a single shared experiment variable e with accuracy(A,e) >= 90% and latency(A,e) <= 2 ms. Checking each predicate with its own independent e incorrectly allows X and Y to be mixed. A claim that explicitly compares X with Y instead contains distinct variables and must not be rejected for that reason.

An ambiguity record would retain at least two outcome-disagreeing bindings and the attributes on which they differ. Candidate source requests are restricted to obtainable fragments whose contents could constrain those attributes. A methods paragraph may reveal hardware identity; a table header may reveal the dataset. No expected benefit is reported without a justified outcome model. A deterministic cost-aware policy can initially evaluate bounded possible outcomes, returning unresolved when no available request can resolve the uncertainty.

Revalidation must record both positive dependencies and candidate-selection predicates. Updating or deleting an existing referenced cell invalidates dependent results; inserting a new competing cell can also invalidate them. If dependency coverage cannot be established, use full recomputation. A replay record should contain source versions, predicates, candidate bindings, decisions, policy version, retrieved-fragment references and unresolved assumptions. Hashes provide change detection relative to trusted records, not truth or independent semantic proof.

Limitations: no guarantee of complete extraction from arbitrary PDFs, no automatic establishment of source authority, no interpretation of confidence intervals as hard truth bounds, no fabricated missing contexts and no universal proof of scientific validity. Proposed mechanisms are not yet implemented. The existing code in src/claimaudit/verification remains the original restricted grammar/checker.

## 8. Experimental validation results

**New proposed extension: no experimental results exist.** It has not been implemented, compared with baselines or validated on papers. No accuracy, latency, token-saving or novelty percentage is claimed.

Existing ClaimAudit evidence, provided only as background:

| Existing method | Test binary macro-F1 | Support recall |
| --- | ---: | ---: |
| Embedding similarity | 0.540 | 0.800 |
| NLI | 0.635 | 0.333 |
| NLI + numerical checks | 0.700 | 0.333 |
| NLI + comparison checks | 0.635 | 0.333 |
| Full hybrid | 0.700 | 0.333 |

The recorded test set has 60 synthetic examples from three template families. Numerical checks corrected four NLI errors and introduced none in that split; comparison checks added no corrections. The hybrid still rejected ten of fifteen supported examples. Its paired macro-F1 improvement interval includes zero. These findings do not validate the new mechanism or establish real-paper generalization.

On 18 October 2026, the restored repository passed all 69 existing software tests, and all six saved benchmark artifacts matched the completion manifest hashes. Inference was not rerun. Test success is not patent novelty evidence.

Planned validation: independent paper-level annotations and frozen document splits; compare NLI, the existing hybrid, independent atomic checks, exact-context joins, full-context verification and the proposed method with/without source expansion. Include valid cross-experiment claims, deliberately spliced claims, incomplete scope, corrections and conflicting evidence. Measure false-support rate at matched coverage, support recall, paper-clustered uncertainty, tokens/model calls per resolved case, latency and incremental/full-recompute equivalence. Proceed only if gains survive the simple context-join baseline and source-extraction errors.

## 9. What aspects need protection?

Candidate for professional assessment: the specific sequence linking jointly constrained experiment bindings, identification of verdict-changing binding disagreements, selection of an obtainable source fragment to resolve those disagreements, and safe revalidation of affected claim decisions. A protection request would need a more concrete implementation and a defensible distinction from all close prior art.

Do not claim novelty in NLI, numeric equality, units, rounding, symbolic solvers, all-constraint checking, evidence hashes, relational joins, possible-world semantics, generic retrieval or generic caching. The combination is not automatically inventive. No claim of patent clearance, filing readiness or freedom to operate is made.

Current gate: useful problem and candidate design identified; novelty/inventive step unresolved; implementation withheld under the user's stated condition. Indian eligibility must be assessed under the Patents Act and current CRI guidance. Actual human contributions, ownership, institutional obligations and disclosure history must be documented by the contributors and reviewed with the IP cell. None is invented in this draft.

## 10. Technology readiness level

**Proposed extension: TRL 2 - technology concept formulated (provisional self-assessment).** Do not select TRL 3 or higher for an unimplemented extension. The earlier ClaimAudit prototype has experimental evidence, but that does not transfer readiness to this new mechanism. No bank/fraud application is part of this proposal.

## References

P1. RefChecker (2024): https://arxiv.org/abs/2405.14486

P2. Proof-Carrying Numbers (2025): https://arxiv.org/abs/2509.06902

P3. When Verification Fails (2026): https://arxiv.org/abs/2604.10990

P4. EG-VAR (2026): https://arxiv.org/abs/2607.12650

P5. RT4CHART (2026): https://arxiv.org/abs/2603.27752

P6. Minimal Evidence Group Identification (2024 preprint): https://arxiv.org/abs/2404.15588

P7. US20260127386A1: https://patents.google.com/patent/US20260127386A1/en

P8. US20250077940A1: https://patents.google.com/patent/US20250077940A1/en

P9. Certain answers as objects and knowledge (2016): https://doi.org/10.1016/j.artint.2015.11.004

P10. Towards Robust Numerical Claim Verification (2026): https://arxiv.org/abs/2610.00689

L1. Official patent requirements: https://ipindia.gov.in/basics-of-patents

L2. Section 3 exclusions: https://ipindia.gov.in/acts/patent-act-1970/section-3

L3. Official CRI guidelines catalog: https://ipindia.gov.in/resource/patents-resources-guidelines

Local evidence: results/controlled_v1/report.md and complete.json. Companion analysis: docs/NOVELTY_ASSESSMENT_2026_10_18.md. This is a draft response set, not an executed declaration or patent application.
