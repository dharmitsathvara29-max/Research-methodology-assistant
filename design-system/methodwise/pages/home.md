# Home Page Overrides: MethodWise

> **PROJECT:** MethodWise  
> **Page Type:** Home / Editorial Landing  
> **Overrides MASTER.md for:** Hero composition, Bento feature grid, and connected pipeline layout.

---

## Page-Specific Rules

### 1. Asymmetric Hero Composition
- **Left Column (60%):**
  - Scholarly institution pill badge: `Methodology AI • Academic Decision Support System`
  - Display headline in `Crimson Pro` serif (44px): *"Choose the right research method, with confidence"*
  - Subhead in `Atkinson Hyperlegible` (17px): *"Empowering researchers, doctoral scholars, and academics to formulate epistemologically rigorous, feasible, and defensible research designs."*
  - Trust verification strip with checkmark icon and text.
  - Dual action CTAs: Primary button (*"Get a Recommendation"*) + Secondary button (*"See How It Works"*).
- **Right Column (40%):**
  - Signature **"Method Map" Hero Visual**: Inline SVG diagram showing a branching decision tree with paper background `#FAF7F2`, hairline lines `#CBD5E1`, and leaves for Quantitative, Qualitative, and Mixed Methods with subtle draw-in animation (respects `prefers-reduced-motion`).

### 2. Live Stats Strip
- 4 clean metric boxes on white surface with hairline border (`#E7E2D9`):
  1. *Recommendations Generated* (live SQLite count)
  2. *Average Validation Score* (tabular percent, e.g. `94.5%`)
  3. *Benchmark Pass Rate* (`100.0%` with verification subtext)
  4. *Prompt Architectures* (`3 Engines Evaluated`)

### 3. Connected 4-Step Pipeline Flow ("How It Works")
- Connected horizontal cards numbered 01 to 04 with subtle directional connector indicator:
  1. *Validate & Parse* (Keystroke & injection screening)
  2. *Generate Methodology* (Pydantic schema contract)
  3. *Score & Verify* (Triple-validation engine)
  4. *Refine & Deliver* (Closed-loop feedback & report delivery)

### 4. Bento Box Feature Grid
- Asymmetric 6-card grid with varied visual hierarchy:
  - Card 1 (Span 2): *Structured Specifications* (10 comprehensive methodological sections)
  - Card 2 (Span 1): *Multi-Engine Prompt Lab* (Empirical prompt comparison)
  - Card 3 (Span 1): *Triple-Validation Architecture* (Rubric, reference, rules)
  - Card 4 (Span 2): *Ethics & Vulnerability Protocols* (IRB flags & trauma safeguards)
  - Card 5 (Span 1): *Autonomous Delivery Engine* (Automatic reports & logs)
  - Card 6 (Span 1): *Local Storage & Privacy Rights* (SQLite persistence & purge control)

### 5. Interactive Exemplar Inquiries
- 3 clickable research question cards (Quantitative Causal, Qualitative Exploratory, Mixed Methods) that pre-fill the session state and navigate to `/recommend`.
