#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT_DIR / "src"
OUTPUT_DIR = ROOT_DIR / "data" / "retrieval" / "ch4_fincpa"
QUERIES_PATH = OUTPUT_DIR / "ch4_example_retrieval_queries.jsonl"
MANIFEST_PATH = OUTPUT_DIR / "ch4_example_retrieval_query_manifest.json"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from safeguard_ai.ch4_retrieval import build_retrieval_queries_from_case, load_json


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    examples_dir = ROOT_DIR / "data/runtime/ch4_fincpa/examples"
    results_dir = ROOT_DIR / "data/runtime/ch4_fincpa/results"

    all_queries: list[dict] = []
    processed_inputs: list[str] = []

    for input_path in sorted(examples_dir.glob("*.json")):
        report_path = results_dir / f"{input_path.stem}.review_report.json"
        if not report_path.exists():
            continue
        original_input = load_json(input_path)
        review_report = load_json(report_path)
        queries = build_retrieval_queries_from_case(original_input, review_report)
        if queries:
            all_queries.extend(queries)
            processed_inputs.append(original_input["input_id"])

    write_jsonl(QUERIES_PATH, all_queries)
    manifest = {
        "artifact_type": "ch4_retrieval_query_manifest",
        "version": "0.1.0",
        "purpose": "Example retrieval queries derived from current deterministic Chapter 4 review outputs.",
        "query_count": len(all_queries),
        "processed_input_count": len(processed_inputs),
        "processed_inputs": processed_inputs,
        "query_status_counts": dict(Counter(row["query_status"] for row in all_queries)),
        "rule_family_counts": dict(Counter(row["rule_family"] for row in all_queries)),
        "output_paths": {
            "queries_jsonl": str(QUERIES_PATH.relative_to(ROOT_DIR)),
        },
        "notes": [
            "Each query is tied to one failed or uncertain rule result.",
            "The query contract is designed for vector retrieval plus metadata filtering.",
            "These queries are examples only; production retrieval should build the same structure on demand after runtime evaluation.",
        ],
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
