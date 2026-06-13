from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from functools import lru_cache


DEFAULT_EMBEDDING_MODEL_ID = "nlpai-lab/KURE-v1"
DEFAULT_TOP_K = 5


@dataclass
class RetrievalPaths:
    parse_records_path: Path
    rule_pack_path: Path
    example_inputs_dir: Path
    review_results_dir: Path


def default_retrieval_paths(repo_root: Path) -> RetrievalPaths:
    return RetrievalPaths(
        parse_records_path=repo_root / "data/parsed/ch4_fincpa/law_fincpa_main_ch4_clause_records.jsonl",
        rule_pack_path=repo_root / "data/finalized/ch4_fincpa/law_fincpa_main_ch4_layer4_mvp_rule_pack.jsonl",
        example_inputs_dir=repo_root / "data/runtime/ch4_fincpa/examples",
        review_results_dir=repo_root / "data/runtime/ch4_fincpa/results",
    )


@dataclass
class RetrievalIndexPaths:
    corpus_path: Path
    query_examples_path: Path
    index_rows_path: Path
    embeddings_path: Path
    manifest_path: Path


def default_retrieval_index_paths(repo_root: Path) -> RetrievalIndexPaths:
    base = repo_root / "data" / "retrieval" / "ch4_fincpa"
    return RetrievalIndexPaths(
        corpus_path=base / "ch4_embedding_corpus.jsonl",
        query_examples_path=base / "ch4_example_retrieval_queries.jsonl",
        index_rows_path=base / "ch4_embedding_index_rows.jsonl",
        embeddings_path=base / "ch4_embedding_index_embeddings.npy",
        manifest_path=base / "ch4_embedding_index_manifest.json",
    )


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def build_embedding_corpus(repo_root: Path) -> list[dict[str, Any]]:
    paths = default_retrieval_paths(repo_root)
    parse_rows = load_jsonl(paths.parse_records_path)
    rule_rows = load_jsonl(paths.rule_pack_path)

    parse_by_record = {row["record_id"]: row for row in parse_rows}
    article_map: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in parse_rows:
        article_map[row["article_id"]].append(row)

    corpus_rows: list[dict[str, Any]] = []

    for row in parse_rows:
        citation_label = _build_citation_label(row["article_id"], row.get("paragraph_id"))
        corpus_rows.append(
            {
                "artifact_type": "ch4_embedding_corpus_row",
                "chunk_id": f"{row['record_id']}:chunk:parsed_clause",
                "chunk_type": "parsed_clause",
                "source_type": "official_statute_pdf",
                "source_pdf": row["source_path"],
                "source_title": row["source_title"],
                "record_id": row["record_id"],
                "parent_record_id": row["record_id"],
                "article_id": row["article_id"],
                "paragraph_id": row["paragraph_id"],
                "article_title": row["article_title"],
                "section_id": row["section_id"],
                "section_title": row["section_title"],
                "page_start": row["page_start"],
                "citation_label": citation_label,
                "rule_id": None,
                "rule_family": None,
                "logic_type": None,
                "detection_target": None,
                "product_scope": None,
                "channel_scope": None,
                "sir_candidate_fields": [],
                "delegated_detail_hint": "대통령령" in row["normalized_text"],
                "metadata_filters": {
                    "article_id": row["article_id"],
                    "paragraph_id": row["paragraph_id"],
                    "section_id": row["section_id"],
                },
                "retrieval_text": _render_parsed_clause_text(row),
            }
        )

    for article_id, rows in sorted(article_map.items()):
        first = rows[0]
        ordered_rows = sorted(rows, key=lambda item: (item["paragraph_id"] or ""))
        article_body = "\n".join(
            f"{row['paragraph_id'] or '본문'} {row['normalized_text']}" for row in ordered_rows
        )
        corpus_rows.append(
            {
                "artifact_type": "ch4_embedding_corpus_row",
                "chunk_id": f"{first['source_id']}:{article_id}:chunk:article_rollup",
                "chunk_type": "article_rollup",
                "source_type": "official_statute_pdf",
                "source_pdf": first["source_path"],
                "source_title": first["source_title"],
                "record_id": None,
                "parent_record_id": None,
                "article_id": article_id,
                "paragraph_id": None,
                "article_title": first["article_title"],
                "section_id": first["section_id"],
                "section_title": first["section_title"],
                "page_start": first["page_start"],
                "citation_label": _build_citation_label(article_id, None),
                "rule_id": None,
                "rule_family": None,
                "logic_type": None,
                "detection_target": None,
                "product_scope": None,
                "channel_scope": None,
                "sir_candidate_fields": [],
                "delegated_detail_hint": "대통령령" in article_body,
                "metadata_filters": {
                    "article_id": article_id,
                    "section_id": first["section_id"],
                },
                "retrieval_text": (
                    f"[source] {first['source_title']}\n"
                    f"[section] {first['section_id']} {first['section_title']}\n"
                    f"[article] {article_id} {first['article_title']}\n"
                    f"[citation] {_build_citation_label(article_id, None)}\n"
                    f"[article_context]\n{article_body}"
                ),
            }
        )

    for row in rule_rows:
        parent_clause = parse_by_record.get(row["parent_record_id"])
        citation_label = _build_citation_label(row["article_id"], row.get("paragraph_id"))
        parent_text = parent_clause["normalized_text"] if parent_clause else ""
        corpus_rows.append(
            {
                "artifact_type": "ch4_embedding_corpus_row",
                "chunk_id": f"{row['rule_id']}:chunk:rule_grounded_clause",
                "chunk_type": "rule_grounded_clause",
                "source_type": "compiled_rule_plus_statute_context",
                "source_pdf": "data/raw/official/law_fincpa_main_2026-01-02.pdf",
                "source_title": "금융소비자 보호에 관한 법률",
                "record_id": row["parent_record_id"],
                "parent_record_id": row["parent_record_id"],
                "article_id": row["article_id"],
                "paragraph_id": row["paragraph_id"],
                "article_title": row["article_title"],
                "section_id": row["section_id"],
                "section_title": row["section_title"],
                "page_start": parent_clause["page_start"] if parent_clause else None,
                "citation_label": citation_label,
                "rule_id": row["rule_id"],
                "rule_family": row["rule_family"],
                "logic_type": row["logic_type"],
                "detection_target": row["detection_target"],
                "product_scope": row["product_scope"],
                "channel_scope": row["channel_scope"],
                "sir_candidate_fields": row["sir_candidate_fields"],
                "delegated_detail_hint": ("대통령령" in row["source_span_text"]) or ("대통령령" in row["obligation_summary"]),
                "metadata_filters": {
                    "article_id": row["article_id"],
                    "paragraph_id": row["paragraph_id"],
                    "rule_family": row["rule_family"],
                    "logic_type": row["logic_type"],
                    "detection_target": row["detection_target"],
                    "product_scope": row["product_scope"],
                    "channel_scope": row["channel_scope"],
                },
                "retrieval_text": _render_rule_grounded_text(row, citation_label, parent_text),
            }
        )

    corpus_rows.sort(key=lambda item: (item["article_id"] or "", item["chunk_type"], item["chunk_id"]))
    return corpus_rows


