"""Strict JSONL loading for annotated evidence–claim pairs."""
import json
from pathlib import Path
from claimaudit.schemas import Example


def load_dataset(path: Path) -> list[Example]:
    examples: list[Example] = []
    seen: set[str] = set()
    sources: dict[str, str] = {}
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            try:
                row = json.loads(line)
                if not isinstance(row, dict):
                    raise ValueError("expected a JSON object")
                example = Example(**row)
                if example.id in seen:
                    raise ValueError(f"duplicate id: {example.id}")
                if example.source_id in sources and sources[example.source_id] != example.evidence:
                    raise ValueError(f"inconsistent evidence for source_id: {example.source_id}")
                seen.add(example.id)
                sources[example.source_id] = example.evidence
                examples.append(example)
            except (ValueError, TypeError) as exc:
                raise ValueError(f"{path}:{line_number}: {exc}") from exc
    if not examples:
        raise ValueError(f"{path}: dataset is empty")
    return examples
