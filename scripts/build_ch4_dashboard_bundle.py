#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
PARSE_PATH = ROOT_DIR / "data" / "parsed" / "ch4_fincpa" / "law_fincpa_main_ch4_clause_records.jsonl"
LAYER1_PATH = ROOT_DIR / "data" / "annotations" / "ch4_fincpa" / "law_fincpa_main_ch4_layer1_annotations.gemini.jsonl"
LAYER2_PATH = ROOT_DIR / "data" / "annotations" / "ch4_fincpa" / "law_fincpa_main_ch4_layer2_obligations.gemini.jsonl"
LAYER3_PATH = ROOT_DIR / "data" / "annotations" / "ch4_fincpa" / "law_fincpa_main_ch4_layer3_rule_candidates.gemini.jsonl"
LAYER4_RULES_PATH = ROOT_DIR / "data" / "finalized" / "ch4_fincpa" / "law_fincpa_main_ch4_layer4_mvp_rule_pack.jsonl"
LAYER4_SCHEMA_PATH = ROOT_DIR / "data" / "finalized" / "ch4_fincpa" / "law_fincpa_main_ch4_layer4_mvp_sir_schema.json"
LAYER4_REPORT_PATH = ROOT_DIR / "data" / "finalized" / "ch4_fincpa" / "law_fincpa_main_ch4_layer4_compile_report.json"
RETRIEVAL_CORPUS_PATH = ROOT_DIR / "data" / "retrieval" / "ch4_fincpa" / "ch4_embedding_corpus.jsonl"
RETRIEVAL_MANIFEST_PATH = ROOT_DIR / "data" / "retrieval" / "ch4_fincpa" / "ch4_embedding_manifest.json"
RETRIEVAL_QUERY_MANIFEST_PATH = ROOT_DIR / "data" / "retrieval" / "ch4_fincpa" / "ch4_example_retrieval_query_manifest.json"
RETRIEVAL_INDEX_MANIFEST_PATH = ROOT_DIR / "data" / "retrieval" / "ch4_fincpa" / "ch4_embedding_index_manifest.json"
OUTPUT_PATH = ROOT_DIR / "data" / "finalized" / "ch4_fincpa" / "law_fincpa_main_ch4_dashboard_bundle.json"
DASHBOARD_BUNDLE_JS_PATH = ROOT_DIR / "dashboard" / "ch4_fincpa" / "dashboard-bundle.js"


TOPIC_LABELS = {
    "general_principle": {"ko": "일반 원칙", "en": "General Principle"},
    "internal_control": {"ko": "내부통제", "en": "Internal Control"},
    "consumer_fit_assessment": {"ko": "적합성·적정성", "en": "Consumer Fit Assessment"},
    "explanation_duty": {"ko": "설명의무", "en": "Explanation Duty"},
    "advertising_compliance": {"ko": "광고 준수", "en": "Advertising Compliance"},
    "unfair_sales_practice": {"ko": "불공정 영업행위", "en": "Unfair Sales Practice"},
    "improper_solicitation": {"ko": "부당 권유", "en": "Improper Solicitation"},
    "other": {"ko": "기타", "en": "Other"},
}

OBLIGATION_MODE_LABELS = {
    "general_principle": {"ko": "원칙형", "en": "General Principle"},
    "required_action": {"ko": "행위 의무", "en": "Required Action"},
    "required_content": {"ko": "기재·고지 의무", "en": "Required Content"},
    "prohibited_action": {"ko": "금지 행위", "en": "Prohibited Action"},
    "workflow_control": {"ko": "절차·통제", "en": "Workflow Control"},
    "recordkeeping": {"ko": "기록 보존", "en": "Recordkeeping"},
}

PRODUCT_SCOPE_LABELS = {
    "general": {"ko": "공통", "en": "General"},
    "loan": {"ko": "대출", "en": "Loan"},
    "deposit": {"ko": "예금·적금", "en": "Deposit"},
    "investment": {"ko": "투자", "en": "Investment"},
    "insurance": {"ko": "보험", "en": "Insurance"},
    "multiple": {"ko": "복합", "en": "Multiple"},
    "general|investment": {"ko": "공통·투자", "en": "General|Investment"},
}

