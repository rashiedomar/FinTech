Chapter 4 Pipeline Technical Book
=================================

Purpose
-------
This document is the full technical walkthrough of the current Chapter 4
pipeline in this repository.

It explains the system from the first official PDF parse all the way to the
current LLM advisory handoff.

The goal is to answer these questions clearly:

1. What exact legal source did we use?
2. What was done deterministically?
3. Where was Gemini used?
4. What file is produced at each stage?
5. How does a new runtime input become SIR?
6. What exactly is sent to the LLM now?
7. What still remains unfinished?


Scope
-----
Current legal scope:
- source law: `금융소비자 보호에 관한 법률`
- source file: `data/raw/official/law_fincpa_main_2026-01-02.pdf`
- chapter used: `제4장 금융상품판매업자등의 영업행위 준수사항`
- page range used for extraction: `7` to `16`
- stop boundary: immediately before `제5장 금융소비자 보호`

Current product scope:
- this is a Chapter 4 legal core, not a full Korea financial-law stack
- it does not yet include:
  - Presidential Decrees
  - supervisory regulations
  - financial advertising guidelines
  - FSS enforcement cases

Current architectural scope:
- legal parsing
- layered legal annotation
- MVP rule compilation
- deterministic runtime review
- evidence packaging
- LLM advisory input packaging
- human review packet construction

Not yet completed:
- live Gemini advisory execution, because the current API project has depleted
  prepaid credits
- decree/regulation retrieval
- production-grade reviewer UI logic


One-Page Pipeline Summary
-------------------------
The current repo implements this chain:

1. official PDF
2. deterministic Chapter 4 clause parsing
3. Layer 1 metadata annotation
4. Layer 2 obligation decomposition
5. Layer 3 rule and SIR candidate compilation
6. Layer 4 MVP freeze
7. deterministic runtime review for new inputs
8. statute-grounded evidence package
9. LLM advisory input package
10. human review packet

Short version:
- the law is turned into structured legal units first
- those units are turned into rules and SIR field candidates
- the first MVP subset is frozen
- a new input is mapped into SIR
- the deterministic engine decides first
- only then do we prepare an LLM explanation package


Tooling Inventory
-----------------

### External tools and services
- `pdftotext`
  - used for raw text extraction from the official law PDF
  - used only in the parsing stage
- Gemini API
  - used for Layer 1, Layer 2, and Layer 3 annotation/compilation
  - intended to be used again in the advisory stage
- local Python runtime
  - used for all deterministic processing, data transformation, validation,
    runtime evaluation, and dashboard bundling

### Core repository code
- `scripts/parse_fincpa_ch4_dataset.py`
- `scripts/annotate_ch4_layer1_with_gemini.py`
- `scripts/decompose_ch4_layer2_with_gemini.py`
- `scripts/compile_ch4_layer3_with_gemini.py`
- `scripts/build_ch4_layer4_mvp_artifacts.py`
- `scripts/validate_ch4_layer4_artifacts.py`
- `src/safeguard_ai/ch4_runtime.py`
- `scripts/run_ch4_non_llm_workflow.py`
- `src/safeguard_ai/ch4_postprocess.py`
- `scripts/run_ch4_postprocess_pipeline.py`
- `scripts/run_ch4_gemini_advisory.py`

### Review and support scripts
- `scripts/build_ch4_layer1_annotation_sheet.py`
- `scripts/prefill_ch4_layer1_annotations.py`
- `scripts/build_layer1_review_priority_sheet.py`
- `scripts/build_ch4_layer2_review_priority.py`
- `scripts/build_ch4_layer3_review_priority.py`
- `scripts/validate_ch4_layer1_annotations.py`
- `scripts/validate_ch4_layer2_obligations.py`
- `scripts/validate_ch4_layer3_rule_candidates.py`
- `scripts/run_ch4_example_suite.py`

### Visualization and dashboard scripts
- `scripts/build_ch4_dashboard_bundle.py`
- `scripts/build_ch4_runtime_dashboard_bundle.py`
- `scripts/run_ch4_dashboard.py`
- `scripts/run_ch4_runtime_flow_dashboard.py`
- `dashboard/ch4_fincpa/`
- `dashboard/ch4_runtime_flow/`


