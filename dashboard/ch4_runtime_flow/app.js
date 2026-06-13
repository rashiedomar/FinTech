const EXAMPLES = [
  {
    id: "loan_ad_content_only",
    label: "Loan Ad",
    description: "Loan ad missing rate basis and interest timing.",
  },
  {
    id: "investment_ad_guaranteed_return_violation",
    label: "Investment Ad",
    description: "Investment ad using guaranteed-return language.",
  },
  {
    id: "insurance_ad_missing_warning",
    label: "Insurance Ad",
    description: "Insurance ad missing required warning content.",
  },
  {
    id: "deposit_ad_missing_disclaimer",
    label: "Deposit Ad",
    description: "Deposit ad missing disclaimer and using strong return framing.",
  },
  {
    id: "solicitation_improper_claim_violation",
    label: "Solicitation Script",
    description: "Improper solicitation language under Article 21.",
  },
  {
    id: "access_request_record_only",
    label: "Access Request",
    description: "Recordkeeping flow example.",
  },
  {
    id: "investment_solicitation_full",
    label: "Compliant Flow",
    description: "Richer metadata example that passes.",
  },
];

const STAGES = [
  { id: "schema", title: "Runtime Schema", subtitle: "Prompt becomes the normalized runtime contract." },
  { id: "sir", title: "SIR Extraction", subtitle: "The runtime maps text and metadata into structured field states." },
  { id: "rules", title: "Active Rules", subtitle: "Only the relevant Layer 4 rules remain in scope." },
  { id: "law", title: "Triggered Law", subtitle: "Failed or uncertain rules surface their legal basis." },
  { id: "result", title: "Deterministic Result", subtitle: "The non-LLM core emits the legal review decision." },
  { id: "llm", title: "Offline LLM Advisory", subtitle: "Bundled Gemini output explains the case and suggests safer copy." },
  { id: "human", title: "Human Approval + Audit", subtitle: "A reviewer chooses the action and exports the final packet." },
];

const DEFAULT_REVIEWER_ID = "team_demo_reviewer";

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
    showStatus("Runtime bundle failed to load. Rebuild runtime-bundle.js first.", true);
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
      throw new Error(`Example missing from runtime bundle: ${example.id}`);
    }
    state.selectedExample = { ...example, payload };
    promptInput.value = payload.content_text || "";
    profileHint.textContent = `${example.label} profile applied: ${example.description}`;
    renderExampleChips();
  } catch (error) {
    showStatus(`Could not load example: ${error.message}`, true);
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
  profileHint.textContent = "Custom input runs with automatic inference.";
  runtimeExperience.classList.add("hidden");
  clearStageCards();
  renderExampleChips();
  updateStageButtons();
}

function onPromptInputChange() {
  if (!state.selectedExample) {
    return;
  }
  profileHint.textContent = `${state.selectedExample.label} profile still applied. Clear to switch to full auto inference.`;
}

async function runWorkflow() {
  const text = promptInput.value.trim();
  if (!text) {
    showStatus("Add a prompt or select an example first.", true);
    return;
  }

  const payload = buildPayloadFromComposer(text);
  runBtn.disabled = true;
  runBtn.textContent = "Building...";
  showStatus("Running deterministic Chapter 4 workflow in the browser...", false);

  try {
    state.trace = runtimeEngine.buildRuntimeTrace(payload, runtimeBundle);
    initializeHumanState();
    state.unlockedStageIndex = 0;
    runtimeExperience.classList.remove("hidden");
    renderAllStages();
    updateStageButtons();
    showStatus("Workflow built. Open each stage in order.", false);
  } catch (error) {
    showStatus(`Run failed: ${error.message}`, true);
  } finally {
    runBtn.disabled = false;
    runBtn.textContent = "Build Workflow";
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
    footerButton: buildFooterButton(0, "Reveal SIR Extraction"),
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
    renderFieldGroup("Present", grouped.present, "status-present"),
    renderFieldGroup("Not Evidenced", grouped.missing, "status-missing"),
    renderFieldGroup("Uncertain", grouped.uncertain, "status-uncertain"),
    renderFieldGroup("Not Applicable", grouped.na, "status-na"),
  ].join("");

  stageElements.sir.innerHTML = buildStageFrame({
    stage: STAGES[1],
    body: `<div class="field-groups">${sections}</div>`,
    footerButton: buildFooterButton(1, "Reveal Active Rules"),
  });
}