def build_retrieval_queries_from_case(
    original_input: dict[str, Any],
    review_report: dict[str, Any],
) -> list[dict[str, Any]]:
    content_text = original_input.get("content_text", "")
    title = original_input.get("title", "")
    queries: list[dict[str, Any]] = []
    for result in review_report["rule_results"]:
        if result["status"] not in {"failed", "uncertain"}:
            continue
        citation = result["legal_basis"]["citation_label"]
        source_span = result["legal_basis"]["source_span_text"]
        finding_fields = result["finding_fields"]
        query_text = (
            f"[case] {review_report['input_id']}\n"
            f"[title] {title}\n"
            f"[content] {content_text}\n"
            f"[decision] {review_report['final_decision']}\n"
            f"[rule_id] {result['rule_id']}\n"
            f"[rule_family] {result['rule_family']}\n"
            f"[logic_type] {result['logic_type']}\n"
            f"[reason] {result['reason']}\n"
            f"[finding_fields] {', '.join(finding_fields) or 'none'}\n"
            f"[known_citation] {citation}\n"
            f"[rule_summary] {result['summary']}\n"
            f"[source_span] {source_span}"
        )
        queries.append(
            {
                "artifact_type": "ch4_retrieval_query_row",
                "query_id": f"{review_report['input_id']}::{result['rule_id']}",
                "input_id": review_report["input_id"],
                "rule_id": result["rule_id"],
                "query_status": result["status"],
                "final_decision": review_report["final_decision"],
                "review_scope": review_report["review_scope"],
                "product_scope_hint": review_report["product_scope_hint"],
                "channel_scope_hint": review_report["channel_scope_hint"],
                "rule_family": result["rule_family"],
                "logic_type": result["logic_type"],
                "failed_reason": result["reason"],
                "finding_fields": finding_fields,
                "known_citation_label": citation,
                "preferred_chunk_types": [
                    "rule_grounded_clause",
                    "parsed_clause",
                    "article_rollup",
                ],
                "metadata_filters": {
                    "article_id": result["article_id"],
                    "rule_family": result["rule_family"],
                    "logic_type": result["logic_type"],
                    "product_scope_hint": review_report["product_scope_hint"],
                    "channel_scope_hint": review_report["channel_scope_hint"],
                },
                "query_text": query_text,
            }
        )
    return queries