Data Lineage At A Glance
------------------------

| Stage | Main output | Count / status | Main driver |
| --- | --- | --- | --- |
| Parse | `law_fincpa_main_ch4_clause_records.jsonl` | `60` clause records | `parse_fincpa_ch4_dataset.py` |
| Layer 1 | `law_fincpa_main_ch4_layer1_annotations.gemini.jsonl` | `60` annotated clause rows | `annotate_ch4_layer1_with_gemini.py` |
| Layer 2 | `law_fincpa_main_ch4_layer2_obligations.gemini.jsonl` | `109` obligation units | `decompose_ch4_layer2_with_gemini.py` |
| Layer 3 | `law_fincpa_main_ch4_layer3_rule_candidates.gemini.jsonl` | `109` rule candidates | `compile_ch4_layer3_with_gemini.py` |
| Layer 4 | `law_fincpa_main_ch4_layer4_mvp_rule_pack.jsonl` | `76` included MVP rules | `build_ch4_layer4_mvp_artifacts.py` |
| Layer 4 | `law_fincpa_main_ch4_layer4_mvp_sir_schema.json` | `29` frozen SIR fields | `build_ch4_layer4_mvp_artifacts.py` |
| Runtime | `*.review_report.json` | working deterministic review | `run_ch4_non_llm_workflow.py` |
| Postprocess | `*.evidence_package.json` | working | `run_ch4_postprocess_pipeline.py` |
| Postprocess | `*.llm_advisory_input.json` | working | `run_ch4_postprocess_pipeline.py` |
| Postprocess | `*.human_review_packet.json` | working | `run_ch4_postprocess_pipeline.py` |
| Gemini advisory | `*.gemini_advisory_output.json` | blocked by billing at time of writing | `run_ch4_gemini_advisory.py` |

Actual model used in the legal annotation layers:
- Layer 1 outputs: `gemini-3.5-flash`
- Layer 2 outputs: `gemini-3.5-flash`
- Layer 3 outputs: `gemini-3.5-flash`


Stage 0. Official Source Selection
----------------------------------
The repo does not start from scraped websites or mixed secondary summaries.
It starts from one official law PDF:

- `data/raw/official/law_fincpa_main_2026-01-02.pdf`

Why this matters:
- the dataset is defensible
- every clause can be traced to an official source
- the team can explain the construction process during judging
- the legal core is not based on undocumented internet samples


Stage 1. Deterministic PDF Parsing
----------------------------------

### What this stage does
This stage converts the selected Chapter 4 scope into clause-level records.

It does only these things:
- text extraction from the PDF
- Chapter 4 scope trimming
- section, article, and paragraph segmentation
- clause-level JSONL storage

It does not do these things:
- legal interpretation
- SIR extraction from ads
- rule building
- LLM summarization

### Code used
- `scripts/parse_fincpa_ch4_dataset.py`

### External tool used
- `pdftotext`

### Deterministic parsing logic
The parser uses:
- `CHAPTER_START_MARKER`
- `CHAPTER_END_MARKER`
- section header regex
- article header regex
- paragraph marker regex such as `①`, `②`, `③`

Important parsing functions in the script:
- `run_pdftotext()`
- `clean_page_text()`
- `extract_chapter_scope()`
- `collect_article_blocks()`
- `split_paragraphs()`

### Main outputs
- `data/parsed/ch4_fincpa/law_fincpa_main_ch4_fulltext.txt`
- `data/parsed/ch4_fincpa/law_fincpa_main_ch4_clause_records.jsonl`
- `data/parsed/ch4_fincpa/law_fincpa_main_ch4_parse_report.md`
- `data/parsed/ch4_fincpa/law_fincpa_main_ch4_manifest.json`

### Parsing result
From the manifest:
- source PDF: `data/raw/official/law_fincpa_main_2026-01-02.pdf`
- record count: `60`
- article range included: `제13조` through `제28조`

### Clause record shape
Each parsed row contains:
- `record_id`
- `source_id`
- `source_title`
- `source_path`
- `chapter_id`
- `chapter_title`
- `section_id`
- `section_title`
- `article_id`
- `article_title`
- `paragraph_id`
- `page_start`
- `raw_text`
- `normalized_text`
- `parse_method`
- `manual_verified`

