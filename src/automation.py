"""Stage 4 Automation Engine: Trigger-Action Execution, Report Generation, PDF Export, and Email Automation."""

import os
import json
import time
from datetime import datetime
from typing import Optional, Dict, Any

from src.schemas import MethodologyRecommendation, EvaluationResult, ParsedQuestion
from src.storage import (
    save_run, save_evaluation, log_execution, append_to_csv_log,
    mask_email, hash_email, sanitize_owner_id
)
from src.pdf_report import save_pdf
from src.emailer import send_report_email

REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")


def generate_methodology_report(
    run_id: str,
    research_question: str,
    discipline: str,
    constraints: Dict[str, Any],
    prompt_version: str,
    parsed: Optional[ParsedQuestion],
    rec: MethodologyRecommendation,
    evaluation: EvaluationResult,
    owner_id: Optional[str] = None
) -> str:
    """Generate a publication-grade Markdown and HTML report saved to reports/<owner_id>/."""
    constraints = constraints or {}
    owner = sanitize_owner_id(owner_id or constraints.get("owner_id") or "legacy")
    owner_dir = os.path.join(REPORTS_DIR, owner)
    os.makedirs(owner_dir, exist_ok=True)
    timestamp_slug = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"{timestamp_slug}_{run_id[:8]}_methodology_report.md"
    report_path = os.path.join(owner_dir, report_filename)

    # Format alternatives
    alts_md = ""
    for idx, alt in enumerate(rec.alternative_methodologies, 1):
        alts_md += f"### Alternative {idx}: {alt.design} ({alt.paradigm})\n"
        alts_md += f"**Rationale for Exclusion**: {alt.rationale_for_rejection}\n\n"

    # Format roadmap
    roadmap_md = "| Phase | Title | Actionable Steps | Estimated Duration |\n| :--- | :--- | :--- | :--- |\n"
    for step in rec.step_by_step_roadmap:
        roadmap_md += f"| {step.step_number} | **{step.title}** | {step.description} | {step.estimated_duration} |\n"

    # Format data collection instruments
    instruments_md = "\n".join([f"- {inst}" for inst in rec.data_collection_instruments])

    # Format data analysis techniques
    analysis_md = "\n".join([f"- {tech}" for tech in rec.data_analysis_techniques])

    # Format ethical considerations
    ethics_md = "\n".join([f"- {eth}" for eth in rec.ethical_considerations])

    # Format limitations
    limits_md = "\n".join([f"- {lim}" for lim in rec.limitations_and_risks])

    # Vulnerability badge
    vulnerable_badge = "⚠️ **VULNERABLE POPULATION FLAGGED** (Enhanced safeguards required)" if rec.vulnerable_population_flag else "✅ No protected vulnerable groups identified"
    irb_badge = "🏛️ **IRB / REC APPROVAL MANDATORY**" if rec.irb_ethics_board_required else "ℹ️ Standard departmental ethics clearance"

    content = f"""# Academic Research Methodology Specification Report

**Document ID**: `{run_id}`  
**Generated Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}  
**Discipline / Domain**: {discipline}  
**Prompt Engine Version**: `{prompt_version}`  
**Composite Quality Score**: **{evaluation.composite_score:.1f}%** ({evaluation.label})  
**Confidence Level**: **{rec.confidence_level}** ({rec.confidence_rationale})  

---

## 1. Executive Summary & Problem Formulation
- **Primary Research Question**:
  > "{research_question}"
- **Methodological Scope**: {rec.parsed_question_summary}
- **Target Population**: {parsed.target_population if parsed else 'Specified study cohort'}
- **Context / Setting**: {parsed.context_setting if parsed else discipline}

---

## 2. Research Paradigm & Overarching Design
- **Recommended Paradigm**: **{rec.recommended_paradigm}**
- **Paradigm Epistemological Justification**:
  {rec.paradigm_justification}
- **Specific Research Design**: **{rec.research_design}**
- **Design Rationale**:
  {rec.design_rationale}

---

## 3. Sampling Strategy & Power/Saturation Rationale
- **Sampling Framework**: {rec.sampling_strategy}
- **Sample Size Justification**:
  {rec.sample_size_rationale}

---

## 4. Data Collection Instrumentation & Procedures
### Instruments & Measurement Tools
{instruments_md}

### Data Collection Procedure
{rec.data_collection_procedures}

---

## 5. Analytical Strategies & Statistical Modeling
### Analysis Techniques
{analysis_md}

### Analytical Rationale
{rec.analysis_rationale}

---

## 6. Validity, Reliability & Trustworthiness
{rec.validity_and_reliability_considerations}

---

## 7. Ethical Governance & Participant Protections
- **Vulnerability Status**: {vulnerable_badge}
- **Regulatory Oversight**: {irb_badge}
### Safeguards & Mitigation Protocols
{ethics_md}

---

## 8. Methodological Limitations & Risk Mitigation
{limits_md}

---

## 9. Alternative Methodological Trade-Offs
{alts_md}

---

## 10. Phased Execution Roadmap
{roadmap_md}

---

## 11. Independent Quality Evaluation Scorecard
- **Overall Score**: **{evaluation.composite_score:.1f}/100** | Status: **{evaluation.label}**
- **Rubric Breakdown (0-5 scale, 25 max)**:
  - Alignment: `{evaluation.rubric.alignment.score}/5` — {evaluation.rubric.alignment.critique}
  - Justification Quality: `{evaluation.rubric.justification_quality.score}/5` — {evaluation.rubric.justification_quality.critique}
  - Completeness: `{evaluation.rubric.completeness.score}/5` — {evaluation.rubric.completeness.critique}
  - Feasibility: `{evaluation.rubric.feasibility.score}/5` — {evaluation.rubric.feasibility.critique}
  - Ethical & Validity Awareness: `{evaluation.rubric.ethical_validity_awareness.score}/5` — {evaluation.rubric.ethical_validity_awareness.critique}
- **Reference Ground Truth Match**: {evaluation.reference_match.status} ({evaluation.reference_match.notes})
- **Rule-Based Integrity Score**: {evaluation.rules.rule_score_pct:.0f}% ({'; '.join(evaluation.rules.flags) if evaluation.rules.flags else 'Zero rule violations'})

---

## 12. Standard Academic Advisory Disclaimer
> {rec.academic_disclaimer}
"""

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(content)

    return report_path