def embedding_index_exists(repo_root: Path) -> bool:
    paths = default_retrieval_index_paths(repo_root)
    return paths.index_rows_path.exists() and paths.embeddings_path.exists() and paths.manifest_path.exists()


def build_embedding_index(
    repo_root: Path,
    *,
    model_id: str = DEFAULT_EMBEDDING_MODEL_ID,
    batch_size: int = 16,
    max_length: int = 512,
    device: str | None = None,
) -> dict[str, Any]:
    import numpy as np

    rows = build_embedding_corpus(repo_root)
    retrieval_texts = [row["retrieval_text"] for row in rows]
    embedding_rows, resolved_device = _encode_texts(
        retrieval_texts,
        model_id=model_id,
        batch_size=batch_size,
        max_length=max_length,
        prefix=_embedding_text_prefix(model_id, text_role="passage"),
        device=device,
    )

    paths = default_retrieval_index_paths(repo_root)
    paths.index_rows_path.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(paths.index_rows_path, rows)
    np.save(paths.embeddings_path, embedding_rows)

    manifest = {
        "artifact_type": "ch4_embedding_index_manifest",
        "version": "0.1.0",
        "index_status": "ready",
        "model_id": model_id,
        "encoder_backend": "sentence_transformers",
        "device_used": resolved_device,
        "batch_size": batch_size,
        "max_length": max_length,
        "chunk_count": len(rows),
        "embedding_dimension": int(embedding_rows.shape[1]) if len(rows) else 0,
        "text_prefix_policy": _embedding_prefix_policy_label(model_id),
        "output_paths": {
            "index_rows_jsonl": str(paths.index_rows_path.relative_to(repo_root)),
            "embeddings_npy": str(paths.embeddings_path.relative_to(repo_root)),
            "manifest_json": str(paths.manifest_path.relative_to(repo_root)),
        },
        "notes": [
            "Embeddings are L2-normalized sentence vectors.",
            _embedding_prefix_note(model_id),
            "Retrieval uses cosine similarity plus metadata-aware reranking.",
        ],
    }
    paths.manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def retrieve_support_for_query(
    query_row: dict[str, Any],
    *,
    repo_root: Path,
    top_k: int = DEFAULT_TOP_K,
) -> dict[str, Any]:
    import numpy as np

    paths = default_retrieval_index_paths(repo_root)
    if not embedding_index_exists(repo_root):
        raise FileNotFoundError("Embedding index not found. Build it first.")

    rows = load_jsonl(paths.index_rows_path)
    embeddings = np.load(paths.embeddings_path)
    manifest = load_json(paths.manifest_path)

    query_embedding, resolved_device = _encode_texts(
        [query_row["query_text"]],
        model_id=manifest["model_id"],
        batch_size=1,
        max_length=manifest.get("max_length", 512),
        prefix=_embedding_text_prefix(manifest["model_id"], text_role="query"),
        device=manifest.get("device_used"),
    )
    query_vector = query_embedding[0]

    candidate_indices, candidate_stage = _select_candidate_indices(rows, query_row)
    if not candidate_indices:
        candidate_indices = list(range(len(rows)))
        candidate_stage = "global_fallback"

    candidate_matrix = embeddings[candidate_indices]
    similarities = candidate_matrix @ query_vector
    scored_rows: list[dict[str, Any]] = []

    for local_index, row_index in enumerate(candidate_indices):
        row = rows[row_index]
        similarity = float(similarities[local_index])
        bonus = _score_bonus(row, query_row)
        final_score = similarity + bonus
        scored_rows.append(
            {
                "chunk_id": row["chunk_id"],
                "chunk_type": row["chunk_type"],
                "citation_label": row["citation_label"],
                "article_id": row["article_id"],
                "paragraph_id": row["paragraph_id"],
                "rule_id": row["rule_id"],
                "rule_family": row["rule_family"],
                "logic_type": row["logic_type"],
                "detection_target": row["detection_target"],
                "product_scope": row["product_scope"],
                "channel_scope": row["channel_scope"],
                "delegated_detail_hint": row["delegated_detail_hint"],
                "metadata_filters": row["metadata_filters"],
                "retrieval_text": row["retrieval_text"],
                "similarity": round(similarity, 6),
                "bonus": round(bonus, 6),
                "score": round(final_score, 6),
            }
        )

    scored_rows.sort(key=lambda item: (-item["score"], -item["similarity"], item["chunk_id"]))
    top_rows = []
    for rank, row in enumerate(scored_rows[:top_k], start=1):
        row = dict(row)
        row["rank"] = rank
        top_rows.append(row)

    return {
        "artifact_type": "ch4_vector_retrieval_result",
        "version": "0.1.0",
        "query_id": query_row["query_id"],
        "rule_id": query_row["rule_id"],
        "backend": {
            "type": "local_sentence_transformers_cosine_search",
            "model_id": manifest["model_id"],
            "encoder_backend": manifest.get("encoder_backend", "sentence_transformers"),
            "device_used": resolved_device,
            "candidate_stage": candidate_stage,
            "top_k": top_k,
        },
        "results": top_rows,
    }


