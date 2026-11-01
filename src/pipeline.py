"""Four-Stage Research Methodology Pipeline Orchestrator.

Implements:
- Stage 1: Input Validation & Parsing
- Stage 2: Methodology Generation (with Pydantic schema validation & retry)
- Stage 3: Validation & Scoring (Rubric + Reference + Rule checks)
- Stage 4: Refinement & Delivery (Refinement loop if score < 75% + Trigger-Action Automation)
"""

import time
import uuid
import json
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from src.schemas import (
    ParsedQuestion,
    MethodologyRecommendation,
    EvaluationResult,
    PipelineResult
)
from src.validators import parse_and_validate_question
from src.prompts import format_methodology_prompt
from src.config import call_gemini_model
from src.evaluator import evaluate_recommendation
from src.automation import execute_automation_workflow


def safe_print(*args, **kwargs):
    """Safely print to stdout, catching OSError/IOError (e.g. [Errno 5] Input/output error on detached terminals)."""
    try:
        print(*args, **kwargs)
    except (OSError, IOError):
        pass


def stage1_validate_and_parse(research_question: str, discipline: str) -> ParsedQuestion:
    """Stage 1: Verify question validity and extract structured analytical scope."""
    safe_print(f"[Stage 1] Validating and parsing input question (length={len(research_question)})...")
    parsed = parse_and_validate_question(research_question, discipline)
    safe_print(f"[Stage 1] Valid: {parsed.is_valid_research_question}, Type: {parsed.question_type}")
    return parsed


def stage2_generate_methodology(
    research_question: str,
    discipline: str,
    parsed: ParsedQuestion,
    constraints: Dict[str, Any],
    prompt_version: str = "v3_decomposed",
    refinement_critique: Optional[str] = None
) -> MethodologyRecommendation:
    """Stage 2: Generate complete structured methodology with schema validation and 1 retry on malformed JSON."""
    safe_print(f"[Stage 2] Generating methodology using prompt {prompt_version} (refinement={bool(refinement_critique)})...")

    prompt_text = format_methodology_prompt(
        version=prompt_version,
        research_question=research_question,
        discipline=discipline,
        parsed_json=parsed.model_dump(),
        constraints=constraints
    )

    if refinement_critique:
        prompt_text += f"\n\n### CRITICAL REFINEMENT FEEDBACK FROM EVALUATOR:\n{refinement_critique}\n\nPlease revise the methodology to resolve every critique noted above while maintaining rigorous formatting."

    # First attempt
    for attempt in range(2):
        try:
            raw_response = call_gemini_model(
                contents=prompt_text,
                temperature=0.2 if attempt == 0 else 0.1
            )
            
            cleaned = raw_response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

            data = json.loads(cleaned)
            rec = MethodologyRecommendation.model_validate(data)
            safe_print(f"[Stage 2] Successfully generated and validated methodology on attempt {attempt + 1}.")
            return rec
        except Exception as err:
            safe_print(f"[Stage 2] Attempt {attempt + 1} failed with error: {err}")
            if attempt == 0:
                safe_print("[Stage 2] Retrying once with explicit schema reinforcement...")
                prompt_text += "\n\nCRITICAL: Your previous response could not be parsed as valid JSON. Output ONLY raw, unadorned JSON matching the exact schema."
            else:
                raise RuntimeError(f"Stage 2 failed after 2 attempts to produce valid JSON: {err}")


def stage3_evaluate(
    research_question: str,
    discipline: str,
    constraints: Dict[str, Any],
    recommendation: MethodologyRecommendation
) -> EvaluationResult:
    """Stage 3: Multi-dimensional validation & scoring."""
    safe_print("[Stage 3] Executing rubric, reference-based, and rule-based evaluation...")
    eval_result = evaluate_recommendation(
        research_question=research_question,
        discipline=discipline,
        constraints=constraints,
        rec=recommendation
    )
    safe_print(f"[Stage 3] Evaluation complete: Score = {eval_result.composite_score}%, Label = {eval_result.label}")
    return eval_result


