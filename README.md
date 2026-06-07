# JB Hackathon Chapter 4 Prototype

This repository contains the Chapter 4 legal compilation backbone and two dashboards:

- `dashboard/ch4_fincpa/index.html`
  - legal preparation pipeline
  - parse -> Layer 1 -> Layer 2 -> Layer 3 -> Layer 4

- `dashboard/ch4_runtime_flow/index.html`
  - live non-LLM runtime workflow
  - prompt -> runtime schema -> SIR -> active rules -> triggered law -> final result

## Important directories

- `data/raw/official/`
  - official source PDF
- `data/parsed/ch4_fincpa/`
  - deterministic Chapter 4 parse outputs
- `data/annotations/ch4_fincpa/`
  - Layer 1, Layer 2, Layer 3 artifacts
- `data/finalized/ch4_fincpa/`
  - Layer 4 rule pack, SIR schema, dashboard bundle
- `data/runtime/ch4_fincpa/`
  - runtime examples and results
- `src/safeguard_ai/`
  - Python runtime implementation
- `scripts/`
  - parsing, bundle building, runtime and validation scripts

## Rebuild dashboard bundles

```bash
python scripts/build_ch4_dashboard_bundle.py
python scripts/build_ch4_runtime_dashboard_bundle.py
```

## Local runtime dashboard

For local development with static files only:

```bash
python -m http.server 8765
```

Then open:

- `http://127.0.0.1:8765/dashboard/ch4_fincpa/index.html`
- `http://127.0.0.1:8765/dashboard/ch4_runtime_flow/index.html`

The runtime dashboard also has a local Python server option:

```bash
python scripts/run_ch4_runtime_flow_dashboard.py
```

## GitHub Pages

If GitHub Pages is enabled for the repository root, the landing page is:

- `/index.html`

and both dashboards are linked from there.
