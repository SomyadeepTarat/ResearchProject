# Reserved ScopeGuard evaluation

Frozen on 19 October 2026 before the new BDD, SMT and ProbLog implementations were evaluated. `freeze.json` records the SHA-256 and seed (20261019). Do not regenerate or tune against this set. This is a small reserved internal benchmark, not a blinded external benchmark.

24 sparse, three-way, multi-context topologies differ from the original six development templates. Their labels come from the existing exhaustive oracle, not independent human annotation. The same assistant designed the implementation and fixtures; the development/holdout separation therefore provides limited evidence of generalization.

12 claims use manually transcribed values from two actual paper tables. Annotation was performed by the assistant, checked visually against the paper pages, and has NOT received independent human review. Claims are authored evaluation fixtures, not assertions that the papers contain erroneous claims. All predicates must hold in one listed configuration. The closed domain is only the explicitly selected rows, not the entire original paper/table.

- Vaswani et al., Attention Is All You Need (2017), https://arxiv.org/pdf/1706.03762, Table 3, printed page 9. Base: PPL 4.92, BLEU 25.8, parameters 65 million. Big: PPL 4.33, BLEU 26.4, parameters 213 million. These are English-German newstest2013 development results; they are not the headline test-set BLEU scores.
- He et al., Deep Residual Learning for Image Recognition (2015), https://arxiv.org/pdf/1512.03385, Table 6, printed page 7. CIFAR-10 with augmentation: ResNet-20 error 8.75%, parameters 0.27 million; ResNet-56 6.97%, 0.85 million; ResNet-1202 7.93%, 19.4 million. The ResNet-110 rows (best versus mean) are intentionally excluded from this finite domain.

Each paper contributes two supported, three contradicted and one insufficient claim. Missing energy/latency measurements remain unknown. Six contradicted cases include cross-row conjunctions and impossible thresholds. There is no ambiguous extraction in these 12 cases, so they do not validate real-world source-choice extraction or clarification.

`python scripts/freeze_scope_holdout.py` checks/reproduces the deterministic fixture content and refuses to overwrite differing frozen inputs. The benchmark also adds eight explicitly synthetic scaling controls; those are reported separately from the reserved inputs. Uniform ProbLog weights are enumeration weights, not empirical probabilities of a source interpretation being correct.
