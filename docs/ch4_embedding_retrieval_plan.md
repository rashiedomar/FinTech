Chapter 4 Embedding Retrieval Plan
==================================

Purpose
-------
This document explains the exact embedding and retrieval design for the current
Chapter 4 pipeline.

It answers:
- what we should embed
- what we should not embed
- how to chunk the legal material
- what metadata each chunk should carry
- what the retrieval query should look like
- what the minimal first production version should be


Current State
-------------
The current repo now has a working **local vector retrieval backend** for the
current Chapter 4 corpus.

What exists now:
- deterministic runtime review
- static legal citations from Layer 4
- static evidence package assembly from:
  - Layer 4 rule pack
  - parsed parent clause
  - same-article context
- embedding-ready legal corpus
- local embedding index built with `nlpai-lab/KURE-v1`
- metadata-aware cosine retrieval over legal chunks
- vector support attached to evidence packages when the local index exists

What does not exist yet:
- dynamic retrieval across subordinate legal materials
- decree / regulation / guideline corpora in the same index
- a separate ANN/vector database backend
- retrieval merged into a broader multi-source legal library

So the retrieval layer is:
- corpus-ready
- query-ready
- vectorized for the current Chapter 4 corpus
- still limited to the current official-law scope

Current model note:
- `nlpai-lab/KURE-v1` is now the default retrieval encoder
- rationale: Korean-first legal text retrieval is the current priority
- implementation path: `sentence-transformers`, not raw mean pooling
- prefix policy: no added `query:` / `passage:` prefixes for KURE


What Problem Embeddings Solve Here
----------------------------------
The deterministic engine already answers:
- which rule failed
- which SIR fields triggered
- which citation is linked to the rule

Embeddings are not needed to decide the first compliance result.

Embeddings are needed to improve the **supporting evidence layer**:
- find the best exact clause text
- pull nearby context
- later bring in Presidential Decrees
- later bring in supervisory regulations
- later bring in guidelines or enforcement examples

Short version:
- deterministic engine decides
- retrieval expands evidence
- LLM explains using the expanded evidence


What To Embed
-------------

### Phase 1: embed only official Chapter 4 grounded material
The first embedding corpus should come only from materials already trusted in
the repo:

1. parsed clause records
2. article-level rollups
3. rule-grounded legal chunks

Source files:
- `data/parsed/ch4_fincpa/law_fincpa_main_ch4_clause_records.jsonl`
- `data/finalized/ch4_fincpa/law_fincpa_main_ch4_layer4_mvp_rule_pack.jsonl`

### Why this is the right first scope
- it is official
- it is already reviewed by the team
- it is already connected to deterministic rules
- it keeps the retrieval story defensible

### Do not embed these in the first version
- runtime example ads as if they were legal knowledge
- public web marketing text as authority
- LLM-generated summaries as source law
- internal notes that are not legal authority


Chunk Strategy
--------------

### Chunk family 1. `parsed_clause`
One row per parsed clause record.

Use this when you want:
- the exact clause text
- the exact paragraph-level legal source

Strength:
- highest legal fidelity

Weakness:
- less operational phrasing than compiled rule chunks

### Chunk family 2. `article_rollup`
One row per article, combining all paragraphs in the article.

Use this when you want:
- nearby legal context
- article-level reading for humans or LLMs

Strength:
- better context than one paragraph alone

Weakness:
- larger and less focused

### Chunk family 3. `rule_grounded_clause`
One row per Layer 4 rule, combining:
- legal citation
- rule summary
- obligation summary
- source clause span
- parent clause text
- product and channel metadata

Use this when you want:
- the most operational retrieval result
- direct alignment with deterministic rule failures

Strength:
- best first retrieval target for current architecture

Weakness:
- partially compiled, not pure raw law


Recommended First Retrieval Index
---------------------------------
The first production retrieval index should prioritize:

1. `rule_grounded_clause`
2. `parsed_clause`
3. `article_rollup`

Reason:
- failed cases already come with a rule ID
- rule-grounded chunks speak the same language as the runtime
- parsed clauses and article rollups then expand legal support


Metadata To Store Per Chunk
---------------------------
Every embedding chunk should carry at least:
- `chunk_id`
- `chunk_type`
- `source_type`
- `source_title`
- `source_pdf`
- `article_id`
- `paragraph_id`
- `article_title`
- `section_id`
- `section_title`
- `page_start`
- `citation_label`
- `rule_id`
- `rule_family`
- `logic_type`
- `detection_target`
- `product_scope`
- `channel_scope`
- `sir_candidate_fields`
- `delegated_detail_hint`
- `metadata_filters`
- `retrieval_text`

Why metadata matters:
- vector similarity alone is not enough
- legal retrieval needs scope filters
- we often already know article family, rule family, or detection target


What Query We Should Build
--------------------------
We should not query the vector index with only the raw ad text.

The query should be built **after** deterministic runtime evaluation.