function renderRulesStage() {
  const rules = state.trace.applicable_rules;
  const cards = rules
    .map((rule) => {
      const statusClass = mapStatusClass(rule.status);
      const fieldBadges = rule.candidate_fields.map((field) => `<span class="meta-pill">${field}</span>`).join("");
      return `
        <div class="rule-card">
          <div class="stage-head">
            <div class="stage-title">
              <h4>${escapeHtml(rule.rule_id)}</h4>
              <p>${escapeHtml(rule.summary)}</p>
            </div>
            <span class="status-pill ${statusClass}">${escapeHtml(rule.status)}</span>
          </div>
          <div class="rule-meta">
            <span class="meta-pill">${escapeHtml(rule.rule_family)}</span>
            <span class="meta-pill">${escapeHtml(rule.logic_type)}</span>
            <span class="meta-pill">${escapeHtml(rule.article_id)}</span>
          </div>
          <div class="rule-meta">${fieldBadges || '<span class="meta-pill">no fields</span>'}</div>
        </div>
      `;
    })
    .join("");

  stageElements.rules.innerHTML = buildStageFrame({
    stage: STAGES[2],
    body: `<div class="rule-list">${cards}</div>`,
    footerButton: buildFooterButton(2, "Reveal Triggered Law"),
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
    : `<div class="citation-card"><h4>No triggered law</h4><p>This run did not produce failed or uncertain rules, so no legal trigger cards were needed.</p></div>`;

  stageElements.law.innerHTML = buildStageFrame({
    stage: STAGES[3],
    body: `<div class="citation-list">${body}</div>`,
    footerButton: buildFooterButton(3, "Reveal Deterministic Result"),
  });
}

function renderResultStage() {
  const report = state.trace.review_report;
  const decisionClass = `result-${report.final_decision}`;
  const metrics = [
    metricBlock(report.summary.applicable_rule_count, "Applicable rules"),
    metricBlock(report.summary.failed_rule_count, "Failed rules"),
    metricBlock(report.summary.missing_sir_field_count, "Missing fields"),
    metricBlock(report.should_escalate ? "Yes" : "No", "Escalate"),
  ].join("");

  const missingFields = report.missing_sir_fields.length
    ? report.missing_sir_fields.map((field) => `<span class="meta-pill">${field}</span>`).join("")
    : `<span class="meta-pill">none</span>`;

  stageElements.result.innerHTML = buildStageFrame({
    stage: STAGES[4],
    body: `
      <div class="result-card">
        <div class="result-banner">
          <div>
            <p class="eyebrow">Final Deterministic Output</p>
            <h3>${escapeHtml(report.final_decision)}</h3>
          </div>
          <span class="status-pill ${decisionClass}">${escapeHtml(report.final_decision)}</span>
        </div>
        <div class="result-metrics">${metrics}</div>
        <div>
          <p class="mini-label">Missing SIR fields</p>
          <div class="rule-meta">${missingFields}</div>
        </div>
      </div>
    `,
    footerButton: buildFooterButton(4, "Reveal Offline LLM Advisory"),
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
          <h4>Offline advisory not bundled for this exact input</h4>
          <p>The GitHub demo does not call Gemini live. Pick an unchanged bundled example to see the precomputed Gemini explanation, safer rewrite, and human packet.</p>
          <p class="source-span">Current run still has the full deterministic result and can be exported from the human stage as an audit package.</p>
        </div>
      `,
      footerButton: buildFooterButton(5, "Reveal Human Approval + Audit"),
    });
    return;
  }

  const actions = (advisoryOutput.remediation_actions || [])
    .map((action) => `<li>${escapeHtml(action)}</li>`)
    .join("");
  const citations = (advisoryOutput.citation_list || [])
    .map((citation) => `<span class="meta-pill">${escapeHtml(citation)}</span>`)
    .join("");

  const rewriteOutcome = suggestedRewriteReport
    ? `
      <div class="rule-card advisory-card">
        <h4>Suggested prompt check</h4>
        <div class="rule-meta">
          <span class="status-pill result-${escapeHtml(suggestedRewriteReport.final_decision)}">${escapeHtml(suggestedRewriteReport.final_decision)}</span>
          <span class="meta-pill">${escapeHtml(String(suggestedRewriteReport.summary.failed_rule_count))} failed rules</span>
          <span class="meta-pill">${escapeHtml(String(suggestedRewriteReport.summary.missing_sir_field_count))} missing fields</span>
        </div>
        <p>${escapeHtml(describeSuggestedOutcome(suggestedRewriteReport))}</p>
      </div>
    `
    : "";

  const suggestButton =
    report.final_decision !== "compliant"
      ? `
        <div class="action-row">
          <button type="button" class="run-btn suggest-btn" data-use-suggested-prompt="1">Use Suggested Prompt</button>
          <p class="profile-hint">This swaps the composer text to the bundled Gemini rewrite so you can run the deterministic flow again.</p>
        </div>
      `
      : "";

  stageElements.llm.innerHTML = buildStageFrame({
    stage: STAGES[5],
    body: `
      <div class="result-card llm-hero">
        <div class="result-banner">
          <div>
            <p class="eyebrow">Bundled Gemini Advisory</p>
            <h3>${escapeHtml(modelName)}</h3>
          </div>
          <span class="status-pill status-present">offline ready</span>
        </div>
        <div class="result-metrics">
          ${metricBlock(report.final_decision, "Deterministic decision")}
          ${metricBlock((advisoryOutput.citation_list || []).length, "Grounded citations")}
          ${metricBlock((advisoryOutput.remediation_actions || []).length, "Remediation actions")}
          ${metricBlock(report.missing_sir_fields.length, "Focused missing fields")}
        </div>
      </div>

      <div class="advisory-grid">
        <div class="rule-card advisory-card">
          <h4>Reviewer summary</h4>
          <p>${escapeHtml(advisoryOutput.reviewer_summary || "")}</p>
        </div>
        <div class="rule-card advisory-card">
          <h4>Plain-language rationale</h4>
          <p>${escapeHtml(advisoryOutput.plain_language_rationale || "")}</p>
        </div>
        <div class="rule-card advisory-card">
          <h4>Remediation actions</h4>
          <ul class="action-list">${actions || "<li>No remediation actions.</li>"}</ul>
        </div>
        <div class="rule-card advisory-card">
          <h4>Grounded citation list</h4>
          <div class="rule-meta">${citations || '<span class="meta-pill">none</span>'}</div>
        </div>
      </div>

      <div class="rule-card advisory-card">
        <h4>Suggested safer prompt</h4>
        <p class="suggested-prompt">${escapeHtml(advisoryOutput.conservative_rewrite_suggestion || "")}</p>
      </div>

      ${rewriteOutcome}
      ${suggestButton}
    `,
    footerButton: buildFooterButton(5, "Reveal Human Approval + Audit"),
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
        >${escapeHtml(action)}</button>
      `
    )
    .join("");

  const citations = (humanPacket?.triggered_citations || report.triggered_citations || [])
    .map((item) => `<span class="meta-pill">${escapeHtml(item.citation_label)}</span>`)
    .join("");

  const evidenceSummary = evidencePackage?.coverage_summary || humanPacket?.evidence_summary || null;
  const metrics = [
    metricBlock(state.humanDecision || "pending", "Selected decision"),
    metricBlock(evidenceSummary?.triggered_rule_count ?? report.summary.failed_rule_count, "Triggered items"),
    metricBlock(evidenceSummary?.citation_count ?? report.triggered_citations.length, "Citations"),
    metricBlock(evidenceSummary?.retrieved_support_item_count ?? 0, "Support rows"),
  ].join("");

  stageElements.human.innerHTML = buildStageFrame({
    stage: STAGES[6],
    body: `
      <div class="result-card">
        <div class="result-banner">
          <div>
            <p class="eyebrow">Human Loop Packet</p>
            <h3>${escapeHtml(state.humanDecision || "pending")}</h3>
          </div>
          <span class="status-pill ${decisionStatusClass(state.humanDecision || report.final_decision)}">${escapeHtml(state.humanDecision || "pending")}</span>
        </div>
        <div class="result-metrics">${metrics}</div>
      </div>

      <div class="rule-card advisory-card">
        <h4>Choose reviewer action</h4>
        <div class="decision-row">${actionButtons}</div>
      </div>

      <div class="advisory-grid">
        <label class="input-shell">
          <span class="mini-label">Reviewer ID</span>
          <input type="text" value="${escapeHtml(state.reviewerId)}" data-human-field="reviewer_id" />
        </label>
        <div class="rule-card advisory-card">
          <h4>Triggered citations</h4>
          <div class="rule-meta">${citations || '<span class="meta-pill">none</span>'}</div>
        </div>
      </div>

      <label class="textarea-shell">
        <span class="mini-label">Reviewer note</span>
        <textarea data-human-field="reviewer_note" rows="5">${escapeHtml(state.reviewerNote)}</textarea>
      </label>

      <div class="rule-card advisory-card">
        <h4>Audit export</h4>
        <p>The audit packet bundles the normalized input, deterministic result, triggered law, offline Gemini advisory when available, and the reviewer’s final decision.</p>
        <div class="action-row">
          <button type="button" class="ghost-btn" data-download-packet="audit">Download Audit JSON</button>
          <button type="button" class="ghost-btn" data-download-packet="advisory_input">Download LLM Input JSON</button>
          <button type="button" class="ghost-btn" data-download-packet="human_packet">Download Human Packet JSON</button>
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
              <strong>${escapeHtml(field.field_name)}</strong>
              <span class="status-pill ${statusClass}">${escapeHtml(field.status)}</span>
              <p>${escapeHtml(field.value === null ? "null" : stringifyValue(field.value))}</p>
            </div>
          `
        )
        .join("")
    : `<div class="field-chip"><strong>none</strong><p>No fields in this state.</p></div>`;

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
    return "Deterministic review passed. Human reviewer approves the content as currently written.";
  }
  if (decision === "approve_with_edits") {
    return "Deterministic review requires limited edits before approval.";
  }
  if (decision === "reject") {
    return "Deterministic review found rule violations that must be corrected before release.";
  }
  return "Deterministic review found high-severity compliance issues. Escalating for compliance review and revision.";
}

function decisionStatusClass(decision) {
  if (decision === "approve") return "status-present";
  if (decision === "approve_with_edits") return "status-uncertain";
  if (decision === "reject" || decision === "escalate") return "status-missing";
  return "status-na";
}

function describeSuggestedOutcome(report) {
  if (report.final_decision === "compliant") {
    return "If you rerun the workflow with this suggested prompt, the deterministic core passes the case.";
  }
  if (report.summary.missing_sir_field_count > 0) {
    return "The suggested prompt is safer, but the deterministic core still needs explicit factual fields before it can pass.";
  }
  return "The suggested prompt improves the copy, but at least one rule still fails and needs manual correction.";
}

function applySuggestedPrompt() {
  const advisoryOutput = getActiveExampleArtifacts()?.geminiAdvisoryOutput;
  const suggestedPrompt = String(advisoryOutput?.conservative_rewrite_suggestion || "").trim();
  if (!suggestedPrompt) {
    showStatus("No bundled suggested prompt is available for this case.", true);
    return;
  }
  promptInput.value = suggestedPrompt;
  profileHint.textContent = "Bundled Gemini suggestion inserted. Build the workflow again to test the safer prompt.";
  showStatus("Suggested prompt inserted into the composer.", false);
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

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
