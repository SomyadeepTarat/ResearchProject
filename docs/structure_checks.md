# Structure-aware verification: scope and decision rule

The hybrid runs the unchanged NLI verifier, then checks parsed facts. An enabled structural contradiction sets the final verdict to `not_supported`. Otherwise the NLI verdict is retained. A consistent structured fact never promotes an NLI rejection to support. Each prediction retains `base_verdict`, the original NLI class probabilities, and the NLI entailment score (`score_type = nli_entailment_probability`). This score is not a hybrid confidence estimate.

Each numerical/comparison check reports `consistent`, `contradiction`, `abstain`, or `disabled`, an explanation, the original claim, and evidence spans for conclusive checks. A missing entity or metric produces abstention, not a contradiction. Absence of a contradiction is not proof of support. Both checks inspect only evidence and claim; gold labels are unavailable to them.

## Explicit grammar

This milestone uses a small standard-library parser with full-sentence matching. It is deliberately limited and is not a general scientific-language parser. Examples of accepted forms:

| Assertion | Example |
| --- | --- |
| Metric value | `Model A achieved 84.2% accuracy.` |
| Metric-first value | `System C had a mean latency of 12 ms.` |
| Count | `Group X included 70 participants.` |
| Paired metric values | `Model A achieved 84.2% accuracy, exceeding Model B at 81.4%.` |
| Paired lower values | `System C had a mean latency of 12 ms, lower than System D at 20 ms.` |
| Count partition | `The trial enrolled 120 participants: 70 in group X and 50 in group Y.` |
| Direct comparison | `Model B achieved higher accuracy than Model A.` |
| Reversed entity order | `Model A had lower accuracy than Model B.` |
| Equality | `Model A had the same accuracy as Model B.` |
| Explicit performance comparison | `System C outperformed System D in latency.` |

Entities must be single-token names (e.g. BERT), a category plus one identifier (model, system, method, group, treatment, algorithm), or “the trial”. Names are matched case-insensitively with no alias resolution or coreference. Pronouns abstain. These restrictions reduce scope confusion but limit coverage.

Supported metrics are accuracy, precision, recall, F1, latency, mean latency, runtime, memory, throughput, participants, and samples. `F1 score` and `memory usage` normalize to F1 and memory. **Mean latency and latency remain distinct.** No other synonym or metric equivalence is inferred.

Numerical alignment requires the same entity, metric, and unit dimension. A number appearing elsewhere in the source is insufficient. Comparisons align both entities and the metric, reversing direction when entity order is reversed. A relation can come from an explicit source comparison or two aligned quantities. Equal quantities contradict a strict higher/lower claim; unequal quantities within numerical tolerance cause comparison abstention.

Higher/lower always describe numerical direction. For the explicit word “outperformed”, this grammar assumes accuracy, precision, recall, F1, and throughput are higher-is-better; latency, mean latency, runtime, and memory are lower-is-better. This is an explicit modeling assumption, not a universal interpretation of performance. Comparisons of participant/sample counts use more/fewer, not performance language.

## Units and tolerance

- Percent/percent-sign metrics normalize to proportions; bare values in [0, 1] for accuracy/precision/recall/F1 are interpreted as proportions. This convention is explicit; other scales are unsupported.
- Milliseconds, seconds, and microseconds normalize to seconds.
- Bytes, KB/MB/GB, and KiB/MiB/GiB normalize to bytes; decimal and binary units remain distinct.
- Throughput supports samples/s only. Participant/sample counts must be nonnegative integers and require exact equality, even for large counts.
- Continuous values use `max(absolute_tolerance, relative_tolerance * max(abs(a), abs(b)))`, with defaults 1e-9 in normalized base units and 1e-6 respectively. Decimal arithmetic avoids binary rounding during unit conversion. Defaults are engineering choices, not tuned performance settings.

## Abstention and limitations

Every source sentence must match the grammar; an unparsed sentence causes both checks to abstain. This avoids silently dropping contextual sentences. A claim must be a single quantitative assertion or comparison, not a compound assertion. Negation, approximate values, intervals, statistical uncertainty, scientific notation, negative numbers, dataset/time qualifiers, and unsupported sentence forms abstain. Contradictory evidence values or directions also abstain. Explicit count partitions must be complete and sum to the reported total. Large values with comma separators inside partition lists are currently unsupported.

This parser cannot guarantee semantic correctness outside its defined grammar. It does not resolve paper sections, dataset names, entity aliases, uncertainty, causality, or temporal context. It does not assign the dataset's four-way gold label. The explanation indicates which structural check fired; multiple checks could be relevant in a future broader grammar. Parser coverage and false positives must be measured alongside detection performance.

## Ablations and later evaluation

In a copy of `experiments/structure_smoke.toml`, set `numeric_checks` and `comparison_checks` independently:

| Numerical | Comparison | Method variant |
| --- | --- | --- |
| false | false | NLI decision unchanged |
| true | false | NLI with numerical checks |
| false | true | NLI with comparison checks |
| true | true | Full hybrid |

Run all variants on identical frozen document-grouped splits with identical NLI settings. Report check coverage/abstentions, overrides, corrected errors, newly introduced errors, and supported-case false positives. Keep parser-development examples out of the final test set. The smoke examples and unit tests influenced implementation and are not held-out research evidence.
