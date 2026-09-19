# Evaluation protocol

The current experiment is a controlled synthetic prototype study. Its 300 examples and source grouping are documented in `data/controlled_v1/README.md`. No model weights are trained. The reserved training split is unused. Independent annotation and real-paper evaluation are outstanding research work.

## Reproduce

From the ClaimAudit repository root:

```sh
uv sync --extra models --extra evaluation --locked
uv run --extra models --extra evaluation --locked python -m unittest discover -s tests -v
uv run --extra models --extra evaluation --locked python -m claimaudit.evaluation.benchmark \
  --config experiments/controlled.toml \
  --output-dir results/controlled_v1_rerun
```

Use a new output directory for each run. Both model revisions are pinned, and their weights are cached from the earlier milestones. Set `local_files_only = true` in both model tables (or `HF_HUB_OFFLINE=1` in the environment) for offline inference after downloading weights. The run refuses to overwrite an existing directory. An interrupted directory lacks `complete.json` and must not be reported as a complete evaluation.

## Order of operations

1. Validate the dataset against the frozen manifest: hash, exact ID coverage, group assignments, and no source/evidence leakage.
2. Save `protocol.json`: configuration, dependency versions, source/config/manifest/lock hashes, exact split IDs, model revisions, and seed.
3. Score development pairs once with each model. The verifiers receive only evidence and claim.
4. Select separate embedding and NLI support thresholds by maximizing development binary macro-F1. Candidates are observed scores, valid score-domain endpoints, the original default, and a threshold just above the maximum when within bounds. The decision is `score >= threshold`. Break ties by proximity to the original default, then by the larger threshold. Save all candidates and development IDs to `calibration.json` **before test inference**.
5. Score test pairs once per model. Reuse the NLI predictions/threshold across NLI alone, NLI + numerical checks, NLI + comparison checks, and both checks. Parser rules and tolerances are fixed; they are not tuned on these test examples.
6. Compute metrics and paired whole-group bootstrap intervals. Save all development/test predictions, all test mistakes, and a readable report. Verify that source/config/data hashes did not change during the run, then write artifact hashes to `complete.json`.

“Calibration” here means threshold selection, not probability calibration. NLI softmax scores are not guaranteed calibrated probabilities of truth. The hybrid retains the NLI score even when a rule overrides its verdict; never interpret it as hybrid confidence.

## Metrics

Primary task: supported versus not supported. Both contradiction labels and unsupported map to not supported. All five variants are compared on identical examples and splits.

Report accuracy, binary macro-F1, support precision/recall/F1, false rejection rate among supported claims, and false acceptance rate among not-supported claims. Error-type detection recall is the fraction flagged as not supported within each of the three error labels; it is not four-way classification accuracy. Confusion matrices have gold rows and prediction columns, ordered `not_supported`, `supported`. Undefined precision/F1 uses zero; absent error classes report null.

The metric definitions and label ordering use scikit-learn's [precision/recall/F-score API](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.precision_recall_fscore_support.html) and [confusion matrix API](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.confusion_matrix.html). Threshold search and bootstrap use equivalent binary confusion-count calculations, covered by tests against hand-calculated cases.

Structural diagnostics report conclusive-check coverage, abstention/contradiction counts, overrides, corrected NLI mistakes, and new mistakes introduced by the override. Report both gains and harms. Results by test family help expose where limited parser coverage affects the comparison.

## Uncertainty and interpretation

The percentile bootstrap draws whole `group_id` clusters with replacement, preserving all claims and sources within each selected family. The same 2,000 draws are used across methods; paired macro-F1 differences are calculated against NLI. This avoids treating correlated mutations as independent claims. The current test set has only three template-family clusters. Its intervals are highly limited and must not be used to claim reliable significance or generalization.

A fully balanced synthetic dataset does not represent real-world hallucination frequency. Some test grammar forms overlap earlier parser-development fixtures, though whole families are separated from threshold selection within this dataset. New paper-derived data, independent annotation, more independent documents, and fresh held-out evaluation are required before making broad research claims.

## Artifacts

- `protocol.json`: frozen inputs, environment, and split assignments.
- `calibration.json`: development-only threshold search and example IDs.
- `predictions.jsonl`: every scored example with all method outputs and check explanations.
- `failures.jsonl`: every test error for every method, including original text and rationale.
- `summary.json`: all numerical results, per-family metrics, and paired intervals.
- `report.md`: readable tables and limitations, generated from actual results.
- `complete.json`: successful completion marker and artifact hashes.

Changing test labels cannot change thresholds: this is enforced by a workflow test. Reusing inspected test results for subsequent method design is exploratory; it does not preserve an untouched test set.
