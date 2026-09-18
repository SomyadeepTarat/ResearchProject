# Results

Embedding and NLI runs write diagnostic JSON artifacts here. The 12 synthetic smoke cases and arbitrary threshold do not support research accuracy claims. No benchmark metrics are generated at this milestone.

Run `uv run --extra models --locked claimaudit --method embedding --config experiments/embedding_smoke.toml --output results/embedding_smoke.json` from the repository root. Use a fresh output filename for each run. Each artifact records predictions, scores, inputs, gold annotations, model revision, configuration, hashes, dependency versions, seed, and runtime details. Future benchmark runs must additionally record frozen split IDs and evaluated metrics.

Milestone 3 produced `nli_smoke.json` with 12 NLI predictions and three class probabilities per example. `embedding_smoke_m3.json` checks the embedding path after the shared-runner refactor; `embedding_smoke.json` remains the original milestone 2 artifact. These files are local and ignored by Git.
