#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT_DIR / "src"
API_KEY_PATH = ROOT_DIR / "gemini_api.txt"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from safeguard_ai.ch4_postprocess import build_postprocess_pipeline, default_postprocess_paths


DEFAULT_MODEL = "gemini-2.5-flash"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to a runtime input JSON example.",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    parser.add_argument("--reviewer-id", default="omar_demo_human")
    parser.add_argument(
        "--decision",
        default="reject",
        choices=["approve", "approve_with_edits", "reject", "escalate"],
        help="Simulated human-loop decision.",
    )
    parser.add_argument(
        "--reviewer-note",
        default="Contains explicit prohibited investment-guarantee language and misses the required investment risk warning.",
    )
    return parser.parse_args()


def load_api_key() -> str:
    return API_KEY_PATH.read_text(encoding="utf-8").strip()


def build_system_instruction() -> str:
    return """You are the advisory explanation layer in a Korean financial compliance workflow.

You are downstream from a deterministic legal rule engine.
Your role is explanation and advisory support only.

Hard rules:
- Do not change the deterministic final decision.
- Do not invent legal citations or legal requirements.
- Use only the supplied evidence package.
- Be conservative and operational.
- Keep the answer compact and reviewer-friendly.
- When writing a rewrite suggestion for customer-facing content, write one ready-to-use Korean text snippet, not bullets.
- Remove prohibited signals that the deterministic core already flagged.
- If a required content field is missing and it can be expressed in customer-facing text, add it to the rewrite suggestion.
- Do not use placeholders such as [은행명], [금리], or TBD.
- Preserve known seller identity and product identity from the case context whenever possible.
- Avoid absolute expressions such as "반드시", "무조건", "확정", or similar phrasing that can itself trigger the rule engine.
- If deposit_disclaimer is missing, prefer explicit wording that includes "예금자보호", "보호한도", or "예금보험공사" when appropriate.
- If investment_warning is missing, prefer explicit wording that includes "원금 손실 가능성".
- If insurance_warning is missing, mention the concrete switching-risk warnings already present in the evidence package.
- Write every output field in Korean.
- Write remediation_actions as short Korean action sentences.

Return exactly one JSON object with these keys:
- reviewer_summary
- plain_language_rationale
- remediation_actions
- conservative_rewrite_suggestion
- citation_list
"""


def build_response_schema() -> dict:
    return {
        "type": "OBJECT",
        "properties": {
            "reviewer_summary": {"type": "STRING"},
            "plain_language_rationale": {"type": "STRING"},
            "remediation_actions": {
                "type": "ARRAY",
                "items": {"type": "STRING"},
            },
            "conservative_rewrite_suggestion": {"type": "STRING"},
            "citation_list": {
                "type": "ARRAY",
                "items": {"type": "STRING"},
            },
        },
        "required": [
            "reviewer_summary",
            "plain_language_rationale",
            "remediation_actions",
            "conservative_rewrite_suggestion",
            "citation_list",
        ],
    }