def _build_citation_label(article_id: str, paragraph_id: str | None) -> str:
    if paragraph_id:
        return f"금융소비자 보호에 관한 법률 {article_id}{paragraph_id}"
    return f"금융소비자 보호에 관한 법률 {article_id}"


def _render_parsed_clause_text(row: dict[str, Any]) -> str:
    return (
        f"[source] {row['source_title']}\n"
        f"[section] {row['section_id']} {row['section_title']}\n"
        f"[article] {row['article_id']} {row['article_title']}\n"
        f"[paragraph] {row['paragraph_id'] or '본문'}\n"
        f"[citation] {_build_citation_label(row['article_id'], row.get('paragraph_id'))}\n"
        f"[text] {row['normalized_text']}"
    )


def _render_rule_grounded_text(
    row: dict[str, Any],
    citation_label: str,
    parent_text: str,
) -> str:
    return (
        f"[source] 금융소비자 보호에 관한 법률\n"
        f"[section] {row['section_id']} {row['section_title']}\n"
        f"[article] {row['article_id']} {row['article_title']}\n"
        f"[citation] {citation_label}\n"
        f"[rule_id] {row['rule_id']}\n"
        f"[rule_family] {row['rule_family']}\n"
        f"[logic_type] {row['logic_type']}\n"
        f"[detection_target] {row['detection_target']}\n"
        f"[product_scope] {row['product_scope']}\n"
        f"[channel_scope] {row['channel_scope']}\n"
        f"[sir_fields] {', '.join(row['sir_candidate_fields'])}\n"
        f"[rule_summary] {row['rule_candidate_summary']}\n"
        f"[obligation_summary] {row['obligation_summary']}\n"
        f"[source_span] {row['source_span_text']}\n"
        f"[parent_clause] {parent_text}"
    )


def _scope_tokens(value: str | None) -> set[str]:
    if not value:
        return set()
    return {token.strip() for token in str(value).split("|") if token.strip()}