def execute_automation_workflow(
    run_id: str,
    research_question: str,
    discipline: str,
    constraints: Dict[str, Any],
    prompt_version: str,
    parsed: Optional[ParsedQuestion],
    rec: Optional[MethodologyRecommendation],
    evaluation: Optional[EvaluationResult],
    latency_ms: int,
    refinement_iterations: int = 0,
    **kwargs
) -> Dict[str, Any]:
    """Execute trigger-action workflow (Markdown, PDF export, Gmail automation, and verifiable logging)."""
    timestamp = datetime.now().isoformat()
    constraints = constraints or {}

    # Check for email opt-in, recipient, verification and session/owner ID
    email_opt_in = kwargs.get("email_opt_in") or constraints.get("email_opt_in", False)
    recipient_email = kwargs.get("recipient_email") or constraints.get("recipient_email")
    email_verified = kwargs.get("email_verified") or constraints.get("email_verified", False)
    session_id = kwargs.get("session_id") or constraints.get("session_id", "default_session")
    owner_id = kwargs.get("owner_id") or constraints.get("owner_id") or session_id
    masked_rec = mask_email(recipient_email) if recipient_email else None
    email_h = hash_email(recipient_email) if recipient_email else None

    # If invalid question rejected at Stage 1
    if not parsed or not parsed.is_valid_research_question:
        status = "REJECTED_INPUT"
        trigger = "STAGE_1_INPUT_REJECTION"
        action = "REFUSE_MALFORMED_INPUT_AND_SUGGEST_CLARIFICATION"

        # Edge case: No PDF and No Email are generated for rejected inputs
        save_run(
            run_id=run_id,
            timestamp=timestamp,
            research_question=research_question,
            discipline=discipline,
            constraints=constraints,
            prompt_version=prompt_version,
            parsed_json=parsed.model_dump() if parsed else None,
            recommendation_json=None,
            latency_ms=latency_ms,
            session_id=session_id,
            owner_id=owner_id
        )

        log_execution(
            run_id=run_id,
            trigger_event=trigger,
            action_taken=action,
            status=status,
            output_file_path=None,
            duration_ms=latency_ms,
            action_type="REJECTION",
            pdf_path=None,
            email_status="NOT_APPLICABLE",
            session_id=session_id,
            owner_id=owner_id
        )

        # Note: Do not append user runs to shared CSV to maintain user session isolation.
        return {
            "status": status,
            "report_path": None,
            "pdf_path": None,
            "email_result": {"status": "NOT_APPLICABLE"},
            "trigger": trigger,
            "action": action
        }

    # For valid recommendations
    if evaluation and evaluation.label == "PASS":
        status = "DELIVERED"
        trigger = "VALIDATION_PASSED_THRESHOLD_GE_75"
        action = "GENERATE_ACADEMIC_REPORT_AND_DELIVER"
    else:
        # REVIEW or FAIL
        status = "FLAGGED_FOR_HUMAN_REVIEW"
        trigger = "VALIDATION_SCORE_BELOW_THRESHOLD"
        action = f"FLAGGED_FOR_HUMAN_REVIEW_AFTER_{refinement_iterations}_REFINEMENTS"

    # Action 1: Generate Markdown report
    report_path = generate_methodology_report(
        run_id, research_question, discipline, constraints,
        prompt_version, parsed, rec, evaluation,
        owner_id=owner_id
    )

    # Action 2: Generate PDF report (ReportLab)
    run_record = {
        "run_id": run_id,
        "id": run_id,
        "timestamp": timestamp,
        "research_question": research_question,
        "discipline": discipline,
        "prompt_version": prompt_version,
        "constraints": constraints,
        "status": status,
        "owner_id": owner_id
    }
    t_pdf_start = time.time()
    pdf_path = save_pdf(run_record, rec, evaluation, owner_id=owner_id)
    pdf_duration_ms = int((time.time() - t_pdf_start) * 1000)

    # Action 3: Gmail Automation (if opted in)
    email_result = {"status": "SKIPPED_NO_CONSENT", "message_id": None, "error": None}
    if email_opt_in and recipient_email:
        summary_payload = {
            "paradigm": rec.recommended_paradigm if rec else "",
            "design": rec.research_design if rec else "",
            "confidence": rec.confidence_level if rec else "",
            "label": evaluation.label if evaluation else "",
            "roadmap_preview": [f"Phase {s.step_number}: {s.title}" for s in rec.step_by_step_roadmap[:3]] if rec else []
        }
        is_review = (status != "DELIVERED")
        email_result = send_report_email(
            recipient=recipient_email,
            run_record=run_record,
            pdf_path=pdf_path,
            summary=summary_payload,
            is_review=is_review,
            session_id=session_id,
            is_verified=email_verified
        )

    # Persist in SQLite runs and evaluations tables
    save_run(
        run_id=run_id,
        timestamp=timestamp,
        research_question=research_question,
        discipline=discipline,
        constraints=constraints,
        prompt_version=prompt_version,
        parsed_json=parsed.model_dump() if parsed else None,
        recommendation_json=rec.model_dump() if rec else None,
        latency_ms=latency_ms,
        session_id=session_id,
        owner_id=owner_id
    )

    if evaluation:
        save_evaluation(
            run_id=run_id,
            rubric_scores=evaluation.rubric.model_dump(),
            reference_match=evaluation.reference_match.model_dump(),
            rule_flags=evaluation.rules.flags,
            final_score=evaluation.composite_score,
            label=evaluation.label,
            owner_id=owner_id
        )

    # Log 1: Overall Pipeline Delivery
    log_execution(
        run_id=run_id,
        trigger_event=trigger,
        action_taken=action,
        status=status,
        output_file_path=report_path,
        duration_ms=latency_ms,
        action_type="PIPELINE_COMPLETE",
        session_id=session_id,
        pdf_path=pdf_path,
        email_status=email_result.get("status"),
        owner_id=owner_id
    )

    # Log 2: PDF Generation Event
    log_execution(
        run_id=run_id,
        trigger_event="METHODOLOGY_SPEC_READY",
        action_taken="GENERATE_PDF_REPORT",
        status="DELIVERED",
        output_file_path=pdf_path,
        duration_ms=pdf_duration_ms,
        action_type="PDF_GENERATED",
        session_id=session_id,
        pdf_path=pdf_path,
        owner_id=owner_id
    )

    # Log 3: Email Dispatch Event (if attempted or configured)
    if email_opt_in and recipient_email:
        log_execution(
            run_id=run_id,
            trigger_event="DELIVERABLE_PDF_ATTACHED",
            action_taken="SEND_GMAIL_NOTIFICATION",
            status=email_result.get("status", "FAILED"),
            output_file_path=pdf_path,
            duration_ms=email_result.get("duration_ms", 0),
            action_type="EMAIL_SENT",
            recipient_masked=masked_rec,
            recipient_hash=email_h,
            session_id=session_id,
            email_status=email_result.get("status"),
            message_id=email_result.get("message_id"),
            pdf_path=pdf_path,
            owner_id=owner_id
        )

    # Note: Stop writing user rows into shared results_log.csv for per-session privacy.
    # Exports are generated on demand from owner's rows only via generate_owner_csv(owner_id).

    return {
        "status": status,
        "report_path": report_path,
        "pdf_path": pdf_path,
        "email_result": email_result,
        "trigger": trigger,
        "action": action
    }
