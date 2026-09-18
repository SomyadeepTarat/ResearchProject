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
