Chapter 4 Runtime Execution Report
==================================

Purpose
-------
This note records the first deterministic runtime executions built on top of the
Layer 4 MVP rule pack and SIR schema.


Runtime command
---------------
All runs used:

```bash
python scripts/run_ch4_non_llm_workflow.py --input <example.json>
```


Executed examples
-----------------

### 1. `loan_ad_content_only`
Input:
- `data/runtime/ch4_fincpa/examples/loan_ad_content_only.json`

Result:
- final decision: `non_compliant`
- escalate: `true`
- applicable rules: `3`
- failed rules: `1`
- uncertain rules: `0`

Main reason:
- the runtime extracted:
  - `seller_identity = present`
  - `product_identity = present`
  - `loan_conditions = present`
  - `loan_costs = present`
- but:
  - `loan_rate_basis = not_evidenced`
  - `loan_interest_timing = not_evidenced`

Triggered rule:
- `law_fincpa_main_2026-01-02:제22조:④:ob04:rule01`

Meaning:
- the ad showed a loan/cost signal
- but it did not evidence rate-basis or interest-timing disclosures


### 2. `investment_solicitation_full`
Input:
- `data/runtime/ch4_fincpa/examples/investment_solicitation_full.json`

Result:
- final decision: `compliant`
- escalate: `false`
- applicable rules: `17`
- failed rules: `0`
- uncertain rules: `0`

Meaning:
- the provided content/workflow/record metadata was sufficient for the selected
  Layer 4 rule families
- the deterministic runtime found no missing required evidence in scope


### 3. `access_request_record_only`
Input:
- `data/runtime/ch4_fincpa/examples/access_request_record_only.json`

Result:
- final decision: `compliant`
- escalate: `false`
- applicable rules: `4`
- failed rules: `0`
- uncertain rules: `0`

Meaning:
- the provided access-request and response evidence was enough for the selected
  recordkeeping rules in scope


Output files
------------
JSON review reports:
- `data/runtime/ch4_fincpa/results/loan_ad_content_only.review_report.json`
- `data/runtime/ch4_fincpa/results/investment_solicitation_full.review_report.json`
- `data/runtime/ch4_fincpa/results/access_request_record_only.review_report.json`

Markdown summaries:
- `data/runtime/ch4_fincpa/results/loan_ad_content_only.summary.md`
- `data/runtime/ch4_fincpa/results/investment_solicitation_full.summary.md`
- `data/runtime/ch4_fincpa/results/access_request_record_only.summary.md`


What these runs prove
---------------------
They prove that the repo now supports:
- new runtime input
- deterministic SIR extraction
- deterministic Layer 4 evaluation
- final non-LLM review output

So the remaining major stages are no longer:
- parsing
- legal annotation
- rule freezing
- non-LLM rule evaluation

The remaining major stages are:
- evidence retrieval
- LLM advisory / rewrite
- human review flow

