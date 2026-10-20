# Exact paths and handoff - 20 October 2026

Root: /Users/somyadeeptarat/Desktop/Claim. This review supersedes the earlier ScopeGuard novelty discussion. Decision: no defensible novelty established; research-paper-only route. Previous files remain preserved as history.

## Code and configuration changes in this review

- /Users/somyadeeptarat/Desktop/Claim/pyproject.toml - pinned optional research dependencies.
- /Users/somyadeeptarat/Desktop/Claim/uv.lock - resolved dependency lock.
- /Users/somyadeeptarat/Desktop/Claim/src/claimaudit/verification/compiled_scope.py - known-method BDD compilation and source-choice restriction.
- /Users/somyadeeptarat/Desktop/Claim/src/claimaudit/evaluation/scope_backends.py - actual ProbLog/PySDD, Z3, exhaustive, original DP and BDD rebuild adapters.
- /Users/somyadeeptarat/Desktop/Claim/src/claimaudit/evaluation/adversarial_benchmark.py - isolated reproducible comparison, raw timing samples and explicit caps.
- /Users/somyadeeptarat/Desktop/Claim/tests/test_scope_backends.py - seven differential/backend checks, including exact rare-world probabilities.
- /Users/somyadeeptarat/Desktop/Claim/scripts/freeze_scope_holdout.py - reserved dataset creation/checking.
- /Users/somyadeeptarat/Desktop/Claim/scripts/evaluate_local_scope_llm.py - one-shot local Ollama comparison, protocol and full responses.
- /Users/somyadeeptarat/Desktop/Claim/scripts/build_adversarial_report.py - generates reports from saved measured results.
- /Users/somyadeeptarat/Desktop/Claim/scripts/render_adversarial_disclosure.py - one-page memo and completed IDF-B rendering.

## Inputs and reports

- /Users/somyadeeptarat/Desktop/Claim/data/scope_v2/heldout.jsonl
- /Users/somyadeeptarat/Desktop/Claim/data/scope_v2/freeze.json
- /Users/somyadeeptarat/Desktop/Claim/data/scope_v2/README.md
- /Users/somyadeeptarat/Desktop/Claim/data/scope_v2/paper_sources.json
- /Users/somyadeeptarat/Desktop/Claim/docs/adversarial_review/STAGE1_PRIOR_ART.md
- /Users/somyadeeptarat/Desktop/Claim/docs/adversarial_review/STAGE2_DECISION_MEMO.md
- /Users/somyadeeptarat/Desktop/Claim/docs/adversarial_review/STAGE3_RESULTS.md
- /Users/somyadeeptarat/Desktop/Claim/docs/adversarial_review/STAGE4_COMPLETED_IDF_B.md
- /Users/somyadeeptarat/Desktop/Claim/docs/adversarial_review/CHANGESET.md
- /Users/somyadeeptarat/Desktop/Claim/docs/adversarial_review/solver_summary.json
- /Users/somyadeeptarat/Desktop/Claim/docs/adversarial_review/solver_measurements.jsonl
- /Users/somyadeeptarat/Desktop/Claim/docs/adversarial_review/ollama_protocol.json
- /Users/somyadeeptarat/Desktop/Claim/docs/adversarial_review/ollama_responses.jsonl
- /Users/somyadeeptarat/Desktop/Claim/docs/adversarial_review/ollama_summary.json
- /Users/somyadeeptarat/Desktop/Claim/docs/adversarial_review/tests.txt
- /Users/somyadeeptarat/Desktop/Claim/docs/adversarial_review/artifact_manifest.json
- /Users/somyadeeptarat/Desktop/Claim/output/pdf/ClaimAudit_Novelty_Decision_Memo.pdf
- /Users/somyadeeptarat/Desktop/Claim/output/pdf/ClaimAudit_IDF_B_Adversarial_Review.pdf

Raw run directories: /Users/somyadeeptarat/Desktop/Claim/results/adversarial_v2 and /Users/somyadeeptarat/Desktop/Claim/results/ollama_scope_v2. Re-run into fresh directories; original measurements are never overwritten by experiment runners. Source-data hashes are validated before solver evaluation. The saved report copies preserve evidence even though results/ is ignored by Git.

README.md and CHANGELOG.md link this checkpoint. Existing modified ScopeGuard v1 code/UI and earlier disclosure files predate this review and were preserved; they are not claimed as new modifications in this stage. No commit, public publication, deployment or patent filing is performed.
