"""Cosine similarity baseline. Similarity scores are not probabilities of support."""
from collections.abc import Sequence
import math
from typing import Protocol

from claimaudit.config import EmbeddingConfig
from claimaudit.schemas import ClaimInput, Prediction, Verdict


class Encoder(Protocol):
    def encode(self, texts: list[str]) -> Sequence[Sequence[float]]: ...


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) == 0 or len(left) != len(right):
        raise ValueError("Embedding vectors must be nonempty and have equal dimensions")
    if not all(math.isfinite(float(x)) for x in (*left, *right)):
        raise ValueError("Embedding vectors must be finite")
    left_norm = math.hypot(*left)
    right_norm = math.hypot(*right)
    if left_norm == 0 or right_norm == 0:
        raise ValueError("Embedding vectors must have nonzero norms")
    score = math.fsum((a / left_norm) * (b / right_norm) for a, b in zip(left, right))
    return max(-1.0, min(1.0, score))


class SentenceTransformerEncoder:
    """Lazy optional dependency; reject overlength inputs instead of truncating."""

    def __init__(self, config: EmbeddingConfig) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError("Install the model extra: uv sync --extra models") from exc
        self.config = config
        self.model = SentenceTransformer(
            config.model_id, revision=config.revision, device=config.device,
            cache_folder=str(config.cache_dir), local_files_only=config.local_files_only,
            trust_remote_code=False,
        )
        self.model.eval()

    def encode(self, texts: list[str]) -> Sequence[Sequence[float]]:
        # Including special tokens makes the check match the actual model input.
        tokens = self.model.tokenizer(texts, truncation=False, padding=False)["input_ids"]
        for index, ids in enumerate(tokens):
            if len(ids) > self.model.max_seq_length:
                raise ValueError(
                    f"Input {index} has {len(ids)} tokens; model limit is "
                    f"{self.model.max_seq_length}. Supply shorter evidence; no text was truncated."
                )
        return self.model.encode(
            texts, batch_size=self.config.batch_size, show_progress_bar=False,
            convert_to_numpy=True, normalize_embeddings=True,
        )


class EmbeddingVerifier:
    def __init__(self, config: EmbeddingConfig, encoder: Encoder | None = None) -> None:
        self.config = config
        self.encoder = encoder if encoder is not None else SentenceTransformerEncoder(config)

    def verify(self, claim: ClaimInput) -> Prediction:
        return self.verify_many([claim])[0]

    def verify_many(self, claims: Sequence[ClaimInput]) -> list[Prediction]:
        if not claims:
            return []
        # Stable deduplication avoids repeatedly encoding a shared source passage.
        texts = list(dict.fromkeys(text for item in claims for text in (item.evidence, item.claim)))
        vectors = self.encoder.encode(texts)
        if len(vectors) != len(texts):
            raise ValueError("Encoder returned an unexpected number of vectors")
        lookup = dict(zip(texts, vectors))
        predictions = []
        for item in claims:
            score = cosine_similarity(lookup[item.evidence], lookup[item.claim])
            verdict = Verdict.SUPPORTED if score >= self.config.threshold else Verdict.NOT_SUPPORTED
            predictions.append(Prediction(
                method="embedding", verdict=verdict,
                explanation=f"Cosine similarity {score:.6f}; support threshold >= {self.config.threshold:g}.",
                score=score, score_type="cosine_similarity",
            ))
        return predictions
