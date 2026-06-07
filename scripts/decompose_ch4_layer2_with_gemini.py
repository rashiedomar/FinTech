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
LAYER1_CSV_PATH = ROOT_DIR / "data" / "annotations" / "ch4_fincpa" / "law_fincpa_main_ch4_layer1_annotations.gemini.csv"
PARSED_JSONL_PATH = ROOT_DIR / "data" / "parsed" / "ch4_fincpa" / "law_fincpa_main_ch4_clause_records.jsonl"
LABEL_GUIDE_PATH = ROOT_DIR / "data" / "annotations" / "ch4_fincpa" / "layer2_label_guide.json"
OUTPUT_CSV_PATH = ROOT_DIR / "data" / "annotations" / "ch4_fincpa" / "law_fincpa_main_ch4_layer2_obligations.gemini.csv"
OUTPUT_JSONL_PATH = ROOT_DIR / "data" / "annotations" / "ch4_fincpa" / "law_fincpa_main_ch4_layer2_obligations.gemini.jsonl"
PARENT_SUMMARY_CSV_PATH = ROOT_DIR / "data" / "annotations" / "ch4_fincpa" / "law_fincpa_main_ch4_layer2_parent_summary.csv"
REPORT_JSON_PATH = ROOT_DIR / "data" / "annotations" / "ch4_fincpa" / "law_fincpa_main_ch4_layer2_gemini_report.json"

DEFAULT_MODEL = "gemini-3.5-flash"

OUTPUT_FIELDS = [
    "parent_record_id",
    "obligation_id",
    "article_id",
    "paragraph_id",
    "article_title",
    "section_id",
    "section_title",
    "page_start",
    "parent_topic_family",
    "parent_layer1_product_scope",
    "parent_layer1_channel_scope",
    "parent_layer1_obligation_mode",
    "parent_needs_decomposition",
    "parent_decomposition_strategy",
    "obligation_order",
    "obligation_label",
    "obligation_summary",
    "source_span_text",
    "product_scope",
    "channel_scope",
    "obligation_mode",
    "trigger_type",
    "operationality",
    "consumer_visibility",
    "manual_verified",
    "reviewer_note",
    "gemini_model",
    "gemini_confidence",
    "gemini_reasoning_summary",
]

PARENT_SUMMARY_FIELDS = [
    "parent_record_id",
    "article_id",
    "paragraph_id",
    "article_title",
    "parent_topic_family",
    "parent_needs_decomposition",
    "parent_decomposition_strategy",
    "obligation_count",
    "gemini_model",
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


def load_jsonl_map(path: Path) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            rows[row["record_id"]] = row
    return rows


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_response_schema() -> dict:
    obligation_properties = {
        "obligation_label": {"type": "STRING"},
        "obligation_summary": {"type": "STRING"},
        "source_span_text": {"type": "STRING"},
        "product_scope": {"type": "STRING"},
        "channel_scope": {"type": "STRING"},
        "obligation_mode": {"type": "STRING"},
        "trigger_type": {"type": "STRING"},
        "operationality": {"type": "STRING"},
        "consumer_visibility": {"type": "STRING"},
        "reviewer_note": {"type": "STRING"},
        "gemini_confidence": {"type": "STRING"},
        "gemini_reasoning_summary": {"type": "STRING"},
    }
    return {
        "type": "OBJECT",
        "properties": {
            "parent_decomposition_strategy": {"type": "STRING"},
            "parent_decomposition_reason": {"type": "STRING"},
            "obligations": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": obligation_properties,
                    "required": list(obligation_properties.keys()),
                },
            },
        },
        "required": [
            "parent_decomposition_strategy",
            "parent_decomposition_reason",
            "obligations",
        ],
    }


def build_system_instruction(label_guide: dict) -> str:
    return f"""You are assisting Layer 2 legal decomposition for clause-level legal records from Chapter 4 of the Korean Financial Consumer Protection Act.

Goal:
- convert one Layer 1 legal clause record into one or more smaller operational obligation units

Rules:
- stay faithful to the source clause text
- do not invent obligations not supported by the source clause
- if the parent clause is already atomic, return exactly 1 obligation unit
- if the parent clause clearly contains multiple operational duties, split it into multiple obligation units
- use only the allowed controlled labels below
- keep source_span_text as an exact short excerpt or close direct span from the parent clause
- keep obligation_summary short and operational
- do not create SIR fields yet

Allowed labels:
{json.dumps(label_guide['fields'], ensure_ascii=False, indent=2)}

Return one JSON object with:
- parent_decomposition_strategy
- parent_decomposition_reason
- obligations (array)
"""