### `raw_text` vs `normalized_text`
- `raw_text`
  - keeps the parser’s closer-to-source segmented text
  - still reflects original line structure more closely
- `normalized_text`
  - collapses whitespace into a cleaner single-space form
  - is easier for downstream annotation and matching

This is important because:
- `raw_text` is better for traceability
- `normalized_text` is better for controlled downstream processing


Stage 2. Layer 1 Legal Metadata Annotation
------------------------------------------

### Goal
Layer 1 does not create executable rules yet.
It gives each clause a first legal metadata profile.

This answers questions like:
- is this clause relevant to the current Theme 2 workflow slice?
- what topic family is it?
- what product scope does it touch?
- what channel scope does it touch?
- what kind of obligation is it?
- does it need decomposition?

### Code used
- `scripts/annotate_ch4_layer1_with_gemini.py`
- label guide: `data/annotations/ch4_fincpa/layer1_label_guide.json`

### Gemini usage
This is the first stage that uses Gemini.

Prompt design in the script:
- strict controlled labels only
- conservative classification
- no SIR creation yet
- one clause record at a time
- JSON schema enforced by `responseSchema`

### Output fields
Main Layer 1 annotation fields:
- `is_relevant_to_theme2`
- `topic_family`
- `product_scope`
- `channel_scope`
- `obligation_mode`
- `needs_decomposition`
- `reviewer_note`
- `gemini_confidence`
- `gemini_reasoning_summary`

### Main outputs
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer1_annotations.gemini.csv`
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer1_annotations.gemini.jsonl`
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer1_gemini_report.json`

### Result snapshot
- row count: `60`
- model used in output: `gemini-3.5-flash`

### What Layer 1 is not
Layer 1 is not:
- final rule logic
- final SIR schema
- runtime matching
- evidence retrieval

It is just controlled legal metadata.


Stage 3. Layer 2 Obligation Decomposition
-----------------------------------------

### Goal
One legal clause can contain more than one operational duty.
Layer 2 breaks one parent clause into one or more smaller obligation units.

Example idea:
- one clause may require both a disclosure and a process
- those need to become separate future rule units

### Code used
- `scripts/decompose_ch4_layer2_with_gemini.py`
- label guide: `data/annotations/ch4_fincpa/layer2_label_guide.json`

### Gemini usage
Gemini receives:
- the parsed clause text
- the Layer 1 hint
- the instruction to stay faithful to source text

Gemini must return:
- `parent_decomposition_strategy`
- `parent_decomposition_reason`
- `obligations`

Each obligation contains controlled labels such as:
- `obligation_summary`
- `source_span_text`
- `product_scope`
- `channel_scope`
- `obligation_mode`
- `trigger_type`
- `operationality`
- `consumer_visibility`

### Why this layer matters
Without Layer 2:
- many clauses remain too broad
- runtime rules become vague
- one clause would need to do multiple jobs at once

With Layer 2:
- the legal text becomes operationally separable
- later rule logic can be much more explicit

### Main outputs
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer2_obligations.gemini.csv`
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer2_obligations.gemini.jsonl`
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer2_parent_summary.csv`
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer2_gemini_report.json`

### Result snapshot
- obligation row count: `109`
- model used in output: `gemini-3.5-flash`


Stage 4. Layer 3 Rule And SIR Candidate Compilation
---------------------------------------------------

### Goal
Layer 3 converts each Layer 2 obligation unit into:
- one first-pass rule candidate
- one first-pass SIR-link proposal

This is where the system begins to ask:
- what kind of future rule is this?
- what would the runtime need to observe?
- what kind of SIR field would connect to it?

### Code used
- `scripts/compile_ch4_layer3_with_gemini.py`
- label guide: `data/annotations/ch4_fincpa/layer3_label_guide.json`

### Gemini usage
Gemini receives one obligation unit and must return:
- `rule_candidate_summary`
- `rule_family`
- `logic_type`
- `detection_target`
- `sir_link_type`
- `sir_candidate_fields`
- `evidence_source`
- `ready_for_v1`
- `reviewer_note`
- `gemini_confidence`
- `gemini_reasoning_summary`

### Meaning of the key Layer 3 fields
- `rule_family`
  - the legal business family, such as advertising or suitability
- `logic_type`
  - the kind of runtime check, such as required presence or prohibited presence
- `detection_target`
  - where evidence is expected to live:
    - content text
    - workflow metadata
    - record system
    - document bundle
    - consumer profile
- `sir_link_type`
  - how directly this obligation can map to SIR
- `sir_candidate_fields`
  - the future structured fields the runtime would look at
- `ready_for_v1`
  - whether the candidate is strong enough to include in the first deterministic MVP

### Main outputs
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer3_rule_candidates.gemini.csv`
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer3_rule_candidates.gemini.jsonl`
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer3_gemini_report.json`

