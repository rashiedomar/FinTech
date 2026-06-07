#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SOURCE_PDF_PATH = ROOT_DIR / "data" / "raw" / "official" / "law_fincpa_main_2026-01-02.pdf"
LAYER2_PATH = ROOT_DIR / "data" / "annotations" / "ch4_fincpa" / "law_fincpa_main_ch4_layer2_obligations.gemini.jsonl"
LAYER3_PATH = ROOT_DIR / "data" / "annotations" / "ch4_fincpa" / "law_fincpa_main_ch4_layer3_rule_candidates.gemini.jsonl"
OUTPUT_DIR = ROOT_DIR / "data" / "finalized" / "ch4_fincpa"
RULE_PACK_JSONL_PATH = OUTPUT_DIR / "law_fincpa_main_ch4_layer4_mvp_rule_pack.jsonl"
RULE_PACK_CSV_PATH = OUTPUT_DIR / "law_fincpa_main_ch4_layer4_mvp_rule_pack.csv"
SIR_SCHEMA_JSON_PATH = OUTPUT_DIR / "law_fincpa_main_ch4_layer4_mvp_sir_schema.json"
FIELD_SUMMARY_CSV_PATH = OUTPUT_DIR / "law_fincpa_main_ch4_layer4_mvp_sir_field_summary.csv"
EXCLUDED_CSV_PATH = OUTPUT_DIR / "law_fincpa_main_ch4_layer4_excluded_candidates.csv"
REPORT_JSON_PATH = OUTPUT_DIR / "law_fincpa_main_ch4_layer4_compile_report.json"

STATUS_MODEL = {
    "status_values": [
        "present",
        "not_evidenced",
        "not_applicable",
        "uncertain",
    ],
    "notes": (
        "Layer 4 freezes only the first MVP field inventory and first MVP rule pack. "
        "Future runtime objects should track both the field value and an evidence status "
        "instead of forcing every field into a binary yes/no state."
    ),
}

EVALUATION_HINTS = {
    "required_presence": "Flag when the mapped field is not evidenced where the obligation requires visible or document-backed presence.",
    "prohibited_presence": "Flag when the mapped signal or misleading condition is evidenced in visible content or workflow evidence.",
    "required_process": "Flag when the required workflow step or control checkpoint cannot be evidenced in process metadata.",
    "required_record": "Flag when the required log, archive entry, or registry record is missing.",
    "required_response": "Flag when a triggering request or event exists but the required response evidence is missing.",
    "delegated_detail": "Carry this rule only after decree-level details are added.",
    "principle_guardrail": "Use as a policy guardrail or reviewer principle, not as a deterministic pass/fail rule by itself.",
}

