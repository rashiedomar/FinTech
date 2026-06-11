#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT_DIR / "src"
OUTPUT_DIR = ROOT_DIR / "data" / "retrieval" / "ch4_fincpa"
CORPUS_PATH = OUTPUT_DIR / "ch4_embedding_corpus.jsonl"
MANIFEST_PATH = OUTPUT_DIR / "ch4_embedding_manifest.json"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from safeguard_ai.ch4_retrieval import build_embedding_corpus


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = build_embedding_corpus(ROOT_DIR)
    write_jsonl(CORPUS_PATH, rows)

    manifest = {
        "artifact_type": "ch4_embedding_manifest",
        "version": "0.1.0",
        "purpose": "Embedding-ready legal retrieval corpus for the Chapter 4 evidence retrieval layer.",
        "embedding_status": "corpus_ready_vectors_not_computed",
        "source_scope": {
            "source_pdf": "data/raw/official/law_fincpa_main_2026-01-02.pdf",
            "chapter_id": "제4장",
            "chapter_title": "금융상품판매업자등의 영업행위 준수사항",
        },
        "chunk_count": len(rows),
        "chunk_type_counts": dict(Counter(row["chunk_type"] for row in rows)),
        "article_count": len({row["article_id"] for row in rows if row["article_id"]}),
        "rule_grounded_rule_count": len({row["rule_id"] for row in rows if row["rule_id"]}),
        "output_paths": {
            "corpus_jsonl": str(CORPUS_PATH.relative_to(ROOT_DIR)),
        },
        "notes": [
            "This file is embedding-ready but does not contain vectors yet.",
            "The recommended first retrieval index is the rule_grounded_clause chunk family.",
            "parsed_clause and article_rollup chunks should be retained for legal context expansion and human review support.",
        ],
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