### Result snapshot
- rule candidate row count: `109`
- model used in output: `gemini-3.5-flash`


Stage 5. Layer 4 MVP Freeze
---------------------------

### Goal
Layer 4 freezes the first runtime-safe legal core.

This stage turns the softer Layer 3 candidate layer into two hard artifacts:
- the MVP rule pack
- the MVP SIR schema

### Code used
- `scripts/build_ch4_layer4_mvp_artifacts.py`
- validation: `scripts/validate_ch4_layer4_artifacts.py`

### Selection rule
Only Layer 3 rows with:
- `ready_for_v1 == yes`

are included in the Layer 4 MVP rule pack.

### What the builder adds
The builder adds:
- normalized rule rows
- `evaluation_hint` from the logic type
- frozen `sir_candidate_fields` lists
- field metadata such as `value_type` and descriptions

### Main outputs
- `data/finalized/ch4_fincpa/law_fincpa_main_ch4_layer4_mvp_rule_pack.jsonl`
- `data/finalized/ch4_fincpa/law_fincpa_main_ch4_layer4_mvp_rule_pack.csv`
- `data/finalized/ch4_fincpa/law_fincpa_main_ch4_layer4_mvp_sir_schema.json`
- `data/finalized/ch4_fincpa/law_fincpa_main_ch4_layer4_mvp_sir_field_summary.csv`
- `data/finalized/ch4_fincpa/law_fincpa_main_ch4_layer4_excluded_candidates.csv`
- `data/finalized/ch4_fincpa/law_fincpa_main_ch4_layer4_compile_report.json`
- `data/finalized/ch4_fincpa/law_fincpa_main_ch4_layer4_validation_report.json`

### Layer 4 result snapshot
From the compile report:
- total Layer 3 candidates: `109`
- included MVP rules: `76`
- excluded candidates: `33`
- frozen SIR fields: `29`

Rule family counts:
- `advertising`: `10`
- `adequacy`: `8`
- `advisory`: `4`
- `contract_documents`: `1`
- `explanation`: `9`
- `intermediary`: `11`
- `internal_control`: `1`
- `recordkeeping`: `9`
- `solicitation`: `10`
- `suitability`: `7`
- `unfair_sales`: `6`

Logic type counts:
- `required_presence`: `23`
- `prohibited_presence`: `24`
- `required_process`: `17`
- `required_record`: `5`
- `required_response`: `7`

Detection target counts:
- `workflow_metadata`: `36`
- `content_text`: `28`
- `record_system`: `8`
- `consumer_profile`: `2`
- `document_bundle`: `2`

### What Layer 4 means in practice
After Layer 4, the legal compilation side is no longer just exploratory.
It becomes executable input for the runtime.


Stage 6. Runtime Input Contract
-------------------------------

### Runtime schema artifact
- `data/finalized/ch4_fincpa/law_fincpa_main_ch4_runtime_input_schema.json`

This file describes the contract for new review cases after Layer 4.

### Required top-level fields
- `input_id`
- `review_scope`
- `product_scope_hint`
- `channel_scope_hint`
- `business_role_hint`

### Important optional fields
- `title`
- `content_text`
- `include_rule_families`
- `exclude_rule_families`
- `field_inputs`
- `content_metadata`
- `workflow_metadata`
- `record_metadata`

### Allowed review scopes
- `content_only`
- `workflow_only`
- `record_only`
- `full`

### Allowed business roles
- `direct_seller`
- `intermediary`
- `advisory`
- `independent_advisory`