def build_user_prompt(layer1_row: dict, parsed_row: dict) -> str:
    payload = {
        "record_id": parsed_row["record_id"],
        "chapter_id": parsed_row["chapter_id"],
        "chapter_title": parsed_row["chapter_title"],
        "section_id": parsed_row["section_id"],
        "section_title": parsed_row["section_title"],
        "article_id": parsed_row["article_id"],
        "article_title": parsed_row["article_title"],
        "paragraph_id": parsed_row["paragraph_id"],
        "page_start": parsed_row["page_start"],
        "normalized_text": parsed_row["normalized_text"],
        "layer1_hint": {
            "topic_family": layer1_row["topic_family"],
            "product_scope": layer1_row["product_scope"],
            "channel_scope": layer1_row["channel_scope"],
            "obligation_mode": layer1_row["obligation_mode"],
            "needs_decomposition": layer1_row["needs_decomposition"],
            "reviewer_note": layer1_row["reviewer_note"],
        },
    }
    return (
        "Perform Layer 2 decomposition for this legal clause record.\n"
        "Use the clause text as the source of truth.\n"
        "Use the Layer 1 hint only as context, not as binding truth.\n"
        "If needs_decomposition is 'yes', split where the clause clearly contains multiple smaller duties.\n"
        "If needs_decomposition is 'no', prefer a single obligation unit unless the clause obviously contains multiple distinct duties.\n\n"
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
    timeout_seconds: float,
) -> dict:
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body = {
        "system_instruction": {
            "parts": [{"text": system_instruction}],
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": user_prompt}],
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json",
            "responseSchema": build_response_schema(),
            "maxOutputTokens": 2048,
            "thinkingConfig": {
                "thinkingBudget": 0,
            },
        },
    }
    request = urllib.request.Request(
        f"{api_url}?key={api_key}",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        data = json.load(response)
    parts = data["candidates"][0]["content"]["parts"]
    text = "".join(part.get("text", "") for part in parts).strip()
    return parse_json_text(text)


def append_jsonl_rows(path: Path, rows: list[dict]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_existing_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def build_obligation_rows(layer1_row: dict, parsed_row: dict, response: dict, model: str) -> list[dict]:
    out_rows: list[dict] = []
    for idx, obligation in enumerate(response["obligations"], start=1):
        out_rows.append(
            {
                "parent_record_id": parsed_row["record_id"],
                "obligation_id": f"{parsed_row['record_id']}:ob{idx:02d}",
                "article_id": parsed_row["article_id"],
                "paragraph_id": parsed_row["paragraph_id"] or "",
                "article_title": parsed_row["article_title"],
                "section_id": parsed_row["section_id"] or "",
                "section_title": parsed_row["section_title"] or "",
                "page_start": parsed_row["page_start"],
                "parent_topic_family": layer1_row["topic_family"],
                "parent_layer1_product_scope": layer1_row["product_scope"],
                "parent_layer1_channel_scope": layer1_row["channel_scope"],
                "parent_layer1_obligation_mode": layer1_row["obligation_mode"],
                "parent_needs_decomposition": layer1_row["needs_decomposition"],
                "parent_decomposition_strategy": response["parent_decomposition_strategy"],
                "obligation_order": idx,
                "obligation_label": obligation["obligation_label"],
                "obligation_summary": obligation["obligation_summary"],
                "source_span_text": obligation["source_span_text"],
                "product_scope": obligation["product_scope"],
                "channel_scope": obligation["channel_scope"],
                "obligation_mode": obligation["obligation_mode"],
                "trigger_type": obligation["trigger_type"],
                "operationality": obligation["operationality"],
                "consumer_visibility": obligation["consumer_visibility"],
                "manual_verified": "no",
                "reviewer_note": obligation["reviewer_note"],
                "gemini_model": model,
                "gemini_confidence": obligation["gemini_confidence"],
                "gemini_reasoning_summary": obligation["gemini_reasoning_summary"],
            }
        )
    return out_rows


def build_parent_summary(rows: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(row["parent_record_id"], []).append(row)

    summaries: list[dict] = []
    for parent_record_id, items in grouped.items():
        first = items[0]
        summaries.append(
            {
                "parent_record_id": parent_record_id,
                "article_id": first["article_id"],
                "paragraph_id": first["paragraph_id"],
                "article_title": first["article_title"],
                "parent_topic_family": first["parent_topic_family"],
                "parent_needs_decomposition": first["parent_needs_decomposition"],
                "parent_decomposition_strategy": first["parent_decomposition_strategy"],
                "obligation_count": len(items),
                "gemini_model": first["gemini_model"],
            }
        )
    summaries.sort(key=lambda row: row["parent_record_id"])
    return summaries


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_report(path: Path, report: dict) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def main() -> int:
    args = parse_args()
    api_key = API_KEY_PATH.read_text(encoding="utf-8").strip()
    layer1_rows = load_csv_rows(LAYER1_CSV_PATH)
    parsed_rows = load_jsonl_map(PARSED_JSONL_PATH)
    label_guide = load_json(LABEL_GUIDE_PATH)
    system_instruction = build_system_instruction(label_guide)

    if args.limit > 0:
        layer1_rows = layer1_rows[: args.limit]

    if args.resume:
        existing_rows = load_existing_rows(OUTPUT_JSONL_PATH)
    else:
        existing_rows = []
        for path in (OUTPUT_JSONL_PATH, OUTPUT_CSV_PATH, PARENT_SUMMARY_CSV_PATH, REPORT_JSON_PATH):
            if path.exists():
                path.unlink()

    completed_parents = {row["parent_record_id"] for row in existing_rows}
    all_rows: list[dict] = list(existing_rows)
    errors: list[dict] = []
    started = time.time()

    for layer1_row in layer1_rows:
        parent_record_id = layer1_row["record_id"]
        if parent_record_id in completed_parents:
            continue
        parsed_row = parsed_rows[parent_record_id]
        last_error: dict | None = None
        for attempt in range(1, args.max_retries + 2):
            try:
                response = call_gemini(
                    api_key=api_key,
                    model=args.model,
                    system_instruction=system_instruction,
                    user_prompt=build_user_prompt(layer1_row, parsed_row),
                    timeout_seconds=args.timeout_seconds,
                )
                out_rows = build_obligation_rows(layer1_row, parsed_row, response, args.model)
                append_jsonl_rows(OUTPUT_JSONL_PATH, out_rows)
                all_rows.extend(out_rows)
                completed_parents.add(parent_record_id)
                last_error = None
                break
            except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, KeyError, TimeoutError) as exc:
                last_error = {
                    "parent_record_id": parent_record_id,
                    "attempt": attempt,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "model": args.model,
                }
                time.sleep(1.0)
        if last_error is not None:
            errors.append(last_error)
        time.sleep(args.sleep_seconds)

    all_rows.sort(key=lambda row: (row["parent_record_id"], row["obligation_order"]))
    parent_summary = build_parent_summary(all_rows)
    write_csv(OUTPUT_CSV_PATH, all_rows, OUTPUT_FIELDS)
    write_csv(PARENT_SUMMARY_CSV_PATH, parent_summary, PARENT_SUMMARY_FIELDS)

    report = {
        "model": args.model,
        "source_layer1_csv": str(LAYER1_CSV_PATH.relative_to(ROOT_DIR)),
        "source_parsed_jsonl": str(PARSED_JSONL_PATH.relative_to(ROOT_DIR)),
        "output_csv": str(OUTPUT_CSV_PATH.relative_to(ROOT_DIR)),
        "output_jsonl": str(OUTPUT_JSONL_PATH.relative_to(ROOT_DIR)),
        "parent_summary_csv": str(PARENT_SUMMARY_CSV_PATH.relative_to(ROOT_DIR)),
        "total_parent_records": len(layer1_rows),
        "successful_parent_records": len({row["parent_record_id"] for row in all_rows}),
        "total_obligation_rows": len(all_rows),
        "parent_decomposition_strategy_distribution": dict(Counter(row["parent_decomposition_strategy"] for row in all_rows)),
        "obligation_mode_distribution": dict(Counter(row["obligation_mode"] for row in all_rows)),
        "trigger_type_distribution": dict(Counter(row["trigger_type"] for row in all_rows)),
        "operationality_distribution": dict(Counter(row["operationality"] for row in all_rows)),
        "consumer_visibility_distribution": dict(Counter(row["consumer_visibility"] for row in all_rows)),
        "error_count": len(errors),
        "errors": errors,
        "elapsed_seconds": round(time.time() - started, 2),
        "resume_used": args.resume,
        "method": "Gemini-assisted Layer 2 obligation decomposition on top of Layer 1 clause metadata; deterministic parsing remains source of truth; manual review still required.",
    }
    write_report(REPORT_JSON_PATH, report)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
