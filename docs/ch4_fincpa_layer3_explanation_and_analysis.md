Chapter 4 Layer 3 Explanation And Analysis
==========================================

Purpose
-------
This note explains what Layer 3 is, how the recent Layer 3 run was performed,
what each Layer 3 field means, and how to interpret the resulting rule and
SIR-link candidate dataset.

Important clarification
-----------------------
Layer 3 is still not the final rule engine.

Layer 3 works on the output of Layer 2:
- one Layer 2 obligation unit in
- one Layer 3 rule/SIR-link candidate out

So Layer 3 is:
- first-pass rule compilation
- first-pass SIR-link design

It is not yet:
- final executable code
- final SIR schema
- final compliance judgment


What happened just now
----------------------
We already had:
- deterministic parsing into 60 clause records
- Layer 1 legal metadata
- Layer 2 decomposition into 109 obligation units

Then we ran Layer 3.

### Step 1. Inputs used
Layer 3 used:
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer2_obligations.gemini.csv`
- `data/annotations/ch4_fincpa/layer3_label_guide.json`

### Step 2. Gemini-assisted rule compilation
For each Layer 2 obligation unit, Gemini was asked to propose:
- a rule family
- a logic type
- a detection target
- a SIR-link type
- candidate SIR fields
- an evidence source
- whether it looks usable for an MVP (`ready_for_v1`)

Gemini model used:
- `gemini-3.5-flash`

As with earlier layers:
- structured JSON output was enforced
- the thinking budget was disabled to avoid truncated responses


What Layer 3 actually is
------------------------
Layer 2 answers:
- what smaller obligations exist in the law?

Layer 3 answers:
- what kind of future rule could check this obligation?
- what kind of evidence would that rule need?
- can the obligation connect to a future SIR field?

So:
- Layer 2 = legal obligation decomposition
- Layer 3 = rule candidate and SIR-link candidate design


What Layer 3 outputs look like
------------------------------
Main output:
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer3_rule_candidates.gemini.csv`
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer3_rule_candidates.gemini.jsonl`

Validation:
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer3_validation_report.json`

Review priority:
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer3_review_priority.csv`
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer3_review_priority_report.json`

Run report:
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer3_gemini_report.json`


What each Layer 3 field means
-----------------------------

### `source_obligation_id`
The Layer 2 obligation unit that this Layer 3 rule candidate comes from.

### `rule_candidate_id`
A generated id for the compiled rule candidate.

### `rule_candidate_summary`
A short operational summary of the future rule.

This is the most important human-readable Layer 3 field.

### `rule_family`
This is the broad rule category.

Allowed values:
- `general_principle`
- `suitability`
- `adequacy`
- `explanation`
- `advertising`
- `unfair_sales`
- `solicitation`
- `contract_documents`
- `internal_control`
- `recordkeeping`
- `intermediary`
- `advisory`

Examples:
- Article 22 ad obligations -> usually `advertising`
- Article 17 obligations -> usually `suitability`
- Article 19 obligations -> usually `explanation`

### `logic_type`
This says what kind of rule logic would later enforce the obligation.

Allowed values:
- `required_presence`
- `prohibited_presence`
- `required_process`
- `required_record`
- `required_response`
- `delegated_detail`
- `principle_guardrail`

Meaning:
- `required_presence`
  - a required visible field or disclosure
- `prohibited_presence`
  - prohibited claim, phrase, or act
- `required_process`
  - a workflow/process step must exist
- `required_record`
  - a record/log/evidence item must exist
- `required_response`
  - the organization must respond when a triggering event occurs
- `delegated_detail`
  - the specific content is still delegated to decree/subrule
- `principle_guardrail`
  - broad principle, still too abstract for direct deterministic execution

### `detection_target`
This says what the future rule would examine.

Allowed values:
- `content_text`
- `workflow_metadata`
- `consumer_profile`
- `document_bundle`
- `record_system`
- `mixed`

Meaning:
- `content_text`
  - check visible customer-facing text
- `workflow_metadata`
  - check process logs / workflow state / approval metadata
- `consumer_profile`
  - check suitability/adequacy input profiles
- `document_bundle`
  - check document packages or explanation materials
- `record_system`
  - check archives, logs, or registries
- `mixed`
  - needs more than one evidence type

### `sir_link_type`
This says how directly the rule candidate can connect to future SIR or workflow fields.

Allowed values:
- `direct_content_field`
- `direct_workflow_field`
- `direct_record_field`
- `derived_decision_field`
- `delegated_external_detail`
- `principle_only`

Meaning:
- `direct_content_field`
  - likely maps directly to a visible content-side SIR field
- `direct_workflow_field`
  - maps to workflow/system state rather than content text
- `direct_record_field`
  - maps to logs, archives, or registry fields
- `derived_decision_field`
  - needs derived logic based on several inputs
- `delegated_external_detail`
  - not fully usable until decree/subrule details are added
- `principle_only`
  - still too abstract for concrete SIR mapping

### `sir_candidate_fields`
These are candidate future fields that could represent the rule operationally.

Examples from the controlled list:
- `consumer_type`
- `consumer_profile`
- `suitability_check`
- `adequacy_check`
- `explanation_material`
- `explanation_confirmation`
- `contract_document_delivery`
- `seller_identity`
- `product_identity`
- `product_core_terms`
- `loan_conditions`
- `loan_rate_basis`
- `loan_interest_timing`
- `loan_costs`
- `prohibited_claim_signal`
- `internal_control_standard`
- `activity_record`
- `access_request`
- `access_response`

### `evidence_source`
This says where the future rule would likely pull evidence from.

Allowed values:
- `visible_content`
- `workflow_log`
- `consumer_profile_form`
- `explanation_form`
- `contract_document`
- `record_archive`
- `decree_reference`
- `mixed`

### `ready_for_v1`
This is a practical MVP-readiness judgment.

Allowed values:
- `yes`
- `review`
- `no`

Meaning:
- `yes`
  - likely usable for a first MVP rule set
- `review`
  - needs legal or product review before inclusion
- `no`
  - not a good first-MVP candidate in current form


What Gemini was actually given
------------------------------
Gemini was given:
- one Layer 2 obligation row at a time
- the parent clause/article metadata
- the obligation summary
- the source span text
- the Layer 3 controlled label guide

Gemini was told:
- do not invent new legal obligations
- compile only one rule candidate per obligation
- decide how the obligation would later be checked
- decide what type of SIR/workflow field could support it

Gemini was **not** given:
- the final SIR schema
- the final rule engine code
- ad examples


Layer 3 run results
-------------------
Source:
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer3_gemini_report.json`