### Allowed field status values
- `present`
- `not_evidenced`
- `not_applicable`
- `uncertain`


Stage 7. Deterministic Runtime
------------------------------

### Goal
The runtime answers:

If a new case arrives now, can we produce a first compliance result without an
LLM?

Current answer:
- yes, for the current MVP scope

### Code used
- library: `src/safeguard_ai/ch4_runtime.py`
- runner: `scripts/run_ch4_non_llm_workflow.py`

### Runtime steps

#### 7.1 Input normalization
`normalize_runtime_input()` fills defaults and normalizes scope values.

If hints are missing, the runtime can infer:
- channel scope from text
- product scope from product keywords
- business role from context

#### 7.2 SIR extraction
`extract_sir()` converts the runtime input into the `29` frozen Layer 4 SIR
fields.

Field sources are applied in priority order:
1. `field_inputs`
2. `content_metadata`, `workflow_metadata`, `record_metadata`
3. deterministic text heuristics
4. context-based `not_applicable`

#### 7.3 Rule applicability filtering
The runtime filters rules by:
- `review_scope`
- `product_scope_hint`
- `channel_scope_hint`
- `business_role_hint`
- include/ exclude rule family filters

This stops irrelevant rules from firing on the wrong case type.

#### 7.4 Deterministic rule evaluation
`evaluate_rule()` handles logic types such as:
- `required_presence`
- `required_process`
- `required_record`
- `required_response`
- `prohibited_presence`

#### 7.5 Final review report
`build_review_report()` computes:
- final decision
- escalation flag
- active rule IDs
- missing SIR fields
- triggered citations

### Runtime heuristics actually present in code
The runtime currently has deterministic pattern sets for:
- product keywords
- seller name patterns
- prohibited claim patterns
- warning patterns
- loan condition patterns

Examples:
- prohibited signals:
  - `원금 보장`
  - `확정 수익`
  - `무조건`
  - `즉시 승인`
- warning signals:
  - `원금 손실`
  - `예금자보호`
  - `면책`
- loan signals:
  - `금리`
  - `중도상환수수료`
  - `연체이자`

### Runtime decision model
- `non_compliant`
  - at least one failed applicable rule
- `needs_human_review`
  - no failure, but at least one uncertain rule
- `compliant`
  - applicable rules passed, with no failures or uncertainty
- `insufficient_scope`
  - no applicable rules after filtering

Escalation:
- `true` if any failed or uncertain applicable rule exists
- `false` otherwise

### Main runtime outputs
For each example or input case:
- `*.review_report.json`
- `*.summary.md`

### Example suite runner
- `scripts/run_ch4_example_suite.py`

Current example suite summary:
- `access_request_record_only` -> `compliant`
- `deposit_ad_missing_disclaimer` -> `non_compliant`
- `insurance_ad_missing_warning` -> `non_compliant`
- `investment_ad_guaranteed_return_violation` -> `non_compliant`
- `investment_solicitation_full` -> `compliant`
- `loan_ad_content_only` -> `non_compliant`
- `solicitation_improper_claim_violation` -> `non_compliant`


How Raw Input Becomes SIR
-------------------------
This is the most important runtime bridge.

The legal layers do not read the new ad directly.
The runtime does.

### Example input
Suppose the new case is:

`ABC증권 투자상품, 원금 보장, 확정 수익 8%, 지금 바로 가입하세요.`

### Step A. Runtime normalization
The runtime accepts the full JSON case:
- input ID
- raw content text
- review scope
- product and channel hints

Example:
- `review_scope = content_only`
- `product_scope_hint = ["investment"]`
- `channel_scope_hint = ["advertising"]`

### Step B. Field extraction
The runtime checks the frozen SIR fields and tries to fill them.

In this case:
- `prohibited_claim_signal`
  - becomes `present`
  - evidence includes `원금 보장`, `확정 수익`
- `investment_warning`
  - remains `not_evidenced`

### Step C. Rule applicability
Only the Layer 4 rules matching:
- investment
- advertising
- content review

stay active.

### Step D. Rule evaluation
The runtime checks:
- is a required investment warning present?
- are prohibited guarantee-like claims present?

### Step E. Final report
The engine emits:
- `final_decision = non_compliant`
- `should_escalate = true`

