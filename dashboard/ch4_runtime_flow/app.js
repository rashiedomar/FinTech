const EXAMPLES = [
  {
    id: "loan_ad_content_only",
    label: "대출 광고",
    description: "금리 기준과 이자 부과 시기가 빠진 대출 광고 예시입니다.",
  },
  {
    id: "investment_ad_guaranteed_return_violation",
    label: "투자 광고",
    description: "원금 보장·확정 수익 표현을 사용한 투자 광고 예시입니다.",
  },
  {
    id: "insurance_ad_missing_warning",
    label: "보험 광고",
    description: "필수 경고 문구가 빠진 보험 광고 예시입니다.",
  },
  {
    id: "deposit_ad_missing_disclaimer",
    label: "예금 광고",
    description: "필수 안내 문구가 빠지고 수익 표현이 강한 예금 광고 예시입니다.",
  },
  {
    id: "solicitation_improper_claim_violation",
    label: "권유 스크립트",
    description: "제21조 부당 권유 표현이 포함된 권유 스크립트 예시입니다.",
  },
  {
    id: "access_request_record_only",
    label: "열람 요청",
    description: "기록 보존·열람 처리 흐름 예시입니다.",
  },
  {
    id: "investment_solicitation_full",
    label: "준수 예시",
    description: "메타데이터가 충분하고 통과하는 예시입니다.",
  },
];

const STAGES = [
  { id: "schema", title: "런타임 스키마", subtitle: "입력 문구가 정규화된 실행 계약으로 바뀝니다." },
  { id: "sir", title: "SIR 추출", subtitle: "텍스트와 메타데이터를 구조화된 필드 상태로 매핑합니다." },
  { id: "rules", title: "적용 규칙", subtitle: "현재 입력에 관련된 Layer 4 규칙만 남깁니다." },
  { id: "law", title: "법적 근거", subtitle: "실패 또는 불확실 규칙의 법 조항 근거를 보여줍니다." },
  { id: "result", title: "결정형 결과", subtitle: "비LLM 코어가 법적 검토 결론을 출력합니다." },
  { id: "llm", title: "오프라인 LLM 자문", subtitle: "번들된 Gemini 출력이 설명과 안전한 수정안을 제공합니다." },
  { id: "human", title: "인간 승인 + 감사 패킷", subtitle: "리뷰어가 최종 조치를 선택하고 패킷을 내려받습니다." },
];

const DEFAULT_REVIEWER_ID = "team_demo_reviewer";

const FIELD_LABELS = {
  seller_identity: "판매자 식별",
  product_identity: "상품 식별",
  product_core_terms: "핵심 상품 조건",
  explanation_material: "설명 자료",
  explanation_confirmation: "설명 확인",
  prohibited_claim_signal: "금지 표현 신호",
  deposit_disclaimer: "예금 안내 문구",
  investment_warning: "투자 위험 경고",
  insurance_warning: "보험 경고 문구",
  loan_conditions: "대출 조건",
  loan_rate_basis: "대출 금리 기준",
  loan_interest_timing: "대출 이자 시기",
  loan_costs: "대출 비용",
  solicitation_purpose: "권유 목적",
  representative_identity: "담당자 식별",
  staff_registry: "인력 등록부",
  internal_control_standard: "내부통제 기준",
  activity_record: "활동 기록",
  record_integrity_control: "기록 무결성 통제",
  access_request: "열람 요청",
  access_response: "열람 응답",
  advisory_independence: "자문 독립성",
  intermediary_status: "대리·중개 상태",
  consumer_profile: "소비자 프로필",
  suitability_check: "적합성 점검",
  adequacy_check: "적정성 점검",
  contract_document_delivery: "계약 문서 제공",
};

const STATUS_LABELS = {
  present: "확인됨",
  not_evidenced: "미확인",
  not_applicable: "해당 없음",
  uncertain: "불확실",
  passed: "통과",
  failed: "실패",
  pending: "대기",
};

const DECISION_LABELS = {
  compliant: "준수",
  non_compliant: "위반",
  insufficient_scope: "범위 부족",
  needs_human_review: "인간 검토 필요",
  approve: "승인",
  approve_with_edits: "수정 후 승인",
  reject: "반려",
  escalate: "에스컬레이션",
  pending: "대기",
};

const RULE_FAMILY_LABELS = {
  advertising: "광고",
  solicitation: "권유",
  explanation: "설명의무",
  suitability: "적합성",
  adequacy: "적정성",
  internal_control: "내부통제",
  recordkeeping: "기록 보존",
  contract_documents: "계약 문서",
  intermediary: "대리·중개",
  advisory: "자문",
  general_principle: "일반 원칙",
  unfair_sales: "불공정 영업행위",
};

