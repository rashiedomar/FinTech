#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
GUIDE_PATH = ROOT_DIR / "data" / "annotations" / "ch4_fincpa" / "layer1_label_guide.json"
INPUT_CSV_PATH = ROOT_DIR / "data" / "annotations" / "ch4_fincpa" / "law_fincpa_main_ch4_layer1_annotations.csv"
OUTPUT_JSONL_PATH = ROOT_DIR / "data" / "annotations" / "ch4_fincpa" / "law_fincpa_main_ch4_layer1_annotations.reviewed.jsonl"
REPORT_JSON_PATH = ROOT_DIR / "data" / "annotations" / "ch4_fincpa" / "law_fincpa_main_ch4_layer1_validation_report.json"


def load_guide(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_csv_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def validate_single(value: str, allowed: set[str]) -> bool:
    return value == "" or value in allowed


def validate_multi(value: str, allowed: set[str]) -> tuple[bool, list[str]]:
    if value == "":
        return True, []
    labels = [part.strip() for part in value.split("|") if part.strip()]
    invalid = [label for label in labels if label not in allowed]
    return not invalid, invalid


def build_report(rows: list[dict], guide: dict) -> tuple[dict, list[str]]:
    errors: list[str] = []
    fields = guide["fields"]

    single_fields = {
        key: set(config["allowed_values"])
        for key, config in fields.items()
        if config["type"] == "single_label"
    }
    multi_fields = {
        key: set(config["allowed_values"])
        for key, config in fields.items()
        if config["type"] == "multi_label_pipe_delimited"
    }

    filled_counter: Counter[str] = Counter()
    manual_verified_counter: Counter[str] = Counter()
    relevant_counter: Counter[str] = Counter()
    topic_counter: Counter[str] = Counter()
    obligation_counter: Counter[str] = Counter()

    for row_index, row in enumerate(rows, start=2):
        for field_name, allowed in single_fields.items():
            value = (row.get(field_name) or "").strip()
            row[field_name] = value
            if not validate_single(value, allowed):
                errors.append(
                    f"row {row_index}: invalid value '{value}' for {field_name}; "
                    f"allowed={sorted(allowed)}"
                )
            if value:
                filled_counter[field_name] += 1

        for field_name, allowed in multi_fields.items():
            value = (row.get(field_name) or "").strip()
            row[field_name] = value
            valid, invalid = validate_multi(value, allowed)
            if not valid:
                errors.append(
                    f"row {row_index}: invalid values {invalid} for {field_name}; "
                    f"allowed={sorted(allowed)}"
                )
            if value:
                filled_counter[field_name] += 1

        note = (row.get("reviewer_note") or "").strip()
        row["reviewer_note"] = note
        if note:
            filled_counter["reviewer_note"] += 1

        manual_verified_counter[row.get("manual_verified", "")] += 1
        relevant_counter[row.get("is_relevant_to_theme2", "")] += 1
        topic_counter[row.get("topic_family", "")] += 1
        obligation_counter[row.get("obligation_mode", "")] += 1

    total_rows = len(rows)
    report = {
        "source_csv": str(INPUT_CSV_PATH.relative_to(ROOT_DIR)),
        "output_jsonl": str(OUTPUT_JSONL_PATH.relative_to(ROOT_DIR)),
        "total_rows": total_rows,
        "validation_error_count": len(errors),
        "completeness": {
            field_name: {
                "filled_rows": filled_counter.get(field_name, 0),
                "fill_rate": round(filled_counter.get(field_name, 0) / total_rows, 4) if total_rows else 0.0,
            }
            for field_name in fields.keys()
        },
        "manual_verified_distribution": dict(manual_verified_counter),
        "relevance_distribution": dict(relevant_counter),
        "topic_family_distribution": dict(topic_counter),
        "obligation_mode_distribution": dict(obligation_counter),
        "errors": errors,
    }
    return report, errors


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_report(path: Path, report: dict) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def main() -> int:
    guide = load_guide(GUIDE_PATH)
    rows = load_csv_rows(INPUT_CSV_PATH)
    report, errors = build_report(rows, guide)
    write_jsonl(OUTPUT_JSONL_PATH, rows)
    write_report(REPORT_JSON_PATH, report)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
