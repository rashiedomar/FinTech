const BUNDLE_PATHS = [
  "/data/finalized/ch4_fincpa/law_fincpa_main_ch4_dashboard_bundle.json",
  "../../data/finalized/ch4_fincpa/law_fincpa_main_ch4_dashboard_bundle.json",
];

const state = {
  bundle: null,
  filteredClauses: [],
  selectedRecordId: null,
  lang: "both",
};

const TOPIC_LABELS = {
  general_principle: { ko: "일반 원칙", en: "General Principle" },
  internal_control: { ko: "내부통제", en: "Internal Control" },
  consumer_fit_assessment: { ko: "적합성·적정성", en: "Consumer Fit Assessment" },
  explanation_duty: { ko: "설명의무", en: "Explanation Duty" },
  advertising_compliance: { ko: "광고 준수", en: "Advertising Compliance" },
  unfair_sales_practice: { ko: "불공정 영업행위", en: "Unfair Sales Practice" },
  improper_solicitation: { ko: "부당 권유", en: "Improper Solicitation" },
  other: { ko: "기타", en: "Other" },
};

const OBLIGATION_MODE_LABELS = {
  general_principle: { ko: "원칙형", en: "General Principle" },
  required_action: { ko: "행위 의무", en: "Required Action" },
  required_content: { ko: "기재·고지 의무", en: "Required Content" },
  prohibited_action: { ko: "금지 행위", en: "Prohibited Action" },
  workflow_control: { ko: "절차·통제", en: "Workflow Control" },
  recordkeeping: { ko: "기록 보존", en: "Recordkeeping" },
};

const PRODUCT_SCOPE_LABELS = {
  general: { ko: "공통", en: "General" },
  loan: { ko: "대출", en: "Loan" },
  deposit: { ko: "예금·적금", en: "Deposit" },
  investment: { ko: "투자", en: "Investment" },
  insurance: { ko: "보험", en: "Insurance" },
  multiple: { ko: "복합", en: "Multiple" },
  "general|investment": { ko: "공통·투자", en: "General|Investment" },
};

const CHANNEL_SCOPE_LABELS = {
  all_customer_facing: { ko: "모든 대고객 채널", en: "All Customer-Facing" },
  advertising: { ko: "광고", en: "Advertising" },
  contracting: { ko: "계약 체결", en: "Contracting" },
  solicitation: { ko: "권유", en: "Solicitation" },
  advisory: { ko: "자문", en: "Advisory" },
  "visit_sales|phone_sales": { ko: "방문·전화 판매", en: "Visit|Phone Sales" },
  "solicitation|contracting": { ko: "권유·계약", en: "Solicitation|Contracting" },
  "solicitation|visit_sales|phone_sales": { ko: "권유·방문·전화", en: "Solicitation|Visit|Phone" },
  "all_customer_facing|solicitation|contracting": { ko: "전 채널·권유·계약", en: "All CF|Solicitation|Contracting" },
  internal_control: { ko: "내부통제", en: "Internal Control" },
};

const TRIGGER_TYPE_LABELS = {
  must_do: { ko: "반드시 해야 함", en: "Must Do" },
  must_disclose: { ko: "반드시 표시/설명", en: "Must Disclose" },
  must_not_do: { ko: "하면 안 됨", en: "Must Not Do" },
  must_keep_record: { ko: "기록 보존 필요", en: "Must Keep Record" },
  must_have_control: { ko: "통제 체계 필요", en: "Must Have Control" },
  delegated_detail: { ko: "하위 규정 필요", en: "Delegated Detail" },
};

const OPERATIONALITY_LABELS = {
  direct_checkable: { ko: "직접 점검 가능", en: "Direct Checkable" },
  needs_subrule_design: { ko: "세부 규칙 설계 필요", en: "Needs Subrule Design" },
  delegated_to_decree: { ko: "시행령·하위규정 의존", en: "Delegated To Decree" },
};

