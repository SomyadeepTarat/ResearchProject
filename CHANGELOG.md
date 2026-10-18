# Milestone 1 checkpoint

Initialized an independent Git repository on codex/milestone-1. Installed the package with uv using CPython 3.12.11. Seven unittest tests passed against the installed package. The installed CLI validated 12 cases from 3 sources, with 3 cases per label. No models ran and no verification metrics were computed.

## Exact files added

- [.gitignore](/Users/somyadeeptarat/Desktop/Claim/.gitignore)
- [.python-version](/Users/somyadeeptarat/Desktop/Claim/.python-version)
- [README.md](/Users/somyadeeptarat/Desktop/Claim/README.md)
- [app/README.md](/Users/somyadeeptarat/Desktop/Claim/app/README.md)
- [data/README.md](/Users/somyadeeptarat/Desktop/Claim/data/README.md)
- [data/smoke.jsonl](/Users/somyadeeptarat/Desktop/Claim/data/smoke.jsonl)
- [experiments/smoke.toml](/Users/somyadeeptarat/Desktop/Claim/experiments/smoke.toml)
- [pyproject.toml](/Users/somyadeeptarat/Desktop/Claim/pyproject.toml)
- [results/README.md](/Users/somyadeeptarat/Desktop/Claim/results/README.md)
- [src/claimaudit/__init__.py](/Users/somyadeeptarat/Desktop/Claim/src/claimaudit/__init__.py)
- [src/claimaudit/baselines/__init__.py](/Users/somyadeeptarat/Desktop/Claim/src/claimaudit/baselines/__init__.py)
- [src/claimaudit/cli.py](/Users/somyadeeptarat/Desktop/Claim/src/claimaudit/cli.py)
- [src/claimaudit/config.py](/Users/somyadeeptarat/Desktop/Claim/src/claimaudit/config.py)
- [src/claimaudit/evaluation/__init__.py](/Users/somyadeeptarat/Desktop/Claim/src/claimaudit/evaluation/__init__.py)
- [src/claimaudit/evaluation/dataset.py](/Users/somyadeeptarat/Desktop/Claim/src/claimaudit/evaluation/dataset.py)
- [src/claimaudit/extraction/__init__.py](/Users/somyadeeptarat/Desktop/Claim/src/claimaudit/extraction/__init__.py)
- [src/claimaudit/schemas.py](/Users/somyadeeptarat/Desktop/Claim/src/claimaudit/schemas.py)
- [src/claimaudit/verification/__init__.py](/Users/somyadeeptarat/Desktop/Claim/src/claimaudit/verification/__init__.py)
- [tests/test_foundation.py](/Users/somyadeeptarat/Desktop/Claim/tests/test_foundation.py)
- [uv.lock](/Users/somyadeeptarat/Desktop/Claim/uv.lock)
- [CHANGELOG.md](/Users/somyadeeptarat/Desktop/Claim/CHANGELOG.md)


# Milestone 2 checkpoint — embedding baseline

Implemented optional sentence-transformers/PyTorch dependencies with uv lock, pinned MiniLM revision, CPU batch inference, explicit cosine scores, configurable threshold, input-length rejection, and a diagnostic JSON runner with reproducibility metadata. Kept the original validation command compatible and prevented output overwrite.

Validation: 17 unittest tests passed. Real inference completed on all 12 smoke examples using sentence-transformers 5.7.0 and torch 2.14.0 on Python 3.12.11. The output artifact was checked for 12 unique IDs and finite cosine scores within [-1, 1]. The loaded model limit was 256 tokens. No benchmark metrics or development calibration were performed.

For inspection only: accuracy-1 scored 0.872480; the numeric mutation accuracy-2 scored 0.855994; the direction reversal accuracy-3 scored 0.825238. All three exceeded the arbitrary 0.75 support threshold. These synthetic examples do not demonstrate generalization or prove that a later method will improve performance.

