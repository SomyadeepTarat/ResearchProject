"""Small, fully anchored grammar for explicit quantitative assertions.

Unknown sentences cause abstention. This is not a general scientific-language parser.
"""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import re

ENTITY = r'(?:the trial|(?:model|system|method|group|treatment|algorithm) [a-z0-9][a-z0-9_-]*|[a-z][a-z0-9_-]*)'
METRIC = r'(?:mean latency|memory usage|f1 score|accuracy|precision|recall|latency|runtime|memory|throughput|participants|samples|f1)'
NUMBER = r'(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?'
UNIT = r'(?:%|percent|milliseconds?|ms|seconds?|s|microseconds?|us|bytes?|kb|mb|gb|kib|mib|gib|samples/s)'
VALUE = rf'(?P<number>{NUMBER})\s*(?P<unit>{UNIT})?'
HIGHER_IS_BETTER = {'accuracy', 'precision', 'recall', 'f1', 'throughput'}
LOWER_IS_BETTER = {'latency', 'mean latency', 'runtime', 'memory'}


@dataclass(frozen=True)
class Quantity:
    entity: str
    metric: str
    value: Decimal
    unit: str
    span: str


@dataclass(frozen=True)
class Comparison:
    left: str
    right: str
    metric: str
    direction: int  # +1: left > right, -1: left < right, 0: equal
    span: str


@dataclass(frozen=True)
class Parsed:
    quantities: tuple[Quantity, ...] = ()
    comparisons: tuple[Comparison, ...] = ()


def canonical_entity(text: str) -> str:
    return ' '.join(text.lower().split()).removeprefix('the ')


def canonical_metric(text: str) -> str:
    return {'f1 score': 'f1', 'memory usage': 'memory'}.get(text.lower(), text.lower())


def quantity(entity: str, metric: str, number: str, unit: str | None, span: str) -> Quantity | None:
    entity = canonical_entity(entity)
    if entity in {'it', 'they', 'we', 'this', 'that', 'these', 'those', 'he', 'she'}:
        return None
    metric = canonical_metric(metric)
    unit = (unit or '').lower()
    try:
        value = Decimal(number.replace(',', ''))
    except InvalidOperation:
        return None
    if metric in {'accuracy', 'precision', 'recall', 'f1'}:
        if unit in {'%', 'percent'}:
            value /= 100
        elif unit != '':
            return None
        if not 0 <= value <= 1:
            return None
        dimension = 'proportion'
    elif metric in {'latency', 'mean latency', 'runtime'}:
        factors = {'ms': '0.001', 'millisecond': '0.001', 'milliseconds': '0.001',
                   's': '1', 'second': '1', 'seconds': '1',
                   'us': '0.000001', 'microsecond': '0.000001', 'microseconds': '0.000001'}
        if unit not in factors:
            return None
        value *= Decimal(factors[unit])
        dimension = 'seconds'
    elif metric == 'memory':
        factors = {'byte': 1, 'bytes': 1, 'kb': 1000, 'mb': 1000000, 'gb': 1000000000,
                   'kib': 1024, 'mib': 1024**2, 'gib': 1024**3}
        if unit not in factors:
            return None
        value *= factors[unit]
        dimension = 'bytes'
    elif metric in {'participants', 'samples'}:
        if unit or value != value.to_integral_value():
            return None
        dimension = 'count'
    elif metric == 'throughput':
        if unit != 'samples/s':
            return None
        dimension = 'samples/second'
    else:
        return None
    return Quantity(entity, metric, value, dimension, span)


def match(pattern: str, text: str):
    return re.fullmatch(pattern, text, re.IGNORECASE)


def parse_quantity(text: str, span: str) -> Quantity | None:
    patterns = [
        rf'(?P<entity>{ENTITY}) (?:achieved|reported|had|has) {VALUE} (?P<metric>{METRIC})',
        rf'(?P<entity>{ENTITY}) (?:achieved|reported|had|has) (?:a |an )?(?P<metric>{METRIC}) of {VALUE}',
        rf'(?P<entity>{ENTITY}) (?:enrolled|included|had|has) {VALUE} (?P<metric>participants|samples)',
    ]
    for pattern in patterns:
        found = match(pattern, text)
        if found:
            return quantity(**found.groupdict(), span=span)
    return None


