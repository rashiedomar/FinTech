from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from safeguard_ai.ch4_runtime import build_runtime_trace
from safeguard_ai.ch4_retrieval import (
    build_retrieval_queries_from_case,
    embedding_index_exists,
    retrieve_support_for_query,
)


@dataclass
class PostprocessPaths:
    parse_records_path: Path
    rule_pack_path: Path
    default_examples_dir: Path
    default_results_dir: Path


def default_postprocess_paths(repo_root: Path) -> PostprocessPaths:
    return PostprocessPaths(
        parse_records_path=repo_root / "data/parsed/ch4_fincpa/law_fincpa_main_ch4_clause_records.jsonl",
        rule_pack_path=repo_root / "data/finalized/ch4_fincpa/law_fincpa_main_ch4_layer4_mvp_rule_pack.jsonl",
        default_examples_dir=repo_root / "data/runtime/ch4_fincpa/examples",
        default_results_dir=repo_root / "data/runtime/ch4_fincpa/results",
    )


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def build_evidence_package(
    original_input: dict[str, Any],
    review_report: dict[str, Any],
    *,
    repo_root: Path,
) -> dict[str, Any]:
    paths = default_postprocess_paths(repo_root)
    parse_rows = load_jsonl(paths.parse_records_path)
    rule_rows = load_jsonl(paths.rule_pack_path)
    retrieval_queries = build_retrieval_queries_from_case(original_input, review_report)
    retrieval_query_by_rule_id = {row["rule_id"]: row for row in retrieval_queries}
    vector_index_available = embedding_index_exists(repo_root)

    parse_by_record = {row["record_id"]: row for row in parse_rows}
    article_context: dict[str, list[dict[str, Any]]] = {}
    for row in parse_rows:
        article_context.setdefault(row["article_id"], []).append(row)
    rules_by_id = {row["rule_id"]: row for row in rule_rows}

    evidence_items: list[dict[str, Any]] = []
    for result in review_report["rule_results"]:
        if result["status"] not in {"failed", "uncertain"}:
            continue
        rule = rules_by_id.get(result["rule_id"])
        if not rule:
            continue
        parent_clause = parse_by_record.get(rule["parent_record_id"])
        retrieval_query = retrieval_query_by_rule_id.get(result["rule_id"])
        retrieved_support = []
        retrieval_backend = None
        retrieval_mode = "static_layer4_plus_parsed_clause_context"
        if vector_index_available and retrieval_query:
            retrieval_result = retrieve_support_for_query(retrieval_query, repo_root=repo_root, top_k=5)
            retrieved_support = retrieval_result["results"]
            retrieval_backend = retrieval_result["backend"]
            retrieval_mode = "static_layer4_plus_vector_support"
        same_article_records = [
            {
                "record_id": row["record_id"],
                "paragraph_id": row["paragraph_id"],
                "page_start": row["page_start"],
                "normalized_text": row["normalized_text"],
                "is_parent_clause": row["record_id"] == rule["parent_record_id"],
            }
            for row in article_context.get(rule["article_id"], [])
        ]
        evidence_items.append(
            {
                "rule_id": result["rule_id"],
                "rule_status": result["status"],
                "severity": result["severity"],
                "logic_type": result["logic_type"],
                "rule_family": result["rule_family"],
                "reason": result["reason"],
                "finding_fields": result["finding_fields"],
                "field_evidence": result["evidence"],
                "legal_basis": result["legal_basis"],
                "parent_clause": {
                    "record_id": parent_clause["record_id"],
                    "page_start": parent_clause["page_start"],
                    "raw_text": parent_clause["raw_text"],
                    "normalized_text": parent_clause["normalized_text"],
                    "manual_verified": parent_clause["manual_verified"],
                }
                if parent_clause
                else None,
                "same_article_context": same_article_records,
                "delegated_detail_hint": ("대통령령" in rule["source_span_text"]) or ("대통령령" in rule["obligation_summary"]),
                "retrieval_mode": retrieval_mode,
                "retrieval_backend": retrieval_backend,
                "retrieved_support": retrieved_support,
            }
        )

    article_refs = sorted({item["legal_basis"]["citation_label"] for item in evidence_items})
    delegated_count = sum(1 for item in evidence_items if item["delegated_detail_hint"])
    retrieved_support_item_count = sum(len(item["retrieved_support"]) for item in evidence_items)

    return {
        "artifact_type": "ch4_evidence_package",
        "version": "0.1.0",
        "input_id": review_report["input_id"],
        "final_decision": review_report["final_decision"],
        "should_escalate": review_report["should_escalate"],
        "coverage_summary": {
            "triggered_rule_count": len(evidence_items),
            "citation_count": len(article_refs),
            "citations": article_refs,
            "delegated_detail_item_count": delegated_count,
            "vector_index_available": vector_index_available,
            "retrieved_support_item_count": retrieved_support_item_count,
        },
        "evidence_items": evidence_items,
    }


