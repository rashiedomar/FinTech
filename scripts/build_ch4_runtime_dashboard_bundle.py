#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT_DIR / "src"
RULE_PACK_PATH = ROOT_DIR / "data" / "finalized" / "ch4_fincpa" / "law_fincpa_main_ch4_layer4_mvp_rule_pack.jsonl"
SIR_SCHEMA_PATH = ROOT_DIR / "data" / "finalized" / "ch4_fincpa" / "law_fincpa_main_ch4_layer4_mvp_sir_schema.json"
EXAMPLES_DIR = ROOT_DIR / "data" / "runtime" / "ch4_fincpa" / "examples"
RESULTS_DIR = ROOT_DIR / "data" / "runtime" / "ch4_fincpa" / "results"
OUTPUT_JS_PATH = ROOT_DIR / "dashboard" / "ch4_runtime_flow" / "runtime-bundle.js"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from safeguard_ai.ch4_runtime import evaluate_runtime_input


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_examples(path: Path) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    for file_path in sorted(path.glob("*.json")):
        rows[file_path.stem] = json.loads(file_path.read_text(encoding="utf-8"))
    return rows


def load_optional_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def load_optional_text(path: Path) -> str | None:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def build_suggested_rewrite_report(example_payload: dict, advisory_output: dict | None) -> dict | None:
    if not advisory_output:
        return None
    rewrite_text = str(advisory_output.get("conservative_rewrite_suggestion") or "").strip()
    if not rewrite_text:
        return None
    payload = copy.deepcopy(example_payload)
    payload["content_text"] = rewrite_text
    if payload.get("title"):
        payload["title"] = f"{payload['title']} (LLM rewrite)"
    else:
        payload["title"] = "LLM rewrite"
    return evaluate_runtime_input(payload, repo_root=ROOT_DIR)


def load_example_artifacts(examples: dict[str, dict]) -> dict[str, dict]:
    artifacts_by_example: dict[str, dict] = {}
    for example_id, example_payload in examples.items():
        review_report = load_optional_json(RESULTS_DIR / f"{example_id}.review_report.json")
        evidence_package = load_optional_json(RESULTS_DIR / f"{example_id}.evidence_package.json")
        llm_advisory_input = load_optional_json(RESULTS_DIR / f"{example_id}.llm_advisory_input.json")
        human_review_packet = load_optional_json(RESULTS_DIR / f"{example_id}.human_review_packet.json")
        gemini_advisory_output = load_optional_json(RESULTS_DIR / f"{example_id}.gemini_advisory_output.json")
        human_review_completed = load_optional_json(RESULTS_DIR / f"{example_id}.human_review_completed.json")
        review_trace = load_optional_json(RESULTS_DIR / f"{example_id}.review_trace.json")
        workflow_bridge_summary = load_optional_text(RESULTS_DIR / f"{example_id}.workflow_bridge_summary.md")
        example_summary = load_optional_text(RESULTS_DIR / f"{example_id}.summary.md")
        suggested_rewrite_report = build_suggested_rewrite_report(example_payload, gemini_advisory_output)
        artifacts_by_example[example_id] = {
            "reviewReport": review_report,
            "evidencePackage": evidence_package,
            "llmAdvisoryInput": llm_advisory_input,
            "humanReviewPacket": human_review_packet,
            "geminiAdvisoryOutput": gemini_advisory_output,
            "humanReviewCompleted": human_review_completed,
            "reviewTrace": review_trace,
            "workflowBridgeSummary": workflow_bridge_summary,
            "exampleSummary": example_summary,
            "suggestedRewriteReport": suggested_rewrite_report,
        }
    return artifacts_by_example


def main() -> None:
    examples = load_examples(EXAMPLES_DIR)
    bundle = {
        "artifact_type": "ch4_runtime_dashboard_bundle",
        "version": "0.2.0",
        "rulePack": load_jsonl(RULE_PACK_PATH),
        "sirSchema": json.loads(SIR_SCHEMA_PATH.read_text(encoding="utf-8")),
        "examples": examples,
        "exampleArtifacts": load_example_artifacts(examples),
        "suiteSummary": load_optional_json(RESULTS_DIR / "example_suite_summary.json"),
    }
    payload = json.dumps(bundle, ensure_ascii=False, separators=(",", ":"))
    OUTPUT_JS_PATH.write_text(
        "window.__CH4_RUNTIME_BUNDLE__ = " + payload + ";\n",
        encoding="utf-8",
    )
    print(f"Wrote {OUTPUT_JS_PATH}")


if __name__ == "__main__":
    main()
