#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT_DIR / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from safeguard_ai.ch4_postprocess import build_postprocess_pipeline, default_postprocess_paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        help="Optional input JSON. If omitted, all example inputs are processed.",
    )
    return parser.parse_args()


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_one(input_path: Path) -> None:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    artifacts = build_postprocess_pipeline(payload, repo_root=ROOT_DIR)

    results_dir = default_postprocess_paths(ROOT_DIR).default_results_dir
    results_dir.mkdir(parents=True, exist_ok=True)
    stem = input_path.stem

    write_json(results_dir / f"{stem}.review_trace.json", artifacts["runtime_trace"])
    write_json(results_dir / f"{stem}.evidence_package.json", artifacts["evidence_package"])
    write_json(results_dir / f"{stem}.llm_advisory_input.json", artifacts["llm_advisory_input"])
    write_json(results_dir / f"{stem}.human_review_packet.json", artifacts["human_review_packet"])
    (results_dir / f"{stem}.workflow_bridge_summary.md").write_text(
        artifacts["bridge_summary_md"],
        encoding="utf-8",
    )
    print(f"Processed {input_path.name}")


def main() -> None:
    args = parse_args()
    paths = default_postprocess_paths(ROOT_DIR)
    if args.input:
        run_one(args.input)
        return

    for input_path in sorted(paths.default_examples_dir.glob("*.json")):
        run_one(input_path)


if __name__ == "__main__":
    main()