def stage4_refine_and_deliver(
    run_id: str,
    research_question: str,
    discipline: str,
    constraints: Dict[str, Any],
    prompt_version: str,
    parsed: ParsedQuestion,
    initial_rec: MethodologyRecommendation,
    initial_eval: EvaluationResult,
    start_time: float
) -> Tuple[MethodologyRecommendation, EvaluationResult, Dict[str, Any], int]:
    """Stage 4: Automated refinement loop (if score < 75%) and delivery automation trigger."""
    safe_print("[Stage 4] Checking threshold for delivery or refinement...")
    rec = initial_rec
    evaluation = initial_eval
    refinement_iterations = 0

    # If score below 75% threshold, perform one automatic refinement regeneration
    if evaluation.label in ["REVIEW", "FAIL"] and evaluation.refinement_needed:
        safe_print(f"[Stage 4] Score {evaluation.composite_score}% is below 75% PASS threshold. Executing automated refinement regeneration...")
        refinement_iterations = 1
        try:
            refined_rec = stage2_generate_methodology(
                research_question=research_question,
                discipline=discipline,
                parsed=parsed,
                constraints=constraints,
                prompt_version=prompt_version,
                refinement_critique=evaluation.critique_feedback
            )
            refined_eval = stage3_evaluate(
                research_question=research_question,
                discipline=discipline,
                constraints=constraints,
                recommendation=refined_rec
            )
            # Accept refinement if score improved
            if refined_eval.composite_score >= evaluation.composite_score:
                safe_print(f"[Stage 4] Refinement improved score: {evaluation.composite_score}% -> {refined_eval.composite_score}%")
                rec = refined_rec
                evaluation = refined_eval
        except Exception as e:
            safe_print(f"[Stage 4] Refinement error: {e}. Preserving initial recommendation.")

    duration_ms = int((time.time() - start_time) * 1000)

    # Execute trigger-action automation
    automation_res = execute_automation_workflow(
        run_id=run_id,
        research_question=research_question,
        discipline=discipline,
        constraints=constraints,
        prompt_version=prompt_version,
        parsed=parsed,
        rec=rec,
        evaluation=evaluation,
        latency_ms=duration_ms,
        refinement_iterations=refinement_iterations
    )

    return rec, evaluation, automation_res, refinement_iterations


def run_methodology_pipeline(
    research_question: str,
    discipline: str = "General Social Science",
    constraints: Optional[Dict[str, Any]] = None,
    prompt_version: str = "v3_decomposed"
) -> PipelineResult:
    """Execute complete 4-stage end-to-end pipeline."""
    start_time = time.time()
    run_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    constraints = constraints or {}

    # Stage 1: Input Validation & Parsing
    parsed = stage1_validate_and_parse(research_question, discipline)
    if not parsed.is_valid_research_question:
        duration_ms = int((time.time() - start_time) * 1000)
        auto_res = execute_automation_workflow(
            run_id=run_id,
            research_question=research_question,
            discipline=discipline,
            constraints=constraints,
            prompt_version=prompt_version,
            parsed=parsed,
            rec=None,
            evaluation=None,
            latency_ms=duration_ms
        )
        return PipelineResult(
            run_id=run_id,
            timestamp=timestamp,
            research_question=research_question,
            discipline=discipline,
            constraints=constraints,
            prompt_version=prompt_version,
            parsed_question=parsed,
            recommendation=None,
            evaluation=None,
            latency_ms=duration_ms,
            status="REJECTED_INPUT",
            report_path=None,
            refinement_iterations=0,
            error_message=parsed.rejection_reason
        )

    # Stage 2: Methodology Generation
    rec = stage2_generate_methodology(
        research_question=research_question,
        discipline=discipline,
        parsed=parsed,
        constraints=constraints,
        prompt_version=prompt_version
    )

    # Stage 3: Validation & Scoring
    evaluation = stage3_evaluate(
        research_question=research_question,
        discipline=discipline,
        constraints=constraints,
        recommendation=rec
    )

    # Stage 4: Refinement & Delivery
    final_rec, final_eval, auto_res, ref_iters = stage4_refine_and_deliver(
        run_id=run_id,
        research_question=research_question,
        discipline=discipline,
        constraints=constraints,
        prompt_version=prompt_version,
        parsed=parsed,
        initial_rec=rec,
        initial_eval=evaluation,
        start_time=start_time
    )

    total_latency = int((time.time() - start_time) * 1000)

    return PipelineResult(
        run_id=run_id,
        timestamp=timestamp,
        research_question=research_question,
        discipline=discipline,
        constraints=constraints,
        prompt_version=prompt_version,
        parsed_question=parsed,
        recommendation=final_rec,
        evaluation=final_eval,
        latency_ms=total_latency,
        status=auto_res.get("status", "DELIVERED"),
        report_path=auto_res.get("report_path"),
        refinement_iterations=ref_iters
    )

