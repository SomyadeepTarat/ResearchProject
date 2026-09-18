"""Gold annotations are separate from the inputs visible to verifiers."""
from dataclasses import dataclass
from enum import StrEnum
import math
from typing import Protocol


class Label(StrEnum):
    SUPPORTED = "supported"
    NUMERIC_CONTRADICTION = "numeric_contradiction"
    COMPARISON_CONTRADICTION = "comparison_contradiction"
    UNSUPPORTED = "unsupported"


class Verdict(StrEnum):
    SUPPORTED = "supported"
    NOT_SUPPORTED = "not_supported"


def require_text(name: str, value: object) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a nonempty string")


@dataclass(frozen=True)
class ClaimInput:
    evidence: str
    claim: str

    def __post_init__(self) -> None:
        require_text("evidence", self.evidence)
        require_text("claim", self.claim)


@dataclass(frozen=True)
class Example:
    id: str
    source_id: str
    evidence: str
    claim: str
    label: Label
    provenance: str
    rationale: str

    def __post_init__(self) -> None:
        for name in ("id", "source_id", "evidence", "claim", "provenance", "rationale"):
            require_text(name, getattr(self, name))
        object.__setattr__(self, "label", Label(self.label))

    def to_input(self) -> ClaimInput:
        return ClaimInput(self.evidence, self.claim)

    @property
    def gold_verdict(self) -> Verdict:
        return Verdict.SUPPORTED if self.label == Label.SUPPORTED else Verdict.NOT_SUPPORTED


@dataclass(frozen=True)
class Prediction:
    method: str
    verdict: Verdict
    explanation: str
    score: float | None = None
    score_type: str | None = None
    class_scores: dict[str, float] | None = None

    def __post_init__(self) -> None:
        require_text("method", self.method)
        require_text("explanation", self.explanation)
        object.__setattr__(self, "verdict", Verdict(self.verdict))
        if (self.score is None) != (self.score_type is None):
            raise ValueError("score and score_type must be supplied together")
        if self.score is not None:
            if isinstance(self.score, bool) or not isinstance(self.score, (int, float)) or not math.isfinite(self.score):
                raise ValueError("score must be finite")
            require_text("score_type", self.score_type)

        if self.class_scores is not None:
            if not isinstance(self.class_scores, dict) or set(self.class_scores) != {"entailment", "neutral", "contradiction"}:
                raise ValueError("class_scores must contain the three NLI labels")
            values = self.class_scores.values()
            if any(type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1 for value in values):
                raise ValueError("NLI probabilities must be finite and in [0, 1]")
            if not math.isclose(sum(values), 1.0, abs_tol=1e-6):
                raise ValueError("NLI probabilities must sum to 1")


class Verifier(Protocol):
    def verify(self, claim: ClaimInput) -> Prediction: ...
