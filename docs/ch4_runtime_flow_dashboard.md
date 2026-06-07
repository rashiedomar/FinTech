## Chapter 4 Runtime Flow Dashboard

This dashboard is the **live runtime view**, not the offline legal-compilation view.

It is designed to show one input moving through the current non-LLM workflow step by step.

### What the user sees

1. **Prompt / Input**
   - The user pastes a financial-content sample or clicks one of the prepared examples.

2. **Runtime Schema**
   - The raw prompt is converted into the normalized runtime input JSON.
   - This is the contract the non-LLM workflow actually runs on.

3. **SIR Extraction**
   - The runtime maps the input into structured field states such as:
     - `present`
     - `not_evidenced`
     - `uncertain`
     - `not_applicable`

4. **Active Rules**
   - The system selects only the relevant Layer 4 rules for this specific input.
   - This is the scoped rule set that will be checked.

5. **Triggered Law**
   - If a rule fails or is uncertain, the workflow shows the legal basis already attached to that rule.
   - This happens **before** any later LLM explanation step.

6. **Final Result**
   - The deterministic workflow emits:
     - final decision
     - escalation flag
     - applicable rule count
     - failed rule count
     - missing SIR fields

### Why this dashboard exists

The team already has the offline legal backbone:

- parse
- Layer 1
- Layer 2
- Layer 3
- Layer 4

This dashboard is for the next part:

`new input -> runtime schema -> SIR -> active rules -> triggered law -> final deterministic result`

### Run locally

```bash
python scripts/run_ch4_runtime_flow_dashboard.py
```

Then open:

```text
http://127.0.0.1:8766/dashboard/ch4_runtime_flow/index.html
```

### Notes

- This dashboard is intentionally runtime-only.
- It does not expose Layer 1 to Layer 4 as the main interaction.
- It is meant to help the team understand what happens **after** the legal compilation pipeline is finished.
