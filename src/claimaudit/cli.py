"""Validate data or explicitly run baseline inference."""
import argparse
from collections import Counter
import json
from pathlib import Path
from claimaudit.config import ExperimentConfig
from claimaudit.evaluation.dataset import load_dataset
from claimaudit.schemas import Label


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--method", choices=("validate", "embedding", "nli"), default="validate")
    parser.add_argument("--output", type=Path, help="New JSON file for baseline predictions")
    args = parser.parse_args()
    if args.method != "validate":
        if args.output is None:
            parser.error("--output is required for baseline inference")
        if args.output.exists():
            parser.error(f"Output already exists: {args.output}; choose a new filename")
        try:
            from claimaudit.evaluation.baseline_run import run_baseline
            report = run_baseline(args.config, args.method)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("x", encoding="utf-8") as handle:
                json.dump(report, handle, indent=2, default=str, allow_nan=False)
                handle.write("\n")
        except (OSError, ValueError, TypeError, RuntimeError) as exc:
            parser.error(str(exc))
        print(json.dumps({"status": "inference_complete", "models_run": True,
                          "examples": len(report["predictions"]), "output": str(args.output),
                          "notice": report["notice"]}, indent=2))
        return
    if args.output is not None:
        parser.error("--output is only supported with --method embedding or nli")
    try:
        config = ExperimentConfig.load(args.config)
        examples = load_dataset(config.dataset)
    except (OSError, ValueError, TypeError) as exc:
        parser.error(str(exc))
    counts = Counter(example.label for example in examples)
    print(json.dumps({
        "status": "validated", "examples": len(examples),
        "sources": len({example.source_id for example in examples}),
        "labels": {label.value: counts[label] for label in Label},
        "seed": config.seed, "models_run": False,
    }, indent=2))


if __name__ == "__main__":
    main()