FIELD_METADATA = {
    "consumer_type": {
        "value_type": "enum",
        "description": "Consumer classification needed for suitability or adequacy handling, such as general or professional consumer status.",
    },
    "consumer_profile": {
        "value_type": "profile_bundle",
        "description": "Collected consumer profile facts used to judge suitability, adequacy, or tailored explanation duties.",
    },
    "suitability_check": {
        "value_type": "enum",
        "description": "Structured suitability assessment result or completion state derived from the consumer profile and product context.",
    },
    "adequacy_check": {
        "value_type": "enum",
        "description": "Structured adequacy assessment result or completion state for products or consumers that require adequacy review.",
    },
    "explanation_material": {
        "value_type": "document_or_text_bundle",
        "description": "Explanation text, script, or material bundle used to communicate key product terms and risks to the consumer.",
    },
    "explanation_confirmation": {
        "value_type": "enum",
        "description": "Evidence that the required explanation was confirmed, acknowledged, or otherwise completed.",
    },
    "contract_document_delivery": {
        "value_type": "enum",
        "description": "Evidence that required contract or pre-contract documents were delivered or made available.",
    },
    "seller_identity": {
        "value_type": "text",
        "description": "Visible identification of the financial seller or responsible institution in customer-facing content.",
    },
    "product_identity": {
        "value_type": "text",
        "description": "Visible identification of the product itself in customer-facing content or documents.",
    },
    "product_core_terms": {
        "value_type": "text_bundle",
        "description": "Core product terms that must be disclosed so the consumer can understand what is being offered.",
    },
    "insurance_warning": {
        "value_type": "text_or_flag",
        "description": "Required insurance-related warning, replacement notice, or caution text that must be surfaced to the consumer.",
    },
    "investment_warning": {
        "value_type": "text_or_flag",
        "description": "Required investment-related risk or caution disclosure that must be surfaced to the consumer.",
    },
    "deposit_disclaimer": {
        "value_type": "text_or_flag",
        "description": "Required deposit or savings disclaimer, including guarantee or protection limitations where applicable.",
    },
    "loan_conditions": {
        "value_type": "text_bundle",
        "description": "Loan conditions that must be disclosed to explain the structure of the loan offer.",
    },
    "loan_rate_basis": {
        "value_type": "text",
        "description": "Interest rate range, rate basis, or rate calculation method disclosed for a loan product.",
    },
    "loan_interest_timing": {
        "value_type": "text",
        "description": "Information showing when interest is charged or how the timing of interest accrual is communicated.",
    },
    "loan_costs": {
        "value_type": "text",
        "description": "Loan-related cost, fee, or penalty disclosures that must be visible to the consumer.",
    },
    "solicitation_purpose": {
        "value_type": "text",
        "description": "Purpose statement or context showing why a solicitation contact or interaction is being made.",
    },
    "representative_identity": {
        "value_type": "text",
        "description": "Identity of the representative, staff member, or solicitor involved in the consumer interaction.",
    },
    "staff_registry": {
        "value_type": "record_ref",
        "description": "Registry or record set tracking staff, intermediaries, or other regulated personnel information.",
    },
    "internal_control_standard": {
        "value_type": "document_ref",
        "description": "Internal control standard or formal compliance procedure document required by the organization.",
    },
    "activity_record": {
        "value_type": "record_ref",
        "description": "Activity log or archived record showing that a regulated action, explanation, or solicitation occurred.",
    },
    "record_integrity_control": {
        "value_type": "enum",
        "description": "Evidence that records are preserved with integrity, retention, and access safeguards.",
    },
    "access_request": {
        "value_type": "record_ref",
        "description": "Record of a consumer request to access, inspect, or receive regulated information or records.",
    },
    "access_response": {
        "value_type": "record_ref",
        "description": "Record of the organization's response to a regulated consumer request or access event.",
    },
    "advisory_independence": {
        "value_type": "enum",
        "description": "Evidence that advisory conduct preserves required independence, neutrality, or conflict controls.",
    },
    "intermediary_status": {
        "value_type": "enum",
        "description": "Status or role of an intermediary, agent, or broker relevant to what conduct or disclosure rules apply.",
    },
    "prohibited_claim_signal": {
        "value_type": "signal_list",
        "description": "Detected prohibited claim, misleading claim, or other disallowed promotional signal in visible content.",
    },
    "fairness_guardrail": {
        "value_type": "enum",
        "description": "Reviewer-facing fairness or consumer-protection guardrail used when a rule is still partially principle-driven.",
    },
}

RULE_PACK_FIELDS = [
    "rule_id",
    "source_rule_candidate_id",
    "source_obligation_id",
    "parent_record_id",
    "article_id",
    "paragraph_id",
    "article_title",
    "section_id",
    "section_title",
    "product_scope",
    "channel_scope",
    "rule_family",
    "logic_type",
    "detection_target",
    "sir_link_type",
    "sir_candidate_fields",
    "evidence_source",
    "evaluation_hint",
    "rule_candidate_summary",
    "obligation_summary",
    "source_span_text",
    "compile_status",
    "manual_verified",
    "reviewer_note",
]

FIELD_SUMMARY_FIELDS = [
    "field_name",
    "field_group",
    "value_type",
    "mvp_priority",
    "source_rule_count",
    "source_obligation_count",
    "description",
    "dominant_sir_link_type",
    "product_scopes",
    "channel_scopes",
    "rule_families",
    "logic_types",
    "detection_targets",
    "evidence_sources",
    "article_refs",
    "source_rule_ids",
]