The model adapter follows the official [SentenceTransformer API](https://www.sbert.net/docs/package_reference/sentence_transformer/model.html). The pinned revision was retrieved from the [Hugging Face model API](https://huggingface.co/api/models/sentence-transformers/all-MiniLM-L6-v2).

## Exact files added or modified

- [.gitignore](/Users/somyadeeptarat/Desktop/Claim/.gitignore)
- [pyproject.toml](/Users/somyadeeptarat/Desktop/Claim/pyproject.toml)
- [uv.lock](/Users/somyadeeptarat/Desktop/Claim/uv.lock)
- [src/claimaudit/schemas.py](/Users/somyadeeptarat/Desktop/Claim/src/claimaudit/schemas.py)
- [src/claimaudit/config.py](/Users/somyadeeptarat/Desktop/Claim/src/claimaudit/config.py)
- [src/claimaudit/cli.py](/Users/somyadeeptarat/Desktop/Claim/src/claimaudit/cli.py)
- [src/claimaudit/baselines/__init__.py](/Users/somyadeeptarat/Desktop/Claim/src/claimaudit/baselines/__init__.py)
- [src/claimaudit/baselines/embedding.py](/Users/somyadeeptarat/Desktop/Claim/src/claimaudit/baselines/embedding.py)
- [src/claimaudit/evaluation/embedding_run.py](/Users/somyadeeptarat/Desktop/Claim/src/claimaudit/evaluation/embedding_run.py)
- [experiments/embedding_smoke.toml](/Users/somyadeeptarat/Desktop/Claim/experiments/embedding_smoke.toml)
- [tests/test_embedding.py](/Users/somyadeeptarat/Desktop/Claim/tests/test_embedding.py)
- [README.md](/Users/somyadeeptarat/Desktop/Claim/README.md)
- [results/README.md](/Users/somyadeeptarat/Desktop/Claim/results/README.md)
- [CHANGELOG.md](/Users/somyadeeptarat/Desktop/Claim/CHANGELOG.md)

Generated local artifact (ignored by Git): [results/embedding_smoke.json](/Users/somyadeeptarat/Desktop/Claim/results/embedding_smoke.json). Model weights are cached under /Users/somyadeeptarat/Desktop/Claim/.cache/huggingface/ and dependencies under /Users/somyadeeptarat/Desktop/Claim/.venv/.

Next checkpoint: implement an NLI baseline with explicit entailment/neutral/contradiction mapping, pinned model revision, and the same input/output contracts.


# Milestone 3 checkpoint — NLI baseline

Added the Hugging Face/PyTorch NLI baseline with evidence as premise and claim as hypothesis. Model and tokenizer use immutable revision b95119ce93d3e065de6214e38cd4a97b0f2f2c6d of cross-encoder/nli-MiniLM2-L6-H768. The downloaded mapping is 0=contradiction, 1=entailment, 2=neutral. Preserve all three softmax probabilities and use entailment >= 0.5 for the untuned smoke decision. Reject overlength pairs at 512 tokens, including special tokens, and reject ambiguous model label mappings.

Extracted a shared diagnostic runner for consistent metadata across both baselines, retaining the original run_embedding entry point. Added validated optional class_scores to Prediction. Added Transformers as a direct optional dependency and updated uv.lock.

Validation: 29 tests passed. Real NLI inference completed on all 12 smoke examples; saved probabilities were verified as finite, in [0, 1], summing to 1, and consistent with binary decisions. The embedding regression run preserved all 12 IDs and verdicts and matched the previous scores within 1e-6. No research metrics were generated and no thresholds were tuned.

On these fixtures only, NLI produced all expected binary decisions. Entailment scores for accuracy-1, accuracy-2, and accuracy-3 were 0.992830, 0.034775, and 0.209953 respectively. This gives no evidence yet that the proposed hybrid will improve on NLI. Broader held-out evaluation remains required.

Model rationale and documented label order: [official model card](https://huggingface.co/cross-encoder/nli-MiniLM2-L6-H768).

## Exact files added or modified

- [pyproject.toml](/Users/somyadeeptarat/Desktop/Claim/pyproject.toml)
- [uv.lock](/Users/somyadeeptarat/Desktop/Claim/uv.lock)
- [src/claimaudit/config.py](/Users/somyadeeptarat/Desktop/Claim/src/claimaudit/config.py)
- [src/claimaudit/schemas.py](/Users/somyadeeptarat/Desktop/Claim/src/claimaudit/schemas.py)
- [src/claimaudit/cli.py](/Users/somyadeeptarat/Desktop/Claim/src/claimaudit/cli.py)
- [src/claimaudit/baselines/__init__.py](/Users/somyadeeptarat/Desktop/Claim/src/claimaudit/baselines/__init__.py)
- [src/claimaudit/baselines/nli.py](/Users/somyadeeptarat/Desktop/Claim/src/claimaudit/baselines/nli.py)
- [src/claimaudit/evaluation/baseline_run.py](/Users/somyadeeptarat/Desktop/Claim/src/claimaudit/evaluation/baseline_run.py)
- [src/claimaudit/evaluation/embedding_run.py](/Users/somyadeeptarat/Desktop/Claim/src/claimaudit/evaluation/embedding_run.py)
- [experiments/nli_smoke.toml](/Users/somyadeeptarat/Desktop/Claim/experiments/nli_smoke.toml)
- [tests/test_nli.py](/Users/somyadeeptarat/Desktop/Claim/tests/test_nli.py)
- [tests/test_baseline_run.py](/Users/somyadeeptarat/Desktop/Claim/tests/test_baseline_run.py)
- [README.md](/Users/somyadeeptarat/Desktop/Claim/README.md)
- [results/README.md](/Users/somyadeeptarat/Desktop/Claim/results/README.md)
- [CHANGELOG.md](/Users/somyadeeptarat/Desktop/Claim/CHANGELOG.md)

Generated local artifacts (ignored by Git):

- [results/nli_smoke.json](/Users/somyadeeptarat/Desktop/Claim/results/nli_smoke.json)
- [results/embedding_smoke_m3.json](/Users/somyadeeptarat/Desktop/Claim/results/embedding_smoke_m3.json)

Next checkpoint: the structure-aware verifier, reusing this NLI baseline and adding numerical and comparison-direction checks with explicit explanations and conservative handling of ambiguous text.


# Milestone 4 checkpoint — structure-aware verifier

Implemented a conservative grammar for explicit entity/metric quantities and comparisons, numerical unit normalization, comparison direction checks, evidence-linked check results, and an NLI-based hybrid. The hybrid reuses the exact NLI model/revision/threshold and only vetoes support when an enabled check finds a contradiction. Both checks can be disabled independently for later ablations. Matching facts never promote an NLI rejection; unknown syntax, ambiguous scope, and conflicting evidence abstain.

Added schema version 3 artifacts preserving the NLI base verdict, NLI probabilities, and check outcomes. The retained score is labeled nli_entailment_probability and is not a hybrid confidence estimate. Integer counts require exact equality; continuous quantities use configurable tolerances after unit normalization. The grammar and its limitations are documented separately. No dependency changes or additional model downloads were needed.

Validation: 47 tests passed, including all three runner paths, label isolation, unit equivalence, decimal/binary memory units, entity and metric alignment, order reversal, lower-is-better metrics, exact counts at large scale, equality/near-equality, ambiguous syntax, contradictory evidence, ablation switches, and hybrid fusion. A real cached-model run completed on all 12 smoke examples. Saved NLI settings, scores (within 1e-6), and base verdicts match Milestone 3; conclusive check spans were verified against original evidence.

Observed diagnostic check counts: numerical — 3 contradictions, 2 consistent, 7 abstentions; comparison — 3 contradictions, 1 consistent, 8 abstentions. Zero verdicts changed from NLI because it had already rejected all six contradiction examples. This fixture therefore shows no detection gain from the hybrid. No held-out research metrics or calibrated thresholds are claimed.

## Exact files added or modified

- [src/claimaudit/config.py](/Users/somyadeeptarat/Desktop/Claim/src/claimaudit/config.py)
- [src/claimaudit/schemas.py](/Users/somyadeeptarat/Desktop/Claim/src/claimaudit/schemas.py)
- [src/claimaudit/cli.py](/Users/somyadeeptarat/Desktop/Claim/src/claimaudit/cli.py)
- [src/claimaudit/evaluation/baseline_run.py](/Users/somyadeeptarat/Desktop/Claim/src/claimaudit/evaluation/baseline_run.py)
- [src/claimaudit/verification/__init__.py](/Users/somyadeeptarat/Desktop/Claim/src/claimaudit/verification/__init__.py)
- [src/claimaudit/verification/parsing.py](/Users/somyadeeptarat/Desktop/Claim/src/claimaudit/verification/parsing.py)
- [src/claimaudit/verification/checks.py](/Users/somyadeeptarat/Desktop/Claim/src/claimaudit/verification/checks.py)
- [src/claimaudit/verification/structure.py](/Users/somyadeeptarat/Desktop/Claim/src/claimaudit/verification/structure.py)
- [experiments/structure_smoke.toml](/Users/somyadeeptarat/Desktop/Claim/experiments/structure_smoke.toml)
- [tests/test_structure.py](/Users/somyadeeptarat/Desktop/Claim/tests/test_structure.py)
- [tests/test_baseline_run.py](/Users/somyadeeptarat/Desktop/Claim/tests/test_baseline_run.py)
- [docs/structure_checks.md](/Users/somyadeeptarat/Desktop/Claim/docs/structure_checks.md)
- [README.md](/Users/somyadeeptarat/Desktop/Claim/README.md)
- [results/README.md](/Users/somyadeeptarat/Desktop/Claim/results/README.md)
- [CHANGELOG.md](/Users/somyadeeptarat/Desktop/Claim/CHANGELOG.md)

Generated local artifacts (ignored by Git):

- [results/structure_smoke.json](/Users/somyadeeptarat/Desktop/Claim/results/structure_smoke.json) — initial integration run.
- [results/structure_smoke_02.json](/Users/somyadeeptarat/Desktop/Claim/results/structure_smoke_02.json) — final verified run.

Next checkpoint: build the evaluation and dataset-expansion workflow toward approximately 300 examples, freeze source/document-grouped splits, compare all three methods and structural ablations, and report uncertainty and failure cases without tuning on the test set. Parser-development examples must remain outside held-out evaluation.


# Milestone 5 checkpoint — controlled evaluation

Added a deterministic 300-example synthetic dataset (75 examples per label, 75 sources, 15 template families), per-row rationales, and explicit author-label provenance. These are not independently reviewed paper excerpts. Added optional group_id metadata and source/group consistency validation. Froze family-level splits before model evaluation: 180 reserved/unused train examples, 60 development examples, and 60 test examples.

Implemented development-only macro-F1 threshold selection, saved calibration before test inference, shared NLI scores across three structural variants, scikit-learn binary metrics, per-error detection recall, all failure records, and 2,000 paired whole-group bootstrap draws. Added a direct optional evaluation dependency on scikit-learn. Extracted the existing fusion policy into a reusable function without changing parser/check logic or tolerances. Runs refuse to overwrite existing directories and produce a completion marker with artifact hashes.

Validation: 59 tests passed. Tests cover deterministic data, exact label balance, group/source/evidence leakage, data hash integrity, hand-computed confusion metrics, deterministic threshold ties, paired bootstrap behavior, and a workflow showing that altered test labels cannot affect development-selected thresholds. Real cached-model evaluation completed, and saved metrics were independently recomputed from prediction records. Artifact hashes, 120 unique development/test IDs, every failure record, check evidence spans, and unchanged shared NLI scores were verified.

Observed 60-example test macro-F1: embedding 0.540; NLI 0.635; NLI + numerical 0.700; NLI + comparison 0.635; full hybrid 0.700. Development-selected thresholds were approximately 0.85486571 for embeddings and 0.5 for NLI. Numerical checks corrected four errors on the accuracy-pair family with no new errors. Comparison checks added no corrections. NLI and the hybrid still rejected 10 of 15 supported examples (all supported interval and precision-proportion cases). The hybrid–NLI macro-F1 difference was about +0.065; its exploratory paired interval included zero, [0.000, 0.220].

These results do not establish real-paper performance or publication-ready superiority. Test families are separated from threshold selection within this dataset, but some grammar forms were used in earlier parser development. Labels are synthetic and not independently reviewed, and only three independent test families are available. The test results are now inspected; method changes informed by them require fresh held-out evaluation or explicitly exploratory reuse.

## Exact files added or modified

- [pyproject.toml](/Users/somyadeeptarat/Desktop/Claim/pyproject.toml)
- [uv.lock](/Users/somyadeeptarat/Desktop/Claim/uv.lock)
- [src/claimaudit/schemas.py](/Users/somyadeeptarat/Desktop/Claim/src/claimaudit/schemas.py)
- [src/claimaudit/config.py](/Users/somyadeeptarat/Desktop/Claim/src/claimaudit/config.py)
- [src/claimaudit/verification/structure.py](/Users/somyadeeptarat/Desktop/Claim/src/claimaudit/verification/structure.py)
- [src/claimaudit/evaluation/__init__.py](/Users/somyadeeptarat/Desktop/Claim/src/claimaudit/evaluation/__init__.py)
- [src/claimaudit/evaluation/dataset.py](/Users/somyadeeptarat/Desktop/Claim/src/claimaudit/evaluation/dataset.py)
- [src/claimaudit/evaluation/synthetic.py](/Users/somyadeeptarat/Desktop/Claim/src/claimaudit/evaluation/synthetic.py)
- [src/claimaudit/evaluation/splits.py](/Users/somyadeeptarat/Desktop/Claim/src/claimaudit/evaluation/splits.py)
- [src/claimaudit/evaluation/metrics.py](/Users/somyadeeptarat/Desktop/Claim/src/claimaudit/evaluation/metrics.py)
- [src/claimaudit/evaluation/benchmark.py](/Users/somyadeeptarat/Desktop/Claim/src/claimaudit/evaluation/benchmark.py)
- [tests/test_evaluation.py](/Users/somyadeeptarat/Desktop/Claim/tests/test_evaluation.py)
- [experiments/controlled.toml](/Users/somyadeeptarat/Desktop/Claim/experiments/controlled.toml)
- [data/controlled_v1/examples.jsonl](/Users/somyadeeptarat/Desktop/Claim/data/controlled_v1/examples.jsonl)
- [data/controlled_v1/splits.json](/Users/somyadeeptarat/Desktop/Claim/data/controlled_v1/splits.json)
- [data/controlled_v1/README.md](/Users/somyadeeptarat/Desktop/Claim/data/controlled_v1/README.md)
- [data/README.md](/Users/somyadeeptarat/Desktop/Claim/data/README.md)
- [docs/evaluation.md](/Users/somyadeeptarat/Desktop/Claim/docs/evaluation.md)
- [README.md](/Users/somyadeeptarat/Desktop/Claim/README.md)
- [results/README.md](/Users/somyadeeptarat/Desktop/Claim/results/README.md)
- [CHANGELOG.md](/Users/somyadeeptarat/Desktop/Claim/CHANGELOG.md)

Generated local evaluation artifacts (ignored by Git):

- [results/controlled_v1/protocol.json](/Users/somyadeeptarat/Desktop/Claim/results/controlled_v1/protocol.json)
- [results/controlled_v1/calibration.json](/Users/somyadeeptarat/Desktop/Claim/results/controlled_v1/calibration.json)
- [results/controlled_v1/predictions.jsonl](/Users/somyadeeptarat/Desktop/Claim/results/controlled_v1/predictions.jsonl)
- [results/controlled_v1/failures.jsonl](/Users/somyadeeptarat/Desktop/Claim/results/controlled_v1/failures.jsonl)
- [results/controlled_v1/summary.json](/Users/somyadeeptarat/Desktop/Claim/results/controlled_v1/summary.json)
- [results/controlled_v1/report.md](/Users/somyadeeptarat/Desktop/Claim/results/controlled_v1/report.md)
- [results/controlled_v1/complete.json](/Users/somyadeeptarat/Desktop/Claim/results/controlled_v1/complete.json)

Next implementation checkpoint: a Streamlit demo for inspecting evidence, predictions, check explanations, and the actual evaluation report. Independent annotation and paper-derived validation remain separate outstanding research work.

# Milestone 6 — local Streamlit demo

Added a live three-method comparison and a saved-evaluation explorer. Live verification shares one NLI result with the structural verifier, uses cached model resources with serialized access, and defaults to compatible development-selected thresholds. Users can inspect structural evidence spans, explore ablations, and download diagnostic predictions. Input or setting changes hide stale predictions. Live inputs do not modify datasets or saved research results.

The evaluation explorer verifies artifact hashes before displaying metrics, uncertainty intervals, corrections, harms, and filterable prediction records. It needs no model inference. The UI explicitly describes synthetic-label and held-out-family limitations. Responsive verdict cards wrap in narrow panels. File watching is disabled to avoid Streamlit scanning Transformers' optional vision modules; code edits require a server restart.

Validation: 69 tests passed, including ten new service/UI tests. Real cached-model inference and saved evaluation browsing were checked in the browser. The numerical smoke claim produced embedding support, NLI rejection, and a numerical contradiction in the hybrid. No benchmark results were regenerated or altered for this milestone.

Launch commands and test commands are in [app/README.md](/Users/somyadeeptarat/Desktop/Claim/app/README.md). Local URL: http://127.0.0.1:8501.

## Exact files added or modified for Milestone 6

- [.streamlit/config.toml](/Users/somyadeeptarat/Desktop/Claim/.streamlit/config.toml)
- [pyproject.toml](/Users/somyadeeptarat/Desktop/Claim/pyproject.toml)
- [uv.lock](/Users/somyadeeptarat/Desktop/Claim/uv.lock)
- [src/claimaudit/demo.py](/Users/somyadeeptarat/Desktop/Claim/src/claimaudit/demo.py)
- [app/streamlit_app.py](/Users/somyadeeptarat/Desktop/Claim/app/streamlit_app.py)
- [app/README.md](/Users/somyadeeptarat/Desktop/Claim/app/README.md)
- [tests/test_demo.py](/Users/somyadeeptarat/Desktop/Claim/tests/test_demo.py)
- [README.md](/Users/somyadeeptarat/Desktop/Claim/README.md)
- [CHANGELOG.md](/Users/somyadeeptarat/Desktop/Claim/CHANGELOG.md)

All six implementation milestones are complete. Independent paper-derived annotation and fresh held-out validation remain outstanding research work.

# 18 October 2026 - novelty assessment and IDF-B discussion draft

Reviewed the restored ClaimAudit repository and the supplied VIT disclosure form. Researched close scientific-verification publications and published patent claims. Defined scope-consistent evidence binding with ambiguity-directed source expansion as a candidate research direction. The novelty-conditioned implementation gate has not passed; no new verifier or model behavior was introduced. The disclosure explicitly distinguishes the proposed TRL 2 extension from the existing prototype and does not claim patentability.

Validation: all 69 existing tests passed; all six controlled_v1 artifact hashes matched their manifest. No model inference was rerun. The seven-page response PDF includes all ten form questions, was rendered and visually reviewed, and preserves the supplied original form unchanged.

Exact new paths:

- `/Users/somyadeeptarat/Desktop/Claim/docs/NOVELTY_ASSESSMENT_2026_10_18.md`
- `/Users/somyadeeptarat/Desktop/Claim/docs/INVENTION_DISCLOSURE_B_CLAIMAUDIT_DRAFT.md`
- `/Users/somyadeeptarat/Desktop/Claim/docs/NOVELTY_VALIDATION_2026_10_18.json`
- `/Users/somyadeeptarat/Desktop/Claim/scripts/render_disclosure_draft.py`
- `/Users/somyadeeptarat/Desktop/Claim/output/pdf/ClaimAudit_IDF_B_Research_Draft.pdf`

This entry modifies `/Users/somyadeeptarat/Desktop/Claim/CHANGELOG.md`. Rebuild the PDF with `python scripts/render_disclosure_draft.py` in an environment containing ReportLab; this optional document tool does not change core project dependencies.
