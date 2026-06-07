#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
RULE_PACK_PATH = ROOT_DIR / "data" / "finalized" / "ch4_fincpa" / "law_fincpa_main_ch4_layer4_mvp_rule_pack.jsonl"
SIR_SCHEMA_PATH = ROOT_DIR / "data" / "finalized" / "ch4_fincpa" / "law_fincpa_main_ch4_layer4_mvp_sir_schema.json"
EXAMPLES_DIR = ROOT_DIR / "data" / "runtime" / "ch4_fincpa" / "examples"
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


def main() -> None:
    bundle = {
        "artifact_type": "ch4_runtime_dashboard_bundle",
        "version": "0.1.0",
        "rulePack": load_jsonl(RULE_PACK_PATH),
        "sirSchema": json.loads(SIR_SCHEMA_PATH.read_text(encoding="utf-8")),
        "examples": load_examples(EXAMPLES_DIR),
    }
    payload = json.dumps(bundle, ensure_ascii=False, separators=(",", ":"))
    OUTPUT_JS_PATH.write_text(
        "window.__CH4_RUNTIME_BUNDLE__ = " + payload + ";\n",
        encoding="utf-8",
    )
    print(f"Wrote {OUTPUT_JS_PATH}")


if __name__ == "__main__":
    main()