def parse_sentence(span: str) -> Parsed | None:
    text = ' '.join(span.strip().removesuffix('.').split())
    # A paired result reports two quantities and explicitly states their order.
    paired = match(
        rf'(?P<base>.+), (?P<relation>exceeding|outperforming|higher than|lower than|greater than|less than) '
        rf'(?P<entity>{ENTITY}) at {VALUE}', text,
    )
    if paired:
        first = parse_quantity(paired['base'], span)
        if first is None:
            return None
        second = quantity(paired['entity'], first.metric, paired['number'], paired['unit'], span)
        if second is None or first.entity == second.entity:
            return None
        relation = paired['relation'].lower()
        if relation == 'outperforming':
            direction = 1 if first.metric in HIGHER_IS_BETTER else -1 if first.metric in LOWER_IS_BETTER else None
            if direction is None:
                return None
        else:
            direction = -1 if relation in {'lower than', 'less than'} else 1
        # A self-contradictory passage must not drive an override.
        actual = (first.value > second.value) - (first.value < second.value)
        if actual != direction:
            return None
        return Parsed((first, second), (Comparison(first.entity, second.entity, first.metric, direction, span),))

    # Exact partition of a study count. All subgroup counts must be present and sum to the total.
    partition = match(rf'(?P<base>.+): (?P<groups>.+)', text)
    if partition:
        total = parse_quantity(partition['base'], span)
        if total is None or total.metric not in {'participants', 'samples'}:
            return None
        groups = re.split(r',\s*(?:and\s+)?|\s+and\s+', partition['groups'])
        quantities = [total]
        for group in groups:
            found = match(rf'(?P<number>{NUMBER}) in (?P<entity>{ENTITY})', group)
            if not found:
                return None
            item = quantity(found['entity'], total.metric, found['number'], None, span)
            if item is None:
                return None
            quantities.append(item)
        if len(quantities) < 3 or len({item.entity for item in quantities}) != len(quantities):
            return None
        if sum(item.value for item in quantities[1:]) != total.value:
            return None
        return Parsed(tuple(quantities))

    relation = match(
        rf'(?P<left>{ENTITY}) (?:had|has|achieved|showed) '
        rf'(?P<direction>higher|lower|greater|less|more|fewer) (?P<metric>{METRIC}) than (?P<right>{ENTITY})', text,
    )
    if relation:
        direction = -1 if relation['direction'].lower() in {'lower', 'less', 'fewer'} else 1
        return comparison_parse(relation, direction, span)
    same = match(rf'(?P<left>{ENTITY}) (?:had|has) the same (?P<metric>{METRIC}) as (?P<right>{ENTITY})', text)
    if same:
        return comparison_parse(same, 0, span)
    better = match(rf'(?P<left>{ENTITY}) outperformed (?P<right>{ENTITY}) in (?P<metric>{METRIC})', text)
    if better:
        metric = canonical_metric(better['metric'])
        direction = 1 if metric in HIGHER_IS_BETTER else -1 if metric in LOWER_IS_BETTER else None
        return comparison_parse(better, direction, span) if direction is not None else None
    item = parse_quantity(text, span)
    return Parsed((item,)) if item else None


def comparison_parse(found, direction: int, span: str) -> Parsed | None:
    left, right = canonical_entity(found['left']), canonical_entity(found['right'])
    if left == right or any(entity in {'it', 'they', 'we', 'this', 'that', 'these', 'those', 'he', 'she'} for entity in (left, right)):
        return None
    return Parsed(comparisons=(Comparison(left, right, canonical_metric(found['metric']), direction, span),))


def parse_text(text: str) -> Parsed | None:
    # Decimal points do not split sentences because they are not followed by whitespace.
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    quantities, comparisons = [], []
    for sentence in sentences:
        parsed = parse_sentence(sentence)
        if parsed is None:
            return None
        quantities.extend(parsed.quantities)
        comparisons.extend(parsed.comparisons)
    # Conflicting values for the same entity and metric indicate unmodeled context.
    values = {}
    for item in quantities:
        key = (item.entity, item.metric)
        if key in values and values[key] != (item.value, item.unit):
            return None
        values[key] = (item.value, item.unit)
    directions = {}
    for relation in comparisons:
        left, right = sorted((relation.left, relation.right))
        direction = relation.direction if relation.left == left else -relation.direction
        key = (left, right, relation.metric)
        if key in directions and directions[key] != direction:
            return None
        directions[key] = direction
        a, b = values.get((relation.left, relation.metric)), values.get((relation.right, relation.metric))
        if a is not None and b is not None:
            if a[1] != b[1] or (a[0] > b[0]) - (a[0] < b[0]) != relation.direction:
                return None
    return Parsed(tuple(quantities), tuple(comparisons))
