#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = ROOT_DIR / "data" / "runtime" / "ch4_fincpa" / "examples"
RESULTS_DIR = ROOT_DIR / "data" / "runtime" / "ch4_fincpa" / "results"
RUNNER_PATH = ROOT_DIR / "scripts" / "run_ch4_gemini_advisory.py"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="gemini-2.5-flash")
    parser.add_argument("--timeout-seconds", type=float, default=90.0)
    parser.add_argument("--reviewer-id", default="omar_demo_human")
    return parser.parse_args()


def load_review_report(example_id: str) -> dict:
    path = RESULTS_DIR / f"{example_id}.review_report.json"
    return json.loads(path.read_text(encoding="utf-8"))


def choose_human_decision(review_report: dict) -> tuple[str, str]:
    decision = review_report["final_decision"]
    if decision == "compliant":
        return "approve", "결정형 검토를 통과했으므로 현재 문구를 승인합니다."
    if review_report.get("should_escalate"):
        return "escalate", "결정형 검토에서 고위험 이슈가 확인되어 컴플라이언스 추가 검토로 에스컬레이션합니다."
    if decision == "non_compliant":
        return "reject", "결정형 검토에서 규칙 위반이 확인되어 배포 전 수정이 필요합니다."
    return "approve_with_edits", "결정형 검토 결과 일부 수정 후 승인할 수 있습니다."


def main() -> None:
    args = parse_args()
    outputs = []
    for input_path in sorted(EXAMPLES_DIR.glob("*.json")):
        example_id = input_path.stem
        review_report = load_review_report(example_id)
        decision, reviewer_note = choose_human_decision(review_report)
        cmd = [
            sys.executable,
            str(RUNNER_PATH),
            "--input",
            str(input_path),
            "--model",
            args.model,
            "--timeout-seconds",
            str(args.timeout_seconds),
            "--reviewer-id",
            args.reviewer_id,
            "--decision",
            decision,
            "--reviewer-note",
            reviewer_note,
        ]
        completed = subprocess.run(cmd, cwd=ROOT_DIR, check=True, capture_output=True, text=True)
        outputs.append(json.loads(completed.stdout))

    print(json.dumps({"cases": outputs, "count": len(outputs), "model": args.model}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