const RULE_FAMILY_LABELS = {
  general_principle: { ko: "일반 원칙", en: "General Principle" },
  suitability: { ko: "적합성", en: "Suitability" },
  adequacy: { ko: "적정성", en: "Adequacy" },
  explanation: { ko: "설명의무", en: "Explanation" },
  advertising: { ko: "광고", en: "Advertising" },
  unfair_sales: { ko: "불공정 영업행위", en: "Unfair Sales" },
  solicitation: { ko: "권유", en: "Solicitation" },
  contract_documents: { ko: "계약서류", en: "Contract Documents" },
  internal_control: { ko: "내부통제", en: "Internal Control" },
  recordkeeping: { ko: "기록 보존", en: "Recordkeeping" },
  intermediary: { ko: "대리·중개", en: "Intermediary" },
  advisory: { ko: "자문", en: "Advisory" },
};

const LOGIC_TYPE_LABELS = {
  required_presence: { ko: "필수 정보 존재", en: "Required Presence" },
  prohibited_presence: { ko: "금지 신호 존재", en: "Prohibited Presence" },
  required_process: { ko: "필수 절차 존재", en: "Required Process" },
  required_record: { ko: "필수 기록 존재", en: "Required Record" },
  required_response: { ko: "필수 대응 존재", en: "Required Response" },
  delegated_detail: { ko: "하위 규정 필요", en: "Delegated Detail" },
  principle_guardrail: { ko: "원칙형 가드레일", en: "Principle Guardrail" },
};

const DETECTION_TARGET_LABELS = {
  content_text: { ko: "대고객 문구", en: "Content Text" },
  workflow_metadata: { ko: "워크플로 메타데이터", en: "Workflow Metadata" },
  consumer_profile: { ko: "소비자 프로필", en: "Consumer Profile" },
  document_bundle: { ko: "문서 묶음", en: "Document Bundle" },
  record_system: { ko: "기록 시스템", en: "Record System" },
  mixed: { ko: "복합", en: "Mixed" },
};

const SIR_LINK_TYPE_LABELS = {
  direct_content_field: { ko: "콘텐츠 필드 직접 연결", en: "Direct Content Field" },
  direct_workflow_field: { ko: "워크플로 필드 직접 연결", en: "Direct Workflow Field" },
  direct_record_field: { ko: "기록 필드 직접 연결", en: "Direct Record Field" },
  derived_decision_field: { ko: "파생 판단 필드", en: "Derived Decision Field" },
  delegated_external_detail: { ko: "하위 규정 추가 필요", en: "Delegated External Detail" },
  principle_only: { ko: "원칙형만 가능", en: "Principle Only" },
};

const EVIDENCE_SOURCE_LABELS = {
  visible_content: { ko: "보이는 콘텐츠", en: "Visible Content" },
  workflow_log: { ko: "워크플로 로그", en: "Workflow Log" },
  consumer_profile_form: { ko: "소비자 프로필 서식", en: "Consumer Profile Form" },
  explanation_form: { ko: "설명 서식", en: "Explanation Form" },
  contract_document: { ko: "계약 문서", en: "Contract Document" },
  record_archive: { ko: "기록 보관소", en: "Record Archive" },
  decree_reference: { ko: "시행령 참조", en: "Decree Reference" },
  mixed: { ko: "복합", en: "Mixed" },
};

