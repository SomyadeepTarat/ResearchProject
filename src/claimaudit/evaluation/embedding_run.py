"""Backward-compatible embedding entry point."""
from pathlib import Path
from claimaudit.evaluation.baseline_run import run_baseline


def run_embedding(config_path: Path) -> dict:
    return run_baseline(config_path, "embedding")
