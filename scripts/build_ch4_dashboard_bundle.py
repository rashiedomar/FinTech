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


def strip_keys(row: dict, keys: set[str]) -> dict:
    return {key: value for key, value in row.items() if key not in keys}


def build_field_description_ko(field: dict) -> str:
    field_label = label_map_value(FIELD_NAME_LABELS, field["field_name"])["ko"]
    field_group = label_map_value(DETECTION_TARGET_LABELS, field["field_group"])["ko"]
    families = [label_map_value(RULE_FAMILY_LABELS, value)["ko"] for value in field["rule_families"]]
    family_text = ", ".join(families) if families else "관련"
    article_text = ", ".join(field["article_refs"]) if field.get("article_refs") else ""
    base = f"{field_label} 필드는 {field_group} 영역에서 확인하며 {family_text} 규칙과 연결됩니다."
    if article_text:
        return f"{base} 관련 조항은 {article_text}입니다."
    return base


def build_layer_explanations() -> list[dict]:
    return [
        {
            "layer_id": "parse",
            "title_ko": "0단계. 파싱",
            "title_en": "0단계. 파싱",
            "meaning_ko": "공식 PDF를 조항 단위로 잘라서 원문과 정규화 텍스트를 만든 단계",
            "meaning_en": "공식 PDF를 조항 단위로 잘라서 원문과 정규화 텍스트를 만든 단계",
        },
        {
            "layer_id": "layer1",
            "title_ko": "1단계. 조항 메타데이터",
            "title_en": "1단계. 조항 메타데이터",
            "meaning_ko": "각 조항이 어떤 주제인지, 어떤 상품군인지, 분해가 필요한지 붙인 단계",
            "meaning_en": "각 조항이 어떤 주제인지, 어떤 상품군인지, 분해가 필요한지 붙인 단계",
        },
        {
            "layer_id": "layer2",
            "title_ko": "2단계. 의무 분해",
            "title_en": "2단계. 의무 분해",
            "meaning_ko": "한 조항 안의 여러 의무를 더 작은 단위로 분해한 단계",
            "meaning_en": "한 조항 안의 여러 의무를 더 작은 단위로 분해한 단계",
        },
        {
            "layer_id": "layer3",
            "title_ko": "3단계. 규칙/SIR 후보",
            "title_en": "3단계. 규칙/SIR 후보",
            "meaning_ko": "각 의무를 미래 규칙과 SIR 필드 후보로 연결한 단계",
            "meaning_en": "각 의무를 미래 규칙과 SIR 필드 후보로 연결한 단계",
        },
        {
            "layer_id": "layer4",
            "title_ko": "4단계. 1차 규칙 확정",
            "title_en": "4단계. 1차 규칙 확정",
            "meaning_ko": "3단계 후보 중 1차 반영 대상으로 확정된 항목만 골라 규칙팩과 SIR 스키마로 고정한 단계",
            "meaning_en": "3단계 후보 중 1차 반영 대상으로 확정된 항목만 골라 규칙팩과 SIR 스키마로 고정한 단계",
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
            "summary": {
                "layer2_count": len(l2_list),
                "layer3_count": len(l3_list),
                "layer4_count": len(l4_list),
                "sir_field_count": len(sir_fields),
                "sir_fields": sir_fields,
            },
        }
        if l1:
            l1_clean = strip_keys(
                l1,
                {
                    "reviewer_note",
                    "gemini_model",
                    "gemini_confidence",
                    "gemini_reasoning_summary",
                },
            )
            clause["layer1"] = {
                **l1_clean,
                "topic_family_label": label_map_value(TOPIC_LABELS, l1_clean["topic_family"]),
                "obligation_mode_label": label_map_value(OBLIGATION_MODE_LABELS, l1_clean["obligation_mode"]),
                "product_scope_labels": list_labels(PRODUCT_SCOPE_LABELS, l1_clean["product_scope"]),
                "channel_scope_labels": list_labels(CHANNEL_SCOPE_LABELS, l1_clean["channel_scope"]),
            }
        for item in l2_list:
            item_clean = strip_keys(
                item,
                {
                    "reviewer_note",
                    "gemini_model",
                    "gemini_confidence",
                    "gemini_reasoning_summary",
                    "obligation_summary",
                },
            )
            clause["layer2"].append(
                {
                    **item_clean,
                    "obligation_mode_label": label_map_value(OBLIGATION_MODE_LABELS, item_clean["obligation_mode"]),
                    "product_scope_labels": list_labels(PRODUCT_SCOPE_LABELS, item_clean["product_scope"]),
                    "channel_scope_labels": list_labels(CHANNEL_SCOPE_LABELS, item_clean["channel_scope"]),
                    "trigger_type_label": label_map_value(TRIGGER_TYPE_LABELS, item_clean["trigger_type"]),
                    "operationality_label": label_map_value(OPERATIONALITY_LABELS, item_clean["operationality"]),
                }
            )
        for item in l3_list:
            item_clean = strip_keys(
                item,
                {
                    "reviewer_note",
                    "gemini_model",
                    "gemini_confidence",
                    "gemini_reasoning_summary",
                    "obligation_summary",
                    "rule_candidate_summary",
                },
            )
            clause["layer3"].append(
                {
                    **item_clean,
                    "rule_family_label": label_map_value(RULE_FAMILY_LABELS, item_clean["rule_family"]),
                    "logic_type_label": label_map_value(LOGIC_TYPE_LABELS, item_clean["logic_type"]),
                    "detection_target_label": label_map_value(DETECTION_TARGET_LABELS, item_clean["detection_target"]),
                    "sir_link_type_label": label_map_value(SIR_LINK_TYPE_LABELS, item_clean["sir_link_type"]),
                    "evidence_source_label": label_map_value(EVIDENCE_SOURCE_LABELS, item_clean["evidence_source"]),
                    "sir_candidate_field_labels": [label_map_value(FIELD_NAME_LABELS, field) for field in item_clean["sir_candidate_fields"].split("|") if field],
                }
            )
        for item in l4_list:
            item_clean = strip_keys(
                item,
                {
                    "reviewer_note",
                    "obligation_summary",
                    "rule_candidate_summary",
                    "evaluation_hint",
                },
            )
            clause["layer4"].append(
                {
                    **item_clean,
                    "rule_family_label": label_map_value(RULE_FAMILY_LABELS, item_clean["rule_family"]),
                    "logic_type_label": label_map_value(LOGIC_TYPE_LABELS, item_clean["logic_type"]),
                    "detection_target_label": label_map_value(DETECTION_TARGET_LABELS, item_clean["detection_target"]),
                    "sir_link_type_label": label_map_value(SIR_LINK_TYPE_LABELS, item_clean["sir_link_type"]),
                    "evidence_source_label": label_map_value(EVIDENCE_SOURCE_LABELS, item_clean["evidence_source"]),
                    "sir_candidate_field_labels": [label_map_value(FIELD_NAME_LABELS, field) for field in item_clean["sir_candidate_fields"]],
                    "product_scope_labels": list_labels(PRODUCT_SCOPE_LABELS, item_clean["product_scope"]),
                    "channel_scope_labels": list_labels(CHANNEL_SCOPE_LABELS, item_clean["channel_scope"]),
                }
            )

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
                **{key: value for key, value in field.items() if key != "description"},
                "description_ko": build_field_description_ko(field),
                "field_label": label_map_value(FIELD_NAME_LABELS, field["field_name"]),
                "field_group_label": label_map_value(DETECTION_TARGET_LABELS, field["field_group"]),
                "rule_family_labels": [label_map_value(RULE_FAMILY_LABELS, value) for value in field["rule_families"]],
            }
        )

    bundle = {
        "meta": {
            "title_ko": "금융소비자보호법 제4장 데이터 구조 대시보드",
            "title_en": "금융소비자보호법 제4장 데이터 구조 대시보드",
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
            "topic_family_counts": compact_counter(layer1_rows, "topic_family"),
            "layer4_rule_family_counts": layer4_report["rule_family_counts"],
            "layer4_logic_type_counts": layer4_report["logic_type_counts"],
            "layer4_field_group_counts": layer4_report["field_group_counts"],
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
