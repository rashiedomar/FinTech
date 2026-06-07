Chapter 4 Layer 4 Explanation And Analysis
==========================================

Purpose
-------
This note explains what Layer 4 is, how the final MVP artifacts were built, what
the output files mean, and how to interpret the last compilation step.

Important clarification
-----------------------
Layer 4 is the first frozen MVP layer.

Layers 1 to 3 were still building interpretation layers:
- Layer 1: clause-level metadata
- Layer 2: obligation decomposition
- Layer 3: rule and SIR-link candidates

Layer 4 changes the mode:
- no new Gemini interpretation is added here
- we compile deterministically from the Layer 3 output
- only candidates marked `ready_for_v1 = yes` are included

So Layer 4 is:
- the first frozen MVP SIR schema
- the first frozen MVP rule pack

It is not yet:
- a runtime engine
- a full evaluator
- the final production ontology


What happened just now
----------------------
We already had:
- deterministic parsing into 60 clause records
- Layer 1 metadata on those clause records
- Layer 2 decomposition into 109 obligation units
- Layer 3 rule/SIR-link candidates for those 109 obligations

Then Layer 4 did one deterministic selection rule:

`include only Layer 3 rows where ready_for_v1 == yes`

That produced:
- `76` included MVP rule rows
- `33` excluded review rows
- `29` MVP SIR fields


Inputs used
-----------
Layer 4 used:
- `data/raw/official/law_fincpa_main_2026-01-02.pdf`
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer2_obligations.gemini.jsonl`
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer3_rule_candidates.gemini.jsonl`

Builder:
- `scripts/build_ch4_layer4_mvp_artifacts.py`

Validator:
- `scripts/validate_ch4_layer4_artifacts.py`

Gemini used at this layer:
- `false`

This is deliberate.
By Layer 4, the repo already has Gemini-assisted candidate generation. The final
MVP freeze is easier to defend if it is compiled by a fixed selection rule
instead of another free-form model call.


What Layer 4 actually is
------------------------
Layer 3 answers:
- what kind of future rule could exist?
- what future SIR field could support it?

Layer 4 answers:
- which of those candidate rules do we keep in the first MVP?
- which SIR fields do we freeze in the first MVP schema?

So:
- Layer 3 = candidate design
- Layer 4 = deterministic MVP freeze


Main output files
-----------------
Final rule pack:
- `data/finalized/ch4_fincpa/law_fincpa_main_ch4_layer4_mvp_rule_pack.jsonl`
- `data/finalized/ch4_fincpa/law_fincpa_main_ch4_layer4_mvp_rule_pack.csv`

Final SIR schema:
- `data/finalized/ch4_fincpa/law_fincpa_main_ch4_layer4_mvp_sir_schema.json`

Field summary:
- `data/finalized/ch4_fincpa/law_fincpa_main_ch4_layer4_mvp_sir_field_summary.csv`

Excluded candidate review file:
- `data/finalized/ch4_fincpa/law_fincpa_main_ch4_layer4_excluded_candidates.csv`

Compile report:
- `data/finalized/ch4_fincpa/law_fincpa_main_ch4_layer4_compile_report.json`

Validation report:
- `data/finalized/ch4_fincpa/law_fincpa_main_ch4_layer4_validation_report.json`


What the final artifacts mean
-----------------------------

### 1. MVP rule pack
This is the first frozen set of rule rows that survived the Layer 3 selection
gate.

Each row includes:
- source legal obligation id
- source clause reference
- product scope
- channel scope
- rule family
- logic type
- detection target
- SIR-link type
- mapped candidate SIR fields
- evidence source
- evaluation hint

This means the rule pack is no longer just “ideas about rules”.
It is the first structured set of rules we can later wire into an actual
workflow.

### 2. MVP SIR schema
This is the first frozen field inventory for the future system.

It is built from the surviving Layer 4 rule rows, not from arbitrary intuition.

Each field includes:
- field name
- field group
- value type
- description
- source rule count
- source obligation count
- product scopes
- channel scopes
- rule families
- evidence sources
- article references

So this schema is not just a hand-written field list.
It is traceable back to the Chapter 4 legal source base through Layers 2 and 3.

### 3. Field summary
This is the easiest spreadsheet-like view for the team.

It shows:
- which fields appear most often
- which fields are high/medium/low MVP priority
- which legal areas support each field

### 4. Excluded candidates
These are the Layer 3 rows marked:
- `ready_for_v1 = review`

They were intentionally not included in the MVP freeze.
This keeps the first version tighter and easier to defend.


Layer 4 results
---------------

### Final selection counts
- total Layer 3 candidates: `109`
- included MVP rules: `76`
- excluded review candidates: `33`
- MVP SIR fields: `29`

### Validation
- rule pack rules: `76`
- SIR schema fields: `29`
- validation errors: `0`
- validation passed: `true`

### Rule family distribution in the final MVP
- `internal_control`: `1`
- `recordkeeping`: `9`
- `intermediary`: `11`
- `solicitation`: `10`
- `suitability`: `7`
- `adequacy`: `8`
- `explanation`: `9`
- `unfair_sales`: `6`
- `advertising`: `10`
- `contract_documents`: `1`
- `advisory`: `4`