def _select_candidate_indices(rows: list[dict[str, Any]], query_row: dict[str, Any]) -> tuple[list[int], str]:
    preferred_types = set(query_row.get("preferred_chunk_types") or [])
    article_id = query_row.get("metadata_filters", {}).get("article_id")

    def matches(row: dict[str, Any], *, require_article: bool, require_preferred: bool) -> bool:
        if require_article and article_id and row.get("article_id") != article_id:
            return False
        if require_preferred and preferred_types and row.get("chunk_type") not in preferred_types:
            return False
        return True

    stages = [
        ("article_and_preferred_type", dict(require_article=True, require_preferred=True)),
        ("article_only", dict(require_article=True, require_preferred=False)),
        ("preferred_type_only", dict(require_article=False, require_preferred=True)),
        ("all_rows", dict(require_article=False, require_preferred=False)),
    ]
    for stage_name, flags in stages:
        matches_idx = [idx for idx, row in enumerate(rows) if matches(row, **flags)]
        if matches_idx:
            return matches_idx, stage_name
    return [], "empty"


def _score_bonus(row: dict[str, Any], query_row: dict[str, Any]) -> float:
    bonus = 0.0
    preferred_types = query_row.get("preferred_chunk_types") or []
    if row.get("chunk_type") in preferred_types:
        type_rank = preferred_types.index(row["chunk_type"])
        bonus += max(0.01, 0.04 - (0.01 * type_rank))

    if row.get("rule_id") and row["rule_id"] == query_row.get("rule_id"):
        bonus += 0.25
    if row.get("citation_label") == query_row.get("known_citation_label"):
        bonus += 0.08
    if row.get("rule_family") and row["rule_family"] == query_row.get("rule_family"):
        bonus += 0.03
    if row.get("logic_type") and row["logic_type"] == query_row.get("logic_type"):
        bonus += 0.02

    query_product = set(query_row.get("product_scope_hint") or [])
    row_product = _scope_tokens(row.get("product_scope"))
    if query_product and row_product and query_product.intersection(row_product):
        bonus += 0.02

    query_channel = set(query_row.get("channel_scope_hint") or [])
    row_channel = _scope_tokens(row.get("channel_scope"))
    if query_channel and row_channel and query_channel.intersection(row_channel):
        bonus += 0.02

    return bonus


@lru_cache(maxsize=4)
def _load_embedding_model(model_id: str, resolved_device: str) -> Any:
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise ImportError(
            "sentence-transformers is required for Chapter 4 retrieval. "
            "Install it with: pip install sentence-transformers"
        ) from exc

    return SentenceTransformer(model_id, device=resolved_device)


def _resolve_device(device: str | None) -> str:
    import torch

    if device:
        if device == "cuda" and not torch.cuda.is_available():
            return "cpu"
        return device
    return "cuda" if torch.cuda.is_available() else "cpu"


def _encode_texts(
    texts: list[str],
    *,
    model_id: str,
    batch_size: int,
    max_length: int,
    prefix: str,
    device: str | None,
) -> tuple[Any, str]:
    import numpy as np

    resolved_device = _resolve_device(device)
    model = _load_embedding_model(model_id, resolved_device)
    if hasattr(model, "max_seq_length"):
        model.max_seq_length = max_length

    prefixed_texts = [prefix + text for text in texts]
    embeddings = model.encode(
        prefixed_texts,
        batch_size=batch_size,
        show_progress_bar=False,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    return np.asarray(embeddings, dtype="float32"), resolved_device


def _embedding_text_prefix(model_id: str, *, text_role: str) -> str:
    normalized_model_id = model_id.lower()
    if "e5" in normalized_model_id:
        if text_role == "query":
            return "query: "
        if text_role == "passage":
            return "passage: "
    return ""


def _embedding_prefix_policy_label(model_id: str) -> str:
    return "e5_query_passage_prefix" if "e5" in model_id.lower() else "no_prefix"


def _embedding_prefix_note(model_id: str) -> str:
    if "e5" in model_id.lower():
        return "Queries and passages are encoded with E5-style text prefixes."
    return "Queries and passages are encoded without additional text prefixes."
