"""Conservative checks over fully parsed, explicitly aligned facts."""
from decimal import Decimal

from claimaudit.config import StructureConfig
from claimaudit.schemas import ClaimInput, StructuralCheck
from claimaudit.verification.parsing import Parsed, parse_text


def close(left: Decimal, right: Decimal, config: StructureConfig) -> bool:
    tolerance = max(Decimal(str(config.absolute_tolerance)),
                    Decimal(str(config.relative_tolerance)) * max(abs(left), abs(right)))
    return abs(left - right) <= tolerance


def result(name: str, status: str, explanation: str, claim: ClaimInput, spans=()) -> StructuralCheck:
    return StructuralCheck(name, status, explanation, tuple(dict.fromkeys(spans)), claim.claim)


def numeric_check(claim: ClaimInput, evidence: Parsed, parsed_claim: Parsed, config: StructureConfig) -> StructuralCheck:
    if len(parsed_claim.quantities) != 1 or parsed_claim.comparisons:
        return result('numeric', 'abstain', 'Claim is not one explicit quantitative assertion.', claim)
    target = parsed_claim.quantities[0]
    aligned = [item for item in evidence.quantities
               if (item.entity, item.metric, item.unit) == (target.entity, target.metric, target.unit)]
    if not aligned:
        return result('numeric', 'abstain', 'No evidence quantity matches the entity, metric, and unit dimension.', claim)
    reference = aligned[0]
    agrees = target.value == reference.value if target.unit == 'count' else close(target.value, reference.value, config)
    explanation = (f'{target.entity} / {target.metric}: claim {target.value} {target.unit}; '
                   f'evidence {reference.value} {reference.unit}. '
                   + ('Values agree within tolerance.' if agrees else 'Aligned values contradict.'))
    return result('numeric', 'consistent' if agrees else 'contradiction', explanation, claim, [x.span for x in aligned])


def comparison_check(claim: ClaimInput, evidence: Parsed, parsed_claim: Parsed, config: StructureConfig) -> StructuralCheck:
    if len(parsed_claim.comparisons) != 1 or parsed_claim.quantities:
        return result('comparison', 'abstain', 'Claim is not one explicit comparison.', claim)
    target = parsed_claim.comparisons[0]
    directions, spans = [], []
    for item in evidence.comparisons:
        if item.metric != target.metric:
            continue
        if (item.left, item.right) == (target.left, target.right):
            directions.append(item.direction)
            spans.append(item.span)
        elif (item.left, item.right) == (target.right, target.left):
            directions.append(-item.direction)
            spans.append(item.span)
    left = [item for item in evidence.quantities if (item.entity, item.metric) == (target.left, target.metric)]
    right = [item for item in evidence.quantities if (item.entity, item.metric) == (target.right, target.metric)]
    if left and right and left[0].unit == right[0].unit:
        a, b = left[0], right[0]
        if a.unit != 'count' and a.value != b.value and close(a.value, b.value, config):
            return result('comparison', 'abstain', 'Aligned quantities differ by less than the comparison tolerance.', claim)
        directions.append(0 if a.value == b.value else 1 if a.value > b.value else -1)
        spans.extend([a.span, b.span])
    if not directions:
        return result('comparison', 'abstain', 'No aligned comparison or pair of quantities for both entities and metric.', claim)
    if len(set(directions)) != 1:
        return result('comparison', 'abstain', 'Evidence directions disagree or quantities are too close for the stated direction.', claim)
    direction = directions[0]
    agrees = direction == target.direction
    symbols = {-1: '<', 0: '=', 1: '>'}
    explanation = (f'{target.metric}: claim {target.left} {symbols[target.direction]} {target.right}; '
                   f'evidence {target.left} {symbols[direction]} {target.right}.')
    return result('comparison', 'consistent' if agrees else 'contradiction', explanation, claim, spans)


def check_structure(claim: ClaimInput, config: StructureConfig) -> tuple[StructuralCheck, ...]:
    evidence, parsed_claim = parse_text(claim.evidence), parse_text(claim.claim)
    checks = []
    for name, enabled, checker in (
        ('numeric', config.numeric_checks, numeric_check),
        ('comparison', config.comparison_checks, comparison_check),
    ):
        if not enabled:
            checks.append(result(name, 'disabled', 'Check disabled by experiment configuration.', claim))
        elif evidence is None or parsed_claim is None:
            checks.append(result(name, 'abstain', 'Evidence or claim is outside the grammar or contains conflicting facts.', claim))
        else:
            checks.append(checker(claim, evidence, parsed_claim, config))
    return tuple(checks)
