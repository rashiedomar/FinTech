Chapter 4 Layer 2 Decomposition Guide
=====================================

Purpose
-------
Layer 2 converts each Layer 1 legal clause record into one or more smaller
obligation units.

Layer 1 answers:
- what kind of clause is this?
- what broad workflow area does it belong to?

Layer 2 answers:
- what exact smaller duties are inside this clause?
- what kind of operational trigger does each duty create?
- can the duty later be linked to a content-side SIR field or review check?

Input
-----
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer1_annotations.gemini.csv`
- `data/parsed/ch4_fincpa/law_fincpa_main_ch4_clause_records.jsonl`
- `data/annotations/ch4_fincpa/layer2_label_guide.json`

Main output
-----------
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer2_obligations.gemini.csv`
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer2_obligations.gemini.jsonl`

Parent summary
--------------
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer2_parent_summary.csv`

Validation
----------
- `scripts/validate_ch4_layer2_obligations.py`
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer2_validation_report.json`

Review priority
---------------
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer2_review_priority.csv`
- `data/annotations/ch4_fincpa/law_fincpa_main_ch4_layer2_review_priority_report.json`

Core rule
---------
For each parent clause:

- if the clause is already atomic, output 1 obligation unit
- if the clause contains multiple operational duties, split it into multiple
  obligation units

Each obligation unit must:
- stay faithful to the source clause
- be smaller than the parent clause
- have a short summary
- include a source-supporting text span
- use controlled labels only

Important caution
-----------------
Layer 2 is still not final compliance logic.

It is a legal decomposition layer, not the final rule engine.

It should help later steps:
- rule compilation
- SIR linkage
- review workflow design