So the SIR is not created by magic.
It is created by:
- the frozen Layer 4 field inventory
- deterministic field state objects
- metadata overrides
- content heuristics
- scope handling


Stage 8. Post-Deterministic Evidence Package
--------------------------------------------

### Goal
The runtime already knows what failed.
The next question is:

What legal proof should travel with that failure?

### Code used
- library: `src/safeguard_ai/ch4_postprocess.py`
- runner: `scripts/run_ch4_postprocess_pipeline.py`

### What evidence retrieval means right now
Current evidence retrieval has two layers:

1. always-on static statute grounding
2. optional local vector support when the Chapter 4 embedding index exists

So it is still statute-grounded, but it is no longer only static.

For each failed or uncertain rule, the postprocess layer attaches:
- the Layer 4 legal basis
- the parent parsed clause
- same-article neighboring context
- a delegated-detail hint when decree-level detail is referenced
- and, when the local index exists, top-k vector-retrieved supporting chunks

### Main evidence artifact
- `*.evidence_package.json`

Key contents:
- `coverage_summary`
- `evidence_items`

Each evidence item includes:
- `rule_id`
- `rule_status`
- `severity`
- `reason`
- `finding_fields`
- `field_evidence`
- `legal_basis`
- `parent_clause`
- `same_article_context`
- `delegated_detail_hint`
- `retrieval_mode`
- `retrieval_backend`
- `retrieved_support`

### Why this stage matters
This proves that legal grounding exists before the LLM stage.
The LLM is not being asked to search for law from scratch.


Stage 9. LLM Advisory Input Package
-----------------------------------

### Goal
The LLM should not receive only raw ad text.
It should receive the deterministic decision plus the legal context package.

### Code used
- package builder: `build_llm_advisory_input()` in `src/safeguard_ai/ch4_postprocess.py`
- live runner: `scripts/run_ch4_gemini_advisory.py`

### What the advisory input contains
Main sections:
- `tasking`
- `case_context`
- `deterministic_core`
- `sir_focus_fields`
- `evidence_package`
- `suggested_output_schema`

### LLM role constraints
The advisory package explicitly tells the model:
- do not override the deterministic final decision
- do not invent legal citations
- do not claim certainty if the engine is uncertain

### Expected LLM outputs
- `reviewer_summary`
- `plain_language_rationale`
- `remediation_actions`
- `conservative_rewrite_suggestion`
- `citation_list`

### Current status
The advisory runner is implemented and ready:
- `scripts/run_ch4_gemini_advisory.py`

But the last live call failed because the Gemini API project currently has:
- depleted prepaid credits

So the current advisory stage is technically wired, but billing-blocked.


Stage 10. Human Review Packet
-----------------------------

### Goal
The deterministic system and the LLM advisory layer are not the final authority.
The final authority is still the human reviewer.

### What the packet contains
- original content
- deterministic final decision
- escalation state
- failed and uncertain counts
- missing SIR fields
- evidence summary
- triggered citations

### Allowed reviewer actions
- `approve`
- `approve_with_edits`
- `reject`
- `escalate`

### Main artifact
- `*.human_review_packet.json`

This is the bridge into the final human oversight layer.


Concrete End-To-End Example
---------------------------

### Input
File:
- `data/runtime/ch4_fincpa/examples/investment_ad_guaranteed_return_violation.json`

Content:
- `ABC증권 투자상품, 원금 보장, 확정 수익 8%, 지금 바로 가입하세요.`

### Runtime result
Files:
- `data/runtime/ch4_fincpa/results/investment_ad_guaranteed_return_violation.review_report.json`
- `data/runtime/ch4_fincpa/results/investment_ad_guaranteed_return_violation.llm_advisory_input.json`
- `data/runtime/ch4_fincpa/results/investment_ad_guaranteed_return_violation.human_review_packet.json`

Deterministic result:
- final decision: `non_compliant`
- escalate: `true`
- missing SIR field: `investment_warning`

Triggered citations:
- `금융소비자 보호에 관한 법률 제22조③`
- `금융소비자 보호에 관한 법률 제22조④`

Why it failed:
- the engine found prohibited guarantee-like claims
- the engine did not find required investment warning evidence

