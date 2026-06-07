#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from safeguard_ai.ch4_runtime import evaluate_runtime_input, render_markdown_summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Chapter 4 non-LLM runtime workflow.")
    parser.add_argument("--input", required=True, help="Path to a runtime input JSON file.")
    parser.add_argument(
        "--output-dir",
        default=str(REPO_ROOT / "data/runtime/ch4_fincpa/results"),
        help="Directory for JSON and Markdown outputs.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    with input_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    report = evaluate_runtime_input(payload, repo_root=REPO_ROOT)
    stem = input_path.stem
    json_path = output_dir / f"{stem}.review_report.json"
    md_path = output_dir / f"{stem}.summary.md"

    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    with md_path.open("w", encoding="utf-8") as handle:
        handle.write(render_markdown_summary(report))

    print(f"Wrote: {json_path}")
    print(f"Wrote: {md_path}")
    print(f"Decision: {report['final_decision']}")
    print(f"Escalate: {report['should_escalate']}")
    print(
        "Rule summary: "
        f"applicable={report['summary']['applicable_rule_count']} "
        f"failed={report['summary']['failed_rule_count']} "
        f"uncertain={report['summary']['uncertain_rule_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