EXCLUDED_FIELDS = [
    "source_obligation_id",
    "parent_record_id",
    "article_id",
    "paragraph_id",
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


def load_jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def split_pipe_labels(value: str) -> list[str]:
    return [item.strip() for item in value.split("|") if item.strip()]


def unique_sorted(values: set[str]) -> list[str]:
    return sorted(value for value in values if value)


def dominant_label(counter: Counter) -> str:
    if not counter:
        return ""
    return sorted(counter.items(), key=lambda item: (-item[1], item[0]))[0][0]


def compute_priority(source_rule_count: int) -> str:
    if source_rule_count >= 8:
        return "high"
    if source_rule_count >= 4:
        return "medium"
    return "low"


def build_rule_row(layer3_row: dict, layer2_row: dict) -> dict:
    sir_fields = split_pipe_labels(layer3_row["sir_candidate_fields"])
    return {
        "rule_id": layer3_row["rule_candidate_id"],
        "source_rule_candidate_id": layer3_row["rule_candidate_id"],
        "source_obligation_id": layer3_row["source_obligation_id"],
        "parent_record_id": layer3_row["parent_record_id"],
        "article_id": layer3_row["article_id"],
        "paragraph_id": layer3_row["paragraph_id"],
        "article_title": layer3_row["article_title"],
        "section_id": layer3_row["section_id"],
        "section_title": layer3_row["section_title"],
        "product_scope": layer2_row["product_scope"],
        "channel_scope": layer2_row["channel_scope"],
        "rule_family": layer3_row["rule_family"],
        "logic_type": layer3_row["logic_type"],
        "detection_target": layer3_row["detection_target"],
        "sir_link_type": layer3_row["sir_link_type"],
        "sir_candidate_fields": sir_fields,
        "evidence_source": layer3_row["evidence_source"],
        "evaluation_hint": EVALUATION_HINTS[layer3_row["logic_type"]],
        "rule_candidate_summary": layer3_row["rule_candidate_summary"],
        "obligation_summary": layer3_row["obligation_summary"],
        "source_span_text": layer3_row["source_span_text"],
        "compile_status": "included_in_layer4_mvp_v0_1",
        "manual_verified": "no",
        "reviewer_note": layer3_row["reviewer_note"],
    }


def build_field_rows(rule_rows: list[dict]) -> tuple[list[dict], dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rule_rows:
        for field_name in row["sir_candidate_fields"]:
            grouped[field_name].append(row)

    missing = [field for field in grouped if field not in FIELD_METADATA]
    if missing:
        raise KeyError(f"Missing field metadata for: {', '.join(sorted(missing))}")

    field_rows: list[dict] = []
    schema_fields: list[dict] = []
    priority_counts: Counter = Counter()
    field_group_counts: Counter = Counter()

    for field_name in sorted(grouped):
        rows = grouped[field_name]
        detection_counter = Counter(row["detection_target"] for row in rows)
        sir_link_counter = Counter(row["sir_link_type"] for row in rows)
        field_group = dominant_label(detection_counter)
        dominant_sir_link_type = dominant_label(sir_link_counter)
        product_scopes = unique_sorted({row["product_scope"] for row in rows})
        channel_scopes = unique_sorted({row["channel_scope"] for row in rows})
        rule_families = unique_sorted({row["rule_family"] for row in rows})
        logic_types = unique_sorted({row["logic_type"] for row in rows})
        detection_targets = unique_sorted({row["detection_target"] for row in rows})
        evidence_sources = unique_sorted({row["evidence_source"] for row in rows})
        article_refs = unique_sorted(
            {
                f"{row['article_id']}{row['paragraph_id']}" if row["paragraph_id"] else row["article_id"]
                for row in rows
            }
        )
        source_rule_ids = unique_sorted({row["rule_id"] for row in rows})
        source_obligation_ids = unique_sorted({row["source_obligation_id"] for row in rows})
        source_rule_count = len(source_rule_ids)
        source_obligation_count = len(source_obligation_ids)
        mvp_priority = compute_priority(source_rule_count)
        priority_counts[mvp_priority] += 1
        field_group_counts[field_group] += 1

        meta = FIELD_METADATA[field_name]
        field_row = {
            "field_name": field_name,
            "field_group": field_group,
            "value_type": meta["value_type"],
            "mvp_priority": mvp_priority,
            "source_rule_count": source_rule_count,
            "source_obligation_count": source_obligation_count,
            "description": meta["description"],
            "dominant_sir_link_type": dominant_sir_link_type,
            "product_scopes": "|".join(product_scopes),
            "channel_scopes": "|".join(channel_scopes),
            "rule_families": "|".join(rule_families),
            "logic_types": "|".join(logic_types),
            "detection_targets": "|".join(detection_targets),
            "evidence_sources": "|".join(evidence_sources),
            "article_refs": "|".join(article_refs),
            "source_rule_ids": "|".join(source_rule_ids),
        }
        field_rows.append(field_row)

        schema_fields.append(
            {
                "field_name": field_name,
                "field_group": field_group,
                "value_type": meta["value_type"],
                "description": meta["description"],
                "dominant_sir_link_type": dominant_sir_link_type,
                "status_values": STATUS_MODEL["status_values"],
                "mvp_priority": mvp_priority,
                "source_rule_count": source_rule_count,
                "source_obligation_count": source_obligation_count,
                "product_scopes": product_scopes,
                "channel_scopes": channel_scopes,
                "rule_families": rule_families,
                "logic_types": logic_types,
                "detection_targets": detection_targets,
                "evidence_sources": evidence_sources,
                "article_refs": article_refs,
                "source_rule_ids": source_rule_ids,
                "source_obligation_ids": source_obligation_ids,
            }
        )

    schema_fields.sort(key=lambda item: (item["field_group"], item["mvp_priority"], item["field_name"]))
    field_rows.sort(key=lambda item: (item["field_group"], item["mvp_priority"], item["field_name"]))
    return field_rows, {
        "schema_fields": schema_fields,
        "priority_counts": dict(priority_counts),
        "field_group_counts": dict(field_group_counts),
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    layer2_rows = load_jsonl(LAYER2_PATH)
    layer3_rows = load_jsonl(LAYER3_PATH)
    layer2_by_obligation = {row["obligation_id"]: row for row in layer2_rows}

    ready_rows = [row for row in layer3_rows if row["ready_for_v1"] == "yes"]
    excluded_rows = [row for row in layer3_rows if row["ready_for_v1"] != "yes"]

    rule_rows = []
    for layer3_row in ready_rows:
        layer2_row = layer2_by_obligation[layer3_row["source_obligation_id"]]
        rule_rows.append(build_rule_row(layer3_row, layer2_row))

    rule_rows.sort(key=lambda row: (row["article_id"], row["paragraph_id"], row["rule_id"]))

    field_rows, field_build_meta = build_field_rows(rule_rows)
    schema_fields = field_build_meta["schema_fields"]

    rule_pack_jsonl_rows = rule_rows
    rule_pack_csv_rows = []
    for row in rule_rows:
        csv_row = dict(row)
        csv_row["sir_candidate_fields"] = "|".join(row["sir_candidate_fields"])
        rule_pack_csv_rows.append(csv_row)

    write_jsonl(RULE_PACK_JSONL_PATH, rule_pack_jsonl_rows)
    write_csv(RULE_PACK_CSV_PATH, RULE_PACK_FIELDS, rule_pack_csv_rows)
    write_csv(FIELD_SUMMARY_CSV_PATH, FIELD_SUMMARY_FIELDS, field_rows)

    excluded_csv_rows = []
    for row in excluded_rows:
        excluded_csv_rows.append({field: row[field] for field in EXCLUDED_FIELDS})
    write_csv(EXCLUDED_CSV_PATH, EXCLUDED_FIELDS, excluded_csv_rows)

    sir_schema = {
        "version": "0.1.0",
        "artifact_type": "layer4_mvp_sir_schema",
        "source_pdf": str(SOURCE_PDF_PATH.relative_to(ROOT_DIR)),
        "source_layer2_dataset": str(LAYER2_PATH.relative_to(ROOT_DIR)),
        "source_layer3_dataset": str(LAYER3_PATH.relative_to(ROOT_DIR)),
        "selection_rule": "include only layer3 rows where ready_for_v1 == yes",
        "status_model": STATUS_MODEL,
        "field_count": len(schema_fields),
        "fields": schema_fields,
    }
    SIR_SCHEMA_JSON_PATH.write_text(json.dumps(sir_schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = {
        "version": "0.1.0",
        "layer": "layer4_final_mvp_compilation",
        "source_pdf": str(SOURCE_PDF_PATH.relative_to(ROOT_DIR)),
        "source_layer2_dataset": str(LAYER2_PATH.relative_to(ROOT_DIR)),
        "source_layer3_dataset": str(LAYER3_PATH.relative_to(ROOT_DIR)),
        "selection_rule": "ready_for_v1 == yes",
        "total_layer3_candidates": len(layer3_rows),
        "included_mvp_rule_count": len(rule_rows),
        "excluded_candidate_count": len(excluded_rows),
        "mvp_sir_field_count": len(schema_fields),
        "rule_family_counts": dict(Counter(row["rule_family"] for row in rule_rows)),
        "logic_type_counts": dict(Counter(row["logic_type"] for row in rule_rows)),
        "detection_target_counts": dict(Counter(row["detection_target"] for row in rule_rows)),
        "sir_link_type_counts": dict(Counter(row["sir_link_type"] for row in rule_rows)),
        "evidence_source_counts": dict(Counter(row["evidence_source"] for row in rule_rows)),
        "product_scope_counts": dict(Counter(row["product_scope"] for row in rule_rows)),
        "channel_scope_counts": dict(Counter(row["channel_scope"] for row in rule_rows)),
        "field_group_counts": field_build_meta["field_group_counts"],
        "field_priority_counts": field_build_meta["priority_counts"],
        "output_paths": {
            "rule_pack_jsonl": str(RULE_PACK_JSONL_PATH.relative_to(ROOT_DIR)),
            "rule_pack_csv": str(RULE_PACK_CSV_PATH.relative_to(ROOT_DIR)),
            "sir_schema_json": str(SIR_SCHEMA_JSON_PATH.relative_to(ROOT_DIR)),
            "field_summary_csv": str(FIELD_SUMMARY_CSV_PATH.relative_to(ROOT_DIR)),
            "excluded_candidates_csv": str(EXCLUDED_CSV_PATH.relative_to(ROOT_DIR)),
        },
    }
    REPORT_JSON_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
