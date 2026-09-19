"""Shared diagnostic inference runner for all verification methods."""
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import platform
import time

from claimaudit.baselines.embedding import EmbeddingVerifier
from claimaudit.baselines.nli import NLIVerifier
from claimaudit.verification.structure import StructureAwareVerifier
from claimaudit.config import ExperimentConfig
from claimaudit.evaluation.dataset import load_dataset


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_baseline(config_path: Path, method: str) -> dict:
    config = ExperimentConfig.load(config_path)
    if method not in ("embedding", "nli", "structure-aware"):
        raise ValueError(f"Unknown baseline: {method}")
    settings = config.nli if method == "structure-aware" else getattr(config, method)
    if method == "structure-aware" and config.structure is None:
        raise ValueError("structure-aware inference requires [nli] and [structure] configuration tables")
    if settings is None:
        raise ValueError(f"{method} inference requires an [{'nli' if method == 'structure-aware' else method}] configuration table")
    rows = load_dataset(config.dataset)
    # Importing model libraries is restricted to this inference path.
    try:
        import torch
        from transformers import set_seed
    except ImportError as exc:
        raise RuntimeError("Install the model extra: uv sync --extra models") from exc
    set_seed(config.seed)
    start = time.perf_counter()
    if method == "structure-aware":
        verifier = StructureAwareVerifier(settings, config.structure)
        nli_backend = verifier.nli.backend
    elif method == "nli":
        verifier = NLIVerifier(settings)
        nli_backend = verifier.backend
    else:
        verifier = EmbeddingVerifier(settings)
    predictions = verifier.verify_many([row.to_input() for row in rows])
    elapsed = time.perf_counter() - start
    if len(predictions) != len(rows):
        raise ValueError("Verifier returned an unexpected number of predictions")
    model_metadata = (
        {"model_max_seq_length": verifier.encoder.model.max_seq_length}
        if method == "embedding" else
        {"model_max_seq_length": nli_backend.max_length,
         "nli_id2label": dict(enumerate(nli_backend.labels)),
         "pair_order": ["evidence", "claim"]}
    )
    if method == "structure-aware":
        model_metadata["fusion_policy"] = "Veto NLI support on a structural contradiction; otherwise retain NLI."
        model_metadata["parser"] = "explicit_quantitative_grammar_v1"
    packages = {}
    for name in ("claimaudit", "sentence-transformers", "transformers", "torch", "numpy", "huggingface-hub"):
        try:
            packages[name] = version(name)
        except PackageNotFoundError:
            packages[name] = None
    root = Path(__file__).resolve().parents[3]
    lock = root / "uv.lock"
    return {
        "schema_version": 3,
        "purpose": "diagnostic_inference_only",
        "notice": "No benchmark metrics. Smoke fixtures and the example threshold are not research evidence.",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "method": method, "models_run": True,
        "dataset": {"path": str(config.dataset), "sha256": sha256(config.dataset)},
        "config_sha256": sha256(config_path),
        "config": asdict(config),
        "runtime": {"python": platform.python_version(), "platform": platform.platform(),
                    "packages": packages, "elapsed_seconds_including_model_load": elapsed,
                    "torch_threads": torch.get_num_threads(),
                    **model_metadata},
        "uv_lock_sha256": sha256(lock) if lock.exists() else None,
        "source_sha256": {str(p.relative_to(root)): sha256(p) for p in sorted((root / "src/claimaudit").rglob('*.py'))},
        "predictions": [
            {"id": row.id, "source_id": row.source_id, "gold_label": row.label.value,
             "evidence": row.evidence, "claim": row.claim, **asdict(prediction)}
            for row, prediction in zip(rows, predictions)
        ],
    }