const LOGIC_TYPE_LABELS = {
  required_presence: "필수 정보 존재",
  prohibited_presence: "금지 신호 존재",
  required_process: "필수 절차 존재",
  required_record: "필수 기록 존재",
  required_response: "필수 대응 존재",
  delegated_detail: "하위 규정 필요",
  principle_guardrail: "원칙형 가드레일",
};

const state = {
  selectedExample: null,
  trace: null,
  unlockedStageIndex: -1,
  humanDecision: "",
  reviewerId: DEFAULT_REVIEWER_ID,
  reviewerNote: "",
};

const promptInput = document.getElementById("promptInput");
const exampleChips = document.getElementById("exampleChips");
const profileHint = document.getElementById("profileHint");
const runBtn = document.getElementById("runBtn");
const clearBtn = document.getElementById("clearBtn");
const runtimeExperience = document.getElementById("runtimeExperience");
const stageButtons = document.getElementById("stageButtons");
const statusBanner = document.getElementById("statusBanner");
const runtimeBundle = window.__CH4_RUNTIME_BUNDLE__ || null;
const runtimeEngine = window.CH4RuntimeEngine || null;

const stageElements = {
  schema: document.getElementById("stage-schema"),
  sir: document.getElementById("stage-sir"),
  rules: document.getElementById("stage-rules"),
  law: document.getElementById("stage-law"),
  result: document.getElementById("stage-result"),
  llm: document.getElementById("stage-llm"),
  human: document.getElementById("stage-human"),
};

init();

function init() {
  if (!runtimeBundle || !runtimeEngine) {
    showStatus("런타임 번들을 불러오지 못했습니다. `runtime-bundle.js`를 다시 빌드하세요.", true);
    return;
  }
  renderExampleChips();
  renderStageButtons();
  bindEvents();
}

function bindEvents() {
  runBtn.addEventListener("click", runWorkflow);
  clearBtn.addEventListener("click", clearComposer);
  promptInput.addEventListener("input", onPromptInputChange);

  document.addEventListener("click", (event) => {
    const revealButton = event.target.closest("[data-reveal-index]");
    if (revealButton) {
      const targetIndex = Number.parseInt(revealButton.dataset.revealIndex, 10);
      if (!Number.isNaN(targetIndex) && targetIndex > state.unlockedStageIndex) {
        state.unlockedStageIndex = targetIndex;
        updateStageButtons();
        const stage = STAGES[targetIndex];
        if (stage) {
          stageElements[stage.id]?.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      }
      return;
    }

    const decisionButton = event.target.closest("[data-human-decision]");
    if (decisionButton) {
      state.humanDecision = decisionButton.dataset.humanDecision;
      if (!state.reviewerNote.trim()) {
        state.reviewerNote = defaultHumanNote(state.trace?.review_report, state.humanDecision);
      }
      renderHumanStage();
      updateStageButtons();
      return;
    }

    const suggestButton = event.target.closest("[data-use-suggested-prompt]");
    if (suggestButton) {
      applySuggestedPrompt();
      return;
    }

    const downloadButton = event.target.closest("[data-download-packet]");
    if (downloadButton) {
      downloadPacket(downloadButton.dataset.downloadPacket);
    }
  });

  document.addEventListener("input", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) {
      return;
    }
    if (target.matches("[data-human-field='reviewer_id']")) {
      state.reviewerId = target.value;
      return;
    }
    if (target.matches("[data-human-field='reviewer_note']")) {
      state.reviewerNote = target.value;
    }
  });
}

function renderExampleChips() {
  exampleChips.innerHTML = "";
  for (const example of EXAMPLES) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "chip";
    button.textContent = example.label;
    button.title = example.description;
    button.addEventListener("click", () => selectExample(example));
    if (state.selectedExample?.id === example.id) {
      button.classList.add("active");
    }
    exampleChips.appendChild(button);
  }
}

function renderStageButtons() {
  stageButtons.innerHTML = "";
  STAGES.forEach((stage, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "stage-nav-btn";
    button.dataset.stageId = stage.id;
    button.disabled = true;
    button.innerHTML = `
      <span class="stage-dot">${index + 1}</span>
      <span class="stage-nav-copy">
        <strong>${stage.title}</strong>
        <span>${stage.subtitle}</span>
      </span>
    `;
    button.addEventListener("click", () => unlockStage(index));
    stageButtons.appendChild(button);
  });
}

async function selectExample(example) {
  try {
    const payload = runtimeBundle.examples?.[example.id];
    if (!payload) {
      throw new Error(`런타임 번들에 예시가 없습니다: ${example.id}`);
    }
    state.selectedExample = { ...example, payload };
    promptInput.value = payload.content_text || "";
    profileHint.textContent = `${example.label} 프로필을 적용했습니다. ${example.description}`;
    renderExampleChips();
  } catch (error) {
    showStatus(`예시를 불러오지 못했습니다: ${error.message}`, true);
  }
}

