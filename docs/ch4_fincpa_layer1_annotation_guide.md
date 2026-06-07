Chapter 4 Layer 1 Annotation Guide
==================================

Purpose
-------
Layer 1 annotation adds controlled legal metadata on top of the parsed Chapter 4
clause dataset.

This is still a manual review layer.

We are not yet:

- compiling rules
- deriving SIR targets
- matching ads
- using an LLM as the source of truth

Layer 1 only answers:

- Is this clause relevant to our Theme 2 workflow?
- What kind of legal topic is it?
- What product scope does it apply to?
- What channel or business process does it govern?
- What kind of obligation does it create?
- Does it need a second decomposition step later?

Input
-----
Source parsed dataset:

- `data/parsed/ch4_fincpa/law_fincpa_main_ch4_clause_records.jsonl`

Generated annotation sheet:

- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer1_annotations.csv`
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer1_annotations.blank.jsonl`
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer1_annotations.prefilled.csv`
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer1_annotations.prefilled.jsonl`

Controlled label guide:

- `data/annotations/ch4_fincpa/layer1_label_guide.json`

Validation and reviewed export:

- `scripts/prefill_ch4_layer1_annotations.py`
- `scripts/annotate_ch4_layer1_with_gemini.py`
- `scripts/validate_ch4_layer1_annotations.py`
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer1_annotations.reviewed.jsonl`
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer1_validation_report.json`
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer1_prefill_report.json`
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer1_annotations.gemini.csv`
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer1_annotations.gemini.jsonl`
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer1_gemini_report.json`

How to annotate
---------------
For each parsed clause record, fill these annotation fields:

1. `is_relevant_to_theme2`
- `yes`
- `no`
- `review`

Meaning:
- `yes`: clearly useful for the intended compliance workflow
- `no`: out of immediate scope for the first workflow
- `review`: not clear yet, needs team discussion

2. `topic_family`
Choose one:

- `general_principle`
- `internal_control`
- `consumer_fit_assessment`
- `explanation_duty`
- `unfair_sales_practice`
- `improper_solicitation`
- `advertising_compliance`
- `other`

3. `product_scope`
Choose one or more, separated by `|`

- `general`
- `loan`
- `deposit`
- `investment`
- `insurance`
- `multiple`

Guideline:
- use `general` when the clause applies broadly
- use `multiple` when the clause explicitly spans several product families

4. `channel_scope`
Choose one or more, separated by `|`

- `all_customer_facing`
- `advertising`
- `solicitation`
- `contracting`
- `advisory`
- `visit_sales`
- `phone_sales`
- `internal_control`

5. `obligation_mode`
Choose one:

- `general_principle`
- `required_action`
- `required_content`
- `prohibited_action`
- `workflow_control`
- `recordkeeping`

6. `needs_decomposition`
- `yes`
- `no`

Meaning:
- `yes`: the clause contains multiple operational requirements and should later be
  split into separate obligation records
- `no`: the clause is already specific enough to stay as one unit for now

7. `manual_verified`
- `yes`
- `no`

Meaning:
- `yes`: reviewer has checked the annotation and accepts it
- `no`: still pending

8. `reviewer_note`
Free text.

Use this for:
- ambiguity
- scope concerns
- product-specific reasoning
- future decomposition hints

Example
-------
For `제22조:③` a reasonable Layer 1 annotation might be:

- `is_relevant_to_theme2 = yes`
- `topic_family = advertising_compliance`
- `product_scope = multiple`
- `channel_scope = advertising|all_customer_facing`
- `obligation_mode = required_content`
- `needs_decomposition = yes`
- `manual_verified = yes`

Why?
- it is clearly relevant to customer-facing financial content review
- it applies across several product families
- it contains multiple required content obligations
- it should later be decomposed into more specific legal obligation units

Important rule
--------------
Layer 1 is still a metadata layer, not an interpretation engine.

Do not rewrite the law text.
Do not convert it to SIR targets yet.
Do not guess more than the clause supports.

Review workflow
---------------
1. Generate the deterministic prefill:

```bash
python scripts/prefill_ch4_layer1_annotations.py
```

2. Review and correct:
- `law_fincpa_main_ch4_layer1_annotations.prefilled.csv`

3. Save the checked version back into:
- `law_fincpa_main_ch4_layer1_annotations.csv`

4. Keep labels inside the controlled values in `layer1_label_guide.json`.
5. Run:

```bash
python scripts/validate_ch4_layer1_annotations.py
```

6. Check:
- `law_fincpa_main_ch4_layer1_validation_report.json`
- `law_fincpa_main_ch4_layer1_annotations.reviewed.jsonl`

The prefill is deterministic:
- article id mapping
- paragraph id overrides
- section structure
- small text-trigger adjustments
- no LLM used

Alternative assisted workflow
-----------------------------
If you want Gemini to propose Layer 1 labels and the team to only verify them:

```bash
python scripts/annotate_ch4_layer1_with_gemini.py
```

This produces:
- `law_fincpa_main_ch4_layer1_annotations.gemini.csv`
- `law_fincpa_main_ch4_layer1_annotations.gemini.jsonl`

Important:
- the clause text and boundaries still come from deterministic parsing
- Gemini is only suggesting metadata labels
- manual review is still required before accepting the file

If the validator reports errors, fix the CSV and run it again.
