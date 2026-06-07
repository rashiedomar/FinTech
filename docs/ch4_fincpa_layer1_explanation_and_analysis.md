Chapter 4 Layer 1 Explanation And Analysis
==========================================

Purpose
-------
This note explains what Layer 1 is, what happened in the recent Gemini-assisted
annotation run, what each Layer 1 field means, and how to interpret the 60
annotated clause records.

Important clarification
-----------------------
The 60 items in Layer 1 are **not business cases** and **not ad samples**.
They are **60 clause-level legal records** parsed from Chapter 4 of the
official Financial Consumer Protection Act PDF:

- `data/raw/official/law_fincpa_main_2026-01-02.pdf`

Layer 1 is a **legal metadata layer** on top of those 60 parsed legal clauses.


What happened just now
----------------------
We did the work in 2 stages.

### 1. Deterministic parsing
We first parsed the official PDF into 60 clause records.

Source outputs:
- `data/parsed/ch4_fincpa/law_fincpa_main_ch4_clause_records.jsonl`
- `data/parsed/ch4_fincpa/law_fincpa_main_ch4_parse_report.md`

This parsing step was:
- deterministic
- based on the official PDF only
- not performed by Gemini

### 2. Layer 1 annotation
We then added Layer 1 metadata in 2 different ways:

- deterministic prefill
- Gemini-assisted annotation

Deterministic prefill outputs:
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer1_annotations.prefilled.csv`
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer1_prefill_report.json`

Gemini-assisted outputs:
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer1_annotations.gemini.csv`
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer1_annotations.gemini.jsonl`
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer1_gemini_report.json`

Gemini model used:
- `gemini-3.5-flash`

Important runtime note:
- Gemini initially returned truncated JSON
- the runner was fixed by disabling the thinking budget and forcing structured JSON output
- after that, the full 60-clause run completed successfully


What Layer 1 actually is
------------------------
Layer 1 does **not** create rules yet.
Layer 1 does **not** create SIR fields yet.
Layer 1 does **not** decide compliance for ad content yet.

Layer 1 only adds **high-level legal metadata** such as:
- whether the clause looks relevant to the intended workflow
- what legal topic family it belongs to
- what product family it seems to govern
- what business channel/process it seems to govern
- what kind of obligation it creates
- whether the clause is too large and should later be decomposed


What each Layer 1 field means
-----------------------------

### `is_relevant_to_theme2`
Current meaning in practice:
- "Is this clause relevant to our intended compliance workflow slice?"

This field name is misleading.
Gemini was **not** given the official hackathon Theme 2 PDF and asked to
independently infer hackathon relevance.

Instead, Gemini was given our controlled annotation scope and asked whether the
clause looked relevant to that scope.

So this field should really be interpreted as:
- `is_relevant_to_target_workflow`

Current allowed values:
- `yes`
- `no`
- `review`

### `topic_family`
This is a controlled legal-function grouping.
It is **not** a raw fact copied from the law.

Allowed values:
- `general_principle`
- `internal_control`
- `consumer_fit_assessment`
- `explanation_duty`
- `unfair_sales_practice`
- `improper_solicitation`
- `advertising_compliance`
- `other`

Examples:
- `제17조`, `제18조` -> often `consumer_fit_assessment`
- `제19조` -> often `explanation_duty`
- `제22조` -> often `advertising_compliance`

### `product_scope`
This is an annotation judgment about which product family the clause applies to.
It is **not** a parser fact.

Allowed values:
- `general`
- `loan`
- `deposit`
- `investment`
- `insurance`
- `multiple`

Interpretation:
- `general`: broad, not specific to one product family
- `loan`: clearly loan-specific
- `multiple`: explicitly spans several product families

### `channel_scope`
This is an annotation judgment about which business channel or process the
clause mainly governs.

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
This is one of the most important Layer 1 fields.
It describes **what kind of duty** the clause creates.

Allowed values:
- `general_principle`
- `required_action`
- `required_content`
- `prohibited_action`
- `workflow_control`
- `recordkeeping`

Meaning:
- `general_principle`
  - broad principle, not directly executable on its own
- `required_action`
  - the seller must do something
- `required_content`
  - the seller must include or disclose something
- `prohibited_action`
  - the seller must not do something
- `workflow_control`
  - control/process/system/approval obligation
- `recordkeeping`
  - logging, evidence retention, or record management obligation

### `needs_decomposition`
This asks whether one clause is too large to use later as one direct obligation.

Allowed values:
- `yes`
- `no`

Meaning:
- `yes`
  - the clause contains multiple sub-obligations and should later be split
- `no`
  - the clause is already simple enough to stay as one unit for now

Examples:
- `제22조:③` -> usually `yes`
  - because it contains multiple ad-content requirements across product types
- `제22조:②` -> usually `no`
  - because it is one broad clarity/fairness principle


What Gemini was actually given
------------------------------
Gemini was given:
- clause metadata:
  - `record_id`
  - `chapter_id`
  - `section_id`
  - `article_id`
  - `article_title`
  - `paragraph_id`
  - `page_start`
- `normalized_text`
- the controlled label guide
- explicit instructions to:
  - stay inside allowed values
  - not rewrite the law
  - not create SIR yet
  - output structured JSON only

Gemini was **not** given:
- the full hackathon Theme 2 PDF
- the full original legal PDF as an unstructured whole
- ad samples
- the later SIR schema


Layer 1 analysis of the 60 clause records
-----------------------------------------

### A. Deterministic prefill summary
Source:
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer1_prefill_report.json`