function clearComposer() {
  state.selectedExample = null;
  state.trace = null;
  state.unlockedStageIndex = -1;
  state.humanDecision = "";
  state.reviewerId = DEFAULT_REVIEWER_ID;
  state.reviewerNote = "";
  promptInput.value = "";
  profileHint.textContent = "직접 입력은 자동 추론 모드로 실행됩니다.";
  runtimeExperience.classList.add("hidden");
  clearStageCards();
  renderExampleChips();
  updateStageButtons();
}

function onPromptInputChange() {
  if (!state.selectedExample) {
    return;
  }
  profileHint.textContent = `${state.selectedExample.label} 프로필이 유지됩니다. 자동 전체 추론으로 바꾸려면 초기화를 누르세요.`;
}

async function runWorkflow() {
  const text = promptInput.value.trim();
  if (!text) {
    showStatus("먼저 문구를 입력하거나 예시를 선택하세요.", true);
    return;
  }

  const payload = buildPayloadFromComposer(text);
  runBtn.disabled = true;
  runBtn.textContent = "실행 중...";
  showStatus("브라우저에서 제4장 결정형 워크플로를 실행하고 있습니다...", false);

  try {
    state.trace = runtimeEngine.buildRuntimeTrace(payload, runtimeBundle);
    initializeHumanState();
    state.unlockedStageIndex = 0;
    runtimeExperience.classList.remove("hidden");
    renderAllStages();
    updateStageButtons();
    showStatus("워크플로를 생성했습니다. 순서대로 각 단계를 열어보세요.", false);
  } catch (error) {
    showStatus(`실행 실패: ${error.message}`, true);
  } finally {
    runBtn.disabled = false;
    runBtn.textContent = "워크플로 실행";
  }
}

function buildPayloadFromComposer(text) {
  if (state.selectedExample?.payload) {
    const payload = structuredClone(state.selectedExample.payload);
    payload.content_text = text;
    if (!payload.title) {
      payload.title = deriveTitle(text);
    }
    return payload;
  }

  return {
    input_id: `custom_${Date.now()}`,
    title: deriveTitle(text),
    content_text: text,
    review_scope: "content_only",
    product_scope_hint: [],
    channel_scope_hint: [],
    business_role_hint: "",
    include_rule_families: [],
    exclude_rule_families: [],
    field_inputs: {},
    content_metadata: {},
    workflow_metadata: {},
    record_metadata: {},
  };
}

function initializeHumanState() {
  const artifacts = getActiveExampleArtifacts();
  const completed = artifacts?.humanReviewCompleted;
  const report = state.trace?.review_report;
  state.reviewerId = completed?.completed_review?.reviewer_id || DEFAULT_REVIEWER_ID;
  state.humanDecision = completed?.completed_review?.decision || recommendDecision(report);
  state.reviewerNote =
    completed?.draft_review_form?.reviewer_note ||
    completed?.completed_review?.reviewer_note ||
    defaultHumanNote(report, state.humanDecision);
}

function deriveTitle(text) {
  return text.split(/\n+/)[0].slice(0, 40);
}

function renderAllStages() {
  renderSchemaStage();
  renderSirStage();
  renderRulesStage();
  renderLawStage();
  renderResultStage();
  renderLlmStage();
  renderHumanStage();
}

function clearStageCards() {
  Object.values(stageElements).forEach((node) => {
    node.className = "stage-card locked";
    node.innerHTML = "";
  });
}

