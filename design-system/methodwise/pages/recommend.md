# Recommend Page Overrides: MethodWise

> **PROJECT:** MethodWise  
> **Page Type:** Recommendation Engine & Methodology Brief  
> **Overrides MASTER.md for:** Form layout, staged execution status, and "Methodology Brief" document presentation.

---

## Page-Specific Rules

### 1. Two-Column Input Formulation
- **Left Column (58%):**
  - Textarea for Research Question with character count guidance and explanatory placeholder.
  - Discipline dropdown (+ "Other" text input fallback).
  - Prompt Version engine selection (defaults to `v3_decomposed`).
  - Progressive disclosure expander for *Optional Research Constraints* (Timeframe, Budget, Sample access, Ethical sensitivity, Data collection type, Skill level).
  - Primary Submit CTA button: *"Generate Methodology Specification"*.
- **Right Column (42%):**
  - "What You'll Receive" preview card with hairline border and bulleted deliverables list.

### 2. Staged Progress Tracking
- Live 4-stage pipeline tracker using `st.status`:
  - `Stage 1 of 4: Validating input question & extracting variables...`
  - `Stage 2 of 4: Generating structured methodology specification...`
  - `Stage 3 of 4: Validating against rubric, references & rule checks...`
  - `Stage 4 of 4: Delivering final brief & compiling Markdown report...`

### 3. Deliverable: The "Methodology Brief" (Editorial Document Layout)
- Formatted as a peer-reviewed academic methodology brief / executive summary:
  - **Abstract Header Card:**
    - Document title: Research Design Specification (H1 Serif)
    - Metadata pills: Paradigm (Indigo), Confidence (Segmented), Status (Teal Pass)
    - Executive parsed question summary (italicized abstract style)
    - Confidence rationale footnote
  - **Evidence Ribbon:**
    - Compact 3-chip status bar directly below the abstract:
      - `[Rubric Icon] LLM-as-Judge Score: X% (PASS)`
      - `[Reference Icon] Reference Case: MATCH (REF-00X)`
      - `[Rules Icon] Integrity Checks: ZERO VIOLATIONS`
  - **Ethics Marginal Callout (Conditional):**
    - High-visibility amber/red bordered box for inquiries flagged with vulnerable cohorts (trauma, minors, patients) mandating formal Institutional Review Board (IRB) clearance.
  - **Segmented Confidence Meter:**
    - 3-step indicator (`[Low | Medium | High]`) with active step highlighted.
  - **Numbered Document Clauses (1 to 10):**
    - 1. Epistemological Scope & Paradigm Justification
    - 2. Research Design & Empirical Rationale
    - 3. Target Population & Sampling Strategy
    - 4. Sample Size & Statistical Power / Saturation Rationale
    - 5. Data Collection Instruments & Measurement Protocols
    - 6. Data Collection Procedures
    - 7. Prescribed Analytical Framework & Statistical Tests
    - 8. Validity, Reliability & Trustworthiness Protections
    - 9. Alternative Methodologies & Exclusion Rationale
    - 10. Phased Step-by-Step Execution Roadmap (Vertical Timeline)
  - **Validation Scorecard Tab:**
    - Gauge chart + Horizontal rubric breakdown bar chart + accessible text summary.
  - **Export Action Row:**
    - Primary download button for Formatted Markdown Report (.md).
    - Secondary download button for Structured JSON Specification (.json).
