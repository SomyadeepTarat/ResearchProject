# Results

Embedding, NLI, and structure-aware runs write diagnostic JSON artifacts here. The 12 synthetic smoke cases and arbitrary threshold do not support research accuracy claims. No benchmark metrics are generated at this milestone.

Run `uv run --extra models --locked claimaudit --method embedding --config experiments/embedding_smoke.toml --output results/embedding_smoke.json` from the repository root. Use a fresh output filename for each run. Each artifact records predictions, scores, inputs, gold annotations, model revision, configuration, hashes, dependency versions, seed, and runtime details. Future benchmark runs must additionally record frozen split IDs and evaluated metrics.

Milestone 3 produced `nli_smoke.json` with 12 NLI predictions and three class probabilities per example. `embedding_smoke_m3.json` checks the embedding path after the shared-runner refactor; `embedding_smoke.json` remains the original milestone 2 artifact. These files are local and ignored by Git.

Milestone 4 adds structure-aware artifacts. `structure_smoke_02.json` is the final verification run; `structure_smoke.json` is the earlier integration run. Both retain NLI scores and evidence-linked check outcomes. Neither is a held-out benchmark.


Milestone 5 completed the first controlled synthetic evaluation in `controlled_v1/`. Its `complete.json` records successful completion and hashes every output artifact. `report.md` summarizes real test metrics; `summary.json` contains confusion matrices, per-family metrics, structural effects, and group-bootstrap intervals. `calibration.json` was saved before test inference. Every development/test prediction is in `predictions.jsonl` and every test mistake is in `failures.jsonl`.

The 60-example test split has only three template families and is not independently annotated. Numerical checks corrected four NLI errors, but both NLI and the hybrid rejected 10 of 15 supported claims. Do not treat this result as proof of broad research superiority. Keep a new untouched set for future model changes informed by these results.
