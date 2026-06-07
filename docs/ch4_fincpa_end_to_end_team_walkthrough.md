Chapter 4 End-To-End Team Walkthrough
=====================================

Purpose
-------
This note explains the current scope from the official law input all the way to
the first working non-LLM runtime review output.

This is the clean story to show the team:

1. official law PDF in
2. deterministic parsing
3. Layer 1 legal metadata
4. Layer 2 obligation decomposition
5. Layer 3 rule/SIR-link candidates
6. Layer 4 final MVP rule pack and SIR schema
7. runtime input schema
8. runtime SIR extraction
9. deterministic Layer 4 rule matching
10. handoff to the next stages: evidence retrieval, LLM advisory, human review


What we completed
-----------------
We completed:

- the **legal compilation side**
- the **first non-LLM runtime execution side**

That means:
- we took the official law PDF as the source of truth
- we turned it into structured legal records
- we annotated and decomposed those records
- we compiled them into the first frozen MVP rule pack and SIR schema
- we built a runtime input contract
- we built a deterministic SIR extractor
- we built a deterministic Layer 4 matcher
- we built a final non-LLM review report output

What we did **not** complete yet:
- evidence retrieval
- LLM explanation / rewrite
- human review UI logic

So the current deliverable is:

**law-to-rule-to-SIR-to-deterministic-review is ready**

but:

**evidence retrieval, LLM advisory, and human review are still the next stages**


Source of truth
---------------
Official source file:
- `data/raw/official/law_fincpa_main_2026-01-02.pdf`

Scope we selected:
- Chapter 4 only
- from `제4장 금융상품판매업자등의 영업행위 준수사항`
- up to just before `제5장 금융소비자 보호`

Why this matters:
- official source only
- limited, defensible scope
- easy to explain to judges and teammates


Stage 0. Raw Legal Input
------------------------
Input at the very beginning:
- one official Korean law PDF

At this point, the input is still:
- unstructured for machines
- difficult to match directly against future content
- not yet decomposed into executable legal units

So the first job is:

**turn the law document into structured legal records**


Stage 1. Deterministic Parsing
------------------------------
Goal:
- extract the selected Chapter 4 text
- split it into clause-level legal records

Files:
- `scripts/parse_fincpa_ch4_dataset.py`
- `data/parsed/ch4_fincpa/law_fincpa_main_ch4_clause_records.jsonl`
- `data/parsed/ch4_fincpa/law_fincpa_main_ch4_parse_report.md`
- `data/parsed/ch4_fincpa/law_fincpa_main_ch4_manifest.json`

Important facts:
- Gemini used here: `no`
- parsing is deterministic
- based only on the official PDF

Output:
- `60` clause-level legal records
- covering `제13조` through `제28조`

Each parsed row contains:
- source identifiers
- article / paragraph boundaries
- `raw_text`
- `normalized_text`

Meaning:
- `raw_text` = direct parsed text
- `normalized_text` = same legal content with formatting noise cleaned

So after parsing, we no longer have:
- one big PDF blob

We now have:
- `60` structured legal clause records


Stage 2. Layer 1 Legal Metadata
-------------------------------
Goal:
- add high-level meaning to each clause record

Layer 1 does **not** create rules yet.
Layer 1 does **not** create final SIR fields yet.
Layer 1 only says what kind of legal clause each row is.

Files:
- `docs/ch4_fincpa_layer1_explanation_and_analysis.md`
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer1_annotations.gemini.jsonl`

Gemini used here:
- `yes`
- model: `gemini-3.5-flash`

Important note:
- Gemini was used as an annotation assistant
- not as the source of truth
- human review is still expected

Layer 1 fields:
- `is_relevant_to_theme2`
- `topic_family`
- `product_scope`
- `channel_scope`
- `obligation_mode`
- `needs_decomposition`

What those fields mean:

- `is_relevant_to_theme2`
  - practical meaning: relevant to our target workflow scope
- `topic_family`
  - legal grouping such as advertising, explanation, solicitation
- `product_scope`
  - general / loan / deposit / investment / insurance / multiple
- `channel_scope`
  - advertising / solicitation / contracting / advisory / internal control
- `obligation_mode`
  - required action / required content / prohibited action / workflow control
- `needs_decomposition`
  - whether one clause is too large and must be split later

Layer 1 result:
- all `60` clause records received legal metadata

Meaning:
- after Layer 1, we know what kind of legal area each clause belongs to


Stage 3. Layer 2 Obligation Decomposition
-----------------------------------------
Goal:
- split broad clauses into smaller legal obligation units

Why this is needed:
- one clause often contains several distinct duties
- later runtime matching will fail if we keep one huge clause as one unit

Files:
- `docs/ch4_fincpa_layer2_explanation_and_analysis.md`
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer2_obligations.gemini.jsonl`