Relevance distribution:
- `yes`: 37
- `review`: 23

Topic family distribution:
- `general_principle`: 4
- `internal_control`: 14
- `consumer_fit_assessment`: 11
- `explanation_duty`: 14
- `unfair_sales_practice`: 5
- `improper_solicitation`: 5
- `advertising_compliance`: 7

Obligation mode distribution:
- `general_principle`: 8
- `prohibited_action`: 12
- `workflow_control`: 7
- `required_action`: 26
- `recordkeeping`: 6
- `required_content`: 1

Interpretation:
- the deterministic prefill was deliberately conservative
- it left many clauses in `review`
- it favored structured process/action interpretations over broad inclusion

### B. Gemini 3.5 Flash summary
Source:
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer1_gemini_report.json`

Run result:
- total input records: `60`
- successful rows: `60`
- errors: `0`
- elapsed: `129.77s`

Relevance distribution:
- `yes`: 60

Topic family distribution:
- `general_principle`: 6
- `internal_control`: 3
- `other`: 13
- `improper_solicitation`: 6
- `consumer_fit_assessment`: 11
- `explanation_duty`: 6
- `unfair_sales_practice`: 7
- `advertising_compliance`: 8

Obligation mode distribution:
- `general_principle`: 6
- `prohibited_action`: 14
- `required_action`: 10
- `workflow_control`: 19
- `recordkeeping`: 3
- `required_content`: 8

Confidence distribution:
- `high`: 60

Interpretation:
- Gemini was operationally successful
- but it was too aggressive
- it marked every clause as relevant
- it used `high` confidence everywhere
- therefore this output is useful as a **review assistant**, not as final truth


Comparison analysis
-------------------
Source:
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer1_review_priority.csv`
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer1_review_priority_report.json`

Total disagreement rows:
- `57`

Field mismatch counts:
- `channel_scope`: 45
- `needs_decomposition`: 38
- `obligation_mode`: 33
- `product_scope`: 24
- `is_relevant_to_theme2`: 23
- `topic_family`: 19

Top disagreement articles:
- `제22조`: 7
- `제17조`: 6
- `제21조의2`: 6
- `제18조`: 5
- `제27조`: 5
- `제28조`: 5
- `제19조`: 4

Interpretation:
- the biggest instability is not just relevance
- the biggest instability is how the clauses are operationalized:
  - channel
  - decomposition
  - obligation type
- this is exactly why Layer 1 still requires human review


How to use Layer 1 correctly
----------------------------
The correct use of Layer 1 right now is:

1. keep deterministic parsing as the legal source of truth
2. use Gemini annotations as a suggested metadata pass
3. use the disagreement sheet for fast manual review
4. finalize the accepted Layer 1 sheet only after human checking

Recommended review order:
- `제22조`
- `제17조`
- `제18조`
- `제19조`
- `제21조의2`
- `제28조`

These are the clauses where:
- the workflow relevance is highest
- the operational interpretation matters most
- or the disagreement level is high


What Layer 1 is NOT
-------------------
Layer 1 is not:
- the final rule engine
- the SIR schema
- the ad-review logic
- legal truth by itself
- benchmark evidence by itself

Layer 1 is only:
- clause-level legal metadata
- used to prepare Layer 2 decomposition


Practical conclusion
--------------------
Layer 1 is functionally complete as an **assistant-generated review layer**.

That means:
- parsing is done
- controlled labels are defined
- deterministic prefill exists
- Gemini-assisted first-pass labels exist
- disagreement review sheet exists

But Layer 1 is **not finalized** until humans check the labels.

The most important caution is:
- `is_relevant_to_theme2` should be read as workflow relevance, not independent hackathon-theme understanding

