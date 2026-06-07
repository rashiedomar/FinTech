#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
INPUT_CSV_PATH = ROOT_DIR / "data" / "annotations" / "ch4_fincpa" / "law_fincpa_main_ch4_layer3_rule_candidates.gemini.csv"
OUTPUT_CSV_PATH = ROOT_DIR / "data" / "annotations" / "ch4_fincpa" / "law_fincpa_main_ch4_layer3_review_priority.csv"
REPORT_JSON_PATH = ROOT_DIR / "data" / "annotations" / "ch4_fincpa" / "law_fincpa_main_ch4_layer3_review_priority_report.json"


OUTPUT_FIELDS = [
    "review_priority",
    "priority_reason",
    "source_obligation_id",
    "parent_record_id",
    "article_id",
    "paragraph_id",
    "article_title",
    "rule_candidate_id",
    "rule_candidate_summary",
    "rule_family",
    "logic_type",
    "detection_target",
    "sir_link_type",
    "sir_candidate_fields",
    "evidence_source",
    "ready_for_v1",
    "gemini_confidence",
    "reviewer_note",
]


def load_csv_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def score_row(row: dict) -> tuple[str, list[str]]:
    reasons: list[str] = []
    high_articles = {"제17조", "제18조", "제19조", "제20조", "제21조", "제22조", "제23조", "제28조"}

    if row["article_id"] in high_articles:
        reasons.append("high_priority_article")
    if row["ready_for_v1"] != "yes":
        reasons.append("not_ready_for_v1")
    if row["logic_type"] in {"delegated_detail", "principle_guardrail"}:
        reasons.append("abstract_logic")
    if row["sir_link_type"] in {"delegated_external_detail", "principle_only"}:
        reasons.append("weak_sir_link")
    if row["detection_target"] == "mixed":
        reasons.append("mixed_detection")

    if len(reasons) >= 3:
        return "high", reasons
    if len(reasons) >= 2:
        return "medium", reasons
    return "low", reasons


def main() -> int:
    rows = load_csv_rows(INPUT_CSV_PATH)
    out_rows: list[dict] = []
    for row in rows:
        priority, reasons = score_row(row)
        out_rows.append(
            {
                "review_priority": priority,
                "priority_reason": "|".join(reasons),
                "source_obligation_id": row["source_obligation_id"],
                "parent_record_id": row["parent_record_id"],
                "article_id": row["article_id"],
                "paragraph_id": row["paragraph_id"],
                "article_title": row["article_title"],
                "rule_candidate_id": row["rule_candidate_id"],
                "rule_candidate_summary": row["rule_candidate_summary"],
                "rule_family": row["rule_family"],
                "logic_type": row["logic_type"],
                "detection_target": row["detection_target"],
                "sir_link_type": row["sir_link_type"],
                "sir_candidate_fields": row["sir_candidate_fields"],
                "evidence_source": row["evidence_source"],
                "ready_for_v1": row["ready_for_v1"],
                "gemini_confidence": row["gemini_confidence"],
                "reviewer_note": row["reviewer_note"],
            }
        )

    rank = {"high": 0, "medium": 1, "low": 2}
    out_rows.sort(key=lambda row: (rank[row["review_priority"]], row["parent_record_id"], row["rule_candidate_id"]))

    with OUTPUT_CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(out_rows)

    report = {
        "source_csv": str(INPUT_CSV_PATH.relative_to(ROOT_DIR)),
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