This is important.
The final MVP is not dominated by one narrow rule family. It already spans:
- advertising
- explanation
- suitability/adequacy
- solicitation
- recordkeeping
- intermediary conduct

### Logic type distribution in the final MVP
- `required_presence`: `23`
- `prohibited_presence`: `24`
- `required_process`: `17`
- `required_record`: `5`
- `required_response`: `7`

This means the MVP is not just a “find bad phrases in text” system.
It includes:
- required visible content checks
- prohibited signal checks
- workflow checks
- recordkeeping checks
- response-control checks

### Detection target distribution
- `workflow_metadata`: `36`
- `content_text`: `28`
- `record_system`: `8`
- `consumer_profile`: `2`
- `document_bundle`: `2`

This is one of the most important Layer 4 conclusions.

The law does not reduce cleanly to only customer-facing text review.
The MVP already needs:
- content-side fields
- workflow/process fields
- record/archive fields

### SIR field group distribution
- `content_text`: `15`
- `workflow_metadata`: `10`
- `record_system`: `4`

So the frozen SIR schema is also mixed by design.
It is not only an “ad text schema”.


Highest-priority SIR fields
---------------------------
The highest-frequency fields in the frozen MVP are:

- `prohibited_claim_signal`: `17`
- `activity_record`: `13`
- `intermediary_status`: `12`
- `explanation_material`: `9`
- `product_core_terms`: `8`
- `consumer_profile`: `8`
- `adequacy_check`: `8`

This tells us where the first MVP is strongest:

### Content-side strengths
- prohibited claim detection
- core product-term disclosure
- explanation material checks
- intermediary identity/status handling

### Workflow-side strengths
- consumer profile capture
- adequacy/suitability process checks

### Record-side strengths
- activity logs and record evidence


What the final Layer 4 schema tells us
--------------------------------------
The frozen MVP schema now has concrete fields for:

### Content-facing review
- `seller_identity`
- `product_identity`
- `product_core_terms`
- `insurance_warning`
- `investment_warning`
- `deposit_disclaimer`
- `loan_conditions`
- `loan_rate_basis`
- `loan_interest_timing`
- `loan_costs`
- `prohibited_claim_signal`

### Workflow/process review
- `consumer_type`
- `consumer_profile`
- `suitability_check`
- `adequacy_check`
- `explanation_confirmation`
- `solicitation_purpose`
- `representative_identity`
- `intermediary_status`
- `advisory_independence`
- `fairness_guardrail`

### Record/archive review
- `activity_record`
- `staff_registry`
- `internal_control_standard`
- `record_integrity_control`
- `access_request`
- `access_response`
- `contract_document_delivery`

This is the first point in the repo where the law has been turned into a
concrete mixed schema that can support:
- content review
- workflow review
- evidence review


Why 33 candidates were excluded
-------------------------------
The excluded file contains the Layer 3 rows marked `review`.

In practice, those rows are mostly:
- abstract principle-driven rules
- delegated-detail rules
- rules that still need narrower decree/subrule design
- rules where the SIR-link is still too unstable for the first MVP

That is a good exclusion, not a failure.

It means the first MVP freeze is staying inside the legal areas that are:
- more operational
- more evidence-backed
- more directly mappable


How to read a final Layer 4 rule row
------------------------------------
A Layer 4 rule row now means:

1. this obligation survived the MVP selection gate  
2. this is the mapped legal family  
3. this is the logic style the future engine will need  
4. these are the future SIR fields or workflow fields it depends on  
5. this is the evidence source the future reviewer system must access  

So the final rule pack is already usable as the bridge between:
- legal source
- future SIR extraction
- future deterministic matching


How to read a final Layer 4 SIR field
-------------------------------------
A Layer 4 SIR field now means:

1. at least one surviving legal rule depends on this field  
2. the field has a known evidence shape  
3. the field has known supporting articles  
4. the field has known product/channel scope patterns  

So the final SIR schema is no longer conceptual.
It is traceable and backed by the compiled legal workflow.


What still remains after Layer 4
--------------------------------
Layer 4 is the last compilation layer, but not the last engineering step.

After this, the next major work would be:
- build the actual runtime SIR extraction logic for these fields
- define how each field is populated from real content/workflow inputs
- build deterministic checks for the Layer 4 rule pack
- decide how the excluded 33 candidates should be handled in later versions

So Layer 4 finishes:
- legal parsing
- legal annotation
- obligation decomposition
- rule/SIR-link candidate design
- first MVP freeze

It does not yet finish:
- runtime execution
- end-to-end compliance scoring
- content parser implementation


Best short interpretation
-------------------------
Layer 4 is the point where the Chapter 4 legal dataset stopped being only
annotated law and became the first frozen MVP compliance schema:

- `76` selected rules
- `29` selected SIR fields
- `0` validation errors

That is the first version of the legal backbone we can now build the actual
workflow on top of.
