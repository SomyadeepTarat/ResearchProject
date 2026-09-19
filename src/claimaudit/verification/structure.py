"""Reuse NLI; only explicit structured contradictions can override support."""
from collections.abc import Sequence

from claimaudit.baselines.nli import NLIVerifier
from claimaudit.config import NLIConfig, StructureConfig
from claimaudit.schemas import ClaimInput, Prediction, Verdict
from claimaudit.verification.checks import check_structure


class StructureAwareVerifier:
    def __init__(self, nli_config: NLIConfig, config: StructureConfig, nli: NLIVerifier | None = None) -> None:
        self.config = config
        self.nli = nli if nli is not None else NLIVerifier(nli_config)

    def verify(self, claim: ClaimInput) -> Prediction:
        return self.verify_many([claim])[0]

    def verify_many(self, claims: Sequence[ClaimInput]) -> list[Prediction]:
        if not claims:
            return []
        base = self.nli.verify_many(claims)
        if len(base) != len(claims):
            raise ValueError('NLI returned an unexpected number of predictions')
        return fuse_predictions(claims, base, self.config)


def fuse_predictions(claims: Sequence[ClaimInput], base: Sequence[Prediction], config: StructureConfig) -> list[Prediction]:
    """Apply the same fusion policy to saved NLI outputs without rerunning the model."""
    if len(base) != len(claims):
        raise ValueError('NLI returned an unexpected number of predictions')
    output = []
    for item, prediction in zip(claims, base):
        checks = check_structure(item, config)
        contradictions = [check for check in checks if check.status == 'contradiction']
        verdict = Verdict.NOT_SUPPORTED if contradictions else prediction.verdict
        explanation = prediction.explanation + ' '
        explanation += ('Structured contradiction: ' + ' '.join(check.explanation for check in contradictions)
                        if contradictions else 'No structural contradiction established; retained NLI verdict.')
        output.append(Prediction(
            method='structure-aware', verdict=verdict, explanation=explanation,
            score=prediction.score,
            score_type='nli_entailment_probability' if prediction.score is not None else None,
            class_scores=dict(prediction.class_scores) if prediction.class_scores is not None else None,
            checks=checks, base_verdict=prediction.verdict,
        ))
    return output
