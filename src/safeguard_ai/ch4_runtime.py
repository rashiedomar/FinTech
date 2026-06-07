from __future__ import annotations

import json
import re
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any


STATUS_VALUES = {"present", "not_evidenced", "not_applicable", "uncertain"}
NEGATIVE_SIGNAL_FIELDS = {"prohibited_claim_signal", "fairness_guardrail"}

REVIEW_SCOPE_TARGETS = {
    "content_only": {"content_text", "document_bundle"},
    "workflow_only": {"workflow_metadata", "consumer_profile"},
    "record_only": {"record_system"},
    "full": {"content_text", "document_bundle", "workflow_metadata", "consumer_profile", "record_system"},
}

FIELD_GROUP_TARGET = {
    "content_text": "content_text",
    "workflow_metadata": "workflow_metadata",
    "record_system": "record_system",
}

FIELD_SOURCE_PRIORITY = {
    "default": 0,
    "context_scope": 1,
    "heuristic": 2,
    "workflow_metadata": 3,
    "record_metadata": 3,
    "content_metadata": 3,
    "field_inputs": 4,
}

PRODUCT_KEYWORDS = {
    "loan": ["대출", "금리", "중도상환", "상환", "연체이자", "한도", "가산금리", "기준금리"],
    "deposit": ["예금", "적금", "정기예금", "예금자보호", "이자지급", "만기"],
    "investment": ["투자", "펀드", "ETF", "주식", "채권", "수익률", "원금손실", "집합투자"],
    "insurance": ["보험", "보험료", "해약환급금", "면책", "기존계약", "보험계약"],
}

CHANNEL_VALUES = {
    "all_customer_facing",
    "advertising",
    "solicitation",
    "contracting",
    "advisory",
    "visit_sales",
    "phone_sales",
    "internal_control",
}

SELLER_PATTERNS = [
    r"토스뱅크",
    r"카카오뱅크",
    r"케이뱅크",
    r"KB국민은행",
    r"국민은행",
    r"신한은행",
    r"하나은행",
    r"우리은행",
    r"NH농협은행",
    r"농협은행",
    r"IBK기업은행",
    r"기업은행",
    r"부산은행",
    r"대구은행",
    r"광주은행",
    r"전북은행",
    r"경남은행",
    r"수협은행",
    r"SC제일은행",
    r"한국씨티은행",
    r"삼성화재",
    r"현대해상",
    r"메리츠화재",
    r"DB손해보험",
    r"미래에셋증권",
    r"한국투자증권",
    r"NH투자증권",
    r"키움증권",
    r"신한투자증권",
    r"하나증권",
    r"KB증권",
    r"삼성증권",
    r"[가-힣A-Za-z0-9]+은행",
    r"[가-힣A-Za-z0-9]+증권",
    r"[가-힣A-Za-z0-9]+보험",
]

PROHIBITED_SIGNAL_PATTERNS = {
    "principal_guarantee": [r"원금\s*보장", r"원금보장"],
    "guaranteed_return": [r"확정\s*수익", r"수익\s*보장", r"보장\s*수익"],
    "no_loss": [r"손실\s*없", r"손해\s*없"],
    "risk_free": [r"무위험", r"안전한\s*투자"],
    "absolute_claim": [r"반드시", r"무조건"],
    "oversimplification": [r"쉽고\s*간편", r"간편하게", r"부담\s*없이"],
    "universal_eligibility": [r"누구나", r"모두", r"전원"],
    "guaranteed_approval": [r"즉시\s*승인", r"무조건\s*승인", r"승인\s*보장"],
    "absolute_numeric_claim": [r"100%"],
}

WARNING_PATTERNS = {
    "deposit_disclaimer": [r"예금자보호", r"보호한도", r"예금보험공사"],
    "investment_warning": [r"원금\s*손실", r"손실\s*가능", r"예금자보호\s*대상\s*아님", r"실적배당"],
    "insurance_warning": [r"면책", r"해약환급금", r"기존계약", r"보장내용", r"보험료"],
}

LOAN_PATTERNS = {
    "loan_conditions": [r"한도", r"상환", r"기간", r"만기", r"거치", r"분할", r"원리금", r"중도상환"],
    "loan_rate_basis": [r"\d+(?:\.\d+)?\s*%", r"금리", r"기준금리", r"가산금리", r"연\s*\d"],
    "loan_interest_timing": [r"이자\s*부과", r"이자\s*납입", r"매월", r"월납", r"상환일", r"매달"],
    "loan_costs": [r"수수료", r"비용", r"연체이자", r"인지세", r"중도상환수수료"],
}


@dataclass
class RuntimePaths:
    rule_pack_path: Path
    sir_schema_path: Path


