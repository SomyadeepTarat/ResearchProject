"""Author-defined controlled fixtures, NOT independently annotated paper excerpts."""
import argparse
from dataclasses import asdict
from decimal import Decimal
import json
from pathlib import Path

from claimaudit.schemas import Example, Label
from claimaudit.evaluation.splits import create_manifest


def families(i: int) -> dict[str, tuple[str, list[str], list[str]]]:
    a, b = f'Model A{i}', f'Model B{i}'
    x, y = f'System X{i}', f'System Y{i}'
    high, low = 85 + i, 75 + i
    fast, slow = 10 + i, 20 + i
    groups = {}

    def add(name, evidence, claims, reasons):
        groups[name] = (evidence, claims, reasons)

    add('accuracy_pair', f'{a} achieved {high}% accuracy, exceeding {b} at {low}%.',
        [f'{a} achieved {high}% accuracy.', f'{a} achieved {low}% accuracy.',
         f'{b} achieved higher accuracy than {a}.', f'{a} was trained on {1000*i} samples.'],
        [f'Accuracy is explicitly {high}%.', f'{low}% belongs to B, not A.', f'{high} > {low}, so A exceeds B.', 'Training size is absent.'])
    add('latency_units', f'{x} had a mean latency of {fast} ms, lower than {y} at {slow} ms.',
        [f'{x} had a mean latency of {Decimal(fast)/1000} seconds.', f'{x} had a mean latency of {slow} ms.',
         f'{x} had higher mean latency than {y}.', f'{x} uses fewer CPU cores than {y}.'],
        [f'{fast} ms equals {Decimal(fast)/1000} seconds.', f'X has {fast} ms, not {slow} ms.', 'X has lower latency.', 'CPU core counts are absent.'])
    add('memory_units', f'{x} had memory usage of {i} GiB. {y} had memory usage of {i+2} GiB.',
        [f'{x} had memory of {i*1024} MiB.', f'{x} had memory of {i*1000} MiB.',
         f'{x} had greater memory usage than {y}.', f'{x} requires a GPU.'],
        ['GiB to MiB multiplies by 1024.', 'Multiplying by 1000 gives the wrong binary-unit value.', 'X has lower memory usage.', 'Hardware requirements are not stated.'])
    count_x, count_y = 60+3*i, 40+2*i
    add('count_partition', f'The trial enrolled {count_x+count_y} participants: {count_x} in group X{i} and {count_y} in group Y{i}.',
        [f'Group X{i} included {count_x} participants.', f'The trial enrolled {count_x+count_y+10} participants.',
         f'Group Y{i} had more participants than group X{i}.', 'Participants were randomly assigned to their groups.'],
        ['Explicit group count.', 'The total is increased by 10.', 'X has more participants than Y.', 'Assignment mechanism is absent.'])
    add('precision_separate', f'{a} achieved {high}% precision. {b} achieved {low}% precision.',
        [f'{a} had precision of {Decimal(high)/100}.', f'{b} achieved {high}% precision.',
         f'{a} had lower precision than {b}.', f'{a} has better recall than {b}.'],
        ['Equivalent proportion.', 'The value belongs to A, not B.', 'A has higher precision.', 'Recall is not reported.'])
    add('recall_paraphrase', f'The measured recall for {a} was {high}%; the corresponding result for {b} was {low}%.',
        [f'{b} recovered {low}% of the relevant items.', f'{a} achieved {high-5}% recall.',
         f'{b} had higher recall than {a}.', f'{a} was evaluated on multilingual data.'],
        ['Recall is the fraction of relevant items retrieved.', f'Recall is {high}%, not {high-5}%.', 'B has lower recall.', 'Language coverage is absent.'])
    add('f1_report', f'F1 results: {a} = {high}%; {b} = {low}%.',
        [f'{a} achieved an F1 score of {high}%.', f'{b} achieved an F1 score of {high}%.',
         f'{a} scored lower than {b} on F1.', f'The F1 difference was statistically significant.'],
        ['Explicit F1 result.', 'B is assigned the value for A.', 'A has the higher F1.', 'No uncertainty or significance test is supplied.'])
    add('throughput', f'{x} had throughput of {100+i*10} samples/s. {y} had throughput of {60+i*10} samples/s.',
        [f'{x} had higher throughput than {y}.', f'{x} had throughput of {60+i*10} samples/s.',
         f'{y} had higher throughput than {x}.', f'{x} consumes less energy per sample than {y}.'],
        ['X processes 40 more samples each second.', 'Y\'s throughput is attributed to X.', 'Y has lower throughput.', 'Energy consumption is absent.'])
    add('negated_comparison', f'{a} achieved {low}% accuracy, while {b} achieved {high}%; {a} did not outperform {b}.',
        [f'{a} did not outperform {b} in accuracy.', f'{a} achieved {high}% accuracy.',
         f'{a} outperformed {b} in accuracy.', f'{a} was fine-tuned after its initial training.'],
        ['The negated comparison is explicit.', 'The larger value belongs to B.', 'A has lower accuracy and did not outperform B.', 'Training history is absent.'])
    add('dataset_context', f'On Dataset Red, {a} achieved {high}% accuracy and {b} achieved {low}%. On Dataset Blue, {a} achieved {low}% accuracy and {b} achieved {high}%.',
        [f'On Dataset Blue, {a} achieved {low}% accuracy.', f'On Dataset Red, {a} achieved {low}% accuracy.',
         f'On Dataset Blue, {a} had higher accuracy than {b}.', 'Dataset Red contains more examples than Dataset Blue.'],
        ['Correct value and dataset.', 'A value from the wrong dataset is used.', 'B is higher on Blue.', 'Dataset sizes are absent.'])
    add('bounded_intervals', f'{x} had latency between {fast} and {fast+2} ms. {y} had latency between {slow} and {slow+2} ms.',
        [f'{x} had lower latency than {y}.', f'{x} had latency of {slow} ms.',
         f'{x} had higher latency than {y}.', f'{x} uses a faster processor than {y}.'],
        ['The nonoverlapping bounds establish the ordering.', 'The claimed value lies outside the stated interval.', 'Every allowed X value is lower than every Y value.', 'Processors are not described.'])
    add('equal_results', f'{a} achieved {high}% accuracy. {b} achieved {high}% accuracy.',
        [f'{a} had the same accuracy as {b}.', f'{a} achieved {high-2}% accuracy.',
         f'{a} had higher accuracy than {b}.', f'{a} has fewer parameters than {b}.'],
        ['The accuracies are equal.', 'The claimed value is two percentage points too small.', 'Equal values contradict a strict higher claim.', 'Parameter counts are absent.'])
    q = Decimal('83') + Decimal(i)/10
    add('small_gap', f'{a} achieved {q}% accuracy. {b} achieved {q+Decimal("0.1")}% accuracy.',
        [f'{b} achieved {q+Decimal("0.1")}% accuracy.', f'{a} achieved {q+Decimal("0.1")}% accuracy.',
         f'{a} had higher accuracy than {b}.', 'The reported accuracies were averaged over ten random seeds.'],
        ['Exact reported value.', 'The small numerical gap does not make the values equal.', 'B is 0.1 percentage point higher.', 'Number of seeds is absent.'])
    add('reordered_latency', f'At {slow} ms, {y} was slower than {x}, whose latency was {fast} ms.',
        [f'{x} had latency of {fast} ms.', f'{y} had latency of {fast} ms.',
         f'{y} had lower latency than {x}.', 'These latency measurements were collected under peak load.'],
        ['Explicit latency attributed to X.', 'The entities are swapped.', 'Y is slower and has higher latency.', 'Load conditions are absent.'])
    add('causal_gap', f'{x} had runtime of {fast} seconds. {y} had runtime of {slow} seconds. Only {x} used a cache; the study was observational.',
        [f'{x} had runtime of {fast} seconds.', f'{x} had runtime of {slow} seconds.',
         f'{x} had greater runtime than {y}.', f'The cache caused {x} to run faster than {y}.'],
        ['Explicit runtime.', 'The runtime belongs to Y.', 'X has lower runtime.', 'An observational association does not establish causation.'])
    return groups


def generate_examples() -> list[Example]:
    rows = []
    for i in range(1, 6):
        for family, (evidence, claims, reasons) in families(i).items():
            source_id = f'{family}-{i:02d}'
            for label, claim, rationale in zip(Label, claims, reasons, strict=True):
                rows.append(Example(f'{source_id}-{label.value}', source_id, evidence, claim, label,
                                    'programmatic_synthetic_v1; author_rules; not_independently_reviewed',
                                    rationale, group_id=f'template:{family}'))
    return sorted(rows, key=lambda row: row.id)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    rows = generate_examples()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    dataset = args.output_dir / 'examples.jsonl'
    dataset.write_text(''.join(json.dumps(asdict(row), ensure_ascii=False) + '\n' for row in rows), encoding='utf-8')
    manifest = create_manifest(rows, dataset, seed=42)
    (args.output_dir / 'splits.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'examples': len(rows), 'sources': len({r.source_id for r in rows}),
                      'groups': len({r.split_group for r in rows}), 'directory': str(args.output_dir)}))


if __name__ == '__main__':
    main()
