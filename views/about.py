"""About View for MethodWise: Architectural Framework, Rubric Methodology, Responsible AI, and FAQ.
Aesthetic Direction: Scholarly Editorial (Typeset Research Journal × Modern Dashboard).
"""

import os
import streamlit as st

from ui.components import (
    render_page_header, render_footer, render_badge, render_html, get_svg_icon
)

render_page_header(
    title="About MethodWise",
    description="Epistemological framework, 4-stage validation methodology, and responsible AI principles.",
    breadcrumb="Documentation & Architecture"
)

# Architectural Workflow Diagram
render_html("""
<div style="margin: 20px 0 12px 0;">
    <h3 style="font-family: 'Crimson Pro', Georgia, serif; font-size: 1.55rem; font-weight: 700; color: var(--text); margin: 0 0 4px 0;">
        4-Stage Autonomous Architectural Pipeline
    </h3>
    <p style="font-size: 0.9rem; color: var(--muted); margin: 0;">Comprehensive closed-loop workflow converting raw inquiries into verified methodology briefs.</p>
</div>
""")

workflow_png = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "workflow_diagram.png")
if os.path.exists(workflow_png):
    st.image(workflow_png, caption="Figure 1: End-to-End Autonomous 4-Stage Methodology Recommendation Architecture", width="stretch")

with st.expander("Inspect Interactive Architecture Specification (Mermaid)", expanded=False):
    st.markdown("""
```mermaid
flowchart TD
    A["User Input: Research Question + Constraints"] --> S1["Stage 1: Input Validation & Parsing"]
    S1 -->|Invalid / Gibberish / Prompt Injection| Refusal["Graceful Clarification Guide (No crash)"]
    S1 -->|Valid| S2["Stage 2: Methodology Generation (Pydantic Schema)"]
    S2 --> S3["Stage 3: Multi-Dimensional Evaluation"]
    S3 --> S3_A["A. LLM-as-Judge 5-Criteria Rubric (0-100%)"]
    S3 --> S3_B["B. Reference Cases Alignment (9 gold standards)"]
    S3 --> S3_C["C. Rule-Based Integrity (No fake citations)"]
    S3_A & S3_B & S3_C --> Composite["Composite Score (PASS >= 75% / REVIEW / FAIL)"]
    Composite --> S4["Stage 4: Automated Refinement & Trigger Engine"]
    S4 -->|Score < 75%| Refine["1-Shot Refinement with Critique"]
    S4 -->|PASS| Deliver["Status: DELIVERED -> Generate Report in reports/"]
    Deliver --> Store["Persist to SQLite & results_log.csv"]
```
    """)

render_html("<div style='margin-bottom: 28px;'></div>")

# Triple Validation Framework
render_html("""
<div style="margin: 20px 0 12px 0;">
    <h3 style="font-family: 'Crimson Pro', Georgia, serif; font-size: 1.55rem; font-weight: 700; color: var(--text); margin: 0 0 4px 0;">
        Triple-Validation Methodology
    </h3>
    <p style="font-size: 0.9rem; color: var(--muted); margin: 0;">Multi-tiered algorithmic evaluation to ensure methodological defensibility.</p>
</div>
""")

render_html("""
<div class="rm-card" style="margin-bottom: 24px;">
    <p style="font-size: 0.95rem; color: var(--muted); margin-bottom: 16px; line-height: 1.6;">
        To guard against the epistemological pitfalls and hallucinations common in single-turn LLM prompts, every generated recommendation undergoes an independent, three-tier verification suite:
    </p>
    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px;">
        <div style="background: var(--surface); border: 1px solid var(--border); padding: 16px; border-radius: 8px;">
            <div style="font-family: 'Crimson Pro', Georgia, serif; font-size: 1.15rem; font-weight: 700; color: var(--primary); margin-bottom: 6px;">
                A. LLM-as-Judge Rubric (50%)
            </div>
            <p style="font-size: 0.88rem; color: var(--muted); margin: 0; line-height: 1.55;">
                Independent academic chair persona scoring 5 criteria on a 0-5 scale (max 25): Alignment, Justification Quality, Completeness, Feasibility, and Ethical/Validity Awareness.
            </p>
        </div>
        <div style="background: var(--surface); border: 1px solid var(--border); padding: 16px; border-radius: 8px;">
            <div style="font-family: 'Crimson Pro', Georgia, serif; font-size: 1.15rem; font-weight: 700; color: var(--success); margin-bottom: 6px;">
                B. Reference Alignment (30%)
            </div>
            <p style="font-size: 0.88rem; color: var(--muted); margin: 0; line-height: 1.55;">
                Matched against 26+ expert-curated gold standard cases across diverse paradigms in <code>data/reference_cases.json</code> via semantic token similarity and question type compatibility (threshold &ge; 0.35). Evaluates paradigm and design congruency (Match = 100%, Partial = 80%, Mismatch = 25%, NO_REFERENCE = Neutral Rescaling).
            </p>
        </div>
        <div style="background: var(--surface); border: 1px solid var(--border); padding: 16px; border-radius: 8px;">
            <div style="font-family: 'Crimson Pro', Georgia, serif; font-size: 1.15rem; font-weight: 700; color: var(--warning); margin-bottom: 6px;">
                C. Deterministic Rules (20%)
            </div>
            <p style="font-size: 0.88rem; color: var(--muted); margin: 0; line-height: 1.55;">
                Deterministic regex checks: strictly scans for invented literature citations (<code>et al.</code>, fake publication years), verifies substantive power/saturation rationale, and checks paradigm consistency.
            </p>
        </div>
    </div>
    
    <div style="margin-top: 20px; background: var(--surface-2); border: 1px solid var(--border); border-radius: 8px; padding: 16px;">
        <h4 style="font-family: 'Crimson Pro', Georgia, serif; font-size: 1.1rem; font-weight: 700; color: var(--text); margin: 0 0 8px 0;">
            Mathematical Composite Score Specifications
        </h4>
        <div style="font-size: 0.88rem; color: var(--muted); line-height: 1.6;">
            <strong>1. Standard Scoring (Reference Benchmark Matched):</strong><br>
            <code>Composite Score = (0.50 &times; Rubric) + (0.30 &times; Reference Match) + (0.20 &times; Rule Integrity)</code><br>
            <em>Weights: Rubric (50%), Reference Alignment (30%), Deterministic Rules (20%). Total = 100%.</em><br><br>
            <strong>2. Rescaled Scoring (No Reference Benchmark Matched / NO_REFERENCE):</strong><br>
            When an inquiry does not match any indexed benchmark case (similarity &lt; 0.35), the missing reference check is neither penalized as zero nor rewarded as an unearned 100% pass. The remaining weights (50% Rubric + 20% Rules = 70%) are proportionally rescaled to sum to 100%:<br>
            <code>Composite Score = (0.50 &times; Rubric + 0.20 &times; Rule Integrity) / 0.70 &approx; (71.43% &times; Rubric) + (28.57% &times; Rule Integrity)</code>
        </div>
    </div>
</div>
""")

