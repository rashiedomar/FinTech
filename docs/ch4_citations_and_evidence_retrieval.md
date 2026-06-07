Chapter 4 Citations And Evidence Retrieval
==========================================

Purpose
-------
This note explains two different things that are easy to confuse:

1. the **citations already present now**
2. the future **evidence retrieval** stage


What citations exist right now
------------------------------
The current non-LLM runtime already includes legal basis data in every triggered
rule result.

That legal basis comes from the frozen Layer 4 rule pack, which already stores:
- source law article
- paragraph
- article title
- obligation summary
- source clause text span

So when a rule fires now, the runtime can already say:
- which law article it came from
- what paragraph it came from
- what the source text says

This is why the current runtime reports can show:
- `금융소비자 보호에 관한 법률 제22조④`
- the exact summarized rule meaning
- the source clause span copied from the legal compilation pipeline

This is a **static citation path**.

It is static because:
- the citation was already attached during the legal compilation layers
- the runtime is not searching the law dynamically
- it is using the pre-linked legal basis frozen into Layer 4


What evidence retrieval will do later
-------------------------------------
Evidence retrieval is the next stage after deterministic non-LLM rule matching.

Its job is not to decide the first rule trigger from scratch.
Its job is to build a richer evidence package around the triggered result.

That means:

### 1. Fetch the best official law snippets
For a triggered rule, retrieval can pull:
- the exact current clause text
- neighboring paragraph context
- related decree clauses
- related supervisory rule clauses

### 2. Resolve delegated-detail gaps
Some Layer 3 or Layer 4 rules are weak because the law says:
- "as prescribed by Presidential Decree"
- or references external rules

Retrieval will help here by finding:
- the decree article
- the supervising regulation
- the related guidance clause

### 3. Build a better LLM context package
Right now the LLM stage would receive:
- the triggered rule
- the current static legal basis

With evidence retrieval, the LLM can receive:
- the triggered rule
- the exact official clause
- related subordinate law
- nearby legal context
- maybe internal policy text later

That improves:
- explanation quality
- rewrite quality
- citation quality
- auditability

### 4. Support human review
The reviewer should not only see:
- "rule X failed"

The reviewer should also see:
- exact supporting clause
- exact source title
- relevant neighboring context
- maybe a highlighted snippet

That is the real reviewer value of retrieval.


Simple split
------------

### Current runtime citations
- static
- already attached through Layer 4
- enough to prove legal grounding exists before LLM

### Future evidence retrieval
- dynamic
- expands the legal basis package
- adds decree / regulation / neighboring context
- improves LLM and reviewer support


Best short explanation
----------------------
The current system already has built-in legal citations because every Layer 4
rule is traceable back to a specific Chapter 4 law clause. Evidence retrieval
comes later to enrich that static legal basis with dynamically fetched official
snippets, subordinate rules, and surrounding context before the case is sent to
the LLM and human reviewer.

