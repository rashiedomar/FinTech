Korean Public Retrieval Benchmark Report
=======================================

Profile: `core`
Task count: `3`

Benchmark scope
---------------
- Public Korean retrieval tasks from the KURE / MTEB benchmark family
- Model comparison: `nlpai-lab/KURE-v1` vs `intfloat/multilingual-e5-small`
- Main score reported here: `ndcg_at_10`
- Internal add-on check: exact top-1 rule recovery on the Chapter 4 failed-rule retrieval queries

Skipped Public Tasks
--------------------
- `MultiLongDocRetrieval`: Excluded from the core profile because it is substantially slower than the short public tasks and was not completed within the current run window.
- `XPQARetrieval`: Excluded from the core profile because it evaluates multiple Korean-involved retrieval directions and takes materially longer than the short public tasks.
- `BelebeleRetrieval`: Skipped from the runnable fast profile because MTEB 2.15.4 fails to auto-select the Korean HF dataset config for this task.
- `MIRACLRetrieval`: Excluded from the fast profile because it is a known long-running leaderboard task with a very large corpus.
- `MrTidyRetrieval`: Excluded from the fast profile because it is a known long-running leaderboard task.

Average Results
---------------

| model | avg ndcg@10 | avg recall@10 | avg precision@10 | avg mrr@10 |
|---|---:|---:|---:|---:|
| `nlpai-lab/KURE-v1` | 0.82997 | 0.93005 | 0.11739 | 0.80913 |
| `intfloat/multilingual-e5-small` | 0.76298 | 0.89272 | 0.11216 | 0.73694 |

Per-Task Results
----------------

| task | KURE ndcg@10 | e5-small ndcg@10 | KURE recall@10 | e5-small recall@10 |
|---|---:|---:|---:|---:|
| `Ko-StrategyQA` | 0.79990 | 0.75157 | 0.85963 | 0.82169 |
| `AutoRAGRetrieval` | 0.87076 | 0.80068 | 0.98246 | 0.94737 |
| `PublicHealthQA` | 0.81925 | 0.73668 | 0.94805 | 0.90909 |

Internal Chapter 4 Retrieval Check
----------------------------------
- query count: `8`
- top-1 exact rule hits: `8`
- top-1 exact rule hit rate: `1.00000`

Interpretation
--------------
- The public benchmark section shows broad Korean retrieval quality on external datasets.
- The internal Chapter 4 check shows whether the embedding retriever preserves exact rule alignment for this product's legal evidence flow.
- If KURE beats e5-small on both the public benchmark average and the internal check stays perfect, the switch is justified for the current Korean legal scope.

Output Files
------------
- [Ko-StrategyQA result](/data/omar/RESEARCH/JB_hachkaton/data/benchmarks/ko_public_retrieval/kure_v1/nlpai-lab__KURE-v1/d14c8a9423946e268a0c9952fecf3a7aabd73bd9/Ko-StrategyQA.json)
- [AutoRAGRetrieval result](/data/omar/RESEARCH/JB_hachkaton/data/benchmarks/ko_public_retrieval/kure_v1/nlpai-lab__KURE-v1/d14c8a9423946e268a0c9952fecf3a7aabd73bd9/AutoRAGRetrieval.json)
- [PublicHealthQA result](/data/omar/RESEARCH/JB_hachkaton/data/benchmarks/ko_public_retrieval/kure_v1/nlpai-lab__KURE-v1/d14c8a9423946e268a0c9952fecf3a7aabd73bd9/PublicHealthQA.json)
- [Ko-StrategyQA result](/data/omar/RESEARCH/JB_hachkaton/data/benchmarks/ko_public_retrieval/multilingual_e5_small/intfloat__multilingual-e5-small/no_revision_available/Ko-StrategyQA.json)
- [AutoRAGRetrieval result](/data/omar/RESEARCH/JB_hachkaton/data/benchmarks/ko_public_retrieval/multilingual_e5_small/intfloat__multilingual-e5-small/no_revision_available/AutoRAGRetrieval.json)
- [PublicHealthQA result](/data/omar/RESEARCH/JB_hachkaton/data/benchmarks/ko_public_retrieval/multilingual_e5_small/intfloat__multilingual-e5-small/no_revision_available/PublicHealthQA.json)
