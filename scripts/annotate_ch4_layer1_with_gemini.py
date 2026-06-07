#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
API_KEY_PATH = ROOT_DIR / "gemini_api.txt"
INPUT_JSONL_PATH = ROOT_DIR / "data" / "parsed" / "ch4_fincpa" / "law_fincpa_main_ch4_clause_records.jsonl"
LABEL_GUIDE_PATH = ROOT_DIR / "data" / "annotations" / "ch4_fincpa" / "layer1_label_guide.json"
OUTPUT_CSV_PATH = ROOT_DIR / "data" / "annotations" / "ch4_fincpa" / "law_fincpa_main_ch4_layer1_annotations.gemini.csv"
OUTPUT_JSONL_PATH = ROOT_DIR / "data" / "annotations" / "ch4_fincpa" / "law_fincpa_main_ch4_layer1_annotations.gemini.jsonl"
REPORT_PATH = ROOT_DIR / "data" / "annotations" / "ch4_fincpa" / "law_fincpa_main_ch4_layer1_gemini_report.json"

DEFAULT_MODEL = "gemini-2.5-flash-lite"

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
    "gemini_model",
    "gemini_confidence",
    "gemini_reasoning_summary",
]


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_system_instruction(label_guide: dict) -> str:
    fields = label_guide["fields"]
    return f"""You are assisting legal metadata annotation for a clause-level dataset parsed from Chapter 4 of the Korean Financial Consumer Protection Act.

Your job is NOT to rewrite the law and NOT to generate new legal text.
Your job is only to suggest Layer 1 metadata labels for one clause record at a time.

Rules:
- Use only the allowed label values provided below.
- Be conservative. If relevance is unclear, use "review".
- product_scope and channel_scope must use pipe-delimited values when multiple labels apply.
- Do not invent labels outside the allowed set.
- Do not convert this into SIR fields yet.
- Keep reasoning short and operational.

Allowed labels:
{json.dumps(fields, ensure_ascii=False, indent=2)}

Return a single JSON object with exactly these keys:
- is_relevant_to_theme2
- topic_family
- product_scope
- channel_scope
- obligation_mode
- needs_decomposition
- reviewer_note
- gemini_confidence
- gemini_reasoning_summary
"""


def build_response_schema() -> dict:
    return {
        "type": "OBJECT",
        "properties": {
            "is_relevant_to_theme2": {"type": "STRING"},
            "topic_family": {"type": "STRING"},
            "product_scope": {"type": "STRING"},
            "channel_scope": {"type": "STRING"},
            "obligation_mode": {"type": "STRING"},
            "needs_decomposition": {"type": "STRING"},
            "reviewer_note": {"type": "STRING"},
            "gemini_confidence": {"type": "STRING"},
            "gemini_reasoning_summary": {"type": "STRING"},
        },
        "required": [
            "is_relevant_to_theme2",
            "topic_family",
            "product_scope",
            "channel_scope",
            "obligation_mode",
            "needs_decomposition",
            "reviewer_note",
            "gemini_confidence",
            "gemini_reasoning_summary",
        ],
    }


def build_user_prompt(record: dict) -> str:
    payload = {
        "record_id": record["record_id"],
        "chapter_id": record["chapter_id"],
        "chapter_title": record["chapter_title"],
        "section_id": record["section_id"],
        "section_title": record["section_title"],
        "article_id": record["article_id"],
        "article_title": record["article_title"],
        "paragraph_id": record["paragraph_id"],
        "page_start": record["page_start"],
        "normalized_text": record["normalized_text"],
    }
    return (
        "Annotate this parsed legal clause record for Layer 1.\n"
        "If the clause is broad, strategic, or outside the first compliance workflow slice, prefer 'review'.\n"
        "If it is clearly part of ad/content review, explanation, suitability, unfair sales, solicitation, internal control, or recordkeeping, choose the closest controlled label.\n\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--sleep-seconds", type=float, default=0.1)
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    parser.add_argument("--max-retries", type=int, default=2)
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


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
    api_key: str,
    model: str,
    system_instruction: str,
    user_prompt: str,
    timeout_seconds: float,
) -> tuple[dict, str]:
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
            "maxOutputTokens": 512,
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
    return parse_json_text(text), text


