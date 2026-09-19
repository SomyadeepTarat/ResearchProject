# Controlled synthetic dataset v1

This release contains **300 programmatically generated, author-labeled examples**, not excerpts from published papers. There are 75 source passages and 15 template families. Each source has exactly four claims: one supported, one numeric contradiction, one comparison contradiction, and one unsupported claim. Each label therefore has 75 examples.

The generator and mathematical templates are in `src/claimaudit/evaluation/synthetic.py`. Each row records its provenance and annotation rationale. Labels have **not been independently reviewed**. The generator contains five parameterized sources per family; these are not 300 independent observations.

## Families

- Accuracy pairs: altered quantities and swapped model values.
- Latency units: equivalent seconds/milliseconds and lower-is-better ordering.
- Memory units: binary GiB/MiB versus decimal scaling.
- Count partitions: totals and subgroup counts.
- Precision in separate sentences: percentages/proportions and entity alignment.
- Recall paraphrases: semantic reformulations outside the structural grammar.
- F1 reports: compact result listings.
- Throughput: explicit samples-per-second comparisons.
- Negated comparisons: explicit failure to outperform.
- Dataset context: the same entities rank differently on two datasets.
- Bounded intervals: disjoint ranges establish ordering.
- Equal results: strict ordering is contradicted by equal measurements.
- Small gaps: 0.1-percentage-point numerical differences.
- Reordered latency: value/entity association across clauses.
- Causal gap: observational co-occurrence does not establish causation.

A comparison contradiction can be reversed ordering or an asserted strict ordering where the source states equality. Numeric contradictions alter an explicit value or assert a value outside a stated interval. Unsupported claims add an unreported fact or causal explanation. The construction avoids intentionally mixing these error types in one claim.

## Frozen split

| Split | Examples | Sources | Whole template families | Per label |
| --- | ---: | ---: | ---: | ---: |
| train (reserved, unused) | 180 | 45 | 9 | 45 |
| dev (threshold selection) | 60 | 15 | 3 | 15 |
| test (evaluation) | 60 | 15 | 3 | 15 |

`group_id` identifies a complete template family. The split was created with seed 42 and recorded in `splits.json` before model evaluation. The manifest contains the dataset SHA-256, every example ID, and group assignments. The evaluator rejects changed data, missing/duplicate IDs, groups/sources crossing splits, and identical normalized evidence across splits.

Development families: count partitions, dataset context, recall paraphrases. Test families: accuracy pairs, bounded intervals, precision in separate sentences. All other families are reserved as training/development material for a future version; they are not used to train or tune this run.

Family separation applies within this release. Some grammar patterns were used in earlier smoke tests and parser design. The test set is therefore held out from threshold selection, **not guaranteed unseen by parser design**. Once results have been inspected, changes informed by those results require a new untouched evaluation set or an explicitly exploratory rerun.

## Limitations and next review

This dataset is balanced, templated, short, and synthetic. There may be lexical cues, limited linguistic diversity, and annotation blind spots. It cannot establish real-world error prevalence, scientific-paper performance, research novelty, or publication-ready superiority. The three test families are too few for strong uncertainty claims. Bootstrap intervals are exploratory summaries only.

For stronger evidence, independently annotate paper-derived claims, retain document IDs/citations and disagreements, include naturally occurring errors and varied supported paraphrases, and split at the document level. Do not choose new examples only because one method fails or the hybrid succeeds.

## Reproduce without overwriting

```sh
uv run python -m claimaudit.evaluation.synthetic --output-dir /tmp/claimaudit-controlled-reproduction
```

Generation is deterministic and requires a new output directory. Existing frozen data and manifests are never overwritten by this command. The 12 earlier smoke cases are separate from this dataset.