CHANNEL_SCOPE_LABELS = {
    "all_customer_facing": {"ko": "모든 대고객 채널", "en": "All Customer-Facing"},
    "advertising": {"ko": "광고", "en": "Advertising"},
    "contracting": {"ko": "계약 체결", "en": "Contracting"},
    "solicitation": {"ko": "권유", "en": "Solicitation"},
    "advisory": {"ko": "자문", "en": "Advisory"},
    "visit_sales|phone_sales": {"ko": "방문·전화 판매", "en": "Visit|Phone Sales"},
    "solicitation|contracting": {"ko": "권유·계약", "en": "Solicitation|Contracting"},
    "solicitation|visit_sales|phone_sales": {"ko": "권유·방문·전화", "en": "Solicitation|Visit|Phone"},
    "all_customer_facing|solicitation|contracting": {"ko": "전 채널·권유·계약", "en": "All CF|Solicitation|Contracting"},
    "internal_control": {"ko": "내부통제", "en": "Internal Control"},
}

TRIGGER_TYPE_LABELS = {
    "must_do": {"ko": "반드시 해야 함", "en": "Must Do"},
    "must_disclose": {"ko": "반드시 표시/설명", "en": "Must Disclose"},
    "must_not_do": {"ko": "하면 안 됨", "en": "Must Not Do"},
    "must_keep_record": {"ko": "기록 보존 필요", "en": "Must Keep Record"},
    "must_have_control": {"ko": "통제 체계 필요", "en": "Must Have Control"},
    "delegated_detail": {"ko": "하위 규정 필요", "en": "Delegated Detail"},
}

OPERATIONALITY_LABELS = {
    "direct_checkable": {"ko": "직접 점검 가능", "en": "Direct Checkable"},
    "needs_subrule_design": {"ko": "세부 규칙 설계 필요", "en": "Needs Subrule Design"},
    "delegated_to_decree": {"ko": "시행령·하위규정 의존", "en": "Delegated To Decree"},
}

RULE_FAMILY_LABELS = {
    "general_principle": {"ko": "일반 원칙", "en": "General Principle"},
    "suitability": {"ko": "적합성", "en": "Suitability"},
    "adequacy": {"ko": "적정성", "en": "Adequacy"},
    "explanation": {"ko": "설명의무", "en": "Explanation"},
    "advertising": {"ko": "광고", "en": "Advertising"},
    "unfair_sales": {"ko": "불공정 영업행위", "en": "Unfair Sales"},
    "solicitation": {"ko": "권유", "en": "Solicitation"},
    "contract_documents": {"ko": "계약서류", "en": "Contract Documents"},
    "internal_control": {"ko": "내부통제", "en": "Internal Control"},
    "recordkeeping": {"ko": "기록 보존", "en": "Recordkeeping"},
    "intermediary": {"ko": "대리·중개", "en": "Intermediary"},
    "advisory": {"ko": "자문", "en": "Advisory"},
}

LOGIC_TYPE_LABELS = {
    "required_presence": {"ko": "필수 정보 존재", "en": "Required Presence"},
    "prohibited_presence": {"ko": "금지 신호 존재", "en": "Prohibited Presence"},
    "required_process": {"ko": "필수 절차 존재", "en": "Required Process"},
    "required_record": {"ko": "필수 기록 존재", "en": "Required Record"},
    "required_response": {"ko": "필수 대응 존재", "en": "Required Response"},
    "delegated_detail": {"ko": "하위 규정 필요", "en": "Delegated Detail"},
    "principle_guardrail": {"ko": "원칙형 가드레일", "en": "Principle Guardrail"},
}