def build_output_row(record: dict, suggestion: dict, model: str) -> dict:
    return {
        "record_id": record["record_id"],
        "article_id": record["article_id"],
        "paragraph_id": record["paragraph_id"] or "",
        "article_title": record["article_title"],
        "section_id": record["section_id"] or "",
        "section_title": record["section_title"] or "",
        "page_start": record["page_start"],
        "normalized_text": record["normalized_text"],
        "is_relevant_to_theme2": suggestion["is_relevant_to_theme2"],
        "topic_family": suggestion["topic_family"],
        "product_scope": suggestion["product_scope"],
        "channel_scope": suggestion["channel_scope"],
        "obligation_mode": suggestion["obligation_mode"],
        "needs_decomposition": suggestion["needs_decomposition"],
        "manual_verified": "no",
        "reviewer_note": suggestion["reviewer_note"],
        "gemini_model": model,
        "gemini_confidence": suggestion["gemini_confidence"],
        "gemini_reasoning_summary": suggestion["gemini_reasoning_summary"],
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


def append_jsonl_row(path: Path, row: dict) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_report(path: Path, report: dict) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


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
            rows[row["record_id"]] = row
    return rows


def main() -> int:
    args = parse_args()
    api_key = API_KEY_PATH.read_text(encoding="utf-8").strip()
    records = load_jsonl(INPUT_JSONL_PATH)
    label_guide = load_json(LABEL_GUIDE_PATH)
    system_instruction = build_system_instruction(label_guide)

    if args.limit > 0:
        records = records[: args.limit]

    if args.resume:
        existing_rows = load_existing_rows(OUTPUT_JSONL_PATH)
    else:
        existing_rows = {}
        if OUTPUT_JSONL_PATH.exists():
            OUTPUT_JSONL_PATH.unlink()
        if OUTPUT_CSV_PATH.exists():
            OUTPUT_CSV_PATH.unlink()
        if REPORT_PATH.exists():
            REPORT_PATH.unlink()

    rows_by_id: dict[str, dict] = dict(existing_rows)
    errors: list[dict] = []
    started = time.time()

    for record in records:
        if record["record_id"] in rows_by_id:
            continue
        last_error: dict | None = None
        for attempt in range(1, args.max_retries + 2):
            try:
                suggestion, raw_text = call_gemini(
                    api_key=api_key,
                    model=args.model,
                    system_instruction=system_instruction,
                    user_prompt=build_user_prompt(record),
                    timeout_seconds=args.timeout_seconds,
                )
                row = build_output_row(record, suggestion, args.model)
                rows_by_id[row["record_id"]] = row
                append_jsonl_row(OUTPUT_JSONL_PATH, row)
                last_error = None
                break
            except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, KeyError, TimeoutError) as exc:
                last_error = {
                    "record_id": record["record_id"],
                    "attempt": attempt,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "model": args.model,
                }
                time.sleep(1.0)
        if last_error is not None:
            errors.append(last_error)
        time.sleep(args.sleep_seconds)

    ordered_rows = [rows_by_id[record["record_id"]] for record in records if record["record_id"] in rows_by_id]
    write_csv(OUTPUT_CSV_PATH, ordered_rows)
    write_report(
        REPORT_PATH,
        {
            "model": args.model,
            "source_dataset": str(INPUT_JSONL_PATH.relative_to(ROOT_DIR)),
            "output_csv": str(OUTPUT_CSV_PATH.relative_to(ROOT_DIR)),
            "output_jsonl": str(OUTPUT_JSONL_PATH.relative_to(ROOT_DIR)),
            "total_input_records": len(records),
            "successful_rows": len(ordered_rows),
            "error_count": len(errors),
            "errors": errors,
            "resume_used": args.resume,
            "elapsed_seconds": round(time.time() - started, 2),
            "method": "Gemini-assisted constrained Layer 1 annotation; deterministic parsing remains source of truth; manual review still required.",
        },
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