For each failed or uncertain rule, build one retrieval query containing:
- original content text
- final decision
- rule ID
- rule family
- logic type
- failure reason
- finding fields
- known citation label
- rule summary
- source clause span

This makes retrieval:
- targeted
- explainable
- aligned with the legal engine


Recommended Retrieval Flow
--------------------------

### Step 1. Deterministic review runs first
Do not search the legal library before the rule engine.

The engine first produces:
- failed rule IDs
- failed reasons
- missing fields
- known citations

### Step 2. Build one query per failed or uncertain rule
If two rules fail, build two retrieval queries.

This keeps evidence focused instead of mixing all legal issues into one big
semantic search.

### Step 3. Apply metadata filtering before or with vector search
At minimum, filter by:
- `article_id` when known
- `rule_family`
- `logic_type`
- product scope
- channel scope

This reduces noise.

### Step 4. Vector search
Search across:
- `rule_grounded_clause`
- `parsed_clause`
- `article_rollup`

### Step 5. Merge and rerank
Prefer results in this order:
- exact known rule-grounded citation match
- exact parsed clause match
- same-article context
- broader article support

### Step 6. Build final evidence package
The final evidence package should contain:
- top exact legal support
- same-article context
- any related subordinate-law chunk later


Minimal First Version
---------------------
The minimal first real embedding version should do only this:

1. build the current embedding-ready corpus
2. compute vectors for the current corpus
3. store them in a simple vector index
4. build one retrieval query per failed rule
5. return top `k` results with metadata filters

That is enough for a credible v1.

What v1 does **not** need yet:
- hybrid BM25 + vector fusion
- cross-encoder reranking
- multilingual benchmark suite
- case-law retrieval
- enforcement-case retrieval


What Has Already Been Added To The Repo
--------------------------------------
This repo now includes:

### Corpus builder
- `scripts/build_ch4_embedding_corpus.py`

Output:
- `data/retrieval/ch4_fincpa/ch4_embedding_corpus.jsonl`
- `data/retrieval/ch4_fincpa/ch4_embedding_manifest.json`

### Retrieval query builder
- `scripts/build_ch4_retrieval_queries.py`

Output:
- `data/retrieval/ch4_fincpa/ch4_example_retrieval_queries.jsonl`
- `data/retrieval/ch4_fincpa/ch4_example_retrieval_query_manifest.json`

### Shared retrieval logic
- `src/safeguard_ai/ch4_retrieval.py`

### Real local vector index builder
- `scripts/build_ch4_embedding_index.py`

Index outputs:
- `data/retrieval/ch4_fincpa/ch4_embedding_index_rows.jsonl`
- `data/retrieval/ch4_fincpa/ch4_embedding_index_embeddings.npy`
- `data/retrieval/ch4_fincpa/ch4_embedding_index_manifest.json`

So the repo now has:
- an embedding-ready corpus
- a retrieval-ready query contract
- a working local vector backend for the current legal corpus


Current Corpus Design In This Repo
----------------------------------
The generated corpus contains three chunk types:
- `parsed_clause`
- `article_rollup`
- `rule_grounded_clause`

That means the first retrieval backend can be added without redesigning the
legal data model.


How To Plug In A Real Embedding Backend Later
---------------------------------------------
Once the team decides the embedding provider, the next code layer should:

1. read `ch4_embedding_corpus.jsonl`
2. compute embeddings from `retrieval_text`
3. store vectors plus metadata
4. expose a retrieval function like:
   - `retrieve_evidence(query_row, top_k=5)`

The return shape should preserve:
- `chunk_id`
- `chunk_type`
- `score`
- `citation_label`
- `article_id`
- `paragraph_id`
- `retrieval_text`
- metadata

That output can then be merged into `build_evidence_package()`.


Recommended Architecture Split
------------------------------

### Deterministic core
- Chapter 4 runtime
- first-pass legal decision

### Retrieval layer
- vector evidence expansion
- legal context gathering

### LLM layer
- explanation only
- rewrite/advisory only

### Human layer
- final operational decision

This keeps retrieval in the correct place:
- after rule trigger
- before advisory explanation


What “Finished” Means For Embeddings
-----------------------------------
We should only say the embedding layer is fully finished when all of these are true:

1. embedding-ready corpus exists
2. vectors are computed
3. vector index exists
4. retrieval queries are built from real failed cases
5. top-k legal results are returned with metadata
6. evidence package actually consumes those results

Right now, only:
- `1`
- `2`
- the query side of `4`
- and `5`

are done for the current Chapter 4 corpus.

`6` is partially done because the evidence package now attaches retrieved
support when the index exists, but the retrieval scope is still only the
current Chapter 4 official-law corpus.


Best Short Explanation
----------------------
The deterministic engine already knows which legal rule failed. The embedding
layer is the next support layer: it should semantically retrieve the best
supporting law chunks around that failure. In this repo, the corpus, query
contract, local embedding index, and metadata-aware cosine retrieval backend are
now implemented for the current Chapter 4 legal corpus; the next expansion is
to add subordinate legal sources and broader multi-source retrieval.
