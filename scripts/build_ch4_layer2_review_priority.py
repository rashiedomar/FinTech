#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
INPUT_CSV_PATH = ROOT_DIR / "data" / "annotations" / "ch4_fincpa" / "law_fincpa_main_ch4_layer2_obligations.gemini.csv"
PARENT_SUMMARY_PATH = ROOT_DIR / "data" / "annotations" / "ch4_fincpa" / "law_fincpa_main_ch4_layer2_parent_summary.csv"
OUTPUT_CSV_PATH = ROOT_DIR / "data" / "annotations" / "ch4_fincpa" / "law_fincpa_main_ch4_layer2_review_priority.csv"
REPORT_JSON_PATH = ROOT_DIR / "data" / "annotations" / "ch4_fincpa" / "law_fincpa_main_ch4_layer2_review_priority_report.json"


OUTPUT_FIELDS = [
    "review_priority",
    "priority_reason",
    "parent_record_id",
    "obligation_id",
    "article_id",
    "paragraph_id",
    "article_title",
    "parent_topic_family",
    "parent_decomposition_strategy",
    "obligation_label",
    "obligation_summary",
    "source_span_text",
    "product_scope",
    "channel_scope",
    "obligation_mode",
    "trigger_type",
    "operationality",
    "consumer_visibility",
    "gemini_confidence",
    "reviewer_note",
]


def load_csv_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def build_parent_counts(rows: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["parent_record_id"]] = int(row["obligation_count"])
    return counts


def score_row(row: dict, parent_obligation_count: int) -> tuple[str, list[str]]:
    reasons: list[str] = []
    high_articles = {"제17조", "제18조", "제19조", "제20조", "제21조", "제22조", "제23조", "제28조"}

    if row["article_id"] in high_articles:
        reasons.append("high_priority_article")
    if parent_obligation_count > 1:
        reasons.append("split_parent")
    if row["operationality"] != "direct_checkable":
        reasons.append("not_direct_checkable")
    if row["obligation_mode"] in {"required_content", "prohibited_action", "workflow_control"}:
        reasons.append("core_obligation_mode")

    if len(reasons) >= 3:
        return "high", reasons
    if len(reasons) >= 2:
        return "medium", reasons
    return "low", reasons


def main() -> int:
    rows = load_csv_rows(INPUT_CSV_PATH)
    parent_summary = load_csv_rows(PARENT_SUMMARY_PATH)
    parent_counts = build_parent_counts(parent_summary)

    out_rows: list[dict] = []
    for row in rows:
        priority, reasons = score_row(row, parent_counts.get(row["parent_record_id"], 1))
        out_rows.append(
            {
                "review_priority": priority,
                "priority_reason": "|".join(reasons),
                "parent_record_id": row["parent_record_id"],
                "obligation_id": row["obligation_id"],
                "article_id": row["article_id"],
                "paragraph_id": row["paragraph_id"],
                "article_title": row["article_title"],
                "parent_topic_family": row["parent_topic_family"],
                "parent_decomposition_strategy": row["parent_decomposition_strategy"],
                "obligation_label": row["obligation_label"],
                "obligation_summary": row["obligation_summary"],
                "source_span_text": row["source_span_text"],
                "product_scope": row["product_scope"],
                "channel_scope": row["channel_scope"],
                "obligation_mode": row["obligation_mode"],
                "trigger_type": row["trigger_type"],
                "operationality": row["operationality"],
                "consumer_visibility": row["consumer_visibility"],
                "gemini_confidence": row["gemini_confidence"],
                "reviewer_note": row["reviewer_note"],
            }
        )

    priority_rank = {"high": 0, "medium": 1, "low": 2}
    out_rows.sort(key=lambda row: (priority_rank[row["review_priority"]], row["parent_record_id"], row["obligation_id"]))

    with OUTPUT_CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(out_rows)

    report = {
        "source_csv": str(INPUT_CSV_PATH.relative_to(ROOT_DIR)),
        "parent_summary_csv": str(PARENT_SUMMARY_PATH.relative_to(ROOT_DIR)),
        "output_csv": str(OUTPUT_CSV_PATH.relative_to(ROOT_DIR)),
        "total_rows": len(out_rows),
        "high_priority_rows": sum(1 for row in out_rows if row["review_priority"] == "high"),
        "medium_priority_rows": sum(1 for row in out_rows if row["review_priority"] == "medium"),
        "low_priority_rows": sum(1 for row in out_rows if row["review_priority"] == "low"),
    }
    with REPORT_JSON_PATH.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
