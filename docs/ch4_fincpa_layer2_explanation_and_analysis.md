Chapter 4 Layer 2 Explanation And Analysis
==========================================

Purpose
-------
This note explains what Layer 2 is, how the recent Layer 2 run was performed,
 what the output fields mean, and how to interpret the resulting obligation-level
 dataset.

Important clarification
-----------------------
Layer 2 does **not** work on ad examples yet.

Layer 2 still works on the **legal side**:
- the input is the 60 clause-level legal records from Chapter 4
- the output is a larger set of smaller legal obligation units

So Layer 2 is:
- **legal decomposition**

It is not yet:
- SIR
- compliance judgment
- ad review


What happened just now
----------------------
We already had:
- deterministic parsing of Chapter 4 into 60 clause records
- Layer 1 Gemini-assisted metadata labels on top of those 60 records

Then we ran Layer 2.

### Step 1. Inputs used
Layer 2 used:
- `data/parsed/ch4_fincpa/law_fincpa_main_ch4_clause_records.jsonl`
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer1_annotations.gemini.csv`
- `data/annotations/ch4_fincpa/layer2_label_guide.json`

### Step 2. Gemini-assisted decomposition
For each parent clause record, Gemini was asked to:
- keep the clause text as source truth
- use Layer 1 only as a hint
- decide whether the clause should stay as one unit or be split
- produce one or more smaller obligation units
- stay inside a controlled Layer 2 schema

Gemini model used:
- `gemini-3.5-flash`

Important runtime note:
- as with Layer 1, the runner disables the thinking budget to avoid truncated JSON
- the full 60-parent run completed successfully


What Layer 2 actually is
------------------------
Layer 1 answers:
- what kind of clause is this?
- what broad workflow area does it belong to?

Layer 2 answers:
- what exact smaller obligations are inside this clause?
- which of those are direct prohibitions, required disclosures, workflow duties,
  delegated details, or recordkeeping duties?

So:

- Layer 1 = clause metadata
- Layer 2 = obligation decomposition


What Layer 2 outputs look like
------------------------------
Each Layer 2 row is one obligation unit.

Main output:
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer2_obligations.gemini.csv`
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer2_obligations.gemini.jsonl`

Parent summary:
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer2_parent_summary.csv`

Validation:
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer2_validation_report.json`

Review priority:
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer2_review_priority.csv`
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer2_review_priority_report.json`


What each Layer 2 field means
-----------------------------

### `parent_record_id`
The original clause-level legal record from Layer 1 / parsed Chapter 4.

Example:
- `law_fincpa_main_2026-01-02:제22조:③`

### `obligation_id`
A generated obligation-level id under that parent.

Example:
- `law_fincpa_main_2026-01-02:제22조:③:ob03`

### `parent_decomposition_strategy`
This says whether the parent clause was treated as:
- `single_unit`
- `split_unit`

Meaning:
- `single_unit`
  - the whole clause stayed as one obligation
- `split_unit`
  - the parent clause was broken into multiple smaller obligation rows

### `obligation_label`
A short identifier for the smaller obligation unit.

This is a Gemini-generated label to help distinguish sibling obligations inside
the same clause.

### `obligation_summary`
A short human-readable summary of the smaller duty.

This is the most important Layer 2 description field.

### `source_span_text`
A short excerpt from the parent clause that supports the obligation unit.

This keeps the decomposition traceable back to the source law text.

### `product_scope`
The product family the obligation applies to.

Allowed values:
- `general`
- `loan`
- `deposit`
- `investment`
- `insurance`
- `multiple`

### `channel_scope`
The business channel or process the obligation mainly governs.

Allowed values:
- `all_customer_facing`
- `advertising`
- `solicitation`
- `contracting`
- `advisory`
- `visit_sales`
- `phone_sales`
- `internal_control`

### `obligation_mode`
What kind of legal duty the smaller obligation creates.

Allowed values:
- `general_principle`
- `required_action`
- `required_content`
- `prohibited_action`
- `workflow_control`
- `recordkeeping`

### `trigger_type`
This is more operational than Layer 1.
It describes what kind of trigger or check the obligation creates.

Allowed values:
- `must_do`
- `must_disclose`
- `must_not_do`
- `must_keep_record`
- `must_have_control`
- `delegated_detail`

Meaning:
- `must_do`
  - a positive action must be performed
- `must_disclose`
  - something must be disclosed or shown
- `must_not_do`
  - a prohibited act
- `must_keep_record`
  - a record/evidence retention duty
- `must_have_control`
  - a process/control/system duty
- `delegated_detail`
  - the clause mainly delegates the specific detail to decree/subrule

### `operationality`
This says how directly usable the obligation already is.

Allowed values:
- `direct_checkable`
- `needs_subrule_design`
- `delegated_to_decree`

Meaning:
- `direct_checkable`
  - can later be turned into a fairly direct review rule
- `needs_subrule_design`
  - legally meaningful, but still needs internal operational design
- `delegated_to_decree`
  - the parent law text mostly points to lower-level decree details

### `consumer_visibility`
This says whether the obligation is mainly:
- `consumer_facing`
- `internal_only`
- `both`

This is useful later for deciding whether the obligation should be matched
against visible ad/content or against internal workflow evidence.


What Gemini was actually given
------------------------------
Gemini was given:
- the parsed clause metadata
- the clause `normalized_text`
- the current Layer 1 labels as a hint:
  - topic family
  - product scope
  - channel scope
  - obligation mode
  - needs decomposition
  - reviewer note
- the controlled Layer 2 label guide
- instructions to decompose the clause into smaller obligation units

Gemini was told explicitly:
- the clause text is the source of truth
- Layer 1 is only a hint
- do not invent obligations outside the source text
- do not create SIR yet


Layer 2 run results
-------------------
Source:
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer2_gemini_report.json`

