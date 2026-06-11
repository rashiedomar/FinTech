Chapter 4 Post-Deterministic Workflow
=====================================

Purpose
-------
This note explains the three stages that come **after** the deterministic
runtime engine:

1. evidence retrieval
2. LLM advisory input packaging
3. human review packet construction


Simple idea
-----------
The deterministic engine already answers:

- what failed
- what legal rule triggered
- what fields were missing

The next workflow stages answer:

- what legal proof should we show?
- what exactly should we send to the LLM?
- what exactly should the human reviewer receive?


Stage 1. Evidence retrieval
---------------------------
In the current MVP, evidence retrieval is still **statute-grounded**, but it can
now also include **local vector-retrieved support** when the Chapter 4
embedding index has been built.

What it does now:
- takes each failed or uncertain rule
- pulls its legal basis from the Layer 4 rule pack
- attaches the parent parsed clause text
- attaches same-article context from the parsed Chapter 4 dataset
- optionally attaches top-k vector-retrieved legal support rows from the local
  Chapter 4 embedding index

So the evidence package now contains:
- citation label
- obligation summary
- source span text
- parent clause raw text
- parent clause normalized text
- same-article neighboring context
- optional retrieved support rows with similarity score, metadata, and chunk text

This is enough to prove that the legal grounding exists before the LLM stage.


Stage 2. LLM advisory input
---------------------------
The LLM should not receive only the raw content text.

Instead, the LLM advisory package gives it:
- original content input
- normalized review scope
- product/channel/business-role hints
- failed rules
- uncertain rules
- missing SIR fields
- focused SIR field states
- evidence package

This means the LLM is asked to:
- explain
- summarize
- advise
- suggest remediation

But it is **not** asked to replace the deterministic legal judgment.


Stage 3. Human review packet
----------------------------
The human reviewer receives a packet with:
- original content
- deterministic result
- escalation state
- missing fields
- triggered citations
- evidence summary
- allowed actions

Allowed actions:
- approve
- approve_with_edits
- reject
- escalate

This packet is the bridge into the final human oversight layer.


Output artifacts
----------------
For each runtime input, the postprocess pipeline now writes:

- `.review_trace.json`
- `.evidence_package.json`
- `.llm_advisory_input.json`
- `.human_review_packet.json`
- `.workflow_bridge_summary.md`

All outputs go into:
- `data/runtime/ch4_fincpa/results/`


How to run
----------
Run for all examples:

```bash
python scripts/run_ch4_postprocess_pipeline.py
```

Run for one example:

```bash
python scripts/run_ch4_postprocess_pipeline.py \
  --input data/runtime/ch4_fincpa/examples/investment_ad_guaranteed_return_violation.json
```


Best short explanation
----------------------
The deterministic engine decides the first compliance result. Evidence retrieval
then builds the legal proof package, the LLM advisory input wraps the result and
evidence into an explanation-ready structure, and the human review packet
prepares the final reviewer action stage.
