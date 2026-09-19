# ClaimAudit Streamlit demo

Run from the repository root:

```sh
uv sync --extra models --extra evaluation --extra app --locked
uv run --extra models --extra evaluation --extra app --locked streamlit run app/streamlit_app.py \
  --server.address 127.0.0.1 --server.port 8501 --server.headless true
```

Open [the local demo](http://127.0.0.1:8501). Stop the server with Ctrl+C in its terminal. The project configuration binds to localhost and disables Streamlit usage telemetry. File watching is disabled because scanning Transformers lazy modules produces irrelevant optional-vision import errors; restart the server after editing code. No paid service or API key is needed.

## Verify a claim

Choose a synthetic smoke example or enter your own evidence and claim, then press **Run verification**. The UI shows embedding, NLI, and structure-aware verdicts; cosine/entailment scores; NLI class probabilities; and structural statuses with matching evidence text. It explains that abstention is not support and that the hybrid's retained NLI score is not hybrid confidence.

When a completed matching evaluation is available, development-selected thresholds are the default. Manual thresholds and independent structural check switches support exploration without modifying the saved benchmark. Different model IDs/revisions/devices or NLI length settings prevent silent reuse of saved calibration. Changes to text or settings hide stale predictions until you run again.

Models load only after clicking the button and are cached between runs. Access is serialized for shared model resources. **Use cached models only** is enabled initially; uncheck it to permit downloading pinned public weights when needed. If the entire server was started with `HF_HUB_OFFLINE=1`, restart without that environment setting before downloading. Inputs exceeding model token limits fail explicitly rather than being truncated.

Entered text stays in Streamlit session state and is not written to datasets or result files. **Download this prediction** creates a diagnostic JSON download when requested. Predictions are exploratory and do not update research metrics.

## Explore evaluation

Select a completed run from `results/*/complete.json`. The UI verifies all recorded artifact hashes before displaying it. It shows all methods and ablations, uncertainty intervals, support precision/recall, false rejections, and structural corrections/harms. Filter saved predictions by split, method, gold label, template family, and mistakes only. Inspect every method's output and download the report or a selected example.

This page does not load or run models. An app-only installation (`uv sync --extra app`) can browse existing local artifacts. A fresh clone without result artifacts still supports the live form; generate a benchmark using the evaluation instructions before browsing saved results. A failed integrity check disables the saved run instead of displaying stale or altered numbers.

## Verification

```sh
uv run --extra models --extra evaluation --extra app --locked python -m unittest discover -s tests -v
```

Streamlit AppTest covers initial rendering without inference, required fields, prediction submission, stale results, model errors, saved evaluation display, and filtering. Service tests cover hash validation, calibration compatibility, shared NLI output, thresholds, ablations, and input validation. UI tests skip when the app extra is not installed; the saved-result UI test also skips if the local evaluation artifact is absent.

The implementation follows the official [resource caching API](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.cache_resource), [responsive containers](https://docs.streamlit.io/develop/api-reference/layout/st.container), and [AppTest API](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest).

The current evaluation uses synthetic author-labeled examples and only three independent test families. It does not establish scientific-paper performance. Saved results represent their recorded source/configuration; live verification uses the current checkout. Independent paper-derived annotation and a fresh held-out evaluation remain outstanding research work.
