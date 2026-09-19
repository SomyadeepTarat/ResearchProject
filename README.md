# ClaimAudit

A research prototype testing whether numerical and comparison-direction checks improve evidence-grounded scientific claim verification beyond embedding similarity and NLI. This is a hypothesis to test; no improvement is assumed.

Implemented: all three verification methods, controlled synthetic data expansion to 300 examples, frozen family-grouped splits, development-only threshold selection, paired evaluation with ablations, and reproducible reports. The Streamlit demo provides live verification and saved-result exploration. Independent real-paper annotation, retrieval, and automatic claim extraction remain later work.

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
4. Structure-aware (implemented): reuse the same NLI model with entity/metric-aligned numerical and comparison checks, unit normalization, conservative abstention, evidence-linked explanations, and independent ablation switches.
5. Evaluation (prototype complete): 300 synthetic, author-labeled cases; frozen grouped splits; development-only threshold selection; three methods plus structural ablations; paired bootstrap intervals and full failure records. Independent annotation and paper-derived evaluation remain outstanding.
6. Demo (implemented): Streamlit live verification, evidence-linked explanations, saved evaluation browsing, filters, and diagnostic downloads.

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

## Running the structure-aware verifier

```sh
uv run --extra models --locked python -m unittest discover -s tests -v
uv run --extra models --locked claimaudit --method structure-aware \
  --config experiments/structure_smoke.toml \
  --output results/structure_smoke_03.json
```

This configuration reuses the exact NLI model, revision, threshold, and evidence–claim pairs from Milestone 3. A structural contradiction vetoes NLI support; otherwise the NLI verdict is retained. Matching a number never overrides an NLI rejection. The parser matches a narrow explicit grammar; ambiguous or unsupported forms abstain. No additional model or dependency is required.

Version 3 artifacts preserve `base_verdict`, all NLI probabilities, and separate `checks` with statuses and evidence spans. The retained score is explicitly named `nli_entailment_probability`, not hybrid confidence. Set `numeric_checks` and `comparison_checks` independently under `[structure]` to run ablations. Both disabled preserves the NLI decision.

Read [the complete grammar, units, assumptions, limitations, and ablation protocol](docs/structure_checks.md) before treating a check as evidence. Dataset expansion and held-out evaluation remain necessary to establish whether the hybrid helps.

## Controlled evaluation checkpoint

The [dataset card](data/controlled_v1/README.md) describes 300 synthetic examples (75 per label), 75 sources, and 15 template families. Whole families are assigned to 180 reserved training, 60 development, and 60 test examples. No weights are trained. Labels are author-defined and have not been independently reviewed.

```sh
uv sync --extra models --extra evaluation --locked
uv run --extra models --extra evaluation --locked python -m unittest discover -s tests -v
uv run --extra models --extra evaluation --locked python -m claimaudit.evaluation.benchmark \
  --config experiments/controlled.toml \
  --output-dir results/controlled_v1_rerun
```

The runner selects embedding/NLI thresholds on development data, writes the calibration artifact, then scores the frozen test split. It reuses the same NLI predictions for all structural ablations. It refuses to overwrite an existing run directory. The training split is reserved and unused. The complete [protocol](docs/evaluation.md) explains metric definitions, leakage checks, uncertainty, and artifacts.

Actual first-run test macro-F1: embedding **0.540**, NLI **0.635**, NLI + numerical checks **0.700**, NLI + comparison checks **0.635**, full hybrid **0.700**. Numerical checks corrected four errors without adding errors on this split. NLI and the hybrid nevertheless rejected 10 of 15 supported examples, so support recall was only 0.333. The hybrid–NLI paired bootstrap interval for macro-F1 improvement includes zero ([0.000, 0.220]). There are only three independent test families.

These are controlled synthetic results, not evidence of general performance on scientific papers. Some grammar patterns were used in earlier parser development. The inspected test set must not be treated as untouched after making changes based on these results. See [the generated report](results/controlled_v1/report.md), full `predictions.jsonl`, and all errors in `failures.jsonl` beside it. Result files are ignored by Git by default and generated locally.

Validation at this checkpoint: **59 passing tests**, plus a real evaluation run whose artifact hashes, metrics, complete failure records, shared NLI scores, and development/test isolation were checked.

## Streamlit demo

```sh
uv sync --extra models --extra evaluation --extra app --locked
uv run --extra models --extra evaluation --extra app --locked streamlit run app/streamlit_app.py \
  --server.address 127.0.0.1 --server.port 8501 --server.headless true
```

Open [ClaimAudit locally](http://127.0.0.1:8501). **Verify a claim** accepts custom text or smoke examples and runs all three methods. It defaults to saved development-selected thresholds when compatible, supports exploratory thresholds/ablations, and shows structural evidence spans. **Explore evaluation** reads verified saved artifacts without loading models, displays actual metrics and limitations, and filters mistakes by method, label, family, or split. Text/settings changes hide stale predictions.

The server is local, model inference runs on your machine, and live inputs are not written into datasets or result files. Model weights are cached; downloading missing public weights is optional. See [app setup and behavior](app/README.md) for details.

Milestone 6 validation: **69 tests passed**, including Streamlit AppTest interactions. The running browser demo was checked with a real model prediction and the recorded evaluation. Responsive verdict cards wrap on narrow panels.

The six implementation milestones are now in place. Independent annotation and paper-derived evaluation are still needed to support broader research claims; the current synthetic results are limited prototype evidence.

See CHANGELOG.md for exact paths changed at each checkpoint.