Run result:
- parent records processed: `60`
- successful parent records: `60`
- total obligation rows: `109`
- errors: `0`
- elapsed: `241.42s`

Validation result:
- validation errors: `0`

Source:
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer2_validation_report.json`


Parent-level decomposition analysis
-----------------------------------
Source:
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer2_parent_summary.csv`

Parent decomposition strategy:
- `split_unit`: `26`
- `single_unit`: `34`

Interpretation:
- 34 clauses were treated as already atomic enough to stay as one obligation
- 26 clauses were split into multiple smaller obligations

Top parent clauses by obligation count:
- `제20조:①` -> `7`
- `제19조:①` -> `6`
- `제26조:①` -> `5`
- `제22조:③` -> `5`
- `제22조:④` -> `4`
- `제21조` -> `4`
- `제18조:①` -> `4`
- `제25조:①` -> `3`
- `제17조:②` -> `3`

Interpretation:
- the richest clauses for later rule design are concentrated in:
  - `제17조`
  - `제18조`
  - `제19조`
  - `제20조`
  - `제21조`
  - `제22조`
  - `제26조`


Obligation-level distribution analysis
--------------------------------------
Source:
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer2_validation_report.json`

### Obligation mode distribution
- `general_principle`: `9`
- `prohibited_action`: `30`
- `required_action`: `14`
- `workflow_control`: `28`
- `recordkeeping`: `6`
- `required_content`: `22`

Interpretation:
- Chapter 4 is not just advertising law
- it contains a large mix of:
  - prohibitions
  - workflow controls
  - required content

This is useful because later the system can treat different obligation modes
differently in rule design.

### Trigger type distribution
- `must_do`: `41`
- `must_not_do`: `30`
- `must_have_control`: `5`
- `must_keep_record`: `6`
- `delegated_detail`: `15`
- `must_disclose`: `12`

Interpretation:
- the strongest direct operational categories are:
  - `must_do`
  - `must_not_do`
- but a meaningful portion of the law still points to:
  - lower-level decree details
  - internal control design

### Operationality distribution
- `direct_checkable`: `48`
- `needs_subrule_design`: `43`
- `delegated_to_decree`: `18`

Interpretation:
- about half the obligation units are already fairly direct
- the rest still need:
  - internal subrule design
  - decree-level elaboration

This is one of the most important Layer 2 outcomes.

It tells us:
- which obligations are immediately usable for a later rule engine
- and which still need more legal-to-operational translation

### Consumer visibility distribution
- `consumer_facing`: `73`
- `internal_only`: `25`
- `both`: `11`

Interpretation:
- most Layer 2 obligations are visible enough to matter in a customer-content or
  customer-interaction workflow
- but a substantial minority are internal-only controls

This is valuable later for deciding:
- content matching
- workflow evidence checks
- dashboard routing


Examples from key articles
--------------------------

### `제22조` advertising compliance
Layer 2 created obligation units such as:
- general ad-required content
- insurance ad-required content
- investment ad-required content
- deposit ad-required content
- loan ad-required content
- product-specific prohibited misleading advertising acts

This is exactly the kind of decomposition needed for later ad-review logic.

### `제19조` explanation duty
Layer 2 split `제19조:①` into several product-family explanation duties:
- insurance
- investment
- deposit
- loan
- linked services
- cooling-off related explanation

This shows why Layer 2 matters:
- one long legal paragraph becomes multiple smaller reviewable obligations

### `제17조` suitability principle
Layer 2 extracted distinct duties such as:
- collect consumer profile information
- confirm information by signature/recording
- provide confirmed information back to the consumer
- prohibit unsuitable recommendations

This is much more operational than the original paragraph-level clause.

### `제28조` record and data management
Layer 2 separated:
- keep business records
- protect record integrity
- respond to consumer access requests
- handle refusal/restriction conditions

This helps distinguish:
- pure recordkeeping
- consumer access workflow
- internal controls


Review priority analysis
------------------------
Source:
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer2_review_priority.csv`
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer2_review_priority_report.json`

Priority counts:
- `high`: `64`
- `medium`: `28`
- `low`: `17`

Review priority was assigned higher when:
- the parent article is one of the main operational articles
- the parent clause was split into multiple obligations
- the obligation is not directly checkable
- the obligation mode is core to workflow design

This means the fastest useful human review order is:
- `제22조`
- `제19조`
- `제17조`
- `제18조`
- `제20조`
- `제21조`
- `제23조`
- `제28조`


Important caution
-----------------
Layer 2 is still **assistant-generated**.

That means:
- the legal source text is trustworthy
- the clause boundaries are trustworthy
- the decomposition itself is still a reviewable suggestion layer

Also:
- Layer 2 currently uses **Layer 1 Gemini output as a hint**
- it does **not** yet use a fully human-finalized Layer 1 file

So if Layer 1 labels change materially for a parent clause, the corresponding
Layer 2 decomposition may later need regeneration.


What Layer 2 is NOT
-------------------
Layer 2 is not:
- the final rule engine
- SIR extraction
- ad classification
- final compliance judgment

Layer 2 is:
- obligation-level legal decomposition


Practical conclusion
--------------------
Layer 2 is now functionally complete as a **Gemini-assisted obligation
decomposition layer**.

That means:
- 60 parent legal clause records were processed
- 109 obligation units were created
- validation passed with `0` schema errors
- review-priority files were generated

The most important value of Layer 2 is:
- it turns long legal clauses into smaller operational obligations
- and makes later rule design and SIR linking much easier

The next legal-to-system bridge after this is:
- deciding how these obligation units map to future rule definitions and SIR-side
  facts