def build_llm_advisory_input(
    original_input: dict[str, Any],
    runtime_trace: dict[str, Any],
    evidence_package: dict[str, Any],
) -> dict[str, Any]:
    report = runtime_trace["review_report"]
    relevant_fields = sorted(
        {
            field_name
            for result in report["rule_results"]
            if result["status"] in {"failed", "uncertain"}
            for field_name in result["candidate_fields"]
        }
    )
    focused_sir = {field: runtime_trace["sir"]["fields"][field] for field in relevant_fields if field in runtime_trace["sir"]["fields"]}
    failed_rules = [
        {
            "rule_id": row["rule_id"],
            "reason": row["reason"],
            "severity": row["severity"],
            "summary": row["summary"],
            "finding_fields": row["finding_fields"],
            "citation_label": row["legal_basis"]["citation_label"],
        }
        for row in report["rule_results"]
        if row["status"] == "failed"
    ]
    uncertain_rules = [
        {
            "rule_id": row["rule_id"],
            "reason": row["reason"],
            "severity": row["severity"],
            "summary": row["summary"],
            "finding_fields": row["finding_fields"],
            "citation_label": row["legal_basis"]["citation_label"],
        }
        for row in report["rule_results"]
        if row["status"] == "uncertain"
    ]
    return {
        "artifact_type": "ch4_llm_advisory_input",
        "version": "0.1.0",
        "tasking": {
            "objective": "Explain the deterministic compliance result in plain language and provide conservative advisory support without changing the legal decision.",
            "llm_role": "explanation_and_advisory_only",
            "must_not_do": [
                "Do not override the deterministic final decision.",
                "Do not invent new legal citations beyond the supplied evidence package.",
                "Do not claim certainty when the deterministic engine returned uncertainty.",
            ],
            "expected_outputs": [
                "reviewer_summary",
                "plain_language_rationale",
                "remediation_actions",
                "conservative_rewrite_suggestion",
                "citation_list",
            ],
        },
        "case_context": {
            "input_id": original_input.get("input_id", report["input_id"]),
            "title": original_input.get("title", ""),
            "content_text": original_input.get("content_text", ""),
            "review_scope": runtime_trace["normalized_input"]["review_scope"],
            "product_scope_hint": runtime_trace["normalized_input"]["product_scope_hint"],
            "channel_scope_hint": runtime_trace["normalized_input"]["channel_scope_hint"],
            "business_role_hint": runtime_trace["normalized_input"]["business_role_hint"],
        },
        "deterministic_core": {
            "final_decision": report["final_decision"],
            "should_escalate": report["should_escalate"],
            "summary": report["summary"],
            "missing_sir_fields": report["missing_sir_fields"],
            "failed_rules": failed_rules,
            "uncertain_rules": uncertain_rules,
        },
        "sir_focus_fields": focused_sir,
        "evidence_package": evidence_package,
        "suggested_output_schema": {
            "reviewer_summary": "string",
            "plain_language_rationale": "string",
            "remediation_actions": ["string"],
            "conservative_rewrite_suggestion": "string",
            "citation_list": ["string"],
        },
    }


