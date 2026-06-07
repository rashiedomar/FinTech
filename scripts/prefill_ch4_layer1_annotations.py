#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
PARSED_JSONL_PATH = ROOT_DIR / "data" / "parsed" / "ch4_fincpa" / "law_fincpa_main_ch4_clause_records.jsonl"
BLANK_CSV_PATH = ROOT_DIR / "data" / "annotations" / "ch4_fincpa" / "law_fincpa_main_ch4_layer1_annotations.csv"
OUTPUT_CSV_PATH = ROOT_DIR / "data" / "annotations" / "ch4_fincpa" / "law_fincpa_main_ch4_layer1_annotations.prefilled.csv"
OUTPUT_JSONL_PATH = ROOT_DIR / "data" / "annotations" / "ch4_fincpa" / "law_fincpa_main_ch4_layer1_annotations.prefilled.jsonl"
REPORT_PATH = ROOT_DIR / "data" / "annotations" / "ch4_fincpa" / "law_fincpa_main_ch4_layer1_prefill_report.json"


BASE_FIELDS = [
    "record_id",
    "article_id",
    "paragraph_id",
    "article_title",
    "section_id",
    "section_title",
    "page_start",
    "normalized_text",
    "is_relevant_to_theme2",
    "topic_family",
    "product_scope",
    "channel_scope",
    "obligation_mode",
    "needs_decomposition",
    "manual_verified",
    "reviewer_note",
]
OUTPUT_FIELDS = BASE_FIELDS + ["auto_prefill_rule", "auto_prefill_confidence"]


