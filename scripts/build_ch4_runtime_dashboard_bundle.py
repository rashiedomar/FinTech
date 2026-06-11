#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
RULE_PACK_PATH = ROOT_DIR / "data" / "finalized" / "ch4_fincpa" / "law_fincpa_main_ch4_layer4_mvp_rule_pack.jsonl"
SIR_SCHEMA_PATH = ROOT_DIR / "data" / "finalized" / "ch4_fincpa" / "law_fincpa_main_ch4_layer4_mvp_sir_schema.json"
EXAMPLES_DIR = ROOT_DIR / "data" / "runtime" / "ch4_fincpa" / "examples"
RESULTS_DIR = ROOT_DIR / "data" / "runtime" / "ch4_fincpa" / "results"
RETRIEVAL_QUERY_PATH = ROOT_DIR / "data" / "retrieval" / "ch4_fincpa" / "ch4_example_retrieval_queries.jsonl"
RETRIEVAL_INDEX_MANIFEST_PATH = ROOT_DIR / "data" / "retrieval" / "ch4_fincpa" / "ch4_embedding_index_manifest.json"
OUTPUT_JS_PATH = ROOT_DIR / "dashboard" / "ch4_runtime_flow" / "runtime-bundle.js"


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


def load_example_evidence_packages(path: Path) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    for file_path in sorted(path.glob("*.evidence_package.json")):
        rows[file_path.stem.replace(".evidence_package", "")] = json.loads(file_path.read_text(encoding="utf-8"))
    return rows


def load_example_retrieval_queries(path: Path) -> dict[str, list[dict]]:
    if not path.exists():
        return {}
    grouped: dict[str, list[dict]] = {}
    for row in load_jsonl(path):
        grouped.setdefault(row["input_id"], []).append(row)
    return grouped


def main() -> None:
    bundle = {
        "artifact_type": "ch4_runtime_dashboard_bundle",
        "version": "0.1.0",
        "rulePack": load_jsonl(RULE_PACK_PATH),
        "sirSchema": json.loads(SIR_SCHEMA_PATH.read_text(encoding="utf-8")),
        "examples": load_examples(EXAMPLES_DIR),
        "exampleEvidencePackages": load_example_evidence_packages(RESULTS_DIR),
        "exampleRetrievalQueries": load_example_retrieval_queries(RETRIEVAL_QUERY_PATH),
        "retrievalIndexManifest": load_optional_json(RETRIEVAL_INDEX_MANIFEST_PATH),
    }
    payload = json.dumps(bundle, ensure_ascii=False, separators=(",", ":"))
    OUTPUT_JS_PATH.write_text(
        "window.__CH4_RUNTIME_BUNDLE__ = " + payload + ";\n",
        encoding="utf-8",
    )
    print(f"Wrote {OUTPUT_JS_PATH}")


if __name__ == "__main__":
    main()