def build_human_review_packet(
    original_input: dict[str, Any],
    runtime_trace: dict[str, Any],
    evidence_package: dict[str, Any],
) -> dict[str, Any]:
    report = runtime_trace["review_report"]
    return {
        "artifact_type": "ch4_human_review_packet",
        "version": "0.1.0",
        "review_status": "pending_human_review",
        "input_id": original_input.get("input_id", report["input_id"]),
        "case_summary": {
            "title": original_input.get("title", ""),
            "content_text": original_input.get("content_text", ""),
            "final_decision_from_engine": report["final_decision"],
            "should_escalate": report["should_escalate"],
            "failed_rule_count": report["summary"]["failed_rule_count"],
            "uncertain_rule_count": report["summary"]["uncertain_rule_count"],
            "missing_sir_fields": report["missing_sir_fields"],
        },
        "reviewer_actions": [
            "approve",
            "approve_with_edits",
            "reject",
            "escalate",
        ],
        "required_reviewer_fields": [
            "reviewer_id",
            "decision",
            "reviewer_note",
        ],
        "draft_review_form": {
            "reviewer_id": "",
            "decision": "",
            "reviewer_note": "",
            "requested_edits": [],
            "linked_rule_ids": report["active_rule_ids"],
        },
        "evidence_summary": evidence_package["coverage_summary"],
        "triggered_citations": report["triggered_citations"],
    }


def render_bridge_summary(
    runtime_trace: dict[str, Any],
    evidence_package: dict[str, Any],
    llm_advisory_input: dict[str, Any],
    human_review_packet: dict[str, Any],
) -> str:
    lines = [
        f"# Workflow Bridge Summary: {runtime_trace['review_report']['input_id']}",
        "",
        f"- deterministic final decision: `{runtime_trace['review_report']['final_decision']}`",
        f"- escalate: `{str(runtime_trace['review_report']['should_escalate']).lower()}`",
        f"- evidence items: `{evidence_package['coverage_summary']['triggered_rule_count']}`",
        f"- citations: `{', '.join(evidence_package['coverage_summary']['citations']) or 'none'}`",
        "",
        "## Evidence Retrieval",
        "",
        "- built from triggered rule results",
        "- enriches static Layer 4 legal basis with parent clause text and same-article context",
        f"- vector support attached: `{str(evidence_package['coverage_summary']['vector_index_available']).lower()}`",
        f"- retrieved support rows: `{evidence_package['coverage_summary']['retrieved_support_item_count']}`",
        "",
        "## LLM Advisory Input",
        "",
        f"- content text included: `{bool(llm_advisory_input['case_context']['content_text'])}`",
        f"- failed rules passed to LLM: `{len(llm_advisory_input['deterministic_core']['failed_rules'])}`",
        f"- uncertain rules passed to LLM: `{len(llm_advisory_input['deterministic_core']['uncertain_rules'])}`",
        "",
        "## Human Review Packet",
        "",
        f"- review status: `{human_review_packet['review_status']}`",
        f"- reviewer actions: `{', '.join(human_review_packet['reviewer_actions'])}`",
        "",
    ]
    return "\n".join(lines) + "\n"


def build_postprocess_pipeline(
    original_input: dict[str, Any],
    *,
    repo_root: Path,
) -> dict[str, Any]:
    runtime_trace = build_runtime_trace(original_input, repo_root=repo_root)
    evidence_package = build_evidence_package(original_input, runtime_trace["review_report"], repo_root=repo_root)
    llm_advisory_input = build_llm_advisory_input(original_input, runtime_trace, evidence_package)
    human_review_packet = build_human_review_packet(original_input, runtime_trace, evidence_package)
    return {
        "runtime_trace": runtime_trace,
        "evidence_package": evidence_package,
        "llm_advisory_input": llm_advisory_input,
        "human_review_packet": human_review_packet,
        "bridge_summary_md": render_bridge_summary(
            runtime_trace,
            evidence_package,
            llm_advisory_input,
            human_review_packet,
        ),
    }
