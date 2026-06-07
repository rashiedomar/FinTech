#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT_DIR / "data" / "parsed" / "ch4_fincpa" / "law_fincpa_main_ch4_clause_records.jsonl"
OUTPUT_DIR = ROOT_DIR / "data" / "annotations" / "ch4_fincpa"
CSV_PATH = OUTPUT_DIR / "law_fincpa_main_ch4_layer1_annotations.csv"
JSONL_PATH = OUTPUT_DIR / "law_fincpa_main_ch4_layer1_annotations.blank.jsonl"


CSV_FIELDS = [
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


def load_records(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def build_annotation_row(record: dict) -> dict:
    return {
        "record_id": record["record_id"],
        "article_id": record["article_id"],
        "paragraph_id": record["paragraph_id"] or "",
        "article_title": record["article_title"],
        "section_id": record["section_id"] or "",
        "section_title": record["section_title"] or "",
        "page_start": record["page_start"],
        "normalized_text": record["normalized_text"],
        "is_relevant_to_theme2": "",
        "topic_family": "",
        "product_scope": "",
        "channel_scope": "",
        "obligation_mode": "",
        "needs_decomposition": "",
        "manual_verified": "no",
        "reviewer_note": "",
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    records = load_records(INPUT_PATH)
    rows = [build_annotation_row(record) for record in records]
    write_csv(CSV_PATH, rows)
    write_jsonl(JSONL_PATH, rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
