Chapter 4 Manual Verification Checklist
=======================================

Purpose
-------
This checklist is for human review after deterministic parsing.

The parser already extracted the Chapter 4 clause dataset without using any LLM.
This checklist is the next control step before the dataset is treated as trusted.

Files to review
---------------
- `data/raw/official/law_fincpa_main_2026-01-02.pdf`
- `data/parsed/ch4_fincpa/law_fincpa_main_ch4_fulltext.txt`
- `data/parsed/ch4_fincpa/law_fincpa_main_ch4_clause_records.jsonl`
- `data/parsed/ch4_fincpa/law_fincpa_main_ch4_parse_report.md`

Verification items
------------------
1. Scope check
- confirm the dataset starts at `제4장 금융상품판매업자등의 영업행위 준수사항`
- confirm the dataset stops before `제5장 금융소비자 보호`

2. Article coverage check
- confirm all intended Chapter 4 articles are present
- confirm no Chapter 5 content is included

3. Section boundary check
- confirm section labels such as:
  - `제1절 영업행위 일반원칙`
  - `제2절 금융상품 유형별 영업행위 준수사항`
  are assigned correctly

4. Article header check
- confirm each `article_id` is correct
- confirm each `article_title` matches the official PDF

5. Paragraph boundary check
- confirm paragraph markers such as `①`, `②`, `③` were split correctly
- confirm articles without paragraph markers remain whole

6. Page traceability check
- confirm `page_start` is reasonable for each article

7. Text fidelity check
- compare a sample of rows against the PDF directly
- confirm no sentences were invented
- confirm no text from another article was merged in by mistake

8. Priority clause check
- manually review high-priority clauses first, especially:
  - `제19조`
  - `제20조`
  - `제21조`
  - `제21조의2`
  - `제22조`

Suggested acceptance rule
-------------------------
For the first trusted legal dataset, mark a row as trusted only after:

- source scope is correct
- article and paragraph boundaries are correct
- raw text is faithful to the PDF

Suggested next step after verification
--------------------------------------
After manual verification, add a second-layer annotation process for:

- topic label
- product scope
- obligation type
- future mapping to SIR facts

Important note
--------------
Manual verification is a review step, not a rewriting step.

The source text should remain tied to the official PDF.
Only metadata, labels, and later legal-to-SIR mappings should be added on top.
