Chapter 4 Layer 3 Rule Compilation Guide
========================================

Purpose
-------
Layer 3 converts each Layer 2 obligation unit into a first-pass rule candidate
and SIR-link candidate.

Layer 2 answers:
- what smaller obligations exist inside the law?

Layer 3 answers:
- what kind of rule might enforce this obligation later?
- what kind of evidence would that rule need?
- can the rule later connect to a SIR field or workflow field?

Input
-----
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer2_obligations.gemini.csv`
- `data/annotations/ch4_fincpa/layer3_label_guide.json`

Main output
-----------
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer3_rule_candidates.gemini.csv`
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer3_rule_candidates.gemini.jsonl`

Validation
----------
- `scripts/validate_ch4_layer3_rule_candidates.py`
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer3_validation_report.json`

Review priority
---------------
- `scripts/build_ch4_layer3_review_priority.py`
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer3_review_priority.csv`
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer3_review_priority_report.json`

Key idea
--------
Layer 3 is still not the final rule engine.

It is a candidate-design layer.

For each obligation unit, the model should propose:
- a rule family
- a logic type
- a detection target
- a SIR link type
- candidate SIR fields
- an evidence source
- whether the candidate looks usable for a first MVP

Important caution
-----------------
Layer 3 is still a reviewable design artifact.
It is not final legal truth and not final code.

