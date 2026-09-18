# Dataset contract

smoke.jsonl contains 12 handwritten synthetic cases (3 per label), from 3 invented source passages. These are plumbing fixtures, not paper excerpts or benchmark evidence. Do not use them to tune or report research performance.

Each line is an object with id, source_id, evidence, claim, label, provenance, and rationale. IDs must be unique. A source_id identifies one evidence passage. Future paper-derived examples should also retain document identity and source citation in provenance, with a documented mapping for document-level splitting.

- supported: the supplied evidence entails the whole claim.
- numeric_contradiction: a quantity contradicts the evidence for the same entity, metric, and context.
- comparison_contradiction: a comparison reverses the relationship in the evidence.
- unsupported: evidence neither entails nor explicitly contradicts the claim within the scoped taxonomy.

For the initial ~300-case study, target approximately 75 examples per class. Keep claims atomic and error types exclusive; exclude or separately annotate mixed/other contradictions. Include paraphrased supported controls, equivalent units, entity swaps, lower-is-better metrics, and irrelevant numbers. Independently review annotations where possible and retain disagreements.

Split by original document (or source family for synthetic passages), keeping all variants together. Freeze held-out test IDs before threshold tuning. The 12 smoke cases remain separate. A balanced controlled dataset does not estimate real-world error prevalence.