ARTICLE_DEFAULTS: dict[str, dict[str, str]] = {
    "제13조": {
        "is_relevant_to_theme2": "review",
        "topic_family": "general_principle",
        "product_scope": "general",
        "channel_scope": "all_customer_facing",
        "obligation_mode": "general_principle",
        "needs_decomposition": "no",
        "auto_prefill_confidence": "medium",
        "reviewer_note": "Auto-prefill: broad interpretive principle; confirm whether to keep it in the first workflow.",
    },
    "제14조": {
        "is_relevant_to_theme2": "yes",
        "topic_family": "general_principle",
        "product_scope": "general",
        "channel_scope": "all_customer_facing",
        "obligation_mode": "general_principle",
        "needs_decomposition": "no",
        "auto_prefill_confidence": "high",
        "reviewer_note": "Auto-prefill: broad fairness and good-faith principle.",
    },
    "제15조": {
        "is_relevant_to_theme2": "review",
        "topic_family": "general_principle",
        "product_scope": "general",
        "channel_scope": "contracting|all_customer_facing",
        "obligation_mode": "prohibited_action",
        "needs_decomposition": "no",
        "auto_prefill_confidence": "medium",
        "reviewer_note": "Auto-prefill: anti-discrimination clause; may be outside the first content-review slice.",
    },
    "제16조": {
        "is_relevant_to_theme2": "yes",
        "topic_family": "internal_control",
        "product_scope": "general",
        "channel_scope": "internal_control",
        "obligation_mode": "workflow_control",
        "needs_decomposition": "no",
        "auto_prefill_confidence": "high",
        "reviewer_note": "Auto-prefill: internal control and management responsibility.",
    },
    "제16조의2": {
        "is_relevant_to_theme2": "review",
        "topic_family": "internal_control",
        "product_scope": "general",
        "channel_scope": "visit_sales|phone_sales|internal_control",
        "obligation_mode": "workflow_control",
        "needs_decomposition": "yes",
        "auto_prefill_confidence": "medium",
        "reviewer_note": "Auto-prefill: visit/phone sales operational controls; likely secondary to the first ad-review slice.",
    },
    "제17조": {
        "is_relevant_to_theme2": "yes",
        "topic_family": "consumer_fit_assessment",
        "product_scope": "multiple",
        "channel_scope": "solicitation|advisory|contracting",
        "obligation_mode": "required_action",
        "needs_decomposition": "yes",
        "auto_prefill_confidence": "high",
        "reviewer_note": "Auto-prefill: suitability principle with product-specific consumer-information requirements.",
    },
    "제18조": {
        "is_relevant_to_theme2": "yes",
        "topic_family": "consumer_fit_assessment",
        "product_scope": "multiple",
        "channel_scope": "contracting",
        "obligation_mode": "required_action",
        "needs_decomposition": "yes",
        "auto_prefill_confidence": "high",
        "reviewer_note": "Auto-prefill: adequacy principle for non-solicited product sales.",
    },
    "제19조": {
        "is_relevant_to_theme2": "yes",
        "topic_family": "explanation_duty",
        "product_scope": "multiple",
        "channel_scope": "solicitation|advisory|contracting|all_customer_facing",
        "obligation_mode": "required_action",
        "needs_decomposition": "yes",
        "auto_prefill_confidence": "high",
        "reviewer_note": "Auto-prefill: explanation duty and explanation materials.",
    },
    "제20조": {
        "is_relevant_to_theme2": "yes",
        "topic_family": "unfair_sales_practice",
        "product_scope": "multiple",
        "channel_scope": "solicitation|contracting|all_customer_facing",
        "obligation_mode": "prohibited_action",
        "needs_decomposition": "yes",
        "auto_prefill_confidence": "high",
        "reviewer_note": "Auto-prefill: unfair sales practices prohibition.",
    },
    "제21조": {
        "is_relevant_to_theme2": "yes",
        "topic_family": "improper_solicitation",
        "product_scope": "general",
        "channel_scope": "solicitation|advisory|all_customer_facing",
        "obligation_mode": "prohibited_action",
        "needs_decomposition": "yes",
        "auto_prefill_confidence": "high",
        "reviewer_note": "Auto-prefill: improper solicitation prohibition.",
    },
    "제21조의2": {
        "is_relevant_to_theme2": "review",
        "topic_family": "improper_solicitation",
        "product_scope": "general",
        "channel_scope": "visit_sales|phone_sales|internal_control",
        "obligation_mode": "required_action",
        "needs_decomposition": "yes",
        "auto_prefill_confidence": "medium",
        "reviewer_note": "Auto-prefill: contact-consent, night-contact, and related system duties for visit/phone sales.",
    },
    "제22조": {
        "is_relevant_to_theme2": "yes",
        "topic_family": "advertising_compliance",
        "product_scope": "multiple",
        "channel_scope": "advertising|all_customer_facing",
        "obligation_mode": "required_content",
        "needs_decomposition": "yes",
        "auto_prefill_confidence": "high",
        "reviewer_note": "Auto-prefill: core advertising compliance article; high priority for the first workflow.",
    },
    "제23조": {
        "is_relevant_to_theme2": "yes",
        "topic_family": "explanation_duty",
        "product_scope": "general",
        "channel_scope": "contracting",
        "obligation_mode": "required_action",
        "needs_decomposition": "yes",
        "auto_prefill_confidence": "high",
        "reviewer_note": "Auto-prefill: contract-document provision duty.",
    },
    "제24조": {
        "is_relevant_to_theme2": "review",
        "topic_family": "internal_control",
        "product_scope": "general",
        "channel_scope": "internal_control",
        "obligation_mode": "prohibited_action",
        "needs_decomposition": "no",
        "auto_prefill_confidence": "medium",
        "reviewer_note": "Auto-prefill: intermediary registration control; may be secondary to the first workflow.",
    },
    "제25조": {
        "is_relevant_to_theme2": "review",
        "topic_family": "unfair_sales_practice",
        "product_scope": "general",
        "channel_scope": "solicitation|contracting",
        "obligation_mode": "prohibited_action",
        "needs_decomposition": "yes",
        "auto_prefill_confidence": "medium",
        "reviewer_note": "Auto-prefill: prohibited actions for sales agencies/intermediaries.",
    },
    "제26조": {
        "is_relevant_to_theme2": "review",
        "topic_family": "explanation_duty",
        "product_scope": "general",
        "channel_scope": "solicitation|contracting|all_customer_facing",
        "obligation_mode": "required_action",
        "needs_decomposition": "yes",
        "auto_prefill_confidence": "medium",
        "reviewer_note": "Auto-prefill: notice/disclosure duties for sales agencies/intermediaries.",
    },
    "제27조": {
        "is_relevant_to_theme2": "review",
        "topic_family": "explanation_duty",
        "product_scope": "multiple",
        "channel_scope": "advisory|all_customer_facing",
        "obligation_mode": "required_action",
        "needs_decomposition": "yes",
        "auto_prefill_confidence": "medium",
        "reviewer_note": "Auto-prefill: advisory business conduct rules; may be outside the first ad-review slice.",
    },
    "제28조": {
        "is_relevant_to_theme2": "yes",
        "topic_family": "internal_control",
        "product_scope": "general",
        "channel_scope": "internal_control",
        "obligation_mode": "recordkeeping",
        "needs_decomposition": "yes",
        "auto_prefill_confidence": "high",
        "reviewer_note": "Auto-prefill: records retention and management duties.",
    },
}


