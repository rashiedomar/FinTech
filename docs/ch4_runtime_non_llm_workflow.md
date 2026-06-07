Chapter 4 Non-LLM Runtime Workflow
==================================

Purpose
-------
This note explains the runtime layer that sits on top of the finalized Layer 4
artifacts.

The runtime answers this question:

**If a new input arrives now, can we run a deterministic review without using an
LLM?**

The answer is:

**yes, for the first MVP scope**


What the runtime uses
---------------------
Legal backbone inputs:
- `data/finalized/ch4_fincpa/law_fincpa_main_ch4_layer4_mvp_rule_pack.jsonl`
- `data/finalized/ch4_fincpa/law_fincpa_main_ch4_layer4_mvp_sir_schema.json`

Runtime code:
- `src/safeguard_ai/ch4_runtime.py`
- `scripts/run_ch4_non_llm_workflow.py`

Runtime input contract:
- `data/finalized/ch4_fincpa/law_fincpa_main_ch4_runtime_input_schema.json`


Runtime stages
--------------

### 1. New input normalization
The runtime accepts a JSON input with:
- `input_id`
- `review_scope`
- `product_scope_hint`
- `channel_scope_hint`
- `business_role_hint`
- optional `include_rule_families`
- optional `exclude_rule_families`
- optional raw `content_text`
- optional structured metadata

This is how we stop different review cases from being mixed together.

Examples:
- content-only ad review
- contracting workflow review
- access-request recordkeeping review

### 2. SIR extraction
The runtime converts the input into the `29` Layer 4 SIR fields.

Each field gets:
- `status`
- `value`
- `evidence`
- `source`

Allowed statuses:
- `present`
- `not_evidenced`
- `not_applicable`
- `uncertain`

The extractor uses 4 sources in order:
1. explicit `field_inputs`
2. structured metadata
3. deterministic text heuristics
4. context-based `not_applicable` handling

### 3. Rule applicability filter
Before evaluation, the runtime filters rules by:
- `review_scope`
- `product_scope_hint`
- `channel_scope_hint`
- `business_role_hint`
- included / excluded rule families

This is important because Layer 4 spans more than one business slice.

Without this filter:
- advisory rules would fire on direct-seller ads
- intermediary rules would fire on non-intermediary cases
- recordkeeping rules could interfere with simple content-only reviews

### 4. Deterministic evaluation
Each applicable Layer 4 rule is evaluated without an LLM.

Output status per rule:
- `passed`
- `failed`
- `uncertain`
- `not_applicable`

### 5. Final review report
The runtime emits:
- JSON report
- Markdown summary

It also computes:
- final decision
- escalation flag
- missing SIR fields
- active rules


Runtime decision model
----------------------

### Final decision
- `non_compliant`
  - at least one failed applicable rule
- `needs_human_review`
  - no failures but at least one uncertain rule
- `compliant`
  - applicable rules passed with no failures or uncertainty
- `insufficient_scope`
  - no applicable rules after filtering

### Escalation
- `true`
  - any failed or uncertain applicable rule
- `false`
  - otherwise


What this runtime does well
---------------------------
- uses only the official-law-derived Layer 4 artifacts
- no Gemini in runtime evaluation
- supports both raw text and structured metadata
- avoids many false positives through scope filtering
- already produces working review outputs


Current limitations
-------------------
- text extraction is still heuristic, not full production parsing
- no evidence retrieval layer yet
- no clause-quote ranking yet
- no LLM rewrite/explanation layer yet
- no human review UI logic yet


How to run it
-------------
Example command:

```bash
python scripts/run_ch4_non_llm_workflow.py \
  --input data/runtime/ch4_fincpa/examples/loan_ad_content_only.json
```

Outputs go to:
- `data/runtime/ch4_fincpa/results/`


Current example files
---------------------
Inputs:
- `data/runtime/ch4_fincpa/examples/loan_ad_content_only.json`
- `data/runtime/ch4_fincpa/examples/investment_solicitation_full.json`
- `data/runtime/ch4_fincpa/examples/access_request_record_only.json`

Outputs:
- `data/runtime/ch4_fincpa/results/*.review_report.json`
- `data/runtime/ch4_fincpa/results/*.summary.md`


Best short explanation
----------------------
The legal layers already produced the Chapter 4 MVP rule pack and SIR schema.
The non-LLM runtime now takes a new case, fills the SIR fields, filters the
relevant Layer 4 rules, evaluates them deterministically, and emits a review
result without using an LLM.

