Chapter 4 Dashboard Guide
=========================

Purpose
-------
This dashboard is meant for team understanding, not model evaluation.

It is a visual explorer that shows how one Chapter 4 clause moves through:
- parsing
- Layer 1 metadata
- Layer 2 obligation decomposition
- Layer 3 rule/SIR candidate design
- Layer 4 final MVP freeze


Why this dashboard exists
-------------------------
The repo now has several structured layers, but reading only JSONL files is hard,
especially during team discussion.

The dashboard makes the pipeline visible clause by clause so the team can:
- click any clause
- see the Korean source text first
- inspect what each layer added
- see which final MVP rules and SIR fields survived


Files
-----
Bundle builder:
- `scripts/build_ch4_dashboard_bundle.py`

Server:
- `scripts/run_ch4_dashboard.py`

Dashboard UI:
- `dashboard/ch4_fincpa/index.html`
- `dashboard/ch4_fincpa/styles.css`
- `dashboard/ch4_fincpa/app.js`

Generated data bundle:
- `data/finalized/ch4_fincpa/law_fincpa_main_ch4_dashboard_bundle.json`


How to rebuild the bundle
-------------------------
Run:

```bash
python scripts/build_ch4_dashboard_bundle.py
```

This regenerates the single JSON file used by the dashboard from the latest:
- parse output
- Layer 1 output
- Layer 2 output
- Layer 3 output
- Layer 4 output


How to run the dashboard
------------------------
Run:

```bash
python scripts/run_ch4_dashboard.py
```

Then open:

```text
http://127.0.0.1:8765/dashboard/ch4_fincpa/index.html
```


What the team will see
----------------------

### Top summary
The top cards show how many objects exist at each layer:
- parsed clauses
- Layer 1 clauses
- Layer 2 obligations
- Layer 3 candidates
- Layer 4 rules
- Layer 4 SIR fields

### Left sidebar
The left side lets the team:
- search by article number or text
- filter by topic family
- filter by whether the clause already has Layer 4 MVP rules

### Main detail panel
For each selected clause, the team can inspect:

#### Layer 0
- raw Korean text
- normalized Korean text

#### Layer 1
- topic family
- obligation mode
- product scope
- channel scope
- whether decomposition was needed

#### Layer 2
- each smaller obligation derived from the clause
- trigger type
- operationality
- source text span used

#### Layer 3
- proposed rule family
- logic type
- detection target
- SIR-link type
- candidate SIR fields

#### Layer 4
- only the final MVP rules that survived
- final SIR fields linked to those rules
- evaluation hint

### SIR field catalog
At the bottom, the dashboard shows the final Layer 4 SIR fields as a catalog so
the team can understand what the frozen MVP schema actually contains.


Design choices
--------------

### Korean-first display
The dashboard shows the Korean source text directly and uses Korean-first labels
for most pipeline labels. English names are still visible in smaller text to
keep the mapping to the JSON artifacts clear.

### Static bundle
The dashboard reads one bundled JSON file instead of reading many JSONL files in
the browser. This keeps it simple and fast to use.

### Deterministic display
The dashboard does not re-run Gemini. It only visualizes the saved artifacts.
That makes team discussion stable and reproducible.
