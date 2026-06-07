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
  { id: "schema", title: "Runtime Schema", subtitle: "Prompt becomes the normalized input contract." },
  { id: "sir", title: "SIR Extraction", subtitle: "The runtime maps text and metadata into structured field states." },
  { id: "rules", title: "Active Rules", subtitle: "Only the relevant Layer 4 rules remain in scope." },
  { id: "law", title: "Triggered Law", subtitle: "Failed or uncertain rules surface their legal basis." },
  { id: "result", title: "Final Result", subtitle: "The deterministic workflow emits the review decision." },
];

const state = {
  selectedExample: null,
  trace: null,
  unlockedStageIndex: -1,
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

function deriveTitle(text) {
  return text.split(/\n+/)[0].slice(0, 40);
}

function renderAllStages() {
  renderSchemaStage();
  renderSirStage();
  renderRulesStage();
  renderLawStage();
  renderResultStage();
}

function clearStageCards() {
  Object.values(stageElements).forEach((node) => {
    node.className = "stage-card locked";
    node.innerHTML = "";
  });
}

function unlockStage(index) {
  if (!state.trace) {
    return;
  }
  if (index > state.unlockedStageIndex) {
    return;
  }
  const nextIndex = Math.min(index + 1, STAGES.length - 1);
  if (index === state.unlockedStageIndex && state.unlockedStageIndex < STAGES.length - 1) {
    state.unlockedStageIndex += 1;
  }
  updateStageButtons();
  applyStageClasses();
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
  const payload = state.trace.normalized_input;
  stageElements.schema.innerHTML = buildStageFrame({
    stage: STAGES[0],
    body: `<pre class="json-panel">${escapeHtml(JSON.stringify(payload, null, 2))}</pre>`,
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
    footerButton: buildFooterButton(3, "Reveal Final Result"),
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

document.addEventListener("click", (event) => {
  const revealButton = event.target.closest("[data-reveal-index]");
  if (!revealButton) {
    return;
  }
  const targetIndex = Number.parseInt(revealButton.dataset.revealIndex, 10);
  if (Number.isNaN(targetIndex)) {
    return;
  }
  if (targetIndex > state.unlockedStageIndex) {
    state.unlockedStageIndex = targetIndex;
    updateStageButtons();
    const stage = STAGES[targetIndex];
    if (stage) {
      stageElements[stage.id].scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }
});

function metricBlock(value, label) {
  return `
    <div class="metric-block">
      <strong>${escapeHtml(String(value))}</strong>
      <span>${escapeHtml(label)}</span>
    </div>
  `;
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