const FIELD_NAME_LABELS = {
  consumer_type: { ko: "소비자 유형", en: "Consumer Type" },
  consumer_profile: { ko: "소비자 프로필", en: "Consumer Profile" },
  suitability_check: { ko: "적합성 점검", en: "Suitability Check" },
  adequacy_check: { ko: "적정성 점검", en: "Adequacy Check" },
  explanation_material: { ko: "설명 자료", en: "Explanation Material" },
  explanation_confirmation: { ko: "설명 확인", en: "Explanation Confirmation" },
  contract_document_delivery: { ko: "계약 문서 제공", en: "Contract Document Delivery" },
  seller_identity: { ko: "판매자 식별", en: "Seller Identity" },
  product_identity: { ko: "상품 식별", en: "Product Identity" },
  product_core_terms: { ko: "핵심 상품 조건", en: "Product Core Terms" },
  insurance_warning: { ko: "보험 경고 문구", en: "Insurance Warning" },
  investment_warning: { ko: "투자 경고 문구", en: "Investment Warning" },
  deposit_disclaimer: { ko: "예금 면책 문구", en: "Deposit Disclaimer" },
  loan_conditions: { ko: "대출 조건", en: "Loan Conditions" },
  loan_rate_basis: { ko: "대출 금리 기준", en: "Loan Rate Basis" },
  loan_interest_timing: { ko: "대출 이자 시기", en: "Loan Interest Timing" },
  loan_costs: { ko: "대출 비용", en: "Loan Costs" },
  solicitation_purpose: { ko: "권유 목적", en: "Solicitation Purpose" },
  representative_identity: { ko: "담당자 식별", en: "Representative Identity" },
  staff_registry: { ko: "인력 등록부", en: "Staff Registry" },
  internal_control_standard: { ko: "내부통제기준", en: "Internal Control Standard" },
  activity_record: { ko: "활동 기록", en: "Activity Record" },
  record_integrity_control: { ko: "기록 무결성 통제", en: "Record Integrity Control" },
  access_request: { ko: "열람 요청", en: "Access Request" },
  access_response: { ko: "열람 응답", en: "Access Response" },
  advisory_independence: { ko: "자문 독립성", en: "Advisory Independence" },
  intermediary_status: { ko: "대리·중개 상태", en: "Intermediary Status" },
  prohibited_claim_signal: { ko: "금지 주장 신호", en: "Prohibited Claim Signal" },
  fairness_guardrail: { ko: "공정성 가드레일", en: "Fairness Guardrail" },
};

const overviewCardsEl = document.getElementById("overviewCards");
const pipelineFlowEl = document.getElementById("pipelineFlow");
const topicFilterEl = document.getElementById("topicFilter");
const ruleFilterEl = document.getElementById("ruleFilter");
const searchInputEl = document.getElementById("searchInput");
const clauseListEl = document.getElementById("clauseList");
const clauseCountTextEl = document.getElementById("clauseCountText");
const detailHeaderEl = document.getElementById("detailHeader");
const detailBodyEl = document.getElementById("detailBody");
const fieldCatalogEl = document.getElementById("fieldCatalog");
const resetFiltersBtn = document.getElementById("resetFiltersBtn");
const statusBannerEl = document.getElementById("statusBanner");
const langSwitchEl = document.getElementById("langSwitch");

