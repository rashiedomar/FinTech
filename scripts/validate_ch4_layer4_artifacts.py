#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
LAYER3_PATH = ROOT_DIR / "data" / "annotations" / "ch4_fincpa" / "law_fincpa_main_ch4_layer3_rule_candidates.gemini.jsonl"
RULE_PACK_PATH = ROOT_DIR / "data" / "finalized" / "ch4_fincpa" / "law_fincpa_main_ch4_layer4_mvp_rule_pack.jsonl"
SIR_SCHEMA_PATH = ROOT_DIR / "data" / "finalized" / "ch4_fincpa" / "law_fincpa_main_ch4_layer4_mvp_sir_schema.json"
REPORT_PATH = ROOT_DIR / "data" / "finalized" / "ch4_fincpa" / "law_fincpa_main_ch4_layer4_compile_report.json"
VALIDATION_REPORT_PATH = ROOT_DIR / "data" / "finalized" / "ch4_fincpa" / "law_fincpa_main_ch4_layer4_validation_report.json"


def load_jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def main() -> None:
    layer3_rows = load_jsonl(LAYER3_PATH)
    rule_rows = load_jsonl(RULE_PACK_PATH)
    sir_schema = json.loads(SIR_SCHEMA_PATH.read_text(encoding="utf-8"))
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    ready_rule_ids = {row["rule_candidate_id"] for row in layer3_rows if row["ready_for_v1"] == "yes"}
    rule_pack_ids = {row["rule_id"] for row in rule_rows}
    schema_field_names = {field["field_name"] for field in sir_schema["fields"]}

    errors: list[str] = []

    missing_rules = sorted(ready_rule_ids - rule_pack_ids)
    extra_rules = sorted(rule_pack_ids - ready_rule_ids)
    if missing_rules:
        errors.append(f"Missing ready_for_v1 rules in rule pack: {missing_rules[:10]}")
    if extra_rules:
        errors.append(f"Unexpected rules in rule pack: {extra_rules[:10]}")

    for row in rule_rows:
        if row["compile_status"] != "included_in_layer4_mvp_v0_1":
            errors.append(f"Unexpected compile status for {row['rule_id']}: {row['compile_status']}")
        for field_name in row["sir_candidate_fields"]:
            if field_name not in schema_field_names:
                errors.append(f"Rule {row['rule_id']} references unknown field {field_name}")

    if sir_schema["field_count"] != len(sir_schema["fields"]):
        errors.append("sir_schema field_count does not match actual field list length")

    if report["included_mvp_rule_count"] != len(rule_rows):
        errors.append("Compile report included_mvp_rule_count mismatch")
    if report["mvp_sir_field_count"] != len(sir_schema["fields"]):
        errors.append("Compile report mvp_sir_field_count mismatch")

    validation_report = {
        "version": "0.1.0",
        "layer": "layer4_final_mvp_compilation",
        "total_layer3_candidates": len(layer3_rows),
        "ready_for_v1_candidates": len(ready_rule_ids),
        "rule_pack_rules": len(rule_rows),
        "sir_schema_fields": len(sir_schema["fields"]),
        "errors": errors,
        "passed": not errors,
    }
    VALIDATION_REPORT_PATH.write_text(json.dumps(validation_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(validation_report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