DETECTION_TARGET_LABELS = {
    "content_text": {"ko": "대고객 문구", "en": "Content Text"},
    "workflow_metadata": {"ko": "워크플로 메타데이터", "en": "Workflow Metadata"},
    "consumer_profile": {"ko": "소비자 프로필", "en": "Consumer Profile"},
    "document_bundle": {"ko": "문서 묶음", "en": "Document Bundle"},
    "record_system": {"ko": "기록 시스템", "en": "Record System"},
    "mixed": {"ko": "복합", "en": "Mixed"},
}

SIR_LINK_TYPE_LABELS = {
    "direct_content_field": {"ko": "콘텐츠 필드 직접 연결", "en": "Direct Content Field"},
    "direct_workflow_field": {"ko": "워크플로 필드 직접 연결", "en": "Direct Workflow Field"},
    "direct_record_field": {"ko": "기록 필드 직접 연결", "en": "Direct Record Field"},
    "derived_decision_field": {"ko": "파생 판단 필드", "en": "Derived Decision Field"},
    "delegated_external_detail": {"ko": "하위 규정 추가 필요", "en": "Delegated External Detail"},
    "principle_only": {"ko": "원칙형만 가능", "en": "Principle Only"},
}

EVIDENCE_SOURCE_LABELS = {
    "visible_content": {"ko": "보이는 콘텐츠", "en": "Visible Content"},
    "workflow_log": {"ko": "워크플로 로그", "en": "Workflow Log"},
    "consumer_profile_form": {"ko": "소비자 프로필 서식", "en": "Consumer Profile Form"},
    "explanation_form": {"ko": "설명 서식", "en": "Explanation Form"},
    "contract_document": {"ko": "계약 문서", "en": "Contract Document"},
    "record_archive": {"ko": "기록 보관소", "en": "Record Archive"},
    "decree_reference": {"ko": "시행령 참조", "en": "Decree Reference"},
    "mixed": {"ko": "복합", "en": "Mixed"},
}

FIELD_NAME_LABELS = {
    "consumer_type": {"ko": "소비자 유형", "en": "Consumer Type"},
    "consumer_profile": {"ko": "소비자 프로필", "en": "Consumer Profile"},
    "suitability_check": {"ko": "적합성 점검", "en": "Suitability Check"},
    "adequacy_check": {"ko": "적정성 점검", "en": "Adequacy Check"},
    "explanation_material": {"ko": "설명 자료", "en": "Explanation Material"},
    "explanation_confirmation": {"ko": "설명 확인", "en": "Explanation Confirmation"},
    "contract_document_delivery": {"ko": "계약 문서 제공", "en": "Contract Document Delivery"},
    "seller_identity": {"ko": "판매자 식별", "en": "Seller Identity"},
    "product_identity": {"ko": "상품 식별", "en": "Product Identity"},
    "product_core_terms": {"ko": "핵심 상품 조건", "en": "Product Core Terms"},
    "insurance_warning": {"ko": "보험 경고 문구", "en": "Insurance Warning"},
    "investment_warning": {"ko": "투자 경고 문구", "en": "Investment Warning"},
    "deposit_disclaimer": {"ko": "예금 면책 문구", "en": "Deposit Disclaimer"},
    "loan_conditions": {"ko": "대출 조건", "en": "Loan Conditions"},
    "loan_rate_basis": {"ko": "대출 금리 기준", "en": "Loan Rate Basis"},
    "loan_interest_timing": {"ko": "대출 이자 시기", "en": "Loan Interest Timing"},
    "loan_costs": {"ko": "대출 비용", "en": "Loan Costs"},
    "solicitation_purpose": {"ko": "권유 목적", "en": "Solicitation Purpose"},
    "representative_identity": {"ko": "담당자 식별", "en": "Representative Identity"},
    "staff_registry": {"ko": "인력 등록부", "en": "Staff Registry"},
    "internal_control_standard": {"ko": "내부통제기준", "en": "Internal Control Standard"},
    "activity_record": {"ko": "활동 기록", "en": "Activity Record"},
    "record_integrity_control": {"ko": "기록 무결성 통제", "en": "Record Integrity Control"},
    "access_request": {"ko": "열람 요청", "en": "Access Request"},
    "access_response": {"ko": "열람 응답", "en": "Access Response"},
    "advisory_independence": {"ko": "자문 독립성", "en": "Advisory Independence"},
    "intermediary_status": {"ko": "대리·중개 상태", "en": "Intermediary Status"},
    "prohibited_claim_signal": {"ko": "금지 주장 신호", "en": "Prohibited Claim Signal"},
    "fairness_guardrail": {"ko": "공정성 가드레일", "en": "Fairness Guardrail"},
}


