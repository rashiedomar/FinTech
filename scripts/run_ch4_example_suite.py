#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = REPO_ROOT / "data/runtime/ch4_fincpa/examples"
RESULTS_DIR = REPO_ROOT / "data/runtime/ch4_fincpa/results"
RUNNER = REPO_ROOT / "scripts/run_ch4_non_llm_workflow.py"


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    examples = sorted(EXAMPLES_DIR.glob("*.json"))
    summary_rows = []

    for example in examples:
        subprocess.run(
            [sys.executable, str(RUNNER), "--input", str(example)],
            cwd=REPO_ROOT,
            check=True,
        )
        report_path = RESULTS_DIR / f"{example.stem}.review_report.json"
        with report_path.open("r", encoding="utf-8") as handle:
            report = json.load(handle)
        summary_rows.append(
            {
                "input_id": report["input_id"],
                "decision": report["final_decision"],
                "escalate": report["should_escalate"],
                "applicable_rules": report["summary"]["applicable_rule_count"],
                "failed_rules": report["summary"]["failed_rule_count"],
                "uncertain_rules": report["summary"]["uncertain_rule_count"],
                "triggered_citations": [item["citation_label"] for item in report["triggered_citations"]],
                "failed_rule_ids": [
                    item["rule_id"] for item in report["rule_results"] if item["status"] == "failed"
                ],
            }
        )

    suite_json = RESULTS_DIR / "example_suite_summary.json"
    with suite_json.open("w", encoding="utf-8") as handle:
        json.dump(summary_rows, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    suite_md = RESULTS_DIR / "example_suite_summary.md"
    lines = [
        "# Chapter 4 Example Suite Summary",
        "",
    ]
    for row in summary_rows:
        lines.extend(
            [
                f"## {row['input_id']}",
                "",
                f"- decision: `{row['decision']}`",
                f"- escalate: `{str(row['escalate']).lower()}`",
                f"- applicable rules: `{row['applicable_rules']}`",
                f"- failed rules: `{row['failed_rules']}`",
                f"- uncertain rules: `{row['uncertain_rules']}`",
                "- triggered citations:",
            ]
        )
        if row["triggered_citations"]:
            for citation in row["triggered_citations"]:
                lines.append(f"  - `{citation}`")
        else:
            lines.append("  - none")
        lines.append("- failed rule ids:")
        if row["failed_rule_ids"]:
            for rule_id in row["failed_rule_ids"]:
                lines.append(f"  - `{rule_id}`")
        else:
            lines.append("  - none")
        lines.append("")

    with suite_md.open("w", encoding="utf-8") as handle:
        handle.write("\n".join(lines).rstrip() + "\n")

    print(f"Wrote: {suite_json}")
    print(f"Wrote: {suite_md}")
    print(f"Examples run: {len(summary_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