function unlockStage(index) {
  if (!state.trace || index > state.unlockedStageIndex) {
    return;
  }
  if (index === state.unlockedStageIndex && state.unlockedStageIndex < STAGES.length - 1) {
    state.unlockedStageIndex += 1;
  }
  updateStageButtons();
  const nextStage = STAGES[Math.min(state.unlockedStageIndex, STAGES.length - 1)];
  if (nextStage) {
    document.getElementById(`stage-${nextStage.id}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

function updateStageButtons() {
  const buttons = stageButtons.querySelectorAll(".stage-nav-btn");
  buttons.forEach((button, index) => {
    button.disabled = !state.trace || index > state.unlockedStageIndex;
    button.classList.remove("active", "completed", "unlocked");
    if (!state.trace) {
      return;
    }
    if (index < state.unlockedStageIndex) {
      button.classList.add("completed");
    } else if (index === state.unlockedStageIndex) {
      button.classList.add("active", "unlocked");
    }
  });
  applyStageClasses();
}

function applyStageClasses() {
  STAGES.forEach((stage, index) => {
    const card = stageElements[stage.id];
    if (!card) {
      return;
    }
    card.classList.remove("locked", "active");
    if (!state.trace || index > state.unlockedStageIndex) {
      card.classList.add("locked");
    } else if (index === state.unlockedStageIndex) {
      card.classList.add("active");
    }
  });
}

function renderSchemaStage() {
  stageElements.schema.innerHTML = buildStageFrame({
    stage: STAGES[0],
    body: `<pre class="json-panel">${escapeHtml(JSON.stringify(state.trace.normalized_input, null, 2))}</pre>`,
    footerButton: buildFooterButton(0, "SIR 추출 보기"),
  });
}

function renderSirStage() {
  const fields = Object.values(state.trace.sir.fields);
  const grouped = {
    present: fields.filter((field) => field.status === "present"),
    missing: fields.filter((field) => field.status === "not_evidenced"),
    uncertain: fields.filter((field) => field.status === "uncertain"),
    na: fields.filter((field) => field.status === "not_applicable"),
  };

  const sections = [
    renderFieldGroup("확인됨", grouped.present, "status-present"),
    renderFieldGroup("미확인", grouped.missing, "status-missing"),
    renderFieldGroup("불확실", grouped.uncertain, "status-uncertain"),
    renderFieldGroup("해당 없음", grouped.na, "status-na"),
  ].join("");

  stageElements.sir.innerHTML = buildStageFrame({
    stage: STAGES[1],
    body: `<div class="field-groups">${sections}</div>`,
    footerButton: buildFooterButton(1, "적용 규칙 보기"),
  });
}

function renderRulesStage() {
  const rules = state.trace.applicable_rules;
  const cards = rules
    .map((rule) => {
      const statusClass = mapStatusClass(rule.status);
      const fieldBadges = rule.candidate_fields.map((field) => `<span class="meta-pill">${escapeHtml(formatFieldLabel(field))}</span>`).join("");
      return `
        <div class="rule-card">
          <div class="stage-head">
            <div class="stage-title">
              <h4>${escapeHtml(rule.rule_id)}</h4>
              <p>${escapeHtml(rule.summary)}</p>
            </div>
            <span class="status-pill ${statusClass}">${escapeHtml(formatStatusLabel(rule.status))}</span>
          </div>
          <div class="rule-meta">
            <span class="meta-pill">${escapeHtml(formatRuleFamilyLabel(rule.rule_family))}</span>
            <span class="meta-pill">${escapeHtml(formatLogicTypeLabel(rule.logic_type))}</span>
            <span class="meta-pill">${escapeHtml(rule.article_id)}</span>
          </div>
          <div class="rule-meta">${fieldBadges || '<span class="meta-pill">필드 없음</span>'}</div>
        </div>
      `;
    })
    .join("");

  stageElements.rules.innerHTML = buildStageFrame({
    stage: STAGES[2],
    body: `<div class="rule-list">${cards}</div>`,
    footerButton: buildFooterButton(2, "법적 근거 보기"),
  });
}

function renderLawStage() {
  const citations = state.trace.triggered_citations;
  const body = citations.length
    ? citations
        .map(
          (citation) => `
            <div class="citation-card">
              <h4>${escapeHtml(citation.citation_label)}</h4>
              <div class="citation-meta">
                <span class="meta-pill">${escapeHtml(citation.article_title)}</span>
                <span class="meta-pill">${escapeHtml(citation.section_title)}</span>
              </div>
              <p>${escapeHtml(citation.summary)}</p>
              <p class="source-span">${escapeHtml(citation.source_span_text)}</p>
            </div>
          `
        )
        .join("")
    : `<div class="citation-card"><h4>추가 법적 근거 없음</h4><p>이번 실행에서는 실패 또는 불확실 규칙이 없어 별도의 법적 근거 카드가 생성되지 않았습니다.</p></div>`;

  stageElements.law.innerHTML = buildStageFrame({
    stage: STAGES[3],
    body: `<div class="citation-list">${body}</div>`,
    footerButton: buildFooterButton(3, "결정형 결과 보기"),
  });
}

function renderResultStage() {
  const report = state.trace.review_report;
  const decisionClass = `result-${report.final_decision}`;
  const metrics = [
    metricBlock(report.summary.applicable_rule_count, "적용 규칙 수"),
    metricBlock(report.summary.failed_rule_count, "실패 규칙 수"),
    metricBlock(report.summary.missing_sir_field_count, "누락 필드 수"),
    metricBlock(report.should_escalate ? "예" : "아니오", "에스컬레이션"),
  ].join("");

  const missingFields = report.missing_sir_fields.length
    ? report.missing_sir_fields.map((field) => `<span class="meta-pill">${escapeHtml(formatFieldLabel(field))}</span>`).join("")
    : `<span class="meta-pill">없음</span>`;

  stageElements.result.innerHTML = buildStageFrame({
    stage: STAGES[4],
    body: `
      <div class="result-card">
        <div class="result-banner">
          <div>
            <p class="eyebrow">최종 결정형 결과</p>
            <h3>${escapeHtml(formatDecisionLabel(report.final_decision))}</h3>
          </div>
          <span class="status-pill ${decisionClass}">${escapeHtml(formatDecisionLabel(report.final_decision))}</span>
        </div>
        <div class="result-metrics">${metrics}</div>
        <div>
          <p class="mini-label">누락된 SIR 필드</p>
          <div class="rule-meta">${missingFields}</div>
        </div>
      </div>
    `,
    footerButton: buildFooterButton(4, "오프라인 LLM 자문 보기"),
  });
}

function renderLlmStage() {
  const report = state.trace.review_report;
  const artifacts = getActiveExampleArtifacts();
  const advisoryOutput = artifacts?.geminiAdvisoryOutput;
  const advisoryInput = artifacts?.llmAdvisoryInput;
  const suggestedRewriteReport = artifacts?.suggestedRewriteReport;
  const modelName =
    artifacts?.humanReviewCompleted?.completed_review?.llm_model ||
    artifacts?.geminiRawResponse?.modelVersion ||
    "gemini-2.5-flash";

  if (!advisoryOutput || !advisoryInput) {
    stageElements.llm.innerHTML = buildStageFrame({
      stage: STAGES[5],
      body: `
        <div class="citation-card">
          <h4>이 입력에는 오프라인 자문이 번들되어 있지 않습니다</h4>
          <p>GitHub 데모는 Gemini를 실시간 호출하지 않습니다. 번들된 원본 예시를 그대로 선택하면 사전 계산된 Gemini 설명, 수정안, 인간 검토 패킷을 볼 수 있습니다.</p>
          <p class="source-span">현재 실행 결과도 인간 승인 단계에서 감사 패킷으로 내려받을 수 있습니다.</p>
        </div>
      `,
      footerButton: buildFooterButton(5, "인간 승인 + 감사 패킷 보기"),
    });
    return;
  }

  const actions = (advisoryOutput.remediation_actions || [])
    .map((action) => `<li>${escapeHtml(normalizeNarrativeText(action))}</li>`)
    .join("");
  const citations = (advisoryOutput.citation_list || [])
    .map((citation) => `<span class="meta-pill">${escapeHtml(citation)}</span>`)
    .join("");

  const rewriteOutcome = suggestedRewriteReport
    ? `
      <div class="rule-card advisory-card">
        <h4>수정안 재검증 결과</h4>
        <div class="rule-meta">
          <span class="status-pill result-${escapeHtml(suggestedRewriteReport.final_decision)}">${escapeHtml(formatDecisionLabel(suggestedRewriteReport.final_decision))}</span>
          <span class="meta-pill">실패 규칙 ${escapeHtml(String(suggestedRewriteReport.summary.failed_rule_count))}개</span>
          <span class="meta-pill">누락 필드 ${escapeHtml(String(suggestedRewriteReport.summary.missing_sir_field_count))}개</span>
        </div>
        <p>${escapeHtml(describeSuggestedOutcome(suggestedRewriteReport))}</p>
      </div>
    `
    : "";

  const suggestButton =
    report.final_decision !== "compliant"
      ? `
        <div class="action-row">
          <button type="button" class="run-btn suggest-btn" data-use-suggested-prompt="1">수정안 적용하기</button>
          <p class="profile-hint">입력창을 번들된 Gemini 수정안으로 바꾼 뒤 다시 워크플로를 실행할 수 있습니다.</p>
        </div>
      `
      : "";

  stageElements.llm.innerHTML = buildStageFrame({
    stage: STAGES[5],
    body: `
      <div class="result-card llm-hero">
        <div class="result-banner">
          <div>
            <p class="eyebrow">번들된 Gemini 자문</p>
            <h3>${escapeHtml(modelName)}</h3>
          </div>
          <span class="status-pill status-present">오프라인 준비 완료</span>
        </div>
        <div class="result-metrics">
          ${metricBlock(formatDecisionLabel(report.final_decision), "결정형 결과")}
          ${metricBlock((advisoryOutput.citation_list || []).length, "근거 인용 수")}
          ${metricBlock((advisoryOutput.remediation_actions || []).length, "수정 조치 수")}
          ${metricBlock(report.missing_sir_fields.length, "집중 필드 수")}
        </div>
      </div>

      <div class="advisory-grid">
        <div class="rule-card advisory-card">
          <h4>리뷰어 요약</h4>
          <p>${escapeHtml(normalizeNarrativeText(advisoryOutput.reviewer_summary || ""))}</p>
        </div>
        <div class="rule-card advisory-card">
          <h4>쉬운 설명</h4>
          <p>${escapeHtml(normalizeNarrativeText(advisoryOutput.plain_language_rationale || ""))}</p>
        </div>
        <div class="rule-card advisory-card">
          <h4>수정 조치</h4>
          <ul class="action-list">${actions || "<li>수정 조치가 없습니다.</li>"}</ul>
        </div>
        <div class="rule-card advisory-card">
          <h4>근거 인용 목록</h4>
          <div class="rule-meta">${citations || '<span class="meta-pill">없음</span>'}</div>
        </div>
      </div>

      <div class="rule-card advisory-card">
        <h4>권장 수정 문구</h4>
        <p class="suggested-prompt">${escapeHtml(advisoryOutput.conservative_rewrite_suggestion || "")}</p>
      </div>

      ${rewriteOutcome}
      ${suggestButton}
    `,
    footerButton: buildFooterButton(5, "인간 승인 + 감사 패킷 보기"),
  });
}

function renderHumanStage() {
  const report = state.trace.review_report;
  const artifacts = getActiveExampleArtifacts();
  const humanPacket = artifacts?.humanReviewPacket;
  const evidencePackage = artifacts?.evidencePackage;
  const actions = humanPacket?.reviewer_actions || ["approve", "approve_with_edits", "reject", "escalate"];
  const actionButtons = actions
    .map(
      (action) => `
        <button
          type="button"
          class="decision-btn ${state.humanDecision === action ? "active" : ""}"
          data-human-decision="${escapeHtml(action)}"
        >${escapeHtml(formatDecisionLabel(action))}</button>
      `
    )
    .join("");

  const citations = (humanPacket?.triggered_citations || report.triggered_citations || [])
    .map((item) => `<span class="meta-pill">${escapeHtml(item.citation_label)}</span>`)
    .join("");

  const evidenceSummary = evidencePackage?.coverage_summary || humanPacket?.evidence_summary || null;
  const metrics = [
    metricBlock(formatDecisionLabel(state.humanDecision || "pending"), "선택된 조치"),
    metricBlock(evidenceSummary?.triggered_rule_count ?? report.summary.failed_rule_count, "트리거 항목 수"),
    metricBlock(evidenceSummary?.citation_count ?? report.triggered_citations.length, "인용 수"),
    metricBlock(evidenceSummary?.retrieved_support_item_count ?? 0, "지원 근거 수"),
  ].join("");

  stageElements.human.innerHTML = buildStageFrame({
    stage: STAGES[6],
    body: `
      <div class="result-card">
        <div class="result-banner">
          <div>
            <p class="eyebrow">인간 검토 패킷</p>
            <h3>${escapeHtml(formatDecisionLabel(state.humanDecision || "pending"))}</h3>
          </div>
          <span class="status-pill ${decisionStatusClass(state.humanDecision || report.final_decision)}">${escapeHtml(formatDecisionLabel(state.humanDecision || "pending"))}</span>
        </div>
        <div class="result-metrics">${metrics}</div>
      </div>

      <div class="rule-card advisory-card">
        <h4>리뷰어 조치 선택</h4>
        <div class="decision-row">${actionButtons}</div>
      </div>

      <div class="advisory-grid">
        <label class="input-shell">
          <span class="mini-label">리뷰어 ID</span>
          <input type="text" value="${escapeHtml(state.reviewerId)}" data-human-field="reviewer_id" />
        </label>
        <div class="rule-card advisory-card">
          <h4>트리거된 인용</h4>
          <div class="rule-meta">${citations || '<span class="meta-pill">없음</span>'}</div>
        </div>
      </div>

      <label class="textarea-shell">
        <span class="mini-label">리뷰어 메모</span>
        <textarea data-human-field="reviewer_note" rows="5">${escapeHtml(state.reviewerNote)}</textarea>
      </label>

      <div class="rule-card advisory-card">
        <h4>감사 패킷 내려받기</h4>
        <p>감사 패킷에는 정규화 입력, 결정형 결과, 법적 근거, 오프라인 Gemini 자문, 그리고 리뷰어 최종 결정을 함께 담습니다.</p>
        <div class="action-row">
          <button type="button" class="ghost-btn" data-download-packet="audit">감사 JSON 내려받기</button>
          <button type="button" class="ghost-btn" data-download-packet="advisory_input">LLM 입력 JSON 내려받기</button>
          <button type="button" class="ghost-btn" data-download-packet="human_packet">인간 검토 JSON 내려받기</button>
        </div>
      </div>
    `,
    footerButton: "",
  });
}

function renderFieldGroup(title, fields, statusClass) {
  const items = fields.length
    ? fields
        .map(
      (field) => `
            <div class="field-chip">
              <strong>${escapeHtml(formatFieldLabel(field.field_name))}</strong>
              <span class="status-pill ${statusClass}">${escapeHtml(formatStatusLabel(field.status))}</span>
              <p>${escapeHtml(field.value === null ? "없음" : stringifyValue(field.value))}</p>
            </div>
          `
        )
        .join("")
    : `<div class="field-chip"><strong>없음</strong><p>이 상태의 필드는 없습니다.</p></div>`;

  return `
    <section class="field-group">
      <h4>${title}</h4>
      <div class="field-grid">${items}</div>
    </section>
  `;
}

function buildStageFrame({ stage, body, footerButton }) {
  const stageIndex = STAGES.findIndex((item) => item.id === stage.id);
  return `
    <div class="stage-head">
      <div class="stage-number">${stageIndex + 1}</div>
      <div class="stage-title">
        <h3>${stage.title}</h3>
        <p>${stage.subtitle}</p>
      </div>
    </div>
    ${body}
    ${footerButton ? `<div class="stage-footer">${footerButton}</div>` : ""}
  `;
}

function buildFooterButton(stageIndex, label) {
  return `<button type="button" class="reveal-btn" data-reveal-index="${stageIndex + 1}">${label}</button>`;
}

function metricBlock(value, label) {
  return `
    <div class="metric-block">
      <strong>${escapeHtml(String(value))}</strong>
      <span>${escapeHtml(label)}</span>
    </div>
  `;
}

function getActiveExampleArtifacts() {
  if (!state.selectedExample?.id || !isExactBundledExample()) {
    return null;
  }
  return runtimeBundle.exampleArtifacts?.[state.selectedExample.id] || null;
}

function isExactBundledExample() {
  const payload = state.selectedExample?.payload;
  if (!payload) {
    return false;
  }
  return String(promptInput.value || "").trim() === String(payload.content_text || "").trim();
}

function recommendDecision(report) {
  if (!report) return "approve";
  if (report.final_decision === "compliant") return "approve";
  if (report.should_escalate) return "escalate";
  if (report.final_decision === "non_compliant") return "reject";
  return "approve_with_edits";
}

function defaultHumanNote(report, decision) {
  if (!report) {
    return "";
  }
  if (decision === "approve") {
    return "결정형 검토를 통과했으므로 현재 문구를 승인합니다.";
  }
  if (decision === "approve_with_edits") {
    return "결정형 검토 결과 일부 수정 후 승인할 수 있습니다.";
  }
  if (decision === "reject") {
    return "결정형 검토에서 규칙 위반이 확인되어 배포 전 수정이 필요합니다.";
  }
  return "결정형 검토에서 고위험 이슈가 확인되어 컴플라이언스 추가 검토로 에스컬레이션합니다.";
}

function decisionStatusClass(decision) {
  if (decision === "approve") return "status-present";
  if (decision === "approve_with_edits") return "status-uncertain";
  if (decision === "reject" || decision === "escalate") return "status-missing";
  return "status-na";
}

function describeSuggestedOutcome(report) {
  if (report.final_decision === "compliant") {
    return "이 수정 문구로 다시 실행하면 결정형 코어가 해당 케이스를 통과합니다.";
  }
  if (report.summary.missing_sir_field_count > 0) {
    return "수정 문구는 더 안전하지만, 결정형 코어가 통과하려면 여전히 명시적인 사실 필드가 더 필요합니다.";
  }
  return "수정 문구는 개선되었지만 아직 실패 규칙이 남아 있어 수동 보정이 필요합니다.";
}

function applySuggestedPrompt() {
  const advisoryOutput = getActiveExampleArtifacts()?.geminiAdvisoryOutput;
  const suggestedPrompt = String(advisoryOutput?.conservative_rewrite_suggestion || "").trim();
  if (!suggestedPrompt) {
    showStatus("이 케이스에는 번들된 수정 문구가 없습니다.", true);
    return;
  }
  promptInput.value = suggestedPrompt;
  profileHint.textContent = "번들된 Gemini 수정 문구를 입력창에 넣었습니다. 다시 실행해 결과를 확인하세요.";
  showStatus("수정 문구를 입력창에 반영했습니다.", false);
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function downloadPacket(kind) {
  const artifacts = getActiveExampleArtifacts();
  let payload = null;
  let filename = "runtime-export.json";

  if (kind === "advisory_input") {
    payload = artifacts?.llmAdvisoryInput || buildFallbackAdvisoryInputExport();
    filename = `${state.trace.review_report.input_id}.llm_advisory_input.export.json`;
  } else if (kind === "human_packet") {
    payload = buildHumanPacketExport();
    filename = `${state.trace.review_report.input_id}.human_review.export.json`;
  } else {
    payload = buildAuditExport();
    filename = `${state.trace.review_report.input_id}.audit_export.json`;
  }

  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 0);
}

function buildFallbackAdvisoryInputExport() {
  return {
    artifact_type: "ch4_llm_advisory_input_export",
    version: "0.1.0",
    note: "Fallback export built in the browser because no bundled advisory input was available for this exact prompt.",
    normalized_input: state.trace.normalized_input,
    deterministic_core: state.trace.review_report,
    triggered_citations: state.trace.triggered_citations,
  };
}

function buildHumanPacketExport() {
  const artifacts = getActiveExampleArtifacts();
  const basePacket = artifacts?.humanReviewPacket ? structuredClone(artifacts.humanReviewPacket) : {};
  const reviewReport = state.trace.review_report;
  return {
    ...basePacket,
    artifact_type: "ch4_human_review_packet_export",
    version: "0.1.0",
    input_id: reviewReport.input_id,
    review_status: "completed_in_dashboard_demo",
    case_summary: {
      title: state.trace.normalized_input.title,
      content_text: state.trace.normalized_input.content_text,
      final_decision_from_engine: reviewReport.final_decision,
      should_escalate: reviewReport.should_escalate,
      failed_rule_count: reviewReport.summary.failed_rule_count,
      uncertain_rule_count: reviewReport.summary.uncertain_rule_count,
      missing_sir_fields: reviewReport.missing_sir_fields,
    },
    completed_review: {
      reviewer_id: state.reviewerId || DEFAULT_REVIEWER_ID,
      decision: state.humanDecision || recommendDecision(reviewReport),
      reviewer_note: state.reviewerNote || defaultHumanNote(reviewReport, state.humanDecision),
      llm_model: artifacts?.humanReviewCompleted?.completed_review?.llm_model || "gemini-2.5-flash",
      llm_reviewer_summary: artifacts?.geminiAdvisoryOutput?.reviewer_summary || null,
      llm_recommended_rewrite: artifacts?.geminiAdvisoryOutput?.conservative_rewrite_suggestion || null,
    },
  };
}

function buildAuditExport() {
  const artifacts = getActiveExampleArtifacts();
  return {
    artifact_type: "ch4_runtime_audit_export",
    version: "0.1.0",
    generated_in: "dashboard/ch4_runtime_flow",
    source_mode: artifacts ? "bundled_demo_case" : "custom_or_modified_input",
    input_id: state.trace.review_report.input_id,
    normalized_input: state.trace.normalized_input,
    deterministic_trace: {
      review_report: state.trace.review_report,
      applicable_rules: state.trace.applicable_rules,
      triggered_citations: state.trace.triggered_citations,
      sir_fields: state.trace.sir.fields,
    },
    llm_advisory: artifacts?.geminiAdvisoryOutput || null,
    llm_advisory_input: artifacts?.llmAdvisoryInput || null,
    suggested_rewrite_report: artifacts?.suggestedRewriteReport || null,
    human_review: buildHumanPacketExport(),
    evidence_package: artifacts?.evidencePackage || null,
  };
}

function mapStatusClass(status) {
  if (status === "present" || status === "passed") return "status-present";
  if (status === "not_evidenced" || status === "failed") return "status-missing";
  if (status === "uncertain") return "status-uncertain";
  return "status-na";
}

function stringifyValue(value) {
  if (typeof value === "string") return value;
  return JSON.stringify(value, null, 0);
}

function showStatus(message, isError) {
  statusBanner.textContent = message;
  statusBanner.classList.remove("hidden");
  statusBanner.style.background = isError ? "rgba(127, 46, 31, 0.92)" : "rgba(31, 46, 42, 0.92)";
}

function formatStatusLabel(value) {
  return STATUS_LABELS[value] || value;
}

function formatDecisionLabel(value) {
  return DECISION_LABELS[value] || STATUS_LABELS[value] || value;
}

function formatFieldLabel(value) {
  return FIELD_LABELS[value] || value;
}

function formatRuleFamilyLabel(value) {
  return RULE_FAMILY_LABELS[value] || value;
}

function formatLogicTypeLabel(value) {
  return LOGIC_TYPE_LABELS[value] || value;
}

function normalizeNarrativeText(value) {
  return String(value)
    .replaceAll("non_compliant", "비준수")
    .replaceAll("compliant", "준수")
    .replaceAll("deposit_disclaimer", "예금자보호 안내 문구")
    .replaceAll("investment_warning", "투자 위험 경고")
    .replaceAll("insurance_warning", "보험 경고 문구")
    .replaceAll("loan_rate_basis", "대출 금리 기준")
    .replaceAll("loan_interest_timing", "대출 이자 시기");
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