### What the LLM would receive
It would receive:
- the original ad text
- the deterministic failure summary
- focused SIR fields:
  - `prohibited_claim_signal`
  - `investment_warning`
- the legal evidence package

### What the human reviewer would receive
They would receive:
- the case summary
- the engine’s decision
- the citations
- the evidence summary
- allowed action choices


Deterministic vs Gemini Responsibility Split
--------------------------------------------

| Stage | Deterministic or Gemini? | What it does |
| --- | --- | --- |
| Parse | Deterministic | extracts and segments official Chapter 4 text |
| Layer 1 | Gemini | clause metadata labeling |
| Layer 2 | Gemini | obligation decomposition |
| Layer 3 | Gemini | rule and SIR candidate proposal |
| Layer 4 | Deterministic | freeze MVP rules and SIR schema |
| Runtime | Deterministic | SIR extraction, filtering, rule evaluation |
| Evidence package | Deterministic | attach legal basis and clause context |
| Advisory output | Gemini | explain and advise without changing decision |
| Human review | Human | final operational decision |

This split is the core design principle of the repo:
- deterministic legal core first
- LLM explanation second
- human oversight last


Support Artifacts For Review And Communication
----------------------------------------------

### Review guides and explanations
- `docs/ch4_fincpa_parsing_method.md`
- `docs/ch4_fincpa_layer1_annotation_guide.md`
- `docs/ch4_fincpa_layer1_explanation_and_analysis.md`
- `docs/ch4_fincpa_layer2_decomposition_guide.md`
- `docs/ch4_fincpa_layer2_explanation_and_analysis.md`
- `docs/ch4_fincpa_layer3_rule_compilation_guide.md`
- `docs/ch4_fincpa_layer3_explanation_and_analysis.md`
- `docs/ch4_fincpa_layer4_explanation_and_analysis.md`
- `docs/ch4_runtime_non_llm_workflow.md`
- `docs/ch4_post_deterministic_workflow.md`
- `docs/ch4_citations_and_evidence_retrieval.md`

### Dashboards
- `dashboard/ch4_fincpa/`
  - dataset and layer visualization
- `dashboard/ch4_runtime_flow/`
  - runtime walkthrough and prompt-to-result flow

### Dashboard bundle builders
- `scripts/build_ch4_dashboard_bundle.py`
- `scripts/build_ch4_runtime_dashboard_bundle.py`


Current Limitations
-------------------
- only the statute itself is currently modeled
- decree-level and supervisory detail are not yet integrated
- runtime text extraction from new inputs is heuristic, not a full NLP parser
- evidence retrieval is still static Chapter 4 grounding, not dynamic retrieval
- the current Gemini advisory call is blocked by depleted API credits
- some rules are excluded from the MVP because they are not yet safe for first-pass deterministic execution


What Is Already Strong
----------------------
- official source provenance is strong
- Chapter 4 scope is explicit and reviewable
- parsing is deterministic and reproducible
- Layer 1 to Layer 3 are controlled and schema-bound
- Layer 4 is frozen into executable artifacts
- non-LLM runtime already works on sample cases
- citations are already carried through the runtime
- LLM is positioned as advisory only, not as the primary legal judge


Recommended Reading Order
-------------------------
If someone is new to the repo, the fastest clean reading order is:

1. this file
2. `docs/ch4_fincpa_parsing_method.md`
3. `docs/ch4_runtime_non_llm_workflow.md`
4. `docs/ch4_post_deterministic_workflow.md`
5. `data/finalized/ch4_fincpa/law_fincpa_main_ch4_layer4_mvp_rule_pack.jsonl`
6. `data/finalized/ch4_fincpa/law_fincpa_main_ch4_layer4_mvp_sir_schema.json`
7. one runtime example in `data/runtime/ch4_fincpa/examples/`
8. the matching result files in `data/runtime/ch4_fincpa/results/`


Best Short Explanation
----------------------
This repository takes one official law PDF, deterministically parses Chapter 4,
uses Gemini in controlled layers to turn clauses into obligation and rule
candidates, freezes the first safe MVP into a rule pack plus SIR schema, runs a
deterministic compliance review on new cases, and only after that prepares an
evidence-backed LLM advisory package and a human review packet.