def build_user_prompt(payload: dict) -> str:
    deterministic_core = payload.get("deterministic_core", {})
    case_context = payload.get("case_context", {})
    sir_focus_fields = payload.get("sir_focus_fields", {})
    content_field_targets = [
        name
        for name, field in sir_focus_fields.items()
        if field.get("field_group") == "content_text"
    ]
    return (
        "Produce the advisory output for this compliance case.\n"
        "The deterministic engine result is authoritative.\n"
        "Use only the supplied evidence and citations.\n"
        "All output fields must be written in Korean.\n\n"
        "Rewrite guidance:\n"
        f"- final_decision: {deterministic_core.get('final_decision')}\n"
        f"- missing_sir_fields: {json.dumps(deterministic_core.get('missing_sir_fields', []), ensure_ascii=False)}\n"
        f"- content_field_targets: {json.dumps(content_field_targets, ensure_ascii=False)}\n"
        "- For non-compliant customer-facing content, the conservative_rewrite_suggestion should remove banned claims and add missing visible disclosures when possible.\n"
        "- For compliant cases, the conservative_rewrite_suggestion may lightly refine the original text but should stay compliant and concise.\n\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )


def parse_json_text(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:].strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Gemini response did not contain a JSON object.")
    return json.loads(text[start : end + 1])


def sanitize_rewrite_suggestion(advisory_output: dict) -> dict:
    rewrite = str(advisory_output.get("conservative_rewrite_suggestion") or "")
    rewrite = re.sub(r"\s*반드시\s*", " ", rewrite)
    rewrite = re.sub(r"\s*무조건\s*", " ", rewrite)
    rewrite = " ".join(rewrite.split())
    advisory_output["conservative_rewrite_suggestion"] = rewrite
    return advisory_output


def call_gemini(api_key: str, model: str, payload: dict, timeout_seconds: float) -> tuple[dict, dict]:
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body = {
        "system_instruction": {
            "parts": [{"text": build_system_instruction()}],
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": build_user_prompt(payload)}],
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json",
            "responseSchema": build_response_schema(),
            "maxOutputTokens": 1024,
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
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw_response = json.load(response)
    except urllib.error.HTTPError as exc:
        error_text = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini API request failed with HTTP {exc.code}: {error_text}") from exc
    parts = raw_response["candidates"][0]["content"]["parts"]
    text = "".join(part.get("text", "") for part in parts)
    advisory_output = parse_json_text(text)
    return sanitize_rewrite_suggestion(advisory_output), raw_response


def build_completed_human_review(
    human_review_packet: dict,
    advisory_output: dict,
    *,
    reviewer_id: str,
    decision: str,
    reviewer_note: str,
    model: str,
) -> dict:
    completed = copy.deepcopy(human_review_packet)
    completed["review_status"] = "completed"
    completed["completed_review"] = {
        "reviewer_id": reviewer_id,
        "decision": decision,
        "reviewer_note": reviewer_note,
        "llm_model": model,
        "llm_reviewer_summary": advisory_output["reviewer_summary"],
        "llm_recommended_rewrite": advisory_output["conservative_rewrite_suggestion"],
    }
    completed["draft_review_form"]["reviewer_id"] = reviewer_id
    completed["draft_review_form"]["decision"] = decision
    completed["draft_review_form"]["reviewer_note"] = reviewer_note
    completed["draft_review_form"]["requested_edits"] = advisory_output["remediation_actions"]
    return completed


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    original_input = json.loads(args.input.read_text(encoding="utf-8"))
    artifacts = build_postprocess_pipeline(original_input, repo_root=ROOT_DIR)
    advisory_input = artifacts["llm_advisory_input"]

    try:
        advisory_output, raw_response = call_gemini(
            load_api_key(),
            args.model,
            advisory_input,
            args.timeout_seconds,
        )
    except RuntimeError as exc:
        raise SystemExit(str(exc))
    completed_human_review = build_completed_human_review(
        artifacts["human_review_packet"],
        advisory_output,
        reviewer_id=args.reviewer_id,
        decision=args.decision,
        reviewer_note=args.reviewer_note,
        model=args.model,
    )

    results_dir = default_postprocess_paths(ROOT_DIR).default_results_dir
    results_dir.mkdir(parents=True, exist_ok=True)
    stem = args.input.stem
    write_json(results_dir / f"{stem}.gemini_advisory_output.json", advisory_output)
    write_json(results_dir / f"{stem}.human_review_completed.json", completed_human_review)
    write_json(results_dir / f"{stem}.gemini_raw_response.json", raw_response)

    print(json.dumps(
        {
            "input_id": original_input["input_id"],
            "model": args.model,
            "deterministic_final_decision": advisory_input["deterministic_core"]["final_decision"],
            "human_decision": args.decision,
            "output_files": {
                "advisory_output": str(results_dir / f"{stem}.gemini_advisory_output.json"),
                "human_review_completed": str(results_dir / f"{stem}.human_review_completed.json"),
                "raw_response": str(results_dir / f"{stem}.gemini_raw_response.json"),
            },
        },
        ensure_ascii=False,
        indent=2,
    ))


if __name__ == "__main__":
    main()
