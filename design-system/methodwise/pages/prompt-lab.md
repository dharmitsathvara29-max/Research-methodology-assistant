# Prompt Lab Page Overrides: MethodWise

> **PROJECT:** MethodWise  
> **Page Type:** Multi-Engine Prompt Benchmarking Laboratory  
> **Overrides MASTER.md for:** 3-way card comparison, winner highlight banner, and benchmark visualizations.

---

## Page-Specific Rules

### 1. Benchmark Execution Controls
- Inquiry selection dropdown with 4 standard academic questions + custom query input.
- Primary CTA: *"Run Multi-Version Benchmark Suite"*.
- Progress bar reporting real-time execution across `v1_basic`, `v2_structured`, and `v3_decomposed`.

### 2. Prompt Architecture & Master Template Inspector
- Tabbed inspector accessible before benchmark execution:
  - Tab 1: Master Prompt Template (`master_template.md`)
  - Tab 2: `v1_basic` (Baseline instruction prompt)
  - Tab 3: `v2_structured` (Role + JSON schema prompt)
  - Tab 4: `v3_decomposed` (8-step CoT + few-shot + guardrails)

### 3. Side-by-Side Version Cards (3 Columns)
- **v1_basic (Baseline):** Hairline slate border (`#CBD5E1`), composite score badge, latency metric, paradigm & design summary.
- **v2_structured (Intermediate):** Indigo border (`#818CF8`), score badge, latency metric, paradigm & design summary.
- **v3_decomposed (Production Champion):** Prominent ochre/indigo badge (`👑 Recommended`), highlighted card surface, complete power calculation callout, score badge.
- Raw prompt text viewable in each card's expander.

### 4. Verdict Banner
- High-trust editorial card highlighting `v3_decomposed` as the superior strategy with empirical justification (power calculations, zero hallucinations, score comparison).

### 5. Benchmark Visualizations
- Plotly Grouped Score Comparison Bar Chart (0–100%) with accessible summary.
- Plotly Latency Comparison Bar Chart (seconds) with accessible summary.
- Both charts follow the scholarly palette: Indigo `#3730A3`, Ochre `#B45309`, Slate `#64748B`.

### 6. Changelog & Empirical History
- Formatted display of `prompts/CHANGELOG.md` documenting measured version score differences.