Run result:
- total input obligations: `109`
- successful rule candidates: `109`
- errors: `0`
- elapsed: `260.41s`

Validation result:
- validation errors: `0`

Source:
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer3_validation_report.json`


Layer 3 distribution analysis
-----------------------------

### Rule family distribution
- `general_principle`: `6`
- `internal_control`: `3`
- `recordkeeping`: `10`
- `intermediary`: `15`
- `solicitation`: `11`
- `suitability`: `10`
- `adequacy`: `10`
- `explanation`: `11`
- `unfair_sales`: `8`
- `advertising`: `15`
- `contract_documents`: `3`
- `advisory`: `7`

Interpretation:
- the strongest operational families in Chapter 4 are:
  - `advertising`
  - `intermediary`
  - `solicitation`
  - `explanation`
  - `suitability`
  - `adequacy`

This matches the legal structure of Chapter 4 well.

### Logic type distribution
- `principle_guardrail`: `7`
- `prohibited_presence`: `28`
- `required_process`: `21`
- `required_presence`: `24`
- `required_record`: `6`
- `required_response`: `7`
- `delegated_detail`: `16`

Interpretation:
- the most important directly usable rule types are:
  - `prohibited_presence`
  - `required_presence`
  - `required_process`

These are the strongest candidates for first MVP implementation.

The least direct ones are:
- `principle_guardrail`
- `delegated_detail`

These are precisely the rules that still need legal or policy design work.

### Detection target distribution
- `record_system`: `14`
- `workflow_metadata`: `56`
- `content_text`: `31`
- `consumer_profile`: `5`
- `document_bundle`: `2`
- `mixed`: `1`

Interpretation:
- the future system will not be only a text checker
- most rules depend on:
  - workflow metadata
  - system records
- only part of the law is directly checkable through visible content text alone

This is a very important business insight.

### SIR-link type distribution
- `principle_only`: `6`
- `derived_decision_field`: `8`
- `direct_record_field`: `9`
- `direct_workflow_field`: `37`
- `direct_content_field`: `29`
- `delegated_external_detail`: `20`

Interpretation:
- the strongest operational bridge is:
  - `direct_workflow_field`
  - followed by `direct_content_field`

This means the future workflow should clearly have two sides:
- content-side SIR fields
- workflow-side/internal evidence fields

Also:
- `delegated_external_detail = 20`
shows that decree-level work still matters for a meaningful chunk of the law

### Evidence source distribution
- `record_archive`: `12`
- `decree_reference`: `19`
- `workflow_log`: `39`
- `visible_content`: `21`
- `consumer_profile_form`: `5`
- `explanation_form`: `12`
- `contract_document`: `1`

Interpretation:
- `workflow_log` is the single most important future evidence source
- `visible_content` is important, but not enough by itself

This strongly supports the idea that the final system must be:
- hybrid
- content-aware
- workflow-aware

### Ready-for-v1 distribution
- `yes`: `76`
- `review`: `33`
- `no`: `0`

Interpretation:
- most rule candidates already look usable for a first MVP
- about one third still need review
- none were marked fully unusable


Top candidate SIR fields
------------------------
Most frequently suggested SIR/workflow fields:
- `prohibited_claim_signal`: `22`
- `activity_record`: `17`
- `intermediary_status`: `16`
- `fairness_guardrail`: `14`
- `consumer_profile`: `12`
- `explanation_material`: `11`
- `internal_control_standard`: `10`
- `product_core_terms`: `10`
- `suitability_check`: `10`
- `adequacy_check`: `10`

Interpretation:
- the future SIR/workflow design should almost certainly include:
  - prohibited claim signals
  - product core terms
  - consumer profile / suitability / adequacy fields
  - internal control and activity record fields


Examples from key articles
--------------------------

### `제22조` advertising rules
Layer 3 produced strong direct content-side candidates such as:
- ad required-content checks
- prohibited misleading-ad checks
- product-family-specific content checks

These mostly became:
- `rule_family = advertising`
- `logic_type = required_presence` or `prohibited_presence`
- `detection_target = content_text`
- `sir_link_type = direct_content_field`

This is the strongest direct bridge to future ad-review SIR.

### `제19조` explanation duty
Layer 3 created:
- content-side explanation rules
- workflow-side explanation confirmation rules
- delegated detail rules for decree-dependent pieces

This suggests a mixed future design:
- visible content checks
- explanation material/document checks
- process confirmation checks

### `제17조` suitability
Layer 3 produced:
- consumer type verification rules
- profile collection rules
- recordkeeping rules
- unsuitable recommendation prohibition rules

These are mostly:
- workflow-driven
- consumer-profile-driven

This means suitability is much more about process metadata than visible content.

### `제28조` recordkeeping and access
Layer 3 produced:
- archive existence rules
- record integrity control rules
- response-timing rules for access requests

This is mostly:
- `record_system`
- `workflow_metadata`
- not customer-facing content text


Review priority analysis
------------------------
Source:
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer3_review_priority.csv`
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer3_review_priority_report.json`

Priority counts:
- `high`: `25`
- `medium`: `5`
- `low`: `79`

Interpretation:
- Layer 3 is more stable than Layer 2
- only a smaller subset now needs concentrated review

High priority was assigned mainly when:
- the article is one of the central operational articles
- the candidate is still `review`
- the logic is abstract (`delegated_detail`, `principle_guardrail`)
- the SIR link is weak (`delegated_external_detail`, `principle_only`)

High-priority review patterns:
- `delegated_detail`: `16`
- `principle_guardrail`: `6`
- `delegated_external_detail`: `19`
- `principle_only`: `6`

So the review team should focus first on:
- abstract principle rules
- decree-dependent rules
- weak-SIR-link rules

Especially in:
- `제22조`
- `제17조`
- `제19조`
- `제18조`
- `제23조`
- `제28조`


What Layer 3 tells us about the future system
--------------------------------------------
Layer 3 gives a strong architectural signal:

### 1. The future system must support both content and workflow evidence
Because:
- `workflow_metadata = 56`
- `content_text = 31`

So a text-only checker is not enough.

### 2. Many rules are already MVP-ready
Because:
- `ready_for_v1 = yes` for `76` candidates

That means we already have a meaningful first rule-candidate set.

### 3. Some rules still depend on decree/policy completion
Because:
- `delegated_external_detail = 20`
- `delegated_detail = 16`

So not everything should be pushed into v1 immediately.

### 4. The future SIR should not only describe visible ad text
It also needs:
- workflow-side fields
- consumer-profile fields
- record/archive fields
- fairness and prohibited-claim signals


What Layer 3 is NOT
-------------------
Layer 3 is not:
- final executable rule code
- final SIR schema
- final legal truth
- final model inference workflow

Layer 3 is:
- a structured rule-design layer
- a structured SIR-link design layer


Practical conclusion
--------------------
Layer 3 is functionally complete as a **Gemini-assisted first-pass rule
compilation layer**.

That means:
- 109 obligation units were compiled into 109 rule candidates
- validation passed with `0` schema errors
- review-priority files were generated
- the strongest V1-ready candidates are now visible

The most important output of Layer 3 is this:

**We now know which legal obligations are likely to become:**
- direct content rules
- workflow rules
- recordkeeping rules
- abstract guardrails
- decree-dependent follow-up rules

This is the exact bridge needed before building the first actual SIR schema and
rule engine implementation.