PARAGRAPH_OVERRIDES: dict[tuple[str, str], dict[str, str]] = {
    ("제17조", "③"): {
        "obligation_mode": "prohibited_action",
        "reviewer_note": "Auto-prefill: prohibits recommending unsuitable products after suitability assessment.",
    },
    ("제19조", "③"): {
        "obligation_mode": "prohibited_action",
        "reviewer_note": "Auto-prefill: explanation duty clause with explicit false/omitted explanation prohibition.",
    },
    ("제21조의2", "④"): {
        "topic_family": "internal_control",
        "obligation_mode": "workflow_control",
        "reviewer_note": "Auto-prefill: requires systems to implement contact-consent controls.",
    },
    ("제21조의2", "⑤"): {
        "topic_family": "internal_control",
        "obligation_mode": "recordkeeping",
        "reviewer_note": "Auto-prefill: communications records access for compliance monitoring.",
    },
    ("제22조", "①"): {
        "obligation_mode": "prohibited_action",
        "reviewer_note": "Auto-prefill: unauthorized advertising prohibition.",
    },
    ("제22조", "②"): {
        "obligation_mode": "general_principle",
        "reviewer_note": "Auto-prefill: ads must be clear and fair so consumers are not misled.",
    },
    ("제22조", "③"): {
        "obligation_mode": "required_content",
        "reviewer_note": "Auto-prefill: advertisement must include required content; core clause for later decomposition.",
    },
    ("제22조", "④"): {
        "obligation_mode": "prohibited_action",
        "reviewer_note": "Auto-prefill: prohibited misleading omissions/exaggerations in advertising.",
    },
    ("제22조", "⑤"): {
        "obligation_mode": "general_principle",
        "needs_decomposition": "no",
        "reviewer_note": "Auto-prefill: cross-reference to fair labeling/advertising law.",
    },
    ("제22조", "⑥"): {
        "topic_family": "internal_control",
        "obligation_mode": "workflow_control",
        "reviewer_note": "Auto-prefill: association-level ad compliance review/notification path.",
    },
    ("제22조", "⑦"): {
        "obligation_mode": "general_principle",
        "needs_decomposition": "no",
        "reviewer_note": "Auto-prefill: details delegated to enforcement decree.",
    },
    ("제23조", "②"): {
        "topic_family": "internal_control",
        "obligation_mode": "recordkeeping",
        "reviewer_note": "Auto-prefill: proof/record path around document provision.",
    },
    ("제23조", "③"): {
        "obligation_mode": "general_principle",
        "needs_decomposition": "no",
        "reviewer_note": "Auto-prefill: detailed procedures delegated to decree.",
    },
    ("제28조", "⑤"): {
        "obligation_mode": "general_principle",
        "needs_decomposition": "no",
        "reviewer_note": "Auto-prefill: detailed retention matters delegated to decree.",
    },
}


def load_blank_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_parsed_rows(path: Path) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            rows[row["record_id"]] = row
    return rows


def apply_prefill(row: dict, parsed_row: dict) -> dict:
    article_id = row["article_id"]
    paragraph_id = row["paragraph_id"]
    defaults = ARTICLE_DEFAULTS.get(article_id, {})
    overrides = PARAGRAPH_OVERRIDES.get((article_id, paragraph_id), {})
    values = {**defaults, **overrides}

    out = dict(row)
    for key in (
        "is_relevant_to_theme2",
        "topic_family",
        "product_scope",
        "channel_scope",
        "obligation_mode",
        "needs_decomposition",
        "reviewer_note",
    ):
        out[key] = values.get(key, "")

    out["manual_verified"] = "no"
    out["auto_prefill_rule"] = f"article={article_id};paragraph={paragraph_id or 'article_level'}"
    out["auto_prefill_confidence"] = values.get("auto_prefill_confidence", "medium")

    text = parsed_row["normalized_text"]
    if article_id == "제22조" and "광고" in text:
        out["topic_family"] = "advertising_compliance"
    if article_id == "제28조" and "기록" in text:
        out["obligation_mode"] = "recordkeeping"

    return out


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def build_report(rows: list[dict]) -> dict:
    return {
        "source_blank_csv": str(BLANK_CSV_PATH.relative_to(ROOT_DIR)),
        "source_parsed_jsonl": str(PARSED_JSONL_PATH.relative_to(ROOT_DIR)),
        "output_prefilled_csv": str(OUTPUT_CSV_PATH.relative_to(ROOT_DIR)),
        "output_prefilled_jsonl": str(OUTPUT_JSONL_PATH.relative_to(ROOT_DIR)),
        "total_rows": len(rows),
        "relevance_distribution": dict(Counter(row["is_relevant_to_theme2"] for row in rows)),
        "topic_family_distribution": dict(Counter(row["topic_family"] for row in rows)),
        "obligation_mode_distribution": dict(Counter(row["obligation_mode"] for row in rows)),
        "auto_prefill_confidence_distribution": dict(Counter(row["auto_prefill_confidence"] for row in rows)),
        "method": "deterministic article/paragraph mapping with small text-trigger adjustments; no LLM used",
    }


def write_report(path: Path, report: dict) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def main() -> int:
    blank_rows = load_blank_rows(BLANK_CSV_PATH)
    parsed_rows = load_parsed_rows(PARSED_JSONL_PATH)
    out_rows = [apply_prefill(row, parsed_rows[row["record_id"]]) for row in blank_rows]
    write_csv(OUTPUT_CSV_PATH, out_rows)
    write_jsonl(OUTPUT_JSONL_PATH, out_rows)
    write_report(REPORT_PATH, build_report(out_rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
