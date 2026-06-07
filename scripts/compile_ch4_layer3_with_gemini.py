#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
API_KEY_PATH = ROOT_DIR / "gemini_api.txt"
LAYER2_CSV_PATH = ROOT_DIR / "data" / "annotations" / "ch4_fincpa" / "law_fincpa_main_ch4_layer2_obligations.gemini.csv"
LABEL_GUIDE_PATH = ROOT_DIR / "data" / "annotations" / "ch4_fincpa" / "layer3_label_guide.json"
OUTPUT_CSV_PATH = ROOT_DIR / "data" / "annotations" / "ch4_fincpa" / "law_fincpa_main_ch4_layer3_rule_candidates.gemini.csv"
OUTPUT_JSONL_PATH = ROOT_DIR / "data" / "annotations" / "ch4_fincpa" / "law_fincpa_main_ch4_layer3_rule_candidates.gemini.jsonl"
REPORT_JSON_PATH = ROOT_DIR / "data" / "annotations" / "ch4_fincpa" / "law_fincpa_main_ch4_layer3_gemini_report.json"

DEFAULT_MODEL = "gemini-3.5-flash"

OUTPUT_FIELDS = [
    "source_obligation_id",
    "parent_record_id",
    "article_id",
    "paragraph_id",
    "article_title",
    "section_id",
    "section_title",
    "page_start",
    "parent_topic_family",
    "source_obligation_mode",
    "source_trigger_type",
    "source_operationality",
    "obligation_label",
    "obligation_summary",
    "source_span_text",
    "rule_candidate_id",
    "rule_candidate_summary",
    "rule_family",
    "logic_type",
    "detection_target",
    "sir_link_type",
    "sir_candidate_fields",
    "evidence_source",
    "ready_for_v1",
    "manual_verified",
    "reviewer_note",
    "gemini_model",
    "gemini_confidence",
    "gemini_reasoning_summary"
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--sleep-seconds", type=float, default=0.1)
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    parser.add_argument("--max-retries", type=int, default=2)
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def load_csv_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_response_schema() -> dict:
    props = {
        "rule_candidate_summary": {"type": "STRING"},
        "rule_family": {"type": "STRING"},
        "logic_type": {"type": "STRING"},
        "detection_target": {"type": "STRING"},
        "sir_link_type": {"type": "STRING"},
        "sir_candidate_fields": {"type": "STRING"},
        "evidence_source": {"type": "STRING"},
        "ready_for_v1": {"type": "STRING"},
        "reviewer_note": {"type": "STRING"},
        "gemini_confidence": {"type": "STRING"},
        "gemini_reasoning_summary": {"type": "STRING"}
    }
    return {
        "type": "OBJECT",
        "properties": props,
        "required": list(props.keys())
    }


def build_system_instruction(label_guide: dict) -> str:
    return f"""You are assisting Layer 3 rule compilation for legal compliance obligations extracted from Chapter 4 of the Korean Financial Consumer Protection Act.

Goal:
- convert one Layer 2 obligation unit into one first-pass rule candidate and SIR-link candidate

Rules:
- use the obligation row as the source truth
- do not invent a new legal obligation
- propose only one rule candidate per input obligation row
- use only the allowed controlled labels below
- keep the rule_candidate_summary short and operational
- sir_candidate_fields must be pipe-delimited when multiple values apply
- if the obligation is too abstract to connect to a concrete SIR field, use sir_link_type = principle_only or delegated_external_detail
- if no current SIR field fits, include no_current_field

Allowed labels:
{json.dumps(label_guide['fields'], ensure_ascii=False, indent=2)}

Return one JSON object with:
- rule_candidate_summary
- rule_family
- logic_type
- detection_target
- sir_link_type
- sir_candidate_fields
- evidence_source
- ready_for_v1
- reviewer_note
- gemini_confidence
- gemini_reasoning_summary
"""


def build_user_prompt(row: dict) -> str:
    payload = {
        "source_obligation_id": row["obligation_id"],
        "parent_record_id": row["parent_record_id"],
        "article_id": row["article_id"],
        "article_title": row["article_title"],
        "paragraph_id": row["paragraph_id"],
        "parent_topic_family": row["parent_topic_family"],
        "source_obligation_mode": row["obligation_mode"],
        "source_trigger_type": row["trigger_type"],
        "source_operationality": row["operationality"],
        "consumer_visibility": row["consumer_visibility"],
        "obligation_label": row["obligation_label"],
        "obligation_summary": row["obligation_summary"],
        "source_span_text": row["source_span_text"],
        "reviewer_note": row["reviewer_note"],
    }
    return (
        "Compile this Layer 2 obligation unit into a Layer 3 rule candidate.\n"
        "Keep the legal meaning stable.\n"
        "Decide what type of future rule this would become, what kind of system evidence it would need, and whether it can connect to a future SIR field.\n\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )


def parse_json_text(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start : end + 1])
        raise


def call_gemini(
    *,
    api_key: str,
    model: str,
    system_instruction: str,
    user_prompt: str,
    timeout_seconds: float
) -> dict:
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body = {
        "system_instruction": {
            "parts": [{"text": system_instruction}]
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": user_prompt}]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json",
            "responseSchema": build_response_schema(),
            "maxOutputTokens": 1024,
            "thinkingConfig": {
                "thinkingBudget": 0
            }
        }
    }
    request = urllib.request.Request(
        f"{api_url}?key={api_key}",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        data = json.load(response)
    parts = data["candidates"][0]["content"]["parts"]
    text = "".join(part.get("text", "") for part in parts).strip()
    return parse_json_text(text)


def build_output_row(source_row: dict, response: dict, model: str) -> dict:
    return {
        "source_obligation_id": source_row["obligation_id"],
        "parent_record_id": source_row["parent_record_id"],
        "article_id": source_row["article_id"],
        "paragraph_id": source_row["paragraph_id"],
        "article_title": source_row["article_title"],
        "section_id": source_row["section_id"],
        "section_title": source_row["section_title"],
        "page_start": source_row["page_start"],
        "parent_topic_family": source_row["parent_topic_family"],
        "source_obligation_mode": source_row["obligation_mode"],
        "source_trigger_type": source_row["trigger_type"],
        "source_operationality": source_row["operationality"],
        "obligation_label": source_row["obligation_label"],
        "obligation_summary": source_row["obligation_summary"],
        "source_span_text": source_row["source_span_text"],
        "rule_candidate_id": f"{source_row['obligation_id']}:rule01",
        "rule_candidate_summary": response["rule_candidate_summary"],
        "rule_family": response["rule_family"],
        "logic_type": response["logic_type"],
        "detection_target": response["detection_target"],
        "sir_link_type": response["sir_link_type"],
        "sir_candidate_fields": response["sir_candidate_fields"],
        "evidence_source": response["evidence_source"],
        "ready_for_v1": response["ready_for_v1"],
        "manual_verified": "no",
        "reviewer_note": response["reviewer_note"],
        "gemini_model": model,
        "gemini_confidence": response["gemini_confidence"],
        "gemini_reasoning_summary": response["gemini_reasoning_summary"],
    }


def append_jsonl_row(path: Path, row: dict) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_existing_rows(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    rows: dict[str, dict] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            rows[row["source_obligation_id"]] = row
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_report(path: Path, report: dict) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def main() -> int:
    args = parse_args()
    api_key = API_KEY_PATH.read_text(encoding="utf-8").strip()
    input_rows = load_csv_rows(LAYER2_CSV_PATH)
    label_guide = load_json(LABEL_GUIDE_PATH)
    system_instruction = build_system_instruction(label_guide)

    if args.limit > 0:
        input_rows = input_rows[: args.limit]

    if args.resume:
        existing_rows = load_existing_rows(OUTPUT_JSONL_PATH)
    else:
        existing_rows = {}
        for path in (OUTPUT_JSONL_PATH, OUTPUT_CSV_PATH, REPORT_JSON_PATH):
            if path.exists():
                path.unlink()

    rows_by_source: dict[str, dict] = dict(existing_rows)
    errors: list[dict] = []
    started = time.time()

    for source_row in input_rows:
        source_obligation_id = source_row["obligation_id"]
        if source_obligation_id in rows_by_source:
            continue
        last_error: dict | None = None
        for attempt in range(1, args.max_retries + 2):
            try:
                response = call_gemini(
                    api_key=api_key,
                    model=args.model,
                    system_instruction=system_instruction,
                    user_prompt=build_user_prompt(source_row),
                    timeout_seconds=args.timeout_seconds,
                )
                out_row = build_output_row(source_row, response, args.model)
                rows_by_source[source_obligation_id] = out_row
                append_jsonl_row(OUTPUT_JSONL_PATH, out_row)
                last_error = None
                break
            except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, KeyError, TimeoutError) as exc:
                last_error = {
                    "source_obligation_id": source_obligation_id,
                    "attempt": attempt,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "model": args.model,
                }
                time.sleep(1.0)
        if last_error is not None:
            errors.append(last_error)
        time.sleep(args.sleep_seconds)

    ordered_rows = [rows_by_source[row["obligation_id"]] for row in input_rows if row["obligation_id"] in rows_by_source]
    write_csv(OUTPUT_CSV_PATH, ordered_rows)

    report = {
        "model": args.model,
        "source_layer2_csv": str(LAYER2_CSV_PATH.relative_to(ROOT_DIR)),
        "output_csv": str(OUTPUT_CSV_PATH.relative_to(ROOT_DIR)),
        "output_jsonl": str(OUTPUT_JSONL_PATH.relative_to(ROOT_DIR)),
        "total_input_obligations": len(input_rows),
        "successful_rule_candidates": len(ordered_rows),
        "error_count": len(errors),
        "errors": errors,
        "rule_family_distribution": dict(Counter(row["rule_family"] for row in ordered_rows)),
        "logic_type_distribution": dict(Counter(row["logic_type"] for row in ordered_rows)),
        "detection_target_distribution": dict(Counter(row["detection_target"] for row in ordered_rows)),
        "sir_link_type_distribution": dict(Counter(row["sir_link_type"] for row in ordered_rows)),
        "evidence_source_distribution": dict(Counter(row["evidence_source"] for row in ordered_rows)),
        "ready_for_v1_distribution": dict(Counter(row["ready_for_v1"] for row in ordered_rows)),
        "elapsed_seconds": round(time.time() - started, 2),
        "resume_used": args.resume,
        "method": "Gemini-assisted Layer 3 rule and SIR-link candidate compilation on top of Layer 2 obligations; deterministic parsing remains source of truth; manual review still required.",
    }
    write_report(REPORT_JSON_PATH, report)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
