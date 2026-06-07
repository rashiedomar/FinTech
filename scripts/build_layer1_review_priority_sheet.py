#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DETERMINISTIC_PATH = ROOT_DIR / "data" / "annotations" / "ch4_fincpa" / "law_fincpa_main_ch4_layer1_annotations.prefilled.csv"
GEMINI_PATH = ROOT_DIR / "data" / "annotations" / "ch4_fincpa" / "law_fincpa_main_ch4_layer1_annotations.gemini.csv"
OUTPUT_CSV_PATH = ROOT_DIR / "data" / "annotations" / "ch4_fincpa" / "law_fincpa_main_ch4_layer1_review_priority.csv"
REPORT_PATH = ROOT_DIR / "data" / "annotations" / "ch4_fincpa" / "law_fincpa_main_ch4_layer1_review_priority_report.json"


COMPARE_FIELDS = [
    "is_relevant_to_theme2",
    "topic_family",
    "product_scope",
    "channel_scope",
    "obligation_mode",
    "needs_decomposition",
]

OUTPUT_FIELDS = [
    "record_id",
    "article_id",
    "paragraph_id",
    "article_title",
    "section_id",
    "section_title",
    "page_start",
    "normalized_text",
    "priority_reason",
    "deterministic_is_relevant_to_theme2",
    "gemini_is_relevant_to_theme2",
    "deterministic_topic_family",
    "gemini_topic_family",
    "deterministic_product_scope",
    "gemini_product_scope",
    "deterministic_channel_scope",
    "gemini_channel_scope",
    "deterministic_obligation_mode",
    "gemini_obligation_mode",
    "deterministic_needs_decomposition",
    "gemini_needs_decomposition",
    "gemini_confidence",
    "deterministic_note",
    "gemini_note",
    "gemini_reasoning_summary",
]


def load_csv(path: Path) -> dict[str, dict]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return {row["record_id"]: row for row in csv.DictReader(handle)}


def build_priority_rows(deterministic: dict[str, dict], gemini: dict[str, dict]) -> list[dict]:
    rows: list[dict] = []
    for record_id, drow in deterministic.items():
        grow = gemini.get(record_id)
        if not grow:
            continue

        mismatches = [field for field in COMPARE_FIELDS if (drow.get(field) or "") != (grow.get(field) or "")]
        if not mismatches:
            continue

        rows.append(
            {
                "record_id": record_id,
                "article_id": drow["article_id"],
                "paragraph_id": drow["paragraph_id"],
                "article_title": drow["article_title"],
                "section_id": drow["section_id"],
                "section_title": drow["section_title"],
                "page_start": drow["page_start"],
                "normalized_text": drow["normalized_text"],
                "priority_reason": "|".join(mismatches),
                "deterministic_is_relevant_to_theme2": drow["is_relevant_to_theme2"],
                "gemini_is_relevant_to_theme2": grow["is_relevant_to_theme2"],
                "deterministic_topic_family": drow["topic_family"],
                "gemini_topic_family": grow["topic_family"],
                "deterministic_product_scope": drow["product_scope"],
                "gemini_product_scope": grow["product_scope"],
                "deterministic_channel_scope": drow["channel_scope"],
                "gemini_channel_scope": grow["channel_scope"],
                "deterministic_obligation_mode": drow["obligation_mode"],
                "gemini_obligation_mode": grow["obligation_mode"],
                "deterministic_needs_decomposition": drow["needs_decomposition"],
                "gemini_needs_decomposition": grow["needs_decomposition"],
                "gemini_confidence": grow["gemini_confidence"],
                "deterministic_note": drow["reviewer_note"],
                "gemini_note": grow["reviewer_note"],
                "gemini_reasoning_summary": grow["gemini_reasoning_summary"],
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_report(path: Path, rows: list[dict]) -> None:
    report = {
        "deterministic_source": str(DETERMINISTIC_PATH.relative_to(ROOT_DIR)),
        "gemini_source": str(GEMINI_PATH.relative_to(ROOT_DIR)),
        "output_csv": str(OUTPUT_CSV_PATH.relative_to(ROOT_DIR)),
        "priority_row_count": len(rows),
    }
    with path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def main() -> int:
    deterministic = load_csv(DETERMINISTIC_PATH)
    gemini = load_csv(GEMINI_PATH)
    rows = build_priority_rows(deterministic, gemini)
    write_csv(OUTPUT_CSV_PATH, rows)
    write_report(REPORT_PATH, rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
