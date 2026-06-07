(function () {
  const STATUS_VALUES = new Set(["present", "not_evidenced", "not_applicable", "uncertain"]);
  const NEGATIVE_SIGNAL_FIELDS = new Set(["prohibited_claim_signal", "fairness_guardrail"]);

  const REVIEW_SCOPE_TARGETS = {
    content_only: ["content_text", "document_bundle"],
    workflow_only: ["workflow_metadata", "consumer_profile"],
    record_only: ["record_system"],
    full: ["content_text", "document_bundle", "workflow_metadata", "consumer_profile", "record_system"],
  };

  const FIELD_GROUP_TARGET = {
    content_text: "content_text",
    workflow_metadata: "workflow_metadata",
    record_system: "record_system",
  };

  const FIELD_SOURCE_PRIORITY = {
    default: 0,
    context_scope: 1,
    heuristic: 2,
    workflow_metadata: 3,
    record_metadata: 3,
    content_metadata: 3,
    field_inputs: 4,
  };

  const PRODUCT_KEYWORDS = {
    loan: ["대출", "금리", "중도상환", "상환", "연체이자", "한도", "가산금리", "기준금리"],
    deposit: ["예금", "적금", "정기예금", "예금자보호", "이자지급", "만기"],
    investment: ["투자", "펀드", "ETF", "주식", "채권", "수익률", "원금손실", "집합투자"],
    insurance: ["보험", "보험료", "해약환급금", "면책", "기존계약", "보험계약"],
  };

  const CHANNEL_VALUES = new Set([
    "all_customer_facing",
    "advertising",
    "solicitation",
    "contracting",
    "advisory",
    "visit_sales",
    "phone_sales",
    "internal_control",
  ]);

  const SELLER_PATTERNS = [
    "토스뱅크",
    "카카오뱅크",
    "케이뱅크",
    "KB국민은행",
    "국민은행",
    "신한은행",
    "하나은행",
    "우리은행",
    "NH농협은행",
    "농협은행",
    "IBK기업은행",
    "기업은행",
    "부산은행",
    "대구은행",
    "광주은행",
    "전북은행",
    "경남은행",
    "수협은행",
    "SC제일은행",
    "한국씨티은행",
    "삼성화재",
    "현대해상",
    "메리츠화재",
    "DB손해보험",
    "미래에셋증권",
    "한국투자증권",
    "NH투자증권",
    "키움증권",
    "신한투자증권",
    "하나증권",
    "KB증권",
    "삼성증권",
    "[가-힣A-Za-z0-9]+은행",
    "[가-힣A-Za-z0-9]+증권",
    "[가-힣A-Za-z0-9]+보험",
  ];

  const PROHIBITED_SIGNAL_PATTERNS = {
    principal_guarantee: ["원금\\s*보장", "원금보장"],
    guaranteed_return: ["확정\\s*수익", "수익\\s*보장", "보장\\s*수익"],
    no_loss: ["손실\\s*없", "손해\\s*없"],
    risk_free: ["무위험", "안전한\\s*투자"],
    absolute_claim: ["반드시", "무조건"],
    oversimplification: ["쉽고\\s*간편", "간편하게", "부담\\s*없이"],
    universal_eligibility: ["누구나", "모두", "전원"],
    guaranteed_approval: ["즉시\\s*승인", "무조건\\s*승인", "승인\\s*보장"],
    absolute_numeric_claim: ["100%"],
  };

  const WARNING_PATTERNS = {
    deposit_disclaimer: ["예금자보호", "보호한도", "예금보험공사"],
    investment_warning: ["원금\\s*손실", "손실\\s*가능", "예금자보호\\s*대상\\s*아님", "실적배당"],
    insurance_warning: ["면책", "해약환급금", "기존계약", "보장내용", "보험료"],
  };

  const LOAN_PATTERNS = {
    loan_conditions: ["한도", "상환", "기간", "만기", "거치", "분할", "원리금", "중도상환"],
    loan_rate_basis: ["\\d+(?:\\.\\d+)?\\s*%", "금리", "기준금리", "가산금리", "연\\s*\\d"],
    loan_interest_timing: ["이자\\s*부과", "이자\\s*납입", "매월", "월납", "상환일", "매달"],
    loan_costs: ["수수료", "비용", "연체이자", "인지세", "중도상환수수료"],
  };

  function deepClone(value) {
    if (typeof structuredClone === "function") {
      return structuredClone(value);
    }
    return JSON.parse(JSON.stringify(value));
  }

  function normalizeScopeList(value) {
    if (value == null) return [];
    if (typeof value === "string") {
      return value
        .split(/[,\s|]+/)
        .map((item) => item.trim())
        .filter(Boolean);
    }
    if (Array.isArray(value)) {
      return value.flatMap((item) => normalizeScopeList(item));
    }
    return [];
  }

  function combineText(payload) {
    return [payload.title || "", payload.content_text || ""].filter(Boolean).join("\n").trim();
  }

  function inferChannelScopes(payload) {
    const text = combineText(payload);
    if (["광고", "이벤트", "혜택", "지금", "가입"].some((word) => text.includes(word))) {
      return ["advertising"];
    }
    return text ? ["advertising"] : ["internal_control"];
  }

  function inferProductScopes(text) {
    const matches = [];
    for (const [scope, keywords] of Object.entries(PRODUCT_KEYWORDS)) {
      if (keywords.some((keyword) => text.includes(keyword))) {
        matches.push(scope);
      }
    }
    return matches;
  }

  function inferBusinessRole(payload) {
    const text = combineText(payload);
    if (["자문업자", "자문"].some((word) => text.includes(word))) return "advisory";
    if (text.includes("독립")) return "independent_advisory";
    if (["판매대리", "중개업자", "대리", "중개"].some((word) => text.includes(word))) return "intermediary";
    return "direct_seller";
  }

  function normalizeRuntimeInput(payload) {
    const normalized = deepClone(payload || {});
    if (normalized.input_id == null) normalized.input_id = "unnamed_input";
    if (normalized.title == null) normalized.title = "";
    if (normalized.content_text == null) normalized.content_text = "";
    if (normalized.review_scope == null) normalized.review_scope = "content_only";
    if (normalized.product_scope_hint == null) normalized.product_scope_hint = [];
    if (normalized.channel_scope_hint == null) normalized.channel_scope_hint = [];
    if (normalized.field_inputs == null) normalized.field_inputs = {};
    if (normalized.content_metadata == null) normalized.content_metadata = {};
    if (normalized.workflow_metadata == null) normalized.workflow_metadata = {};
    if (normalized.record_metadata == null) normalized.record_metadata = {};
    if (normalized.business_role_hint == null) normalized.business_role_hint = "";
    if (normalized.include_rule_families == null) normalized.include_rule_families = [];
    if (normalized.exclude_rule_families == null) normalized.exclude_rule_families = [];

    if (!Object.prototype.hasOwnProperty.call(REVIEW_SCOPE_TARGETS, normalized.review_scope)) {
      throw new Error(`Unsupported review_scope: ${normalized.review_scope}`);
    }

    normalized.product_scope_hint = normalizeScopeList(normalized.product_scope_hint);
    normalized.channel_scope_hint = normalizeScopeList(normalized.channel_scope_hint).filter((scope) => CHANNEL_VALUES.has(scope));
    normalized.include_rule_families = normalizeScopeList(normalized.include_rule_families);
    normalized.exclude_rule_families = normalizeScopeList(normalized.exclude_rule_families);

    if (!normalized.channel_scope_hint.length) {
      normalized.channel_scope_hint = inferChannelScopes(normalized);
    }
    if (!normalized.product_scope_hint.length) {
      normalized.product_scope_hint = inferProductScopes(combineText(normalized));
    }
    if (!normalized.product_scope_hint.length) {
      normalized.product_scope_hint = ["general"];
    }
    if (!normalized.business_role_hint) {
      normalized.business_role_hint = inferBusinessRole(normalized);
    }
    return normalized;
  }

  function defaultFieldState(field) {
    return {
      field_name: field.field_name,
      field_group: field.field_group,
      value_type: field.value_type,
      status: "not_evidenced",
      value: null,
      evidence: [],
      source: "default",
      _priority: FIELD_SOURCE_PRIORITY.default,
    };
  }

  function stripInternalState(state) {
    const copy = { ...state };
    delete copy._priority;
    return copy;
  }

  function updateField(fieldStates, fieldName, { status, value = null, evidence = [], source }) {
    if (!fieldStates[fieldName]) return;
    if (!STATUS_VALUES.has(status)) {
      throw new Error(`Unsupported status for ${fieldName}: ${status}`);
    }
    const priority = FIELD_SOURCE_PRIORITY[source];
    const current = fieldStates[fieldName];
    if (priority < current._priority) return;
    fieldStates[fieldName] = {
      ...current,
      status,
      value,
      evidence,
      source,
      _priority: priority,
    };
  }

  function markScopeNotApplicable(fieldStates, context) {
    const activeTargets = new Set(context.active_targets);
    for (const [name, state] of Object.entries(fieldStates)) {
      const target = FIELD_GROUP_TARGET[state.field_group];
      if (!activeTargets.has(target)) {
        updateField(fieldStates, name, { status: "not_applicable", source: "context_scope" });
      }
    }
  }

  function markProductNotApplicable(fieldStates, context) {
    const scopes = new Set(context.product_scope_hint);
    if (!scopes.has("loan")) {
      for (const name of ["loan_conditions", "loan_rate_basis", "loan_interest_timing", "loan_costs"]) {
        updateField(fieldStates, name, { status: "not_applicable", source: "context_scope" });
      }
    }
    if (!scopes.has("deposit")) {
      updateField(fieldStates, "deposit_disclaimer", { status: "not_applicable", source: "context_scope" });
    }
    if (!scopes.has("investment")) {
      updateField(fieldStates, "investment_warning", { status: "not_applicable", source: "context_scope" });
    }
    if (!scopes.has("insurance")) {
      updateField(fieldStates, "insurance_warning", { status: "not_applicable", source: "context_scope" });
    }
  }

  function markChannelNotApplicable(fieldStates, context) {
    const channels = new Set(context.channel_scope_hint);
    if (!channels.has("advisory")) {
      updateField(fieldStates, "advisory_independence", { status: "not_applicable", source: "context_scope" });
    }
    if (context.business_role_hint === "direct_seller") {
      updateField(fieldStates, "intermediary_status", { status: "not_applicable", source: "context_scope" });
    }
    if (![ "visit_sales", "phone_sales", "solicitation", "advisory" ].some((item) => channels.has(item))) {
      for (const name of ["representative_identity", "solicitation_purpose"]) {
        if (fieldStates[name].source === "default") {
          updateField(fieldStates, name, { status: "not_applicable", source: "context_scope" });
        }
      }
    }
    if (![ "visit_sales", "phone_sales" ].some((item) => channels.has(item))) {
      updateField(fieldStates, "staff_registry", { status: "not_applicable", source: "context_scope" });
    }
  }

  function applyExplicitFieldInputs(fieldStates, fieldInputs) {
    for (const [fieldName, payload] of Object.entries(fieldInputs || {})) {
      if (!fieldStates[fieldName]) continue;
      let status;
      let value;
      let evidence;
      if (payload && typeof payload === "object" && !Array.isArray(payload)) {
        status = payload.status;
        value = payload.value;
        evidence = payload.evidence || [];
        if (status == null) {
          status = value != null && value !== "" && !(Array.isArray(value) && !value.length) ? "present" : "not_evidenced";
        }
      } else {
        value = payload;
        evidence = [];
        status = value != null && value !== "" && !(Array.isArray(value) && !value.length) ? "present" : "not_evidenced";
      }
      updateField(fieldStates, fieldName, { status, value, evidence, source: "field_inputs" });
    }
  }

  function coerceMetadataValue(fieldName, value) {
    if (typeof value === "boolean") {
      return value ? ["present", true] : ["not_evidenced", false];
    }
    if (value == null || value === "" || (Array.isArray(value) && !value.length)) {
      return ["not_evidenced", value];
    }
    if (
      [
        "suitability_check",
        "adequacy_check",
        "fairness_guardrail",
        "advisory_independence",
        "consumer_type",
        "contract_document_delivery",
        "record_integrity_control",
      ].includes(fieldName)
    ) {
      return ["present", value];
    }
    return ["present", value];
  }

  function applyMetadataFieldInputs(fieldStates, metadata, source) {
    if (!metadata) return;
    const directMap = {
      seller_identity: "seller_identity",
      product_identity: "product_identity",
      product_core_terms: "product_core_terms",
      explanation_material: "explanation_material",
      prohibited_claim_signal: "prohibited_claim_signal",
      deposit_disclaimer: "deposit_disclaimer",
      investment_warning: "investment_warning",
      loan_costs: "loan_costs",
      loan_interest_timing: "loan_interest_timing",
      loan_rate_basis: "loan_rate_basis",
      advisory_independence: "advisory_independence",
      explanation_confirmation: "explanation_confirmation",
      insurance_warning: "insurance_warning",
      loan_conditions: "loan_conditions",
      activity_record: "activity_record",
      contract_document_delivery: "contract_document_delivery",
      internal_control_standard: "internal_control_standard",
      record_integrity_control: "record_integrity_control",
      adequacy_check: "adequacy_check",
      consumer_profile: "consumer_profile",
      staff_registry: "staff_registry",
      access_request: "access_request",
      access_response: "access_response",
      consumer_type: "consumer_type",
      fairness_guardrail: "fairness_guardrail",
      representative_identity: "representative_identity",
      solicitation_purpose: "solicitation_purpose",
      suitability_check: "suitability_check",
      intermediary_status: "intermediary_status",
    };
    const aliasMap = {
      seller_name: "seller_identity",
      product_name: "product_identity",
      consumer_profile_bundle: "consumer_profile",
      suitability_check_status: "suitability_check",
      adequacy_check_status: "adequacy_check",
      staff_registry_present: "staff_registry",
      activity_record_present: "activity_record",
      access_request_present: "access_request",
      access_response_present: "access_response",
      record_integrity_control_present: "record_integrity_control",
      contract_document_delivery_status: "contract_document_delivery",
      internal_control_standard_present: "internal_control_standard",
      representative_name: "representative_identity",
    };
    for (const [key, value] of Object.entries(metadata)) {
      const fieldName = directMap[key] || aliasMap[key];
      if (!fieldName) continue;
      const [status, normalizedValue] = coerceMetadataValue(fieldName, value);
      updateField(fieldStates, fieldName, {
        status,
        value: normalizedValue,
        evidence: [`${source}.${key}`],
        source,
      });
    }
  }

  function findKeywordMatches(text, patterns) {
    const matches = [];
    for (const pattern of patterns) {
      const regex = new RegExp(pattern, "g");
      for (const match of text.matchAll(regex)) {
        const token = match[0];
        if (!matches.includes(token)) matches.push(token);
      }
    }
    return matches;
  }

  function firstRegexMatch(text, patterns) {
    for (const pattern of patterns) {
      const regex = new RegExp(pattern);
      const match = text.match(regex);
      if (match) return match[0];
    }
    return null;
  }

  function inferProductIdentity(text) {
    const ordered = [
      ["loan", "대출"],
      ["deposit", "예금"],
      ["deposit", "적금"],
      ["investment", "펀드"],
      ["investment", "투자"],
      ["insurance", "보험"],
    ];
    for (const [, label] of ordered) {
      if (text.includes(label)) return label;
    }
    return null;
  }

  function applyContentHeuristics(fieldStates, payload, text) {
    if (!text) return;

    const seller = firstRegexMatch(text, SELLER_PATTERNS);
    if (seller && fieldStates.seller_identity.source === "default") {
      updateField(fieldStates, "seller_identity", {
        status: "present",
        value: seller,
        evidence: [seller],
        source: "heuristic",
      });
    }

    const productIdentity = inferProductIdentity(text);
    if (productIdentity && fieldStates.product_identity.source === "default") {
      updateField(fieldStates, "product_identity", {
        status: "present",
        value: productIdentity,
        evidence: [productIdentity],
        source: "heuristic",
      });
    }

    const coreTerms = Array.from(
      new Set(
        Object.values(PRODUCT_KEYWORDS)
          .flat()
          .filter((term) => text.includes(term))
      )
    ).sort();
    if (coreTerms.length && fieldStates.product_core_terms.source === "default") {
      updateField(fieldStates, "product_core_terms", {
        status: "present",
        value: coreTerms,
        evidence: coreTerms.slice(0, 5),
        source: "heuristic",
      });
    }

    const signalHits = [];
    for (const [label, patterns] of Object.entries(PROHIBITED_SIGNAL_PATTERNS)) {
      for (const pattern of patterns) {
        const regex = new RegExp(pattern);
        const match = text.match(regex);
        if (match) signalHits.push({ category: label, match: match[0] });
      }
    }
    if (signalHits.length && fieldStates.prohibited_claim_signal.source === "default") {
      updateField(fieldStates, "prohibited_claim_signal", {
        status: "present",
        value: signalHits,
        evidence: signalHits.map((item) => item.match),
        source: "heuristic",
      });
    }

    for (const [fieldName, patterns] of Object.entries(WARNING_PATTERNS)) {
      const matches = findKeywordMatches(text, patterns);
      if (matches.length && fieldStates[fieldName].source === "default") {
        updateField(fieldStates, fieldName, {
          status: "present",
          value: matches,
          evidence: matches,
          source: "heuristic",
        });
      }
    }

    for (const [fieldName, patterns] of Object.entries(LOAN_PATTERNS)) {
      const matches = findKeywordMatches(text, patterns);
      if (matches.length && fieldStates[fieldName].source === "default") {
        updateField(fieldStates, fieldName, {
          status: "present",
          value: matches,
          evidence: matches,
          source: "heuristic",
        });
      }
    }

    if (text.includes("독립") && fieldStates.advisory_independence.source === "default") {
      let value = "independent_claimed";
      if (text.includes("아닌") || text.includes("비독립")) {
        value = "non_independent_disclosed";
      }
      updateField(fieldStates, "advisory_independence", {
        status: "present",
        value,
        evidence: ["독립"],
        source: "heuristic",
      });
    }

    const intermediaryMatches = findKeywordMatches(text, ["대리", "중개", "자문업자", "판매대리", "중개업자"]);
    if (intermediaryMatches.length && fieldStates.intermediary_status.source === "default") {
      updateField(fieldStates, "intermediary_status", {
        status: "present",
        value: "intermediary_disclosed",
        evidence: intermediaryMatches,
        source: "heuristic",
      });
    }

    const explanationTokens = findKeywordMatches(text, ["설명", "약관", "상품설명서", "안내"]);
    if (explanationTokens.length && fieldStates.explanation_material.source === "default") {
      updateField(fieldStates, "explanation_material", {
        status: "present",
        value: explanationTokens,
        evidence: explanationTokens,
        source: "heuristic",
      });
    }

    const confirmationTokens = findKeywordMatches(text, ["확인", "동의", "설명을\\s*들었"]);
    if (confirmationTokens.length && fieldStates.explanation_confirmation.source === "default") {
      updateField(fieldStates, "explanation_confirmation", {
        status: "present",
        value: "confirmed_in_text",
        evidence: confirmationTokens,
        source: "heuristic",
      });
    }

    const repTokens = findKeywordMatches(text, ["담당자", "상담사", "직원", "매니저", "대표"]);
    if (repTokens.length && fieldStates.representative_identity.source === "default") {
      updateField(fieldStates, "representative_identity", {
        status: "present",
        value: repTokens[0],
        evidence: repTokens,
        source: "heuristic",
      });
    }

    if (["권유", "상담", "제안", "추천"].some((word) => text.includes(word)) && fieldStates.solicitation_purpose.source === "default") {
      updateField(fieldStates, "solicitation_purpose", {
        status: "present",
        value: "solicitation_disclosed_in_text",
        evidence: findKeywordMatches(text, ["권유", "상담", "제안", "추천"]),
        source: "heuristic",
      });
    }
  }

  function applyDerivedStates(fieldStates, context) {
    const prohibitedState = fieldStates.prohibited_claim_signal;
    const fairnessState = fieldStates.fairness_guardrail;
    if (prohibitedState.status === "present" && fairnessState.source === "default") {
      updateField(fieldStates, "fairness_guardrail", {
        status: "present",
        value: "potential_violation",
        evidence: prohibitedState.evidence,
        source: "heuristic",
      });
    }

    if (context.channel_scope_hint.includes("advisory") && fieldStates.advisory_independence.status === "not_evidenced") {
      updateField(fieldStates, "advisory_independence", {
        status: "uncertain",
        source: "heuristic",
      });
    }

    if (context.review_scope === "full") {
      for (const name of ["consumer_type", "consumer_profile", "suitability_check", "adequacy_check"]) {
        if (fieldStates[name].source === "default" && context.channel_scope_hint.includes("solicitation")) {
          updateField(fieldStates, name, { status: "uncertain", source: "heuristic" });
        }
      }
    }
  }

  function extractSir(payload, sirSchema) {
    const normalized = normalizeRuntimeInput(payload);
    const text = combineText(normalized);
    const context = {
      review_scope: normalized.review_scope,
      active_targets: REVIEW_SCOPE_TARGETS[normalized.review_scope],
      product_scope_hint: normalized.product_scope_hint,
      channel_scope_hint: normalized.channel_scope_hint,
      business_role_hint: normalized.business_role_hint,
      include_rule_families: normalized.include_rule_families,
      exclude_rule_families: normalized.exclude_rule_families,
    };

    const fieldStates = Object.fromEntries(sirSchema.fields.map((field) => [field.field_name, defaultFieldState(field)]));
    markScopeNotApplicable(fieldStates, context);
    markProductNotApplicable(fieldStates, context);
    markChannelNotApplicable(fieldStates, context);
    applyExplicitFieldInputs(fieldStates, normalized.field_inputs || {});
    applyMetadataFieldInputs(fieldStates, normalized.content_metadata || {}, "content_metadata");
    applyMetadataFieldInputs(fieldStates, normalized.workflow_metadata || {}, "workflow_metadata");
    applyMetadataFieldInputs(fieldStates, normalized.record_metadata || {}, "record_metadata");
    applyContentHeuristics(fieldStates, normalized, text);
    applyDerivedStates(fieldStates, context);

    const cleanedFields = Object.fromEntries(
      Object.entries(fieldStates).map(([name, state]) => [name, stripInternalState(state)])
    );

    return {
      input_id: normalized.input_id,
      context,
      fields: cleanedFields,
    };
  }

  function productScopeMatches(ruleScope, inputScopes) {
    const ruleTokens = new Set(String(ruleScope || "").split("|"));
    if (ruleTokens.has("general") || ruleTokens.has("multiple")) return true;
    return inputScopes.some((scope) => ruleTokens.has(scope));
  }

  function channelScopeMatches(ruleScope, inputScopes) {
    const ruleTokens = new Set(String(ruleScope || "").split("|"));
    const customerFacing = ["advertising", "solicitation", "contracting", "advisory", "visit_sales", "phone_sales"];
    if (ruleTokens.has("all_customer_facing") && inputScopes.some((scope) => customerFacing.includes(scope))) {
      return true;
    }
    return inputScopes.some((scope) => ruleTokens.has(scope));
  }

  function ruleMatchesContext(rule, context) {
    const includeRuleFamilies = new Set(context.include_rule_families);
    const excludeRuleFamilies = new Set(context.exclude_rule_families);
    if (includeRuleFamilies.size && !includeRuleFamilies.has(rule.rule_family)) return false;
    if (excludeRuleFamilies.has(rule.rule_family)) return false;
    if (!context.active_targets.includes(rule.detection_target)) return false;
    if (!productScopeMatches(rule.product_scope, context.product_scope_hint)) return false;
    if (!channelScopeMatches(rule.channel_scope, context.channel_scope_hint)) return false;
    if (rule.rule_family === "intermediary" && context.business_role_hint !== "intermediary") return false;
    if (rule.rule_family === "advisory" && !["advisory", "independent_advisory"].includes(context.business_role_hint)) return false;
    return true;
  }

  function legalBasis(rule) {
    const paragraph = rule.paragraph_id || "";
    return {
      source_title: "금융소비자 보호에 관한 법률",
      article_id: rule.article_id,
      paragraph_id: rule.paragraph_id,
      article_title: rule.article_title,
      citation_label: `금융소비자 보호에 관한 법률 ${rule.article_id}${paragraph}`,
      section_id: rule.section_id,
      section_title: rule.section_title,
      source_obligation_id: rule.source_obligation_id,
      source_span_text: rule.source_span_text,
      summary: rule.obligation_summary,
    };
  }

  function collectEvidence(fieldNames, fields) {
    return fieldNames.map((name) => ({
      field_name: name,
      status: fields[name].status,
      value: fields[name].value,
      evidence: fields[name].evidence,
      source: fields[name].source,
    }));
  }

  function severityForLogicType(logicType) {
    if (logicType === "prohibited_presence") return "high";
    if (logicType === "required_response") return "high";
    if (logicType === "required_record") return "medium";
    if (logicType === "required_process") return "medium";
    return "medium";
  }

  function passedRule(rule, reason, findingFields, fields) {
    return {
      rule_id: rule.rule_id,
      status: "passed",
      severity: "none",
      reason,
      logic_type: rule.logic_type,
      rule_family: rule.rule_family,
      article_id: rule.article_id,
      candidate_fields: rule.sir_candidate_fields,
      summary: rule.rule_candidate_summary,
      finding_fields: findingFields,
      evidence: collectEvidence(findingFields, fields),
      legal_basis: legalBasis(rule),
    };
  }

  function failedRule(rule, reason, findingFields, fields) {
    return {
      rule_id: rule.rule_id,
      status: "failed",
      severity: severityForLogicType(rule.logic_type),
      reason,
      logic_type: rule.logic_type,
      rule_family: rule.rule_family,
      article_id: rule.article_id,
      candidate_fields: rule.sir_candidate_fields,
      summary: rule.rule_candidate_summary,
      finding_fields: findingFields,
      evidence: collectEvidence(findingFields, fields),
      legal_basis: legalBasis(rule),
    };
  }

  function uncertainRule(rule, reason, findingFields, fields) {
    return {
      rule_id: rule.rule_id,
      status: "uncertain",
      severity: "medium",
      reason,
      logic_type: rule.logic_type,
      rule_family: rule.rule_family,
      article_id: rule.article_id,
      candidate_fields: rule.sir_candidate_fields,
      summary: rule.rule_candidate_summary,
      finding_fields: findingFields,
      evidence: collectEvidence(findingFields, fields),
      legal_basis: legalBasis(rule),
    };
  }

  function fieldIndicatesViolation(fieldName, fieldState) {
    if (fieldState.status !== "present") return false;
    const value = fieldState.value;
    if (fieldName === "prohibited_claim_signal") return Boolean(value && value.length);
    if (fieldName === "fairness_guardrail") return ["failed", "potential_violation", "missing"].includes(value);
    if (fieldName === "suitability_check") return ["unsuitable_recommended", "failed"].includes(value);
    if (fieldName === "adequacy_check") return ["inadequate_recommended", "failed"].includes(value);
    if (fieldName === "advisory_independence") return ["misleading_independent_claim", "conflicted"].includes(value);
    if (fieldName === "intermediary_status") return ["undisclosed_intermediary", "misleading_role"].includes(value);
    return false;
  }

  function evaluateRule(rule, fields, context) {
    if (!ruleMatchesContext(rule, context)) {
      return {
        rule_id: rule.rule_id,
        status: "not_applicable",
        severity: "none",
        reason: "scope_mismatch",
        logic_type: rule.logic_type,
        rule_family: rule.rule_family,
        article_id: rule.article_id,
        candidate_fields: rule.sir_candidate_fields,
        summary: rule.rule_candidate_summary,
        finding_fields: [],
        evidence: [],
        legal_basis: legalBasis(rule),
      };
    }

    const candidateFields = rule.sir_candidate_fields;
    const fieldStates = Object.fromEntries(candidateFields.filter((name) => fields[name]).map((name) => [name, fields[name]]));

    if (rule.logic_type === "required_response") {
      const triggerFields = candidateFields.filter((name) => name === "access_request");
      if (triggerFields.length && triggerFields.some((name) => fieldStates[name].status !== "present")) {
        return {
          rule_id: rule.rule_id,
          status: "not_applicable",
          severity: "none",
          reason: "no_trigger_event",
          logic_type: rule.logic_type,
          rule_family: rule.rule_family,
          article_id: rule.article_id,
          candidate_fields: candidateFields,
          summary: rule.rule_candidate_summary,
          finding_fields: [],
          evidence: [],
          legal_basis: legalBasis(rule),
        };
      }
    }

    if (["required_presence", "required_process", "required_record", "required_response"].includes(rule.logic_type)) {
      let requiredFields = candidateFields.filter((name) => !NEGATIVE_SIGNAL_FIELDS.has(name));
      if (!requiredFields.length) requiredFields = candidateFields.slice();
      const missing = requiredFields.filter((name) => fieldStates[name].status === "not_evidenced");
      const uncertain = requiredFields.filter((name) => fieldStates[name].status === "uncertain");
      if (missing.length) return failedRule(rule, "missing_required_evidence", missing, fields);
      if (uncertain.length) return uncertainRule(rule, "uncertain_required_evidence", uncertain, fields);
      return passedRule(rule, "required_evidence_present", requiredFields, fields);
    }

    if (rule.logic_type === "prohibited_presence") {
      const explicitViolations = candidateFields.filter((name) => fieldIndicatesViolation(name, fieldStates[name]));
      const omissionFields = candidateFields.filter(
        (name) => !["prohibited_claim_signal", "fairness_guardrail", "suitability_check", "adequacy_check"].includes(name)
      );
      const omissionMissing = omissionFields.filter((name) => fieldStates[name].status === "not_evidenced");
      const omissionUncertain = omissionFields.filter((name) => fieldStates[name].status === "uncertain");
      if (explicitViolations.length || omissionMissing.length) {
        return failedRule(
          rule,
          "prohibited_condition_detected_or_required_disclosure_missing",
          explicitViolations.concat(omissionMissing),
          fields
        );
      }
      if (omissionUncertain.length) return uncertainRule(rule, "uncertain_prohibited_condition", omissionUncertain, fields);
      return passedRule(rule, "no_prohibited_signal_detected", candidateFields, fields);
    }

    return uncertainRule(rule, "unsupported_logic_type", candidateFields, fields);
  }

  function collectTriggeredCitations(ruleResults) {
    const seen = new Set();
    const citations = [];
    for (const row of ruleResults) {
      if (!["failed", "uncertain"].includes(row.status)) continue;
      const key = row.rule_id;
      if (seen.has(key)) continue;
      seen.add(key);
      citations.push(row.legal_basis);
    }
    return citations;
  }

  function buildReviewReport(payload, sir, ruleResults, rulePack, schema) {
    const applicable = ruleResults.filter((row) => row.status !== "not_applicable");
    const failed = applicable.filter((row) => row.status === "failed");
    const uncertain = applicable.filter((row) => row.status === "uncertain");
    const passed = applicable.filter((row) => row.status === "passed");

    const statusCounts = {};
    for (const row of ruleResults) {
      statusCounts[row.status] = (statusCounts[row.status] || 0) + 1;
    }

    const failedLogicTypeCounts = {};
    for (const row of failed) {
      failedLogicTypeCounts[row.logic_type] = (failedLogicTypeCounts[row.logic_type] || 0) + 1;
    }

    const activeFields = Array.from(
      new Set(
        applicable.flatMap((result) =>
          result.candidate_fields.filter((field) => sir.fields[field] && sir.fields[field].status !== "not_applicable")
        )
      )
    ).sort();

    const missingFields = Array.from(
      new Set(
        failed.flatMap((result) =>
          result.finding_fields.filter((field) => sir.fields[field] && sir.fields[field].status === "not_evidenced")
        )
      )
    ).sort();

    let finalDecision = "insufficient_scope";
    if (failed.length) finalDecision = "non_compliant";
    else if (uncertain.length) finalDecision = "needs_human_review";
    else if (passed.length) finalDecision = "compliant";

    return {
      artifact_type: "ch4_non_llm_review_report",
      version: "0.1.0",
      input_id: payload.input_id || "unnamed_input",
      review_scope: sir.context.review_scope,
      product_scope_hint: sir.context.product_scope_hint,
      channel_scope_hint: sir.context.channel_scope_hint,
      final_decision: finalDecision,
      should_escalate: Boolean(failed.length || uncertain.length),
      summary: {
        total_rules_in_pack: rulePack.length,
        applicable_rule_count: applicable.length,
        passed_rule_count: passed.length,
        failed_rule_count: failed.length,
        uncertain_rule_count: uncertain.length,
        status_counts: statusCounts,
        failed_logic_type_counts: failedLogicTypeCounts,
        active_sir_field_count: activeFields.length,
        missing_sir_field_count: missingFields.length,
      },
      active_rule_ids: applicable.map((row) => row.rule_id),
      active_sir_fields: activeFields,
      missing_sir_fields: missingFields,
      triggered_citations: collectTriggeredCitations(ruleResults),
      sir_fields: sir.fields,
      rule_results: ruleResults,
      schema_field_inventory: schema.fields.map((field) => field.field_name),
    };
  }

  function buildRuntimeTrace(payload, bundle) {
    const activeBundle = bundle || window.__CH4_RUNTIME_BUNDLE__;
    if (!activeBundle) {
      throw new Error("Runtime bundle is not loaded");
    }
    const normalizedInput = normalizeRuntimeInput(payload);
    const sir = extractSir(normalizedInput, activeBundle.sirSchema);
    const results = activeBundle.rulePack.map((rule) => evaluateRule(rule, sir.fields, sir.context));
    const reviewReport = buildReviewReport(normalizedInput, sir, results, activeBundle.rulePack, activeBundle.sirSchema);
    return {
      artifact_type: "ch4_runtime_trace",
      version: "0.1.0",
      normalized_input: normalizedInput,
      sir,
      applicable_rules: results.filter((row) => row.status !== "not_applicable"),
      failing_rules: results.filter((row) => row.status === "failed"),
      uncertain_rules: results.filter((row) => row.status === "uncertain"),
      triggered_citations: reviewReport.triggered_citations,
      review_report: reviewReport,
    };
  }

  window.CH4RuntimeEngine = {
    buildRuntimeTrace,
    normalizeRuntimeInput,
    extractSir,
  };
})();