function textFor(ko, en) {
  if (state.lang === "ko") return ko;
  if (state.lang === "en") return en;
  return `${ko} / ${en}`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function labelText(item) {
  if (!item) return "";
  return textFor(item.ko || "", item.en || "");
}

function normalizeLabel(item, mapping = null) {
  if (!item) return { ko: "", en: "" };
  if (typeof item === "string") {
    if (mapping && mapping[item]) return mapping[item];
    return { ko: item, en: item };
  }
  if (item.ko || item.en) return item;
  return { ko: String(item), en: String(item) };
}

function normalizeLabelList(items, mapping = null) {
  if (!items) return [];
  if (Array.isArray(items)) return items.map((item) => normalizeLabel(item, mapping));
  if (typeof items === "string") {
    return items
      .split("|")
      .map((item) => item.trim())
      .filter(Boolean)
      .map((item) => normalizeLabel(item, mapping));
  }
  return [normalizeLabel(items, mapping)];
}

function renderPills(labels, accent = false) {
  if (!labels || !labels.length) return "";
  return `<div class="pill-row">${labels
    .map((item) => `<span class="pill ${accent ? "accent" : ""}">${escapeHtml(labelText(item))}</span>`)
    .join("")}</div>`;
}

function setStatus(message, visible = true) {
  statusBannerEl.textContent = message;
  statusBannerEl.classList.toggle("hidden", !visible);
}

function buildOverviewCards(bundle) {
  const cards = [
    [textFor("Parse 조항 수", "Parsed Clauses"), bundle.overview.parse_clause_count],
    [textFor("Layer 1 조항 수", "Layer 1 Clauses"), bundle.overview.layer1_clause_count],
    [textFor("Layer 2 의무 수", "Layer 2 Obligations"), bundle.overview.layer2_obligation_count],
    [textFor("Layer 3 후보 수", "Layer 3 Candidates"), bundle.overview.layer3_candidate_count],
    [textFor("Layer 4 규칙 수", "Layer 4 Rules"), bundle.overview.layer4_rule_count],
    [textFor("Layer 4 SIR 필드 수", "Layer 4 SIR Fields"), bundle.overview.layer4_field_count],
  ];
  overviewCardsEl.innerHTML = cards
    .map(
      ([label, value]) => `
      <article class="overview-card">
        <div class="label">${escapeHtml(label)}</div>
        <div class="value">${escapeHtml(value)}</div>
      </article>`
    )
    .join("");
}

function buildPipeline(bundle) {
  pipelineFlowEl.innerHTML = bundle.meta.layer_explanations
    .filter((step) => step.layer_id !== "retrieval")
    .map(
      (step) => `
      <article class="mini-card">
        <div class="step">${escapeHtml(textFor(step.title_ko, step.title_en))}</div>
        <div class="desc">${escapeHtml(textFor(step.meaning_ko, step.meaning_en))}</div>
      </article>`
    )
    .join("");
}

function fillTopicFilter(bundle) {
  const topics = Array.from(
    new Set(bundle.clauses.map((clause) => clause.layer1?.topic_family).filter(Boolean))
  );
  topicFilterEl.innerHTML =
    `<option value="">${escapeHtml(textFor("전체", "All"))}</option>` +
    topics
      .map((topic) => {
        const rawLabel = bundle.clauses.find((clause) => clause.layer1?.topic_family === topic)?.layer1?.topic_family_label;
        const label = normalizeLabel(rawLabel || topic, TOPIC_LABELS);
        return `<option value="${escapeHtml(topic)}">${escapeHtml(labelText(label) || topic)}</option>`;
      })
      .join("");
}

function applyFilters() {
  const search = searchInputEl.value.trim().toLowerCase();
  const topic = topicFilterEl.value;
  const ruleFilter = ruleFilterEl.value;
  const clauses = state.bundle.clauses.filter((clause) => {
    const haystack = [
      clause.record_id,
      clause.article_id,
      clause.paragraph_id,
      clause.article_title,
      clause.raw_text,
      clause.normalized_text,
    ]
      .join(" ")
      .toLowerCase();

    if (search && !haystack.includes(search)) return false;
    if (topic && clause.layer1?.topic_family !== topic) return false;
    if (ruleFilter === "has_rules" && clause.summary.layer4_count === 0) return false;
    if (ruleFilter === "no_rules" && clause.summary.layer4_count > 0) return false;
    return true;
  });

  state.filteredClauses = clauses;
  if (!clauses.find((clause) => clause.record_id === state.selectedRecordId)) {
    state.selectedRecordId = clauses[0]?.record_id || null;
  }
  renderClauseList();
  renderDetail();
}

function renderClauseList() {
  clauseCountTextEl.textContent = textFor(`${state.filteredClauses.length}개`, `${state.filteredClauses.length} items`);
  if (!state.filteredClauses.length) {
    clauseListEl.innerHTML = `<div class="empty-state">${escapeHtml(textFor("조건에 맞는 조항이 없습니다.", "No clauses match the current filters."))}</div>`;
    return;
  }
  clauseListEl.innerHTML = state.filteredClauses
    .map((clause) => {
      const active = clause.record_id === state.selectedRecordId ? "active" : "";
      return `
        <article class="clause-item ${active}" data-record-id="${escapeHtml(clause.record_id)}">
          <h3>${escapeHtml(clause.article_id)} ${escapeHtml(clause.paragraph_id)} ${escapeHtml(clause.article_title)}</h3>
          <p>${escapeHtml(clause.section_title)} · p.${escapeHtml(clause.page_start)}</p>
          <p>${escapeHtml((clause.normalized_text || clause.raw_text || "").slice(0, 110))}${(clause.normalized_text || clause.raw_text || "").length > 110 ? "..." : ""}</p>
          ${clause.layer1 ? renderPills([normalizeLabel(clause.layer1.topic_family_label || clause.layer1.topic_family, TOPIC_LABELS)], true) : ""}
          <div class="pill-row">
            <span class="pill">L2 ${clause.summary.layer2_count}</span>
            <span class="pill">L3 ${clause.summary.layer3_count}</span>
            <span class="pill">L4 ${clause.summary.layer4_count}</span>
          </div>
        </article>`;
    })
    .join("");

  clauseListEl.querySelectorAll(".clause-item").forEach((el) => {
    el.addEventListener("click", () => {
      state.selectedRecordId = el.dataset.recordId;
      renderClauseList();
      renderDetail();
    });
  });
}

function renderLayer2Item(item) {
  return `
    <div class="data-box">
      <h4>${escapeHtml(item.obligation_label)}</h4>
      ${renderPills(normalizeLabelList(item.product_scope_labels || item.product_scope, PRODUCT_SCOPE_LABELS), true)}
      ${renderPills(normalizeLabelList(item.channel_scope_labels || item.channel_scope, CHANNEL_SCOPE_LABELS))}
      <p><strong>${escapeHtml(textFor("의무 요약", "Obligation Summary"))}:</strong> ${escapeHtml(item.obligation_summary)}</p>
      <p><strong>${escapeHtml(textFor("트리거", "Trigger"))}:</strong> ${escapeHtml(labelText(normalizeLabel(item.trigger_type_label || item.trigger_type, TRIGGER_TYPE_LABELS)))}</p>
      <p><strong>${escapeHtml(textFor("운영 가능성", "Operationality"))}:</strong> ${escapeHtml(labelText(normalizeLabel(item.operationality_label || item.operationality, OPERATIONALITY_LABELS)))}</p>
      <pre>${escapeHtml(item.source_span_text || "")}</pre>
    </div>`;
}

function renderLayer3Item(item) {
  return `
    <div class="data-box">
      <h4>${escapeHtml(item.rule_candidate_id)}</h4>
      ${renderPills([normalizeLabel(item.rule_family_label || item.rule_family, RULE_FAMILY_LABELS)], true)}
      <p><strong>${escapeHtml(textFor("후보 규칙", "Candidate Rule"))}:</strong> ${escapeHtml(item.rule_candidate_summary)}</p>
      <p><strong>Logic:</strong> ${escapeHtml(labelText(normalizeLabel(item.logic_type_label || item.logic_type, LOGIC_TYPE_LABELS)))}</p>
      <p><strong>Detection:</strong> ${escapeHtml(labelText(normalizeLabel(item.detection_target_label || item.detection_target, DETECTION_TARGET_LABELS)))}</p>
      <p><strong>${escapeHtml(textFor("SIR 연결", "SIR Link"))}:</strong> ${escapeHtml(labelText(normalizeLabel(item.sir_link_type_label || item.sir_link_type, SIR_LINK_TYPE_LABELS)))}</p>
      ${renderPills(normalizeLabelList(item.sir_candidate_field_labels || item.sir_candidate_fields, FIELD_NAME_LABELS))}
      <p><strong>${escapeHtml(textFor("증거원", "Evidence Source"))}:</strong> ${escapeHtml(labelText(normalizeLabel(item.evidence_source_label || item.evidence_source, EVIDENCE_SOURCE_LABELS)))}</p>
      <p><strong>ready_for_v1:</strong> ${escapeHtml(item.ready_for_v1)}</p>
    </div>`;
}

function renderLayer4Item(item) {
  return `
    <div class="data-box">
      <h4>${escapeHtml(item.rule_id)}</h4>
      ${renderPills([normalizeLabel(item.rule_family_label || item.rule_family, RULE_FAMILY_LABELS)], true)}
      ${renderPills(normalizeLabelList(item.product_scope_labels || item.product_scope, PRODUCT_SCOPE_LABELS))}
      <p><strong>${escapeHtml(textFor("MVP 규칙 요약", "MVP Rule Summary"))}:</strong> ${escapeHtml(item.rule_candidate_summary)}</p>
      <p><strong>Logic:</strong> ${escapeHtml(labelText(normalizeLabel(item.logic_type_label || item.logic_type, LOGIC_TYPE_LABELS)))}</p>
      <p><strong>Detection:</strong> ${escapeHtml(labelText(normalizeLabel(item.detection_target_label || item.detection_target, DETECTION_TARGET_LABELS)))}</p>
      <p><strong>${escapeHtml(textFor("평가 힌트", "Evaluation Hint"))}:</strong> ${escapeHtml(item.evaluation_hint)}</p>
      ${renderPills(normalizeLabelList(item.sir_candidate_field_labels || item.sir_candidate_fields, FIELD_NAME_LABELS))}
      <p><strong>${escapeHtml(textFor("증거원", "Evidence Source"))}:</strong> ${escapeHtml(labelText(normalizeLabel(item.evidence_source_label || item.evidence_source, EVIDENCE_SOURCE_LABELS)))}</p>
    </div>`;
}

function renderDetail() {
  const clause = state.bundle.clauses.find((item) => item.record_id === state.selectedRecordId);
  if (!clause) {
    detailHeaderEl.innerHTML = `<div class="empty-state">${escapeHtml(textFor("왼쪽에서 조항을 선택하세요.", "Select a clause from the left list."))}</div>`;
    detailBodyEl.innerHTML = "";
    return;
  }

  detailHeaderEl.innerHTML = `
    <h2>${escapeHtml(clause.article_id)} ${escapeHtml(clause.paragraph_id)} ${escapeHtml(clause.article_title)}</h2>
    <p>${escapeHtml(clause.section_title)} · 페이지 ${escapeHtml(clause.page_start)} · record_id: ${escapeHtml(clause.record_id)}</p>
    <div class="pill-row">
      <span class="pill accent">Layer 2 ${clause.summary.layer2_count}</span>
      <span class="pill accent">Layer 3 ${clause.summary.layer3_count}</span>
      <span class="pill accent">Layer 4 ${clause.summary.layer4_count}</span>
      <span class="pill accent">SIR fields ${clause.summary.sir_field_count}</span>
    </div>
  `;

  detailBodyEl.innerHTML = `
    <section class="layer-card">
      <h3>${escapeHtml(textFor("Layer 0. 파싱", "Layer 0. Parsing"))}</h3>
      <p class="layer-note">${escapeHtml(textFor("공식 법령 PDF에서 잘라낸 원문과 정규화 텍스트입니다.", "Raw and normalized source text segmented from the official PDF."))}</p>
      <div class="grid-two">
        <div class="data-box">
          <h4>${escapeHtml(textFor("원문 raw_text", "Source raw_text"))}</h4>
          <pre>${escapeHtml(clause.raw_text)}</pre>
        </div>
        <div class="data-box">
          <h4>${escapeHtml(textFor("정규화 normalized_text", "Normalized normalized_text"))}</h4>
          <pre>${escapeHtml(clause.normalized_text)}</pre>
        </div>
      </div>
    </section>

    <section class="layer-card">
      <h3>${escapeHtml(textFor("Layer 1. 조항 메타데이터", "Layer 1. Clause Metadata"))}</h3>
      <p class="layer-note">${escapeHtml(textFor("이 조항이 어떤 주제인지, 어떤 범위인지, 다음 단계에서 분해가 필요한지 부여한 레이어입니다.", "This layer adds topic, scope, and whether decomposition is needed."))}</p>
      ${
        clause.layer1
          ? `
          <div class="grid-two">
            <div class="data-box">
              <h4>${escapeHtml(textFor("핵심 메타데이터", "Core Metadata"))}</h4>
              ${renderPills([normalizeLabel(clause.layer1.topic_family_label || clause.layer1.topic_family, TOPIC_LABELS)], true)}
              ${renderPills([normalizeLabel(clause.layer1.obligation_mode_label || clause.layer1.obligation_mode, OBLIGATION_MODE_LABELS)])}
              ${renderPills(normalizeLabelList(clause.layer1.product_scope_labels || clause.layer1.product_scope, PRODUCT_SCOPE_LABELS))}
              ${renderPills(normalizeLabelList(clause.layer1.channel_scope_labels || clause.layer1.channel_scope, CHANNEL_SCOPE_LABELS))}
              <p><strong>${escapeHtml(textFor("분해 필요", "Needs Decomposition"))}:</strong> ${escapeHtml(clause.layer1.needs_decomposition)}</p>
              <p><strong>${escapeHtml(textFor("우리 workflow 관련성", "Workflow Relevance"))}:</strong> ${escapeHtml(clause.layer1.is_relevant_to_theme2)}</p>
            </div>
            <div class="data-box">
              <h4>Gemini 설명</h4>
              <p>${escapeHtml(clause.layer1.gemini_reasoning_summary)}</p>
              <p><strong>${escapeHtml(textFor("모델", "Model"))}:</strong> ${escapeHtml(clause.layer1.gemini_model)}</p>
              <p><strong>${escapeHtml(textFor("신뢰도", "Confidence"))}:</strong> ${escapeHtml(clause.layer1.gemini_confidence)}</p>
            </div>
          </div>`
          : `<div class="empty-state">${escapeHtml(textFor("Layer 1 데이터가 없습니다.", "No Layer 1 data for this clause."))}</div>`
      }
    </section>

    <section class="layer-card">
      <h3>${escapeHtml(textFor("Layer 2. 의무 분해", "Layer 2. Obligation Decomposition"))}</h3>
      <p class="layer-note">${escapeHtml(textFor("한 조항 안의 여러 의무를 작게 쪼개서 이후 규칙 설계가 가능하도록 만든 레이어입니다.", "This layer splits one clause into smaller obligation units for later rule design."))}</p>
      <div class="stack">
        ${clause.layer2.length ? clause.layer2.map(renderLayer2Item).join("") : `<div class="empty-state">${escapeHtml(textFor("Layer 2 의무가 없습니다.", "No Layer 2 obligations for this clause."))}</div>`}
      </div>
    </section>

    <section class="layer-card">
      <h3>${escapeHtml(textFor("Layer 3. 규칙 / SIR 후보", "Layer 3. Rule / SIR Candidates"))}</h3>
      <p class="layer-note">${escapeHtml(textFor("Layer 2 의무를 기준으로 미래 규칙 형태와 SIR 필드 후보를 제안한 레이어입니다.", "This layer proposes future rule shapes and candidate SIR fields from each obligation."))}</p>
      <div class="stack">
        ${clause.layer3.length ? clause.layer3.map(renderLayer3Item).join("") : `<div class="empty-state">${escapeHtml(textFor("Layer 3 후보가 없습니다.", "No Layer 3 candidates for this clause."))}</div>`}
      </div>
    </section>

    <section class="layer-card">
      <h3>${escapeHtml(textFor("Layer 4. 최종 MVP 고정", "Layer 4. Final MVP Freeze"))}</h3>
      <p class="layer-note">${escapeHtml(textFor("Layer 3 후보 중 ready_for_v1=yes만 살려서 실제 MVP 규칙과 SIR 필드로 고정한 레이어입니다.", "This layer keeps only ready_for_v1=yes candidates and freezes them into the MVP rule pack and SIR fields."))}</p>
      <div class="stack">
        ${clause.layer4.length ? clause.layer4.map(renderLayer4Item).join("") : `<div class="empty-state">${escapeHtml(textFor("이 조항은 아직 Layer 4 MVP 규칙으로 채택되지 않았습니다.", "This clause has not yet been included in the Layer 4 MVP rule pack."))}</div>`}
      </div>
    </section>
  `;
}

function renderFieldCatalog(bundle) {
  fieldCatalogEl.innerHTML = bundle.catalogs.field_catalog
    .map(
      (field) => `
      <article class="field-card">
        <h3>${escapeHtml(labelText(normalizeLabel(field.field_label || field.field_name, FIELD_NAME_LABELS)))} <span style="opacity:.6;font-weight:500;">${escapeHtml(field.field_name)}</span></h3>
        ${renderPills([normalizeLabel(field.field_group_label || field.field_group, DETECTION_TARGET_LABELS)], true)}
        <p>${escapeHtml(field.description || "")}</p>
        <div class="pill-row">
          <span class="pill">priority ${escapeHtml(field.mvp_priority)}</span>
          <span class="pill">rules ${escapeHtml(field.source_rule_count)}</span>
          <span class="pill">obligations ${escapeHtml(field.source_obligation_count)}</span>
        </div>
      </article>`
    )
    .join("");
}

function updateLanguageButtons() {
  langSwitchEl.querySelectorAll("[data-lang]").forEach((button) => {
    button.classList.toggle("active", button.dataset.lang === state.lang);
  });
}

function rerenderAll() {
  if (!state.bundle) return;
  buildOverviewCards(state.bundle);
  buildPipeline(state.bundle);
  fillTopicFilter(state.bundle);
  renderFieldCatalog(state.bundle);
  applyFilters();
}

async function loadBundle() {
  if (window.__CH4_DASHBOARD_BUNDLE__) return window.__CH4_DASHBOARD_BUNDLE__;
  let lastError = null;
  for (const path of BUNDLE_PATHS) {
    try {
      const response = await fetch(path);
      if (!response.ok) throw new Error(`HTTP ${response.status} on ${path}`);
      return await response.json();
    } catch (error) {
      lastError = error;
    }
  }
  throw lastError || new Error("Unable to load dashboard bundle");
}

async function init() {
  const bundle = await loadBundle();
  state.bundle = bundle;
  state.selectedRecordId = bundle.clauses[0]?.record_id || null;

  buildOverviewCards(bundle);
  buildPipeline(bundle);
  fillTopicFilter(bundle);
  renderFieldCatalog(bundle);
  setStatus(textFor("대시보드 데이터 로딩 완료", "Dashboard data loaded"), false);

  searchInputEl.addEventListener("input", applyFilters);
  topicFilterEl.addEventListener("change", applyFilters);
  ruleFilterEl.addEventListener("change", applyFilters);
  langSwitchEl.querySelectorAll("[data-lang]").forEach((button) => {
    button.addEventListener("click", () => {
      state.lang = button.dataset.lang;
      updateLanguageButtons();
      rerenderAll();
    });
  });
  resetFiltersBtn.addEventListener("click", () => {
    searchInputEl.value = "";
    topicFilterEl.value = "";
    ruleFilterEl.value = "";
    applyFilters();
  });

  updateLanguageButtons();
  applyFilters();
}

init().catch((error) => {
  setStatus(
    textFor(
      `대시보드 로딩 실패: ${error.message}. 직접 HTML만 열었다면 python scripts/run_ch4_dashboard.py 로 서버를 띄우거나, 새로 생성된 dashboard-bundle.js 가 존재하는지 확인하세요.`,
      `Dashboard failed to load: ${error.message}. If you opened the HTML directly, run python scripts/run_ch4_dashboard.py or confirm dashboard-bundle.js exists.`
    ),
    true
  );
  detailHeaderEl.innerHTML = `<div class="empty-state">${escapeHtml(textFor("대시보드 로딩 실패", "Dashboard failed to load"))}</div>`;
});