def load_jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def label_map_value(mapping: dict[str, dict[str, str]], value: str) -> dict[str, str]:
    return mapping.get(value, {"ko": value, "en": value})


def list_labels(mapping: dict[str, dict[str, str]], value: str) -> list[dict]:
    parts = [part.strip() for part in str(value).split("|") if part.strip()]
    return [label_map_value(mapping, part) for part in parts]


def compact_counter(rows: list[dict], key: str) -> dict[str, int]:
    return dict(Counter(row[key] for row in rows if row.get(key)))


def build_layer_explanations() -> list[dict]:
    return [
        {
            "layer_id": "parse",
            "title_ko": "Layer 0. 파싱",
            "title_en": "Layer 0. Parsing",
            "meaning_ko": "공식 PDF를 조항 단위로 잘라서 원문과 정규화 텍스트를 만든 단계",
            "meaning_en": "Official PDF segmented into clause-level source records with raw and normalized text.",
        },
        {
            "layer_id": "layer1",
            "title_ko": "Layer 1. 조항 메타데이터",
            "title_en": "Layer 1. Clause Metadata",
            "meaning_ko": "각 조항이 어떤 주제인지, 어떤 상품군인지, 분해가 필요한지 붙인 단계",
            "meaning_en": "High-level clause metadata such as topic, scope, and whether decomposition is needed.",
        },
        {
            "layer_id": "layer2",
            "title_ko": "Layer 2. 의무 분해",
            "title_en": "Layer 2. Obligation Decomposition",
            "meaning_ko": "한 조항 안의 여러 의무를 더 작은 단위로 분해한 단계",
            "meaning_en": "One clause split into smaller legal obligation units.",
        },
        {
            "layer_id": "layer3",
            "title_ko": "Layer 3. 규칙/SIR 후보",
            "title_en": "Layer 3. Rule and SIR Candidates",
            "meaning_ko": "각 의무를 미래 규칙과 SIR 필드 후보로 연결한 단계",
            "meaning_en": "Each obligation mapped to a future rule shape and candidate SIR fields.",
        },
        {
            "layer_id": "layer4",
            "title_ko": "Layer 4. 최종 MVP 고정",
            "title_en": "Layer 4. Final MVP Freeze",
            "meaning_ko": "Layer 3 후보 중 ready_for_v1=yes만 골라 MVP 규칙팩과 SIR 스키마로 고정한 단계",
            "meaning_en": "Only ready_for_v1=yes candidates included in the frozen MVP rule pack and SIR schema.",
        },
        {
            "layer_id": "retrieval",
            "title_ko": "Layer 5. 임베딩 검색 코퍼스",
            "title_en": "Layer 5. Embedding Retrieval Corpus",
            "meaning_ko": "제4장 조항과 MVP 규칙을 임베딩 가능한 검색 청크로 구성하고, 실패 규칙별 검색 쿼리를 준비한 단계",
            "meaning_en": "Chapter 4 clauses and MVP rules transformed into embedding-ready retrieval chunks, with one retrieval query prepared per failed rule.",
        },
    ]