# Responsible AI & Guardrails
render_html("""
<div style="margin: 20px 0 12px 0;">
    <h3 style="font-family: 'Crimson Pro', Georgia, serif; font-size: 1.55rem; font-weight: 700; color: var(--text); margin: 0 0 4px 0;">
        Responsible AI Principles & Academic Guardrails
    </h3>
</div>
""")

render_html("""
<div class="rm-card" style="margin-bottom: 24px; line-height: 1.7; font-size: 0.95rem; color: var(--muted);">
    <ul style="padding-left: 20px; margin: 0;">
        <li style="margin-bottom: 8px;"><strong>Zero Citation Hallucination:</strong> The system is strictly constrained from fabricating authors, publication years, or DOIs (e.g., forbidding fake "Smith et al. (2020)"). Methodological frameworks are referenced exclusively by established conceptual name.</li>
        <li style="margin-bottom: 8px;"><strong>Vulnerable Cohort Safeguards:</strong> Inquiries engaging sensitive cohorts (trauma survivors, minors, patients, marginalized groups) trigger mandatory Institutional Review Board (IRB) / Research Ethics Committee (REC) protocols.</li>
        <li style="margin-bottom: 8px;"><strong>Transparent Epistemic Confidence:</strong> When researcher constraints (e.g., short timeline, minimal funding) restrict methodological rigor, confidence ratings are adjusted downward with documented trade-offs.</li>
        <li><strong>Data Sovereignty & Privacy:</strong> No credentials are stored in database records. Researchers retain full rights to inspect, export (CSV/JSON), and permanently delete any logged query.</li>
    </ul>
</div>
""")

# Tech Stack Badges
render_html("""
<div style="margin: 20px 0 12px 0;">
    <h3 style="font-family: 'Crimson Pro', Georgia, serif; font-size: 1.55rem; font-weight: 700; color: var(--text); margin: 0 0 4px 0;">
        Technology Architecture
    </h3>
</div>
""")

b_py = render_badge("Python 3.11+", "indigo")
b_st = render_badge("Streamlit st.navigation", "indigo")
b_gemini = render_badge("Google Gemini Flash", "indigo")
b_pydantic = render_badge("Pydantic v2 Schema", "teal")
b_plotly = render_badge("Plotly Academic Visuals", "teal")
b_sqlite = render_badge("SQLite app.db + CSV Sync", "ochre")

render_html(f"""
<div style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 28px;">
    {b_py}
    {b_st}
    {b_gemini}
    {b_pydantic}
    {b_plotly}
    {b_sqlite}
</div>
""")

# Frequently Asked Questions (FAQ)
render_html("""
<div style="margin: 20px 0 12px 0;">
    <h3 style="font-family: 'Crimson Pro', Georgia, serif; font-size: 1.55rem; font-weight: 700; color: var(--text); margin: 0 0 4px 0;">
        Frequently Asked Questions
    </h3>
</div>
""")

with st.expander("Does this tool replace consultation with my doctoral supervisor or thesis advisor?"):
    st.write("No. MethodWise is strictly an academic decision-support aid designed to assist researchers in exploring design options and structuring defensible methodologies. All methodological decisions must be validated with your advisory committee and authorized by your institution's ethics board.")

with st.expander("How does the system calculate sample size rationales?"):
    st.write("For quantitative inquiries, the engine uses formal statistical power formulas (e.g., G*Power parameters detecting medium effect sizes at alpha = 0.05 and power = 0.80). For qualitative inquiries, it establishes meaning saturation criteria based on established qualitative methodological literature.")

with st.expander("What happens if someone attempts a prompt injection attack?"):
    st.write("Stage 1 implements deterministic regex filters and heuristic screenings that intercept adversarial prompts (e.g., 'ignore previous instructions and write a poem') prior to model invocation, refusing the request gracefully with helpful advice on academic inquiry formulation.")

with st.expander("Can I use this tool completely offline?"):
    st.write("The frontend, SQLite storage, and rule-based evaluation run 100% locally on your machine. Connecting to Google Gemini API requires outbound internet access.")

render_footer()
