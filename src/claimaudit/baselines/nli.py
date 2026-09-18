"""NLI baseline: premise=evidence, hypothesis=claim; no gold annotations enter inference."""
from collections.abc import Mapping, Sequence
import math
from typing import Protocol

from claimaudit.config import NLIConfig
from claimaudit.schemas import ClaimInput, Prediction, Verdict

NLI_LABELS = frozenset({'entailment', 'neutral', 'contradiction'})


def resolve_labels(id2label: Mapping[int | str, str]) -> tuple[str, ...]:
    """Require descriptive labels; never guess what LABEL_0 means."""
    try:
        mapping = {int(key): value.lower().strip() for key, value in id2label.items()}
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError('Invalid NLI id2label mapping') from exc
    if set(mapping) != {0, 1, 2} or set(mapping.values()) != NLI_LABELS:
        raise ValueError('NLI id2label must map 0, 1, 2 to entailment, neutral, contradiction')
    return tuple(mapping[index] for index in range(3))


def probabilities(logits: Sequence[float], labels: Sequence[str]) -> dict[str, float]:
    if len(logits) != 3 or len(labels) != 3 or set(labels) != NLI_LABELS:
        raise ValueError('Expected three NLI logits and three unique NLI labels')
    if not all(math.isfinite(value) for value in logits):
        raise ValueError('NLI logits must be finite')
    maximum = max(logits)
    exponents = [math.exp(value - maximum) for value in logits]
    total = math.fsum(exponents)
    return {label: value / total for label, value in zip(labels, exponents)}


class NLIBackend(Protocol):
    def predict(self, claims: Sequence[ClaimInput]) -> list[dict[str, float]]: ...


class TransformersNLIBackend:
    def __init__(self, config: NLIConfig) -> None:
        try:
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
        except ImportError as exc:
            raise RuntimeError('Install the model extra: uv sync --extra models') from exc
        self.torch = torch
        self.config = config
        options = dict(revision=config.revision, cache_dir=str(config.cache_dir),
                       local_files_only=config.local_files_only, trust_remote_code=False)
        self.tokenizer = AutoTokenizer.from_pretrained(config.model_id, **options)
        self.model = AutoModelForSequenceClassification.from_pretrained(config.model_id, **options)
        self.labels = resolve_labels(self.model.config.id2label)
        if self.model.config.num_labels != 3:
            raise ValueError('Expected a three-class NLI model')
        self.model.to(config.device)
        self.model.eval()
        capacity = self.model.config.max_position_embeddings
        # RoBERTa reserves position IDs through padding_idx, unlike BERT.
        if self.model.config.model_type == 'roberta':
            capacity -= self.model.config.pad_token_id + 1
        self.max_length = min(config.max_length, self.tokenizer.model_max_length, capacity)
        if self.max_length < 4:
            raise ValueError('Invalid NLI model token capacity')

    def predict(self, claims: Sequence[ClaimInput]) -> list[dict[str, float]]:
        outputs = []
        for start in range(0, len(claims), self.config.batch_size):
            batch = claims[start:start + self.config.batch_size]
            tokens = self.tokenizer(
                [item.evidence for item in batch], [item.claim for item in batch],
                truncation=False, padding=False,
            )
            for offset, ids in enumerate(tokens['input_ids']):
                if len(ids) > self.max_length:
                    raise ValueError(
                        f'NLI pair {start + offset} has {len(ids)} tokens; limit is {self.max_length}. '
                        'Supply shorter evidence; no text was truncated.'
                    )
            features = self.tokenizer.pad(tokens, padding=True, return_tensors='pt').to(self.config.device)
            with self.torch.inference_mode():
                logits = self.model(**features).logits.detach().cpu().tolist()
            if len(logits) != len(batch):
                raise ValueError('NLI model returned an unexpected number of rows')
            outputs.extend(probabilities(row, self.labels) for row in logits)
        return outputs


class NLIVerifier:
    def __init__(self, config: NLIConfig, backend: NLIBackend | None = None) -> None:
        self.config = config
        self.backend = backend if backend is not None else TransformersNLIBackend(config)

    def verify(self, claim: ClaimInput) -> Prediction:
        return self.verify_many([claim])[0]

    def verify_many(self, claims: Sequence[ClaimInput]) -> list[Prediction]:
        if not claims:
            return []
        scores = self.backend.predict(claims)
        if len(scores) != len(claims):
            raise ValueError('NLI backend returned an unexpected number of rows')
        predictions = []
        for row in scores:
            # Schema validation rejects invalid probability dictionaries before use.
            validated = Prediction('nli', Verdict.NOT_SUPPORTED, 'NLI scores', class_scores=row)
            entailment = validated.class_scores['entailment']
            verdict = Verdict.SUPPORTED if entailment >= self.config.threshold else Verdict.NOT_SUPPORTED
            predictions.append(Prediction(
                method='nli', verdict=verdict,
                explanation=f'NLI entailment probability {entailment:.6f}; support threshold >= {self.config.threshold:g}.',
                score=entailment, score_type='entailment_probability', class_scores=dict(row),
            ))
        return predictions