def main() -> None:
    parse_rows = load_jsonl(PARSE_PATH)
    layer1_rows = load_jsonl(LAYER1_PATH)
    layer2_rows = load_jsonl(LAYER2_PATH)
    layer3_rows = load_jsonl(LAYER3_PATH)
    layer4_rows = load_jsonl(LAYER4_RULES_PATH)
    layer4_schema = json.loads(LAYER4_SCHEMA_PATH.read_text(encoding="utf-8"))
    layer4_report = json.loads(LAYER4_REPORT_PATH.read_text(encoding="utf-8"))
    retrieval_rows = load_jsonl(RETRIEVAL_CORPUS_PATH) if RETRIEVAL_CORPUS_PATH.exists() else []
    retrieval_manifest = load_json(RETRIEVAL_MANIFEST_PATH) if RETRIEVAL_MANIFEST_PATH.exists() else {}
    retrieval_query_manifest = load_json(RETRIEVAL_QUERY_MANIFEST_PATH) if RETRIEVAL_QUERY_MANIFEST_PATH.exists() else {}
    retrieval_index_manifest = load_json(RETRIEVAL_INDEX_MANIFEST_PATH) if RETRIEVAL_INDEX_MANIFEST_PATH.exists() else {}

    layer1_by_record = {row["record_id"]: row for row in layer1_rows}
    layer2_by_parent: dict[str, list[dict]] = defaultdict(list)
    for row in layer2_rows:
        layer2_by_parent[row["parent_record_id"]].append(row)
    layer3_by_parent: dict[str, list[dict]] = defaultdict(list)
    for row in layer3_rows:
        layer3_by_parent[row["parent_record_id"]].append(row)
    layer4_by_parent: dict[str, list[dict]] = defaultdict(list)
    for row in layer4_rows:
        layer4_by_parent[row["parent_record_id"]].append(row)
    retrieval_by_parent: dict[str, list[dict]] = defaultdict(list)
    retrieval_by_article: dict[str, list[dict]] = defaultdict(list)
    for row in retrieval_rows:
        if row.get("parent_record_id"):
            retrieval_by_parent[row["parent_record_id"]].append(row)
        if row.get("article_id"):
            retrieval_by_article[row["article_id"]].append(row)

    clauses = []
    article_options = []

    for row in parse_rows:
        record_id = row["record_id"]
        l1 = layer1_by_record.get(record_id)
        l2_list = sorted(layer2_by_parent.get(record_id, []), key=lambda item: (item["obligation_order"], item["obligation_id"]))
        l3_list = sorted(layer3_by_parent.get(record_id, []), key=lambda item: item["source_obligation_id"])
        l4_list = sorted(layer4_by_parent.get(record_id, []), key=lambda item: item["rule_id"])

        sir_fields = sorted({field for rule in l4_list for field in rule["sir_candidate_fields"]})
        clause = {
            "record_id": record_id,
            "article_id": row["article_id"],
            "paragraph_id": row["paragraph_id"],
            "article_title": row["article_title"],
            "section_id": row["section_id"],
            "section_title": row["section_title"],
            "page_start": row["page_start"],
            "raw_text": row["raw_text"],
            "normalized_text": row["normalized_text"],
            "parse_summary": {
                "source_path": row["source_path"],
                "parse_method": row["parse_method"],
                "manual_verified": row["manual_verified"],
            },
            "layer1": None,
            "layer2": [],
            "layer3": [],
            "layer4": [],
            "retrieval": {
                "direct_chunks": [],
                "article_chunks": [],
                "summary": {
                    "total_related_chunk_count": 0,
                    "direct_chunk_count": 0,
                    "article_chunk_count": 0,
                    "chunk_type_counts": {},
                    "vector_index_ready": bool(retrieval_index_manifest.get("index_status") == "ready"),
                },
            },
            "summary": {
                "layer2_count": len(l2_list),
                "layer3_count": len(l3_list),
                "layer4_count": len(l4_list),
                "sir_field_count": len(sir_fields),
                "sir_fields": sir_fields,
            },
        }
        if l1:
            clause["layer1"] = {
                **l1,
                "topic_family_label": label_map_value(TOPIC_LABELS, l1["topic_family"]),
                "obligation_mode_label": label_map_value(OBLIGATION_MODE_LABELS, l1["obligation_mode"]),
                "product_scope_labels": list_labels(PRODUCT_SCOPE_LABELS, l1["product_scope"]),
                "channel_scope_labels": list_labels(CHANNEL_SCOPE_LABELS, l1["channel_scope"]),
            }
        for item in l2_list:
            clause["layer2"].append(
                {
                    **item,
                    "obligation_mode_label": label_map_value(OBLIGATION_MODE_LABELS, item["obligation_mode"]),
                    "product_scope_labels": list_labels(PRODUCT_SCOPE_LABELS, item["product_scope"]),
                    "channel_scope_labels": list_labels(CHANNEL_SCOPE_LABELS, item["channel_scope"]),
                    "trigger_type_label": label_map_value(TRIGGER_TYPE_LABELS, item["trigger_type"]),
                    "operationality_label": label_map_value(OPERATIONALITY_LABELS, item["operationality"]),
                }
            )
        for item in l3_list:
            clause["layer3"].append(
                {
                    **item,
                    "rule_family_label": label_map_value(RULE_FAMILY_LABELS, item["rule_family"]),
                    "logic_type_label": label_map_value(LOGIC_TYPE_LABELS, item["logic_type"]),
                    "detection_target_label": label_map_value(DETECTION_TARGET_LABELS, item["detection_target"]),
                    "sir_link_type_label": label_map_value(SIR_LINK_TYPE_LABELS, item["sir_link_type"]),
                    "evidence_source_label": label_map_value(EVIDENCE_SOURCE_LABELS, item["evidence_source"]),
                    "sir_candidate_field_labels": [label_map_value(FIELD_NAME_LABELS, field) for field in item["sir_candidate_fields"].split("|") if field],
                }
            )
        for item in l4_list:
            clause["layer4"].append(
                {
                    **item,
                    "rule_family_label": label_map_value(RULE_FAMILY_LABELS, item["rule_family"]),
                    "logic_type_label": label_map_value(LOGIC_TYPE_LABELS, item["logic_type"]),
                    "detection_target_label": label_map_value(DETECTION_TARGET_LABELS, item["detection_target"]),
                    "sir_link_type_label": label_map_value(SIR_LINK_TYPE_LABELS, item["sir_link_type"]),
                    "evidence_source_label": label_map_value(EVIDENCE_SOURCE_LABELS, item["evidence_source"]),
                    "sir_candidate_field_labels": [label_map_value(FIELD_NAME_LABELS, field) for field in item["sir_candidate_fields"]],
                    "product_scope_labels": list_labels(PRODUCT_SCOPE_LABELS, item["product_scope"]),
                    "channel_scope_labels": list_labels(CHANNEL_SCOPE_LABELS, item["channel_scope"]),
                }
            )

        direct_retrieval_rows = sorted(
            retrieval_by_parent.get(record_id, []),
            key=lambda item: (item["chunk_type"], item["chunk_id"]),
        )
        article_retrieval_rows = sorted(
            [
                item for item in retrieval_by_article.get(row["article_id"], [])
                if item["chunk_type"] == "article_rollup"
            ],
            key=lambda item: item["chunk_id"],
        )
        direct_chunks = [
            {
                "chunk_id": item["chunk_id"],
                "chunk_type": item["chunk_type"],
                "citation_label": item["citation_label"],
                "rule_id": item["rule_id"],
                "rule_family_label": label_map_value(RULE_FAMILY_LABELS, item["rule_family"]) if item["rule_family"] else None,
                "logic_type_label": label_map_value(LOGIC_TYPE_LABELS, item["logic_type"]) if item["logic_type"] else None,
                "delegated_detail_hint": item["delegated_detail_hint"],
                "retrieval_text_preview": item["retrieval_text"][:480],
            }
            for item in direct_retrieval_rows
        ]
        article_chunks = [
            {
                "chunk_id": item["chunk_id"],
                "chunk_type": item["chunk_type"],
                "citation_label": item["citation_label"],
                "delegated_detail_hint": item["delegated_detail_hint"],
                "retrieval_text_preview": item["retrieval_text"][:480],
            }
            for item in article_retrieval_rows
        ]
        chunk_type_counts = Counter(
            [item["chunk_type"] for item in direct_retrieval_rows] + [item["chunk_type"] for item in article_retrieval_rows]
        )
        clause["retrieval"] = {
            "direct_chunks": direct_chunks,
            "article_chunks": article_chunks,
            "summary": {
                "total_related_chunk_count": len(direct_chunks) + len(article_chunks),
                "direct_chunk_count": len(direct_chunks),
                "article_chunk_count": len(article_chunks),
                "chunk_type_counts": dict(chunk_type_counts),
                "vector_index_ready": bool(retrieval_index_manifest.get("index_status") == "ready"),
            },
        }
        article_options.append(
            {
                "record_id": record_id,
                "article_id": row["article_id"],
                "paragraph_id": row["paragraph_id"],
                "article_title": row["article_title"],
                "section_title": row["section_title"],
                "layer4_count": len(l4_list),
                "topic_family": l1["topic_family"] if l1 else "",
            }
        )
        clauses.append(clause)

    field_catalog = []
    for field in layer4_schema["fields"]:
        field_catalog.append(
            {
                **field,
                "field_label": label_map_value(FIELD_NAME_LABELS, field["field_name"]),
                "field_group_label": label_map_value(DETECTION_TARGET_LABELS, field["field_group"]),
                "rule_family_labels": [label_map_value(RULE_FAMILY_LABELS, value) for value in field["rule_families"]],
            }
        )

    bundle = {
        "meta": {
            "title_ko": "금융소비자보호법 제4장 데이터 구조 대시보드",
            "title_en": "FCPA Chapter 4 Data Structure Dashboard",
            "source_pdf": str(PARSE_PATH.parents[2] / "raw" / "official" / "law_fincpa_main_2026-01-02.pdf"),
            "layer_explanations": build_layer_explanations(),
        },
        "overview": {
            "parse_clause_count": len(parse_rows),
            "layer1_clause_count": len(layer1_rows),
            "layer2_obligation_count": len(layer2_rows),
            "layer3_candidate_count": len(layer3_rows),
            "layer4_rule_count": len(layer4_rows),
            "layer4_field_count": len(field_catalog),
            "retrieval_chunk_count": len(retrieval_rows),
            "retrieval_query_count": retrieval_query_manifest.get("query_count", 0),
            "retrieval_index_status": retrieval_index_manifest.get("index_status", "not_built"),
            "retrieval_model_id": retrieval_index_manifest.get("model_id", ""),
            "retrieval_chunk_type_counts": retrieval_manifest.get("chunk_type_counts", {}),
            "topic_family_counts": compact_counter(layer1_rows, "topic_family"),
            "layer4_rule_family_counts": layer4_report["rule_family_counts"],
            "layer4_logic_type_counts": layer4_report["logic_type_counts"],
            "layer4_field_group_counts": layer4_report["field_group_counts"],
        },
        "retrieval": {
            "manifest": retrieval_manifest,
            "query_manifest": retrieval_query_manifest,
            "index_manifest": retrieval_index_manifest,
        },
        "catalogs": {
            "articles": article_options,
            "field_catalog": field_catalog,
        },
        "clauses": clauses,
    }

    OUTPUT_PATH.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    DASHBOARD_BUNDLE_JS_PATH.write_text(
        "window.__CH4_DASHBOARD_BUNDLE__ = " + json.dumps(bundle, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "output": str(OUTPUT_PATH.relative_to(ROOT_DIR)),
                "embedded_bundle_js": str(DASHBOARD_BUNDLE_JS_PATH.relative_to(ROOT_DIR)),
                "clauses": len(clauses),
                "fields": len(field_catalog),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
