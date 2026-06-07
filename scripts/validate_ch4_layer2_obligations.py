#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
GUIDE_PATH = ROOT_DIR / "data" / "annotations" / "ch4_fincpa" / "layer2_label_guide.json"
INPUT_CSV_PATH = ROOT_DIR / "data" / "annotations" / "ch4_fincpa" / "law_fincpa_main_ch4_layer2_obligations.gemini.csv"
REPORT_JSON_PATH = ROOT_DIR / "data" / "annotations" / "ch4_fincpa" / "law_fincpa_main_ch4_layer2_validation_report.json"


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_csv_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def validate_single(value: str, allowed: set[str]) -> bool:
    return value in allowed


def validate_multi(value: str, allowed: set[str]) -> tuple[bool, list[str]]:
    labels = [part.strip() for part in value.split("|") if part.strip()]
    invalid = [label for label in labels if label not in allowed]
    return not invalid, invalid


def main() -> int:
    guide = load_json(GUIDE_PATH)
    rows = load_csv_rows(INPUT_CSV_PATH)
    fields = guide["fields"]
    errors: list[str] = []

    single_fields = {
        key: set(config["allowed_values"])
        for key, config in fields.items()
        if config["type"] == "single_label"
    }
    multi_fields = {
        key: set(config["allowed_values"])
        for key, config in fields.items()
        if config["type"] == "single_or_pipe_delimited_multi_label"
    }

    for row_index, row in enumerate(rows, start=2):
        for field_name, allowed in single_fields.items():
            value = (row.get(field_name) or "").strip()
            if not validate_single(value, allowed):
                errors.append(
                    f"row {row_index}: invalid value '{value}' for {field_name}; allowed={sorted(allowed)}"
                )
        for field_name, allowed in multi_fields.items():
            value = (row.get(field_name) or "").strip()
            valid, invalid = validate_multi(value, allowed)
            if not valid:
                errors.append(
                    f"row {row_index}: invalid values {invalid} for {field_name}; allowed={sorted(allowed)}"
                )

    report = {
        "source_csv": str(INPUT_CSV_PATH.relative_to(ROOT_DIR)),
        "total_rows": len(rows),
        "validation_error_count": len(errors),
        "parent_record_count": len({row['parent_record_id'] for row in rows}),
        "obligation_mode_distribution": dict(Counter(row["obligation_mode"] for row in rows)),
        "trigger_type_distribution": dict(Counter(row["trigger_type"] for row in rows)),
        "operationality_distribution": dict(Counter(row["operationality"] for row in rows)),
        "consumer_visibility_distribution": dict(Counter(row["consumer_visibility"] for row in rows)),
        "errors": errors,
    }

    with REPORT_JSON_PATH.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

