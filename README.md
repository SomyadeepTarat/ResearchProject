# ClaimAudit

A research prototype testing whether numerical and comparison-direction checks improve evidence-grounded scientific claim verification beyond embedding similarity and NLI. This is a hypothesis to test; no improvement is assumed.

## Current checkpoint — Milestone 3

Implemented: foundation, embedding and NLI baselines, batch inference, explicit scores, strict token-limit checks, and a shared diagnostic runner with reproducibility metadata. Structured verification, retrieval, automatic claim extraction, and research evaluation remain later milestones.

From this repository directory:

```sh
uv sync
uv run python -m unittest discover -s tests -v
uv run claimaudit --config experiments/smoke.toml
```

The validation command reports 12 examples, 3 sources, 3 examples per label, and `models_run: false`. It does not make predictions. Dataset paths resolve relative to the TOML file, not the shell directory.

## Architecture and next checkpoints

All methods will implement `Verifier.verify(ClaimInput) -> Prediction`. Inputs contain only evidence and claim; gold labels and rationales stay in evaluation. Start with manually supplied atomic claims and evidence so retrieval and extraction errors do not confound verification.

1. Foundation (complete): validate packaging, schema, config, and smoke data.
2. Embeddings (implemented): sentence-transformers cosine similarity with a configurable threshold and pinned model revision. Development-set threshold selection remains part of the evaluation milestone; the smoke threshold is untuned.
3. NLI (implemented): Hugging Face/PyTorch premise=evidence, hypothesis=claim, validated label mapping, all three softmax scores, and pair-length rejection. The smoke threshold is untuned; development calibration remains in the evaluation milestone.
4. Structure-aware: reuse the same NLI model and add entity/metric-aligned numerical and comparison checks. Normalize units and direction; avoid flagging every unmatched number. Preserve check explanations and abstain on ambiguous parses.
5. Evaluation: expand toward 300 reviewed cases, freeze grouped splits, compare methods and ablations, and save per-example outputs plus reproducibility metadata.
6. Demo: Streamlit inspection of evidence, predictions, and check explanations.

Model dependencies are optional (`uv sync --extra models`) and locked in uv.lock. Planned free stack: PyTorch, transformers, sentence-transformers, scikit-learn, pandas; spaCy only if parsing requires it. The validation path has no runtime dependencies and tests use standard-library unittest.

## Research protocol

Primary comparison: binary supported versus not-supported, shared across all three methods. Embeddings and generic NLI cannot inherently produce the two contradiction subtypes, so do not claim a fair four-way comparison without an explicit additional classifier. Retain all four gold labels for error-type detection recall and analysis. Report support precision/recall/F1, binary macro-F1, confusion matrices, and supported-case false positives. Later diagnostic subtype results must be reported separately.

Use identical examples and splits for all methods; tune thresholds only on development data. Compare NLI alone, NLI plus numerical checks, NLI plus direction checks, and both. Bootstrap by source/document for uncertainty and inspect paired failures. Keep paraphrases and mutations from the same document in one split to prevent leakage. Record dataset hashes, split IDs, model revisions, uv.lock, configuration, and seeds. Small synthetic fixtures establish software behavior, not scientific generalization or novelty.

## Layout

- `data/`: annotations and data contract.
- `src/claimaudit/extraction/`: future claim extraction.
- `src/claimaudit/baselines/`: future embedding and NLI methods.
- `src/claimaudit/verification/`: future structured checks and hybrid method.
- `src/claimaudit/evaluation/`: dataset loading and future evaluation.
- `experiments/`: reproducible configurations.
- `results/`: real run artifacts only.
- `tests/`: validation and integration checks.
- `app/`: future Streamlit demo.

## Running the embedding baseline

```sh
uv sync --extra models --locked
uv run --extra models --locked python -m unittest discover -s tests -v
uv run --extra models --locked claimaudit --method embedding \
  --config experiments/embedding_smoke.toml \
  --output results/embedding_smoke.json
```

The first inference downloads the public model into `.cache/huggingface/`. Subsequent runs can set `local_files_only = true` in the TOML file after the cache is populated. Choose a new output filename for each run; existing files are never overwritten. Use `--extra models` with uv run to retain the optional model dependencies.

The sample pins [all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) to an immutable revision and uses CPU. The model encodes each passage/claim independently; cosine similarity >= 0.75 produces `supported`. This is an arbitrary smoke threshold, not a probability or a calibrated decision boundary. No smoke labels are used to select it. A high score can coexist with a numerical or directional contradiction, which is precisely what later comparisons will test.

The adapter uses the official [SentenceTransformer API](https://www.sbert.net/docs/package_reference/sentence_transformer/model.html). It batches and deduplicates text, rejects inputs exceeding the loaded model's token limit, and disables remote model code. Long scientific passages will require explicit evidence selection in a later milestone.

Each JSON artifact contains raw cosine scores, binary verdicts, original pairs and gold labels, model revision, configuration, dataset/config/source/lock hashes, dependency versions, seed, device, and elapsed time including model loading. The seed is recorded but does not guarantee identical floating-point results across hardware. Gold labels are attached only after inference. Artifacts are ignored by Git by default; retain selected outputs deliberately when publishing experiments.

## Running the NLI baseline

```sh
uv sync --extra models --locked
uv run --extra models --locked python -m unittest discover -s tests -v
uv run --extra models --locked claimaudit --method nli \
  --config experiments/nli_smoke.toml \
  --output results/nli_smoke.json
```

The checked-in configuration pins [cross-encoder/nli-MiniLM2-L6-H768](https://huggingface.co/cross-encoder/nli-MiniLM2-L6-H768) to revision `b95119ce93d3e065de6214e38cd4a97b0f2f2c6d`. Its model card documents training on SNLI and MultiNLI; it is a general NLI baseline, not a scientific-domain verifier. The first run downloads the public weights. After caching, `local_files_only = true` enables offline model loading. If an output already exists, choose a new filename.

Evidence is always the premise and the claim is the hypothesis. Unlike embedding similarity, the model processes the pair jointly. The adapter reads the model's descriptive `id2label` mapping and refuses ambiguous labels such as `LABEL_0`. It uses evaluation/inference mode and applies numerically stable softmax to the logits. Outputs retain `entailment`, `neutral`, and `contradiction` probabilities. `score` is entailment probability and the binary verdict is supported when it is >= the configured threshold (0.5 for this smoke configuration). These are model probabilities, not calibrated confidence estimates. Thresholds below 0.5 may yield support even if entailment is not the largest class; thresholding is the explicit rule, not three-way argmax.

The combined tokenized pair, including special tokens, must fit the configured and model limits (512 tokens for this model). Overlength pairs fail explicitly. NLI contradiction is not automatically labeled numeric or comparison contradiction; those are gold error categories for later analysis.

Both baselines use the same runner and schema. Version 2 artifacts add optional `class_scores`; NLI metadata also records the resolved label mapping and pair order. The original version 1 embedding artifact remains available unchanged. Gold labels are only attached after inference, and unit tests check that neither model receives them.

Milestone 3 check: 29 tests passed, and real NLI inference completed on all 12 smoke cases. At the untuned 0.5 threshold, these small fixtures produced the expected binary decisions, including rejection of the altered accuracy and reversed comparison. This does not establish general performance or an advantage for the future hybrid. Expand and independently review the dataset before evaluating whether structured checks add value; do not select test cases just to make the hybrid win.

See CHANGELOG.md for exact paths changed at each checkpoint.