Gemini used here:
- `yes`
- model: `gemini-3.5-flash`

Input:
- `60` Layer 1 clause records

Output:
- `109` smaller obligation units

Meaning:
- one legal clause can now produce several smaller operational obligations

Examples of Layer 2 behavior:
- one clause about advertising may split into:
  - seller identity requirement
  - product core terms requirement
  - loan condition requirement
  - warning / disclaimer requirement

Why this matters:
- Layer 2 is the first place where broad law starts becoming operational


Stage 4. Layer 3 Rule And SIR-Link Candidates
---------------------------------------------
Goal:
- for each Layer 2 obligation, propose:
  - what kind of rule it may become
  - what kind of future SIR field could support it

Files:
- `docs/ch4_fincpa_layer3_explanation_and_analysis.md`
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer3_rule_candidates.gemini.jsonl`

Gemini used here:
- `yes`
- model: `gemini-3.5-flash`

Input:
- `109` Layer 2 obligations

Output:
- `109` Layer 3 candidates

Most important Layer 3 output fields:
- `rule_family`
- `logic_type`
- `detection_target`
- `sir_link_type`
- `sir_candidate_fields`
- `ready_for_v1`

What that means:

- `rule_family`
  - advertising / explanation / solicitation / internal control / etc.
- `logic_type`
  - required presence / prohibited presence / required process / required record
- `detection_target`
  - content text / workflow metadata / record system / mixed
- `sir_link_type`
  - direct content field / direct workflow field / direct record field
- `sir_candidate_fields`
  - the future field names a runtime system might need
- `ready_for_v1`
  - whether this candidate is strong enough for the first MVP

Layer 3 result summary:
- `76` candidates marked `ready_for_v1 = yes`
- `33` candidates marked `review`

Meaning:
- by the end of Layer 3, we have candidate rule logic and candidate SIR fields


Stage 5. Layer 4 MVP Freeze
---------------------------
Goal:
- stop free-form interpretation
- freeze the first MVP rule pack and SIR schema deterministically

Files:
- `docs/ch4_fincpa_layer4_explanation_and_analysis.md`
- `data/finalized/ch4_fincpa/law_fincpa_main_ch4_layer4_mvp_rule_pack.jsonl`
- `data/finalized/ch4_fincpa/law_fincpa_main_ch4_layer4_mvp_sir_schema.json`

Gemini used here:
- `no`

Why no Gemini here:
- the MVP freeze is easier to defend if it is deterministic
- Layer 4 simply includes rows where `ready_for_v1 == yes`

Input:
- `109` Layer 3 candidates

Output:
- `76` frozen MVP rules
- `29` frozen MVP SIR fields

This is the first final legal artifact set.

Meaning:
- Layer 4 is not just another suggestion layer
- it is the first frozen design boundary


What the final Layer 4 artifacts are
------------------------------------

### 1. MVP rule pack
File:
- `data/finalized/ch4_fincpa/law_fincpa_main_ch4_layer4_mvp_rule_pack.jsonl`

This contains:
- rule rows ready for future runtime checking

Each row is already tied back to:
- a legal obligation
- a source clause
- a rule family
- a detection target
- one or more candidate SIR fields

### 2. MVP SIR schema
File:
- `data/finalized/ch4_fincpa/law_fincpa_main_ch4_layer4_mvp_sir_schema.json`

This contains:
- the first frozen list of SIR fields the runtime system should populate later

Important result:
- `29` MVP SIR fields

These are not random fields.
They are traceable back through:
- Layer 4
- Layer 3
- Layer 2
- Layer 1
- parsed Chapter 4 law records


How all layers connect
----------------------
This is the simplest way to explain the pipeline:

1. **Official law PDF**
   - source of truth

2. **Parsed clause records**
   - law segmented into `60` structured units

3. **Layer 1 metadata**
   - what kind of clause is this?

4. **Layer 2 obligations**
   - what smaller duties are inside this clause?

5. **Layer 3 rule/SIR candidates**
   - what future rule and SIR field could represent this obligation?

6. **Layer 4 MVP freeze**
   - which rules and fields do we keep in the first executable design?

So the legal transformation is:

**law document -> clause records -> obligation units -> rule candidates -> frozen MVP rule pack + SIR schema**


What SIR means in this pipeline
-------------------------------
SIR here means:

**Structured Intermediate Representation**

In this project, SIR is the structured field layer that future runtime inputs
must be converted into.

Examples of future SIR field types:
- content text fields
- workflow metadata fields
- record system fields

Important clarification:
- we now have both the **SIR schema** and a **first deterministic runtime
  extractor**
- the extractor supports:
  - explicit field overrides
  - content heuristics
  - workflow metadata
  - record metadata
- it is still an MVP extractor, not the final production parser

So:
- schema is ready
- first runtime population is ready
- future production hardening is still possible


Stage 6. Runtime Input Schema
-----------------------------
Goal:
- define what a new incoming review item must look like so the non-LLM engine
  can process it

Files:
- `data/finalized/ch4_fincpa/law_fincpa_main_ch4_runtime_input_schema.json`

The runtime input includes:
- `input_id`
- `review_scope`
- `product_scope_hint`
- `channel_scope_hint`
- `business_role_hint`
- optional `include_rule_families`
- optional `exclude_rule_families`
- optional `field_inputs`
- optional `content_metadata`
- optional `workflow_metadata`
- optional `record_metadata`

Why this matters:
- not every review starts from raw text only
- some cases are content-only
- some cases need workflow metadata
- some cases need record/audit evidence


Stage 7. Runtime SIR Extraction
-------------------------------
Goal:
- convert a new runtime input into the `29` Layer 4 SIR fields with statuses

Files:
- `src/safeguard_ai/ch4_runtime.py`

Outputs per field:
- `present`
- `not_evidenced`
- `not_applicable`
- `uncertain`

The extractor supports:
- direct overrides through `field_inputs`
- content heuristics from `title` and `content_text`
- workflow-side metadata
- record-side metadata
- scope-aware `not_applicable` handling

This is the first working bridge from:

**new input -> SIR object**


Stage 8. Deterministic Layer 4 Matching
---------------------------------------
Goal:
- evaluate the new SIR object against the `76` Layer 4 MVP rules

Files:
- `src/safeguard_ai/ch4_runtime.py`
- `scripts/run_ch4_non_llm_workflow.py`

Important behavior:
- only rules matching the selected:
  - review scope
  - product scope
  - channel scope
  - business role
  - included/excluded rule families
  are evaluated

This prevents false positives from unrelated legal areas.

Output:
- passed / failed / uncertain / not_applicable per rule
- missing SIR fields
- final deterministic review decision
- escalation flag


Stage 9. Final Non-LLM Review Output
------------------------------------
Goal:
- produce a review result that the team can inspect immediately

Files:
- `data/runtime/ch4_fincpa/results/*.review_report.json`
- `data/runtime/ch4_fincpa/results/*.summary.md`

Examples already run:
- `loan_ad_content_only`
- `investment_solicitation_full`
- `access_request_record_only`


What is ready today
-------------------
Ready now:
- official legal source selection
- deterministic parsing
- Layer 1 metadata
- Layer 2 decomposition
- Layer 3 rule/SIR candidates
- Layer 4 frozen MVP rule pack
- Layer 4 frozen MVP SIR schema
- runtime input schema
- deterministic SIR extractor
- deterministic Layer 4 matcher
- final non-LLM review report generation
- dashboard visualization of all layers

Not ready yet:
- evidence retrieval
- LLM advisory generation
- human review execution flow


The clean handoff point
-----------------------
This is the correct handoff to the next team stages:

### Our side completed
- law to structured rule backbone
- law to SIR schema backbone
- new input to deterministic non-LLM review report

### Next stages the team can build
1. evidence retrieval
2. LLM explanation / rewrite
3. human review and audit flow


Best 30-second explanation for the team
---------------------------------------
We started from the official Financial Consumer Protection Act PDF and limited
ourselves to Chapter 4 only. We parsed that official source deterministically
into 60 clause-level legal records. Then we used guided annotation to add legal
metadata in Layer 1, split broad clauses into 109 smaller obligation units in
Layer 2, converted those into rule and SIR-link candidates in Layer 3, and
finally froze the first MVP rule pack and SIR schema in Layer 4. On top of
that, we built a deterministic runtime that accepts a new input, fills the SIR
fields, matches the Layer 4 rules, and emits a non-LLM review result. The next
team stages are evidence retrieval, LLM advisory, and human review.


Best 1-line explanation
-----------------------
We converted official Chapter 4 law text into a traceable MVP rule pack and SIR
schema, then built a first deterministic runtime on top of it; the remaining
work is evidence retrieval, LLM advisory, and human review.
