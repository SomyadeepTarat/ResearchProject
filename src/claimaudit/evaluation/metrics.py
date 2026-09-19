"""Binary support metrics and paired whole-group bootstrap intervals."""
import math
from collections import Counter
from collections.abc import Sequence
import random

from claimaudit.schemas import Example, Label, Verdict


def macro_from_counts(counts: Sequence[int]) -> float:
    tn, fp, fn, tp = counts
    support_denominator = 2 * tp + fp + fn
    reject_denominator = 2 * tn + fp + fn
    return ((2 * tp / support_denominator if support_denominator else 0) +
            (2 * tn / reject_denominator if reject_denominator else 0)) / 2


def binary_counts(gold: Sequence[bool], predicted: Sequence[bool]) -> list[int]:
    if not gold or len(gold) != len(predicted):
        raise ValueError('Expected equally sized, nonempty gold and prediction lists')
    if any(type(value) is not bool for value in (*gold, *predicted)):
        raise ValueError('Binary metrics require booleans')
    counts = [0, 0, 0, 0]  # TN, FP, FN, TP with supported as positive
    for truth, prediction in zip(gold, predicted):
        counts[2 * int(truth) + int(prediction)] += 1
    return counts


def binary_metrics(rows: list[Example], predictions: Sequence[bool]) -> dict:
    from sklearn.metrics import confusion_matrix, precision_recall_fscore_support
    gold = [row.gold_verdict == Verdict.SUPPORTED for row in rows]
    tn, fp, fn, tp = binary_counts(gold, predictions)
    precision, recall, f1, _ = precision_recall_fscore_support(
        gold, predictions, labels=[False, True], average=None, zero_division=0,
    )
    label_counts = Counter(row.label.value for row in rows)
    errors = {}
    for label in Label:
        if label == Label.SUPPORTED:
            continue
        subset = [prediction for row, prediction in zip(rows, predictions) if row.label == label]
        errors[label.value] = sum(not value for value in subset) / len(subset) if subset else None
    return {'examples': len(rows), 'label_counts': dict(label_counts),
            'accuracy': (tp + tn) / len(rows), 'macro_f1': float(sum(f1) / 2),
            'support_precision': float(precision[1]), 'support_recall': float(recall[1]),
            'support_f1': float(f1[1]),
            'supported_false_rejection_rate': fn / (fn + tp) if fn + tp else None,
            'not_supported_false_acceptance_rate': fp / (fp + tn) if fp + tn else None,
            'error_type_detection_recall': errors,
            'confusion_matrix': confusion_matrix(gold, predictions, labels=[False, True]).tolist(),
            'confusion_label_order': ['not_supported', 'supported'],
            'confusion_axes': 'rows=gold, columns=predicted', 'zero_division': 0}


def select_threshold(scores: list[float], gold: list[bool], *, lower: float, upper: float,
                     default: float, split_name: str) -> dict:
    if split_name != 'dev':
        raise ValueError('Threshold selection is allowed only on development data')
    if not scores or len(scores) != len(gold) or set(gold) != {False, True}:
        raise ValueError('Development scores need both gold classes and matching lengths')
    if not all(math.isfinite(x) for x in (lower, upper, default)) or not lower <= default <= upper or any(not math.isfinite(x) or not lower <= x <= upper for x in scores):
        raise ValueError('Invalid threshold bounds or scores')
    candidates = {lower, upper, default, *scores}
    above_max = math.nextafter(max(scores), math.inf)
    if above_max <= upper:
        candidates.add(above_max)
    trace = []
    for threshold in sorted(candidates):
        value = macro_from_counts(binary_counts(gold, [score >= threshold for score in scores]))
        trace.append({'threshold': threshold, 'macro_f1': value})
    best = max(trace, key=lambda row: (row['macro_f1'], -abs(row['threshold'] - default), row['threshold']))
    return {**best, 'objective': 'binary_macro_f1', 'selected_on': 'dev',
            'rule': 'supported when score >= threshold',
            'tie_break': 'closest to original default; then larger threshold', 'candidates': trace}


def percentile(values: list[float], quantile: float) -> float:
    ordered = sorted(values)
    index = (len(ordered) - 1) * quantile
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (index - lower) * (ordered[upper] - ordered[lower])


def paired_group_bootstrap(rows: list[Example], methods: dict[str, list[bool]],
                           samples: int, seed: int, reference: str = 'nli') -> dict:
    if type(samples) is not int or samples < 1 or reference not in methods:
        raise ValueError('Bootstrap requires positive samples and a reference method')
    gold = [row.gold_verdict == Verdict.SUPPORTED for row in rows]
    for predictions in methods.values():
        binary_counts(gold, predictions)
    groups = sorted({row.split_group for row in rows})
    if len(groups) < 2:
        raise ValueError('Bootstrap requires at least two groups')
    indices = {group: [i for i, row in enumerate(rows) if row.split_group == group] for group in groups}
    group_counts = {method: [binary_counts([gold[i] for i in indices[group]],
                                          [predictions[i] for i in indices[group]]) for group in groups]
                    for method, predictions in methods.items()}
    draws = {method: [] for method in methods}
    randomizer = random.Random(seed)
    for _ in range(samples):
        selected = [randomizer.randrange(len(groups)) for _ in groups]
        for method, counts in group_counts.items():
            combined = [sum(counts[index][cell] for index in selected) for cell in range(4)]
            draws[method].append(macro_from_counts(combined))
    interval = lambda values: [percentile(values, .025), percentile(values, .975)]
    return {'resampling_unit': 'split_group', 'independent_groups': len(groups), 'samples': samples,
            'seed': seed, 'confidence_level': .95, 'interval_method': 'percentile',
            'warning': 'Few template groups and synthetic labels make these intervals exploratory, not population guarantees.',
            'macro_f1_intervals': {method: interval(values) for method, values in draws.items()},
            'paired_macro_f1_delta_vs_nli': {
                method: interval([a-b for a,b in zip(values, draws[reference])])
                for method, values in draws.items() if method != reference}}