def default_runtime_paths(repo_root: Path) -> RuntimePaths:
    return RuntimePaths(
        rule_pack_path=repo_root / "data/finalized/ch4_fincpa/law_fincpa_main_ch4_layer4_mvp_rule_pack.jsonl",
        sir_schema_path=repo_root / "data/finalized/ch4_fincpa/law_fincpa_main_ch4_layer4_mvp_sir_schema.json",
    )


def load_sir_schema(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_rule_pack(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def normalize_runtime_input(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = deepcopy(payload)
    normalized.setdefault("input_id", "unnamed_input")
    normalized.setdefault("title", "")
    normalized.setdefault("content_text", "")
    normalized.setdefault("review_scope", "content_only")
    normalized.setdefault("product_scope_hint", [])
    normalized.setdefault("channel_scope_hint", [])
    normalized.setdefault("field_inputs", {})
    normalized.setdefault("content_metadata", {})
    normalized.setdefault("workflow_metadata", {})
    normalized.setdefault("record_metadata", {})
    normalized.setdefault("business_role_hint", "")
    normalized.setdefault("include_rule_families", [])
    normalized.setdefault("exclude_rule_families", [])

    if normalized["review_scope"] not in REVIEW_SCOPE_TARGETS:
        raise ValueError(f"Unsupported review_scope: {normalized['review_scope']}")

    normalized["product_scope_hint"] = _normalize_scope_list(normalized["product_scope_hint"])
    normalized["channel_scope_hint"] = _normalize_scope_list(normalized["channel_scope_hint"])
    normalized["channel_scope_hint"] = [scope for scope in normalized["channel_scope_hint"] if scope in CHANNEL_VALUES]
    normalized["include_rule_families"] = _normalize_scope_list(normalized["include_rule_families"])
    normalized["exclude_rule_families"] = _normalize_scope_list(normalized["exclude_rule_families"])
    if not normalized["channel_scope_hint"]:
        normalized["channel_scope_hint"] = _infer_channel_scopes(normalized)
    if not normalized["product_scope_hint"]:
        normalized["product_scope_hint"] = _infer_product_scopes(_combine_text(normalized))
    if not normalized["product_scope_hint"]:
        normalized["product_scope_hint"] = ["general"]
    if not normalized["business_role_hint"]:
        normalized["business_role_hint"] = _infer_business_role(normalized)
    return normalized


def extract_sir(payload: dict[str, Any], sir_schema: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_runtime_input(payload)
    text = _combine_text(normalized)
    context = {
        "review_scope": normalized["review_scope"],
        "active_targets": REVIEW_SCOPE_TARGETS[normalized["review_scope"]],
        "product_scope_hint": normalized["product_scope_hint"],
        "channel_scope_hint": normalized["channel_scope_hint"],
        "business_role_hint": normalized["business_role_hint"],
        "include_rule_families": normalized["include_rule_families"],
        "exclude_rule_families": normalized["exclude_rule_families"],
    }

    field_states = {field["field_name"]: _default_field_state(field) for field in sir_schema["fields"]}
    _mark_scope_not_applicable(field_states, context)
    _mark_product_not_applicable(field_states, context)
    _mark_channel_not_applicable(field_states, context)

    _apply_explicit_field_inputs(field_states, normalized.get("field_inputs", {}))
    _apply_metadata_field_inputs(field_states, normalized.get("content_metadata", {}), "content_metadata")
    _apply_metadata_field_inputs(field_states, normalized.get("workflow_metadata", {}), "workflow_metadata")
    _apply_metadata_field_inputs(field_states, normalized.get("record_metadata", {}), "record_metadata")
    _apply_content_heuristics(field_states, normalized, text)
    _apply_derived_states(field_states, context)

    cleaned_fields = {name: _strip_internal_state(state) for name, state in field_states.items()}
    return {
        "input_id": normalized["input_id"],
        "context": context,
        "fields": cleaned_fields,
    }


def evaluate_runtime_input(
    payload: dict[str, Any],
    *,
    repo_root: Path,
    rule_pack_path: Path | None = None,
    sir_schema_path: Path | None = None,
) -> dict[str, Any]:
    trace = build_runtime_trace(
        payload,
        repo_root=repo_root,
        rule_pack_path=rule_pack_path,
        sir_schema_path=sir_schema_path,
    )
    return trace["review_report"]


def build_runtime_trace(
    payload: dict[str, Any],
    *,
    repo_root: Path,
    rule_pack_path: Path | None = None,
    sir_schema_path: Path | None = None,
) -> dict[str, Any]:
    paths = default_runtime_paths(repo_root)
    normalized_input = normalize_runtime_input(payload)
    rules = load_rule_pack(rule_pack_path or paths.rule_pack_path)
    schema = load_sir_schema(sir_schema_path or paths.sir_schema_path)
    sir = extract_sir(normalized_input, schema)
    results = [evaluate_rule(rule, sir["fields"], sir["context"]) for rule in rules]
    report = build_review_report(normalized_input, sir, results, rules, schema)
    applicable_rules = [row for row in results if row["status"] != "not_applicable"]
    failing_rules = [row for row in applicable_rules if row["status"] == "failed"]
    uncertain_rules = [row for row in applicable_rules if row["status"] == "uncertain"]
    trace = {
        "artifact_type": "ch4_runtime_trace",
        "version": "0.1.0",
        "normalized_input": normalized_input,
        "sir": sir,
        "applicable_rules": applicable_rules,
        "failing_rules": failing_rules,
        "uncertain_rules": uncertain_rules,
        "triggered_citations": report["triggered_citations"],
        "review_report": report,
    }
    return _json_ready(trace)


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, set):
        return [_json_ready(item) for item in sorted(value)]
    if isinstance(value, Path):
        return str(value)
    return value


def evaluate_rule(rule: dict[str, Any], fields: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    if not _rule_matches_context(rule, context):
        return {
            "rule_id": rule["rule_id"],
            "status": "not_applicable",
            "severity": "none",
            "reason": "scope_mismatch",
            "logic_type": rule["logic_type"],
            "rule_family": rule["rule_family"],
            "article_id": rule["article_id"],
            "candidate_fields": rule["sir_candidate_fields"],
            "summary": rule["rule_candidate_summary"],
            "finding_fields": [],
            "evidence": [],
            "legal_basis": _legal_basis(rule),
        }

    candidate_fields = rule["sir_candidate_fields"]
    field_states = {name: fields[name] for name in candidate_fields if name in fields}

    if rule["logic_type"] == "required_response":
        trigger_fields = [name for name in candidate_fields if name == "access_request"]
        if trigger_fields and any(field_states[name]["status"] != "present" for name in trigger_fields):
            return {
                "rule_id": rule["rule_id"],
                "status": "not_applicable",
                "severity": "none",
                "reason": "no_trigger_event",
                "logic_type": rule["logic_type"],
                "rule_family": rule["rule_family"],
                "article_id": rule["article_id"],
                "candidate_fields": candidate_fields,
                "summary": rule["rule_candidate_summary"],
                "finding_fields": [],
                "evidence": [],
                "legal_basis": _legal_basis(rule),
            }

    if rule["logic_type"] in {"required_presence", "required_process", "required_record", "required_response"}:
        required_fields = [name for name in candidate_fields if name not in NEGATIVE_SIGNAL_FIELDS]
        if not required_fields:
            required_fields = candidate_fields
        missing = [name for name in required_fields if field_states[name]["status"] == "not_evidenced"]
        uncertain = [name for name in required_fields if field_states[name]["status"] == "uncertain"]
        if missing:
            return _failed_rule(rule, "missing_required_evidence", missing, fields)
        if uncertain:
            return _uncertain_rule(rule, "uncertain_required_evidence", uncertain, fields)
        return _passed_rule(rule, "required_evidence_present", required_fields, fields)

    if rule["logic_type"] == "prohibited_presence":
        explicit_violations = [
            name for name in candidate_fields if _field_indicates_violation(name, field_states[name])
        ]
        omission_fields = [
            name for name in candidate_fields
            if name not in {"prohibited_claim_signal", "fairness_guardrail", "suitability_check", "adequacy_check"}
        ]
        omission_missing = [name for name in omission_fields if field_states[name]["status"] == "not_evidenced"]
        omission_uncertain = [name for name in omission_fields if field_states[name]["status"] == "uncertain"]
        if explicit_violations or omission_missing:
            return _failed_rule(
                rule,
                "prohibited_condition_detected_or_required_disclosure_missing",
                explicit_violations + omission_missing,
                fields,
            )
        if omission_uncertain:
            return _uncertain_rule(rule, "uncertain_prohibited_condition", omission_uncertain, fields)
        return _passed_rule(rule, "no_prohibited_signal_detected", candidate_fields, fields)

    return _uncertain_rule(rule, "unsupported_logic_type", candidate_fields, fields)


def build_review_report(
    payload: dict[str, Any],
    sir: dict[str, Any],
    rule_results: list[dict[str, Any]],
    rule_pack: list[dict[str, Any]],
    schema: dict[str, Any],
) -> dict[str, Any]:
    applicable = [result for result in rule_results if result["status"] != "not_applicable"]
    failed = [result for result in applicable if result["status"] == "failed"]
    uncertain = [result for result in applicable if result["status"] == "uncertain"]
    passed = [result for result in applicable if result["status"] == "passed"]

    status_counts = Counter(result["status"] for result in rule_results)
    logic_fail_counts = Counter(result["logic_type"] for result in failed)
    active_fields = sorted(
        {
            field
            for result in applicable
            for field in result["candidate_fields"]
            if sir["fields"][field]["status"] != "not_applicable"
        }
    )
    missing_fields = sorted(
        {
            field
            for result in failed
            for field in result["finding_fields"]
            if sir["fields"][field]["status"] == "not_evidenced"
        }
    )

    if failed:
        final_decision = "non_compliant"
    elif uncertain:
        final_decision = "needs_human_review"
    elif passed:
        final_decision = "compliant"
    else:
        final_decision = "insufficient_scope"

    should_escalate = bool(failed or uncertain)
    active_rule_ids = [result["rule_id"] for result in applicable]
    final_schema_fields = [field["field_name"] for field in schema["fields"]]
    triggered_citations = _collect_triggered_citations(rule_results)

    return {
        "artifact_type": "ch4_non_llm_review_report",
        "version": "0.1.0",
        "input_id": payload.get("input_id", "unnamed_input"),
        "review_scope": sir["context"]["review_scope"],
        "product_scope_hint": sir["context"]["product_scope_hint"],
        "channel_scope_hint": sir["context"]["channel_scope_hint"],
        "final_decision": final_decision,
        "should_escalate": should_escalate,
        "summary": {
            "total_rules_in_pack": len(rule_pack),
            "applicable_rule_count": len(applicable),
            "passed_rule_count": len(passed),
            "failed_rule_count": len(failed),
            "uncertain_rule_count": len(uncertain),
            "status_counts": dict(status_counts),
            "failed_logic_type_counts": dict(logic_fail_counts),
            "active_sir_field_count": len(active_fields),
            "missing_sir_field_count": len(missing_fields),
        },
        "active_rule_ids": active_rule_ids,
        "active_sir_fields": active_fields,
        "missing_sir_fields": missing_fields,
        "triggered_citations": triggered_citations,
        "sir_fields": sir["fields"],
        "rule_results": rule_results,
        "schema_field_inventory": final_schema_fields,
    }


def render_markdown_summary(report: dict[str, Any]) -> str:
    lines = [
        f"# Review Summary: {report['input_id']}",
        "",
        f"- final decision: `{report['final_decision']}`",
        f"- should escalate: `{str(report['should_escalate']).lower()}`",
        f"- review scope: `{report['review_scope']}`",
        f"- product scope hint: `{', '.join(report['product_scope_hint'])}`",
        f"- channel scope hint: `{', '.join(report['channel_scope_hint'])}`",
        f"- applicable rules: `{report['summary']['applicable_rule_count']}`",
        f"- failed rules: `{report['summary']['failed_rule_count']}`",
        f"- uncertain rules: `{report['summary']['uncertain_rule_count']}`",
        f"- missing SIR fields: `{report['summary']['missing_sir_field_count']}`",
        "",
        "## Triggered Citations",
        "",
    ]
    if report["triggered_citations"]:
        for citation in report["triggered_citations"]:
            lines.append(
                f"- `{citation['citation_label']}` | {citation['article_title']} | {citation['summary']}"
            )
    else:
        lines.append("- none")

    lines.extend([
        "",
        "## Missing SIR Fields",
        "",
    ])
    if report["missing_sir_fields"]:
        for field_name in report["missing_sir_fields"]:
            lines.append(f"- `{field_name}`")
    else:
        lines.append("- none")

    lines.extend(["", "## Failed Rules", ""])
    failed = [row for row in report["rule_results"] if row["status"] == "failed"]
    if not failed:
        lines.append("- none")
    else:
        for row in failed:
            lines.append(
                f"- `{row['rule_id']}` | `{row['logic_type']}` | {row['reason']} | fields: {', '.join(row['finding_fields'])}"
            )
            lines.append(f"  legal basis: `{row['legal_basis']['citation_label']}`")
            lines.append(f"  source text: {row['legal_basis']['source_span_text']}")

    lines.extend(["", "## Uncertain Rules", ""])
    uncertain = [row for row in report["rule_results"] if row["status"] == "uncertain"]
    if not uncertain:
        lines.append("- none")
    else:
        for row in uncertain:
            lines.append(
                f"- `{row['rule_id']}` | `{row['logic_type']}` | {row['reason']} | fields: {', '.join(row['finding_fields'])}"
            )
            lines.append(f"  legal basis: `{row['legal_basis']['citation_label']}`")
            lines.append(f"  source text: {row['legal_basis']['source_span_text']}")
    return "\n".join(lines) + "\n"


def _normalize_scope_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        tokens = re.split(r"[,\s|]+", value.strip())
        return [token for token in tokens if token]
    if isinstance(value, list):
        tokens: list[str] = []
        for item in value:
            tokens.extend(_normalize_scope_list(item))
        return tokens
    return []


def _combine_text(payload: dict[str, Any]) -> str:
    return "\n".join(part for part in [payload.get("title", ""), payload.get("content_text", "")] if part).strip()


def _infer_channel_scopes(payload: dict[str, Any]) -> list[str]:
    text = _combine_text(payload)
    if any(word in text for word in ["광고", "이벤트", "혜택", "지금", "가입"]):
        return ["advertising"]
    return ["advertising"] if text else ["internal_control"]


def _infer_product_scopes(text: str) -> list[str]:
    matches = []
    for scope, keywords in PRODUCT_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            matches.append(scope)
    return matches


def _infer_business_role(payload: dict[str, Any]) -> str:
    text = _combine_text(payload)
    if any(word in text for word in ["자문업자", "자문"]):
        return "advisory"
    if "독립" in text:
        return "independent_advisory"
    if any(word in text for word in ["판매대리", "중개업자", "대리", "중개"]):
        return "intermediary"
    return "direct_seller"


def _default_field_state(field: dict[str, Any]) -> dict[str, Any]:
    return {
        "field_name": field["field_name"],
        "field_group": field["field_group"],
        "value_type": field["value_type"],
        "status": "not_evidenced",
        "value": None,
        "evidence": [],
        "source": "default",
        "_priority": FIELD_SOURCE_PRIORITY["default"],
    }


def _strip_internal_state(state: dict[str, Any]) -> dict[str, Any]:
    clean = dict(state)
    clean.pop("_priority", None)
    return clean


def _update_field(
    field_states: dict[str, dict[str, Any]],
    field_name: str,
    *,
    status: str,
    value: Any = None,
    evidence: list[str] | None = None,
    source: str,
) -> None:
    if field_name not in field_states:
        return
    if status not in STATUS_VALUES:
        raise ValueError(f"Unsupported status for {field_name}: {status}")
    priority = FIELD_SOURCE_PRIORITY[source]
    current = field_states[field_name]
    if priority < current["_priority"]:
        return
    field_states[field_name] = {
        **current,
        "status": status,
        "value": value,
        "evidence": evidence or [],
        "source": source,
        "_priority": priority,
    }


def _mark_scope_not_applicable(field_states: dict[str, dict[str, Any]], context: dict[str, Any]) -> None:
    active_targets = context["active_targets"]
    for name, state in field_states.items():
        target = FIELD_GROUP_TARGET[state["field_group"]]
        if target not in active_targets:
            _update_field(field_states, name, status="not_applicable", source="context_scope")


def _mark_product_not_applicable(field_states: dict[str, dict[str, Any]], context: dict[str, Any]) -> None:
    scopes = set(context["product_scope_hint"])
    if "loan" not in scopes:
        for name in ("loan_conditions", "loan_rate_basis", "loan_interest_timing", "loan_costs"):
            _update_field(field_states, name, status="not_applicable", source="context_scope")
    if "deposit" not in scopes:
        _update_field(field_states, "deposit_disclaimer", status="not_applicable", source="context_scope")
    if "investment" not in scopes:
        _update_field(field_states, "investment_warning", status="not_applicable", source="context_scope")
    if "insurance" not in scopes:
        _update_field(field_states, "insurance_warning", status="not_applicable", source="context_scope")


def _mark_channel_not_applicable(field_states: dict[str, dict[str, Any]], context: dict[str, Any]) -> None:
    channels = set(context["channel_scope_hint"])
    if "advisory" not in channels:
        _update_field(field_states, "advisory_independence", status="not_applicable", source="context_scope")
    if context["business_role_hint"] == "direct_seller":
        _update_field(field_states, "intermediary_status", status="not_applicable", source="context_scope")
    if not channels.intersection({"visit_sales", "phone_sales", "solicitation", "advisory"}):
        for name in ("representative_identity", "solicitation_purpose"):
            if field_states[name]["source"] == "default":
                _update_field(field_states, name, status="not_applicable", source="context_scope")
    if not channels.intersection({"visit_sales", "phone_sales"}):
        _update_field(field_states, "staff_registry", status="not_applicable", source="context_scope")


def _apply_explicit_field_inputs(field_states: dict[str, dict[str, Any]], field_inputs: dict[str, Any]) -> None:
    for field_name, payload in field_inputs.items():
        if field_name not in field_states:
            continue
        if isinstance(payload, dict):
            status = payload.get("status")
            value = payload.get("value")
            evidence = payload.get("evidence", [])
            if status is None:
                status = "present" if value not in (None, "", [], {}) else "not_evidenced"
        else:
            value = payload
            evidence = []
            status = "present" if value not in (None, "", [], {}) else "not_evidenced"
        _update_field(field_states, field_name, status=status, value=value, evidence=evidence, source="field_inputs")


def _apply_metadata_field_inputs(field_states: dict[str, dict[str, Any]], metadata: dict[str, Any], source: str) -> None:
    if not metadata:
        return
    direct_map = {
        "seller_identity": "seller_identity",
        "product_identity": "product_identity",
        "product_core_terms": "product_core_terms",
        "explanation_material": "explanation_material",
        "prohibited_claim_signal": "prohibited_claim_signal",
        "deposit_disclaimer": "deposit_disclaimer",
        "investment_warning": "investment_warning",
        "loan_costs": "loan_costs",
        "loan_interest_timing": "loan_interest_timing",
        "loan_rate_basis": "loan_rate_basis",
        "advisory_independence": "advisory_independence",
        "explanation_confirmation": "explanation_confirmation",
        "insurance_warning": "insurance_warning",
        "loan_conditions": "loan_conditions",
        "activity_record": "activity_record",
        "contract_document_delivery": "contract_document_delivery",
        "internal_control_standard": "internal_control_standard",
        "record_integrity_control": "record_integrity_control",
        "adequacy_check": "adequacy_check",
        "consumer_profile": "consumer_profile",
        "staff_registry": "staff_registry",
        "access_request": "access_request",
        "access_response": "access_response",
        "consumer_type": "consumer_type",
        "fairness_guardrail": "fairness_guardrail",
        "representative_identity": "representative_identity",
        "solicitation_purpose": "solicitation_purpose",
        "suitability_check": "suitability_check",
        "intermediary_status": "intermediary_status",
    }
    alias_map = {
        "seller_name": "seller_identity",
        "product_name": "product_identity",
        "consumer_profile_bundle": "consumer_profile",
        "suitability_check_status": "suitability_check",
        "adequacy_check_status": "adequacy_check",
        "staff_registry_present": "staff_registry",
        "activity_record_present": "activity_record",
        "access_request_present": "access_request",
        "access_response_present": "access_response",
        "record_integrity_control_present": "record_integrity_control",
        "contract_document_delivery_status": "contract_document_delivery",
        "internal_control_standard_present": "internal_control_standard",
        "representative_name": "representative_identity",
    }
    for key, value in metadata.items():
        field_name = direct_map.get(key) or alias_map.get(key)
        if not field_name:
            continue
        status, normalized_value = _coerce_metadata_value(field_name, value)
        evidence = [f"{source}.{key}"]
        _update_field(field_states, field_name, status=status, value=normalized_value, evidence=evidence, source=source)


def _coerce_metadata_value(field_name: str, value: Any) -> tuple[str, Any]:
    if isinstance(value, bool):
        if value:
            return "present", True
        return "not_evidenced", False
    if value in (None, "", [], {}):
        return "not_evidenced", value
    if field_name in {"suitability_check", "adequacy_check", "fairness_guardrail", "advisory_independence", "consumer_type", "contract_document_delivery", "record_integrity_control"}:
        return "present", value
    return "present", value


def _apply_content_heuristics(field_states: dict[str, dict[str, Any]], payload: dict[str, Any], text: str) -> None:
    if not text:
        return

    seller = _first_regex_match(text, SELLER_PATTERNS)
    if seller and field_states["seller_identity"]["source"] == "default":
        _update_field(field_states, "seller_identity", status="present", value=seller, evidence=[seller], source="heuristic")

    product_identity = _infer_product_identity(text)
    if product_identity and field_states["product_identity"]["source"] == "default":
        _update_field(
            field_states,
            "product_identity",
            status="present",
            value=product_identity,
            evidence=[product_identity],
            source="heuristic",
        )

    if any(term in text for keywords in PRODUCT_KEYWORDS.values() for term in keywords):
        core_terms = sorted({term for keywords in PRODUCT_KEYWORDS.values() for term in keywords if term in text})
        if field_states["product_core_terms"]["source"] == "default":
            _update_field(
                field_states,
                "product_core_terms",
                status="present",
                value=core_terms,
                evidence=core_terms[:5],
                source="heuristic",
            )

    signal_hits: list[dict[str, str]] = []
    for label, patterns in PROHIBITED_SIGNAL_PATTERNS.items():
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                signal_hits.append({"category": label, "match": match.group(0)})
    if signal_hits and field_states["prohibited_claim_signal"]["source"] == "default":
        _update_field(
            field_states,
            "prohibited_claim_signal",
            status="present",
            value=signal_hits,
            evidence=[item["match"] for item in signal_hits],
            source="heuristic",
        )

    for field_name, patterns in WARNING_PATTERNS.items():
        matches = _find_keyword_matches(text, patterns)
        if matches and field_states[field_name]["source"] == "default":
            _update_field(field_states, field_name, status="present", value=matches, evidence=matches, source="heuristic")

    for field_name, patterns in LOAN_PATTERNS.items():
        matches = _find_keyword_matches(text, patterns)
        if matches and field_states[field_name]["source"] == "default":
            _update_field(field_states, field_name, status="present", value=matches, evidence=matches, source="heuristic")

    if "독립" in text and field_states["advisory_independence"]["source"] == "default":
        value = "independent_claimed"
        if "아닌" in text or "비독립" in text:
            value = "non_independent_disclosed"
        _update_field(
            field_states,
            "advisory_independence",
            status="present",
            value=value,
            evidence=["독립"],
            source="heuristic",
        )

    intermediary_matches = _find_keyword_matches(text, [r"대리", r"중개", r"자문업자", r"판매대리", r"중개업자"])
    if intermediary_matches and field_states["intermediary_status"]["source"] == "default":
        _update_field(
            field_states,
            "intermediary_status",
            status="present",
            value="intermediary_disclosed",
            evidence=intermediary_matches,
            source="heuristic",
        )

    explanation_tokens = _find_keyword_matches(text, [r"설명", r"약관", r"상품설명서", r"안내"])
    if explanation_tokens and field_states["explanation_material"]["source"] == "default":
        _update_field(
            field_states,
            "explanation_material",
            status="present",
            value=explanation_tokens,
            evidence=explanation_tokens,
            source="heuristic",
        )

    confirmation_tokens = _find_keyword_matches(text, [r"확인", r"동의", r"설명을\s*들었"])
    if confirmation_tokens and field_states["explanation_confirmation"]["source"] == "default":
        _update_field(
            field_states,
            "explanation_confirmation",
            status="present",
            value="confirmed_in_text",
            evidence=confirmation_tokens,
            source="heuristic",
        )

    rep_tokens = _find_keyword_matches(text, [r"담당자", r"상담사", r"직원", r"매니저", r"대표"])
    if rep_tokens and field_states["representative_identity"]["source"] == "default":
        _update_field(
            field_states,
            "representative_identity",
            status="present",
            value=rep_tokens[0],
            evidence=rep_tokens,
            source="heuristic",
        )

    if any(word in text for word in ["권유", "상담", "제안", "추천"]) and field_states["solicitation_purpose"]["source"] == "default":
        _update_field(
            field_states,
            "solicitation_purpose",
            status="present",
            value="solicitation_disclosed_in_text",
            evidence=_find_keyword_matches(text, [r"권유", r"상담", r"제안", r"추천"]),
            source="heuristic",
        )


def _apply_derived_states(field_states: dict[str, dict[str, Any]], context: dict[str, Any]) -> None:
    prohibited_state = field_states["prohibited_claim_signal"]
    fairness_state = field_states["fairness_guardrail"]
    if prohibited_state["status"] == "present" and fairness_state["source"] == "default":
        _update_field(
            field_states,
            "fairness_guardrail",
            status="present",
            value="potential_violation",
            evidence=prohibited_state["evidence"],
            source="heuristic",
        )

    if "advisory" in context["channel_scope_hint"] and field_states["advisory_independence"]["status"] == "not_evidenced":
        _update_field(field_states, "advisory_independence", status="uncertain", source="heuristic")

    if "full" == context["review_scope"]:
        for name in ("consumer_type", "consumer_profile", "suitability_check", "adequacy_check"):
            if field_states[name]["source"] == "default" and "solicitation" in context["channel_scope_hint"]:
                _update_field(field_states, name, status="uncertain", source="heuristic")


def _rule_matches_context(rule: dict[str, Any], context: dict[str, Any]) -> bool:
    include_rule_families = set(context["include_rule_families"])
    exclude_rule_families = set(context["exclude_rule_families"])
    if include_rule_families and rule["rule_family"] not in include_rule_families:
        return False
    if exclude_rule_families and rule["rule_family"] in exclude_rule_families:
        return False
    if rule["detection_target"] not in context["active_targets"]:
        return False
    if not _product_scope_matches(rule["product_scope"], context["product_scope_hint"]):
        return False
    if not _channel_scope_matches(rule["channel_scope"], context["channel_scope_hint"]):
        return False
    if rule["rule_family"] == "intermediary" and context["business_role_hint"] != "intermediary":
        return False
    if rule["rule_family"] == "advisory" and context["business_role_hint"] not in {"advisory", "independent_advisory"}:
        return False
    return True


def _product_scope_matches(rule_scope: str, input_scopes: list[str]) -> bool:
    rule_tokens = set(rule_scope.split("|"))
    if "general" in rule_tokens or "multiple" in rule_tokens:
        return True
    return bool(rule_tokens.intersection(input_scopes))


def _channel_scope_matches(rule_scope: str, input_scopes: list[str]) -> bool:
    rule_tokens = set(rule_scope.split("|"))
    if "all_customer_facing" in rule_tokens and set(input_scopes).intersection(
        {"advertising", "solicitation", "contracting", "advisory", "visit_sales", "phone_sales"}
    ):
        return True
    return bool(rule_tokens.intersection(input_scopes))


def _field_indicates_violation(field_name: str, field_state: dict[str, Any]) -> bool:
    if field_state["status"] != "present":
        return False
    value = field_state["value"]
    if field_name == "prohibited_claim_signal":
        return bool(value)
    if field_name == "fairness_guardrail":
        return value in {"failed", "potential_violation", "missing"}
    if field_name == "suitability_check":
        return value in {"unsuitable_recommended", "failed"}
    if field_name == "adequacy_check":
        return value in {"inadequate_recommended", "failed"}
    if field_name == "advisory_independence":
        return value in {"misleading_independent_claim", "conflicted"}
    if field_name == "intermediary_status":
        return value in {"undisclosed_intermediary", "misleading_role"}
    return False


def _passed_rule(rule: dict[str, Any], reason: str, finding_fields: list[str], fields: dict[str, Any]) -> dict[str, Any]:
    return {
        "rule_id": rule["rule_id"],
        "status": "passed",
        "severity": "none",
        "reason": reason,
        "logic_type": rule["logic_type"],
        "rule_family": rule["rule_family"],
        "article_id": rule["article_id"],
        "candidate_fields": rule["sir_candidate_fields"],
        "summary": rule["rule_candidate_summary"],
        "finding_fields": finding_fields,
        "evidence": _collect_evidence(finding_fields, fields),
        "legal_basis": _legal_basis(rule),
    }


def _failed_rule(rule: dict[str, Any], reason: str, finding_fields: list[str], fields: dict[str, Any]) -> dict[str, Any]:
    return {
        "rule_id": rule["rule_id"],
        "status": "failed",
        "severity": _severity_for_logic_type(rule["logic_type"]),
        "reason": reason,
        "logic_type": rule["logic_type"],
        "rule_family": rule["rule_family"],
        "article_id": rule["article_id"],
        "candidate_fields": rule["sir_candidate_fields"],
        "summary": rule["rule_candidate_summary"],
        "finding_fields": finding_fields,
        "evidence": _collect_evidence(finding_fields, fields),
        "legal_basis": _legal_basis(rule),
    }


def _uncertain_rule(rule: dict[str, Any], reason: str, finding_fields: list[str], fields: dict[str, Any]) -> dict[str, Any]:
    return {
        "rule_id": rule["rule_id"],
        "status": "uncertain",
        "severity": "medium",
        "reason": reason,
        "logic_type": rule["logic_type"],
        "rule_family": rule["rule_family"],
        "article_id": rule["article_id"],
        "candidate_fields": rule["sir_candidate_fields"],
        "summary": rule["rule_candidate_summary"],
        "finding_fields": finding_fields,
        "evidence": _collect_evidence(finding_fields, fields),
        "legal_basis": _legal_basis(rule),
    }


def _severity_for_logic_type(logic_type: str) -> str:
    if logic_type == "prohibited_presence":
        return "high"
    if logic_type == "required_response":
        return "high"
    if logic_type == "required_record":
        return "medium"
    if logic_type == "required_process":
        return "medium"
    return "medium"


def _collect_evidence(field_names: list[str], fields: dict[str, Any]) -> list[dict[str, Any]]:
    evidence = []
    for name in field_names:
        field = fields[name]
        evidence.append(
            {
                "field_name": name,
                "status": field["status"],
                "value": field["value"],
                "evidence": field["evidence"],
                "source": field["source"],
            }
        )
    return evidence


def _first_regex_match(text: str, patterns: list[str]) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return None


def _find_keyword_matches(text: str, patterns: list[str]) -> list[str]:
    matches: list[str] = []
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            token = match.group(0)
            if token not in matches:
                matches.append(token)
    return matches


def _infer_product_identity(text: str) -> str | None:
    ordered = [
        ("loan", "대출"),
        ("deposit", "예금"),
        ("deposit", "적금"),
        ("investment", "펀드"),
        ("investment", "투자"),
        ("insurance", "보험"),
    ]
    for _, label in ordered:
        if label in text:
            return label
    return None


def _legal_basis(rule: dict[str, Any]) -> dict[str, Any]:
    paragraph = rule["paragraph_id"] or ""
    citation_label = f"금융소비자 보호에 관한 법률 {rule['article_id']}{paragraph}"
    return {
        "source_title": "금융소비자 보호에 관한 법률",
        "article_id": rule["article_id"],
        "paragraph_id": rule["paragraph_id"],
        "article_title": rule["article_title"],
        "citation_label": citation_label,
        "section_id": rule["section_id"],
        "section_title": rule["section_title"],
        "source_obligation_id": rule["source_obligation_id"],
        "source_span_text": rule["source_span_text"],
        "summary": rule["obligation_summary"],
    }


def _collect_triggered_citations(rule_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    citations: list[dict[str, Any]] = []
    for row in rule_results:
        if row["status"] not in {"failed", "uncertain"}:
            continue
        citation = row["legal_basis"]
        key = row["rule_id"]
        if key in seen:
            continue
        seen.add(key)
        citations.append(citation)
    return citations
