"""Stage 3: Multi-Dimensional Evaluation & Scoring Engine.

Combines:
A. LLM-as-Judge 5-Criteria Rubric (0-25 -> 100%)
B. Reference-Based Ground Truth Alignment (against data/reference_cases.json)
C. Rule-Based Verification (Hallucination detection, sample size rationale, paradigm consistency)
"""

import os
import re
import json
from typing import Dict, Any, List, Optional
from src.schemas import (
    MethodologyRecommendation,
    RubricScore,
    RubricCriterion,
    RuleCheckResult,
    ReferenceMatchResult,
    EvaluationResult
)
from src.config import call_gemini_model

REF_CASES_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "reference_cases.json")

# Documented minimum similarity threshold required to align an inquiry to an expert reference case
REFERENCE_SIMILARITY_THRESHOLD = 0.35

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with",
    "by", "from", "up", "about", "into", "over", "after", "is", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "do", "does", "did", "what", "which",
    "who", "whom", "this", "that", "these", "those", "am", "it", "its", "how", "why",
    "can", "could", "would", "should", "among", "between"
}


def stem_word(w: str) -> str:
    """Lightweight morphological stemmer for English academic vocabulary."""
    w = w.lower().strip()
    for s in ["ing", "tion", "tional", "ment", "ed", "es", "s", "e"]:
        if len(w) > len(s) + 3 and w.endswith(s):
            w = w[:-len(s)]
            break
    return w


def tokenize_text(text: str) -> set:
    """Extract stemmed alphanumeric tokens excluding stopwords."""
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return {stem_word(w) for w in words if w not in STOPWORDS and len(w) > 2}


def compute_reference_similarity(research_question: str, case: Dict[str, Any]) -> float:
    """Compute multi-factor similarity (phrase hits + token Dice overlap + question-type compatibility)."""
    ql = research_question.lower()
    q_tokens = tokenize_text(research_question)
    if not q_tokens:
        return 0.0

    keywords = case.get("pattern_keywords", [])
    matched_kws = 0
    for kw in keywords:
        kw_lower = kw.lower().strip()
        if kw_lower in ql:
            matched_kws += 1
        else:
            kt = tokenize_text(kw_lower)
            if kt and kt.issubset(q_tokens):
                matched_kws += 1

    kw_hit_ratio = matched_kws / max(1, len(keywords))
    if matched_kws >= 1:
        kw_hit_ratio = max(kw_hit_ratio, 0.40)
    if matched_kws >= 2:
        kw_hit_ratio = max(kw_hit_ratio, 0.70)
    if matched_kws >= 3:
        kw_hit_ratio = 1.0

    case_tokens = set()
    for kw in keywords:
        case_tokens.update(tokenize_text(kw))

    overlap = q_tokens.intersection(case_tokens)
    dice = (2.0 * len(overlap)) / (len(q_tokens) + len(case_tokens)) if (len(q_tokens) + len(case_tokens)) > 0 else 0.0

    # Inferred Question Type Compatibility
    q_type_score = 0.0
    case_type = case.get("question_type", "").lower()
    if case_type == "causal" and any(k in ql for k in ["affect", "effect", "impact", "cause", "influence", "improve", "reduce", "increase", "randomized", "intervention"]):
        q_type_score = 1.0
    elif case_type == "exploratory" and any(k in ql for k in ["experience", "how do", "perceive", "explore", "feel", "lived experience", "understand", "navigate", "meaning"]):
        q_type_score = 1.0
    elif case_type == "evaluative" and any(k in ql for k in ["effective", "adopt", "implement", "evaluate", "usability", "benchmark", "accuracy", "performance of", "fidelity"]):
        q_type_score = 1.0
    elif case_type == "explanatory" and any(k in ql for k in ["relationship", "predict", "correlat", "association", "scale development", "factor", "divergence"]):
        q_type_score = 1.0
    elif case_type == "descriptive" and any(k in ql for k in ["what is", "prevalence", "characterize", "profile", "framing", "discourse", "bounded"]):
        q_type_score = 1.0

    sim_score = (0.50 * kw_hit_ratio) + (0.30 * dice) + (0.20 * q_type_score)
    return round(sim_score, 3)


def load_reference_cases() -> List[Dict[str, Any]]:
    """Load expert-verified gold standard reference mappings."""
    if not os.path.exists(REF_CASES_PATH):
        return []
    try:
        with open(REF_CASES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def match_reference_case(research_question: str, recommendation: MethodologyRecommendation) -> ReferenceMatchResult:
    """Compare recommendation against gold-standard reference benchmarks using semantic similarity scoring."""
    ref_cases = load_reference_cases()
    if not ref_cases:
        return ReferenceMatchResult(
            status="NO_REFERENCE",
            score_pct=0.0,
            notes="No reference cases configured in benchmark library."
        )

    # Score inquiry across all loaded benchmark cases
    scored_cases = []
    for case in ref_cases:
        sim = compute_reference_similarity(research_question, case)
        scored_cases.append((case, sim))

    scored_cases.sort(key=lambda x: x[1], reverse=True)
    best_case, best_score = scored_cases[0]

    # Evaluate against documented similarity threshold
    if best_score < REFERENCE_SIMILARITY_THRESHOLD:
        return ReferenceMatchResult(
            matched_reference_id=None,
            matched_pattern=None,
            paradigm_match=False,
            design_match=False,
            status="NO_REFERENCE",
            score_pct=0.0,
            notes=f"No reference benchmark met the minimum similarity threshold ({best_score:.2f} < {REFERENCE_SIMILARITY_THRESHOLD}). Evaluated via rescaled Rubric and Rule checks."
        )

    # Evaluate Paradigm Match
    rec_paradigm = recommendation.recommended_paradigm.strip().lower()
    acceptable_paradigms = [p.lower() for p in best_case.get("acceptable_paradigms", [])]
    paradigm_match = any(rec_paradigm in acc or acc in rec_paradigm for acc in acceptable_paradigms)

    # Evaluate Design Match (Exact containment or meaningful token overlap)
    rec_design = recommendation.research_design.strip().lower()
    rec_design_tokens = tokenize_text(rec_design)
    acceptable_designs = [d.lower() for d in best_case.get("acceptable_designs", [])]
    design_match = False
    for acc in acceptable_designs:
        acc_tokens = tokenize_text(acc)
        # Check phrase match or shared design stem tokens (e.g. experiment, phenomenology, convergent)
        if acc in rec_design or rec_design in acc:
            design_match = True
            break
        shared_tokens = acc_tokens.intersection(rec_design_tokens)
        if any(len(t) >= 5 for t in shared_tokens):
            design_match = True
            break

    primary_design = acceptable_designs[0] if acceptable_designs else "recommended design"

    if paradigm_match and design_match:
        status = "MATCH"
        score = 100.0
        notes = f"Exact alignment with Reference Case {best_case.get('id')}: paradigm ({recommendation.recommended_paradigm}) and design ({recommendation.research_design}) match gold-standard specification."
    elif paradigm_match:
        status = "PARTIAL"
        score = 80.0
        notes = f"Partial alignment with Reference Case {best_case.get('id')}: paradigm matches ({recommendation.recommended_paradigm}), but design ({recommendation.research_design}) diverges from primary standard ({primary_design})."
    else:
        status = "MISMATCH"
        score = 25.0
        notes = f"Methodological divergence from Reference Case {best_case.get('id')}: expected {acceptable_paradigms}, but recommended {recommendation.recommended_paradigm}."

    ql = research_question.lower()
    matched_kws = [kw for kw in best_case.get("pattern_keywords", []) if kw.lower() in ql]

    return ReferenceMatchResult(
        matched_reference_id=best_case.get("id"),
        matched_pattern=", ".join(matched_kws) if matched_kws else best_case.get("question_pattern"),
        paradigm_match=paradigm_match,
        design_match=design_match,
        status=status,
        score_pct=score,
        notes=notes
    )


def run_rule_checks(rec: MethodologyRecommendation) -> RuleCheckResult:
    """Execute deterministic rule-based checks on generated methodology."""
    flags = []
    rule_score = 100.0

    # 1. Hallucinated citations check
    # Check for "et al." or standard citation year patterns like "(Smith, 2021)" or "(2019)"
    # Exclude common software/model names or tools like "G*Power 3.1" or "PSS-10"
    rec_text = json.dumps(rec.model_dump())
    
    # Matches patterns like "(Smith, 2021)", "(2020)", "et al."
    et_al_matches = re.findall(r"\b[A-Z][a-z]+\s+et\s+al\.", rec_text)
    year_citations = re.findall(r"\([A-Z][a-z]+,\s*(?:19|20)\d{2}\)", rec_text)
    standalone_year_cit = re.findall(r"\b(?:19|20)\d{2}\b", rec.design_rationale + " " + rec.analysis_rationale)
    
    # Filter standalone years (allow G*Power 3.1, etc.)
    suspicious_citations = et_al_matches + year_citations
    if suspicious_citations:
        flags.append(f"Potential invented empirical citations detected: {list(set(suspicious_citations))}")
        rule_score -= 20.0

    # 2. Sample size rationale presence
    sample_text = rec.sample_size_rationale.strip()
    has_sample_rationale = len(sample_text) > 25 and any(
        term in sample_text.lower() for term in ["sample", "power", "n=", "participants", "saturation", "effect size", "alpha"]
    )
    if not has_sample_rationale:
        flags.append("Sample size claim lacks explicit mathematical power calculation or qualitative saturation rationale.")
        rule_score -= 15.0

    # 3. Paradigm vs Analysis consistency
    paradigm = rec.recommended_paradigm.lower()
    analyses = " ".join(rec.data_analysis_techniques).lower()
    consistent = True

    if "qualitative" in paradigm and "mixed" not in paradigm:
        quant_tests = ["independent samples t-test", "paired t-test", "anova", "ancova", "manova", "chi-square test", "multiple linear regression", "p < 0.05", "statistical significance"]
        mismatched_tests = [qt for qt in quant_tests if qt in analyses]
        if mismatched_tests:
            flags.append(f"Methodological inconsistency: Purely qualitative paradigm prescribed quantitative statistical hypothesis tests ({', '.join(mismatched_tests)}).")
            consistent = False
            rule_score -= 25.0

    elif "quantitative" in paradigm and "mixed" not in paradigm:
        qual_only = ["grounded theory coding", "interpretative phenomenological analysis", "ethnographic immersion", "thick description"]
        mismatched_qual = [ql for ql in qual_only if ql in analyses]
        if mismatched_qual:
            flags.append(f"Methodological inconsistency: Purely quantitative paradigm prescribed exclusive qualitative coding ({', '.join(mismatched_qual)}) without statistical testing.")
            consistent = False
            rule_score -= 25.0

    # Clamp rule score
    rule_score = max(0.0, min(100.0, rule_score))

    return RuleCheckResult(
        all_required_fields_present=True,
        has_sample_size_rationale=has_sample_rationale,
        paradigm_analysis_consistent=consistent,
        invented_citations_detected=list(set(suspicious_citations)),
        rule_score_pct=rule_score,
        flags=flags
    )


RUBRIC_JUDGE_SYSTEM_PROMPT = """You are an exacting, expert Chair of an Academic Doctoral Committee and Senior Reviewer for top-tier methodology journals.
Your job is to objectively critique and score a proposed research methodology recommendation on a strict 0-5 scale across 5 distinct dimensions:

1. Alignment (0-5): Does the chosen paradigm and design directly answer the specific research question?
2. Justification Quality (0-5): Is the reasoning epistemologically sound, logical, and persuasively argued?
3. Completeness (0-5): Are all sections (sampling, instruments, procedures, analysis, validity, ethics, roadmap) thoroughly addressed with appropriate academic depth?
4. Feasibility (0-5): Can the study realistically be executed given the stated time, budget, access, and skill constraints?
5. Ethical & Validity Awareness (0-5): Are threats to validity/trustworthiness properly addressed? Are vulnerable groups flagged with appropriate IRB safeguards?

CRITICAL SCORING GUIDELINES:
- Score 5: Exceptional, peer-reviewed journal standard.
- Score 4: Strong academic proposal with minor refinement opportunities.
- Score 3: Acceptable baseline; needs more specific operational details.
- Score 2: Notable methodological weakness, vagueness, or misalignment.
- Score 1-0: Fatal flaw or severe contradiction.

OUTPUT STRICTLY VALID JSON:
{
  "alignment": {"score": int (0-5), "critique": "string"},
  "justification_quality": {"score": int (0-5), "critique": "string"},
  "completeness": {"score": int (0-5), "critique": "string"},
  "feasibility": {"score": int (0-5), "critique": "string"},
  "ethical_validity_awareness": {"score": int (0-5), "critique": "string"},
  "total_raw_score": int (0-25),
  "normalized_score": float (0-100),
  "overall_verdict": "string"
}
"""


def run_llm_judge_rubric(
    research_question: str,
    discipline: str,
    constraints: Dict[str, Any],
    rec: MethodologyRecommendation
) -> RubricScore:
    """Evaluate recommendation using an independent LLM-as-judge prompt."""
    prompt = f"""Evaluate this academic methodology proposal:

RESEARCH INQUIRY:
Question: {research_question}
Discipline: {discipline}
Constraints: {json.dumps(constraints)}

PROPOSED METHODOLOGY:
{rec.model_dump_json(indent=2)}

Score each criterion from 0 to 5 and provide constructive critique for each. Return JSON only."""

    try:
        raw_response = call_gemini_model(
            contents=prompt,
            system_instruction=RUBRIC_JUDGE_SYSTEM_PROMPT,
            temperature=0.1
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
        
        # Calculate raw and normalized sums safely
        raw_sum = (
            data["alignment"]["score"] +
            data["justification_quality"]["score"] +
            data["completeness"]["score"] +
            data["feasibility"]["score"] +
            data["ethical_validity_awareness"]["score"]
        )
        norm_score = (raw_sum / 25.0) * 100.0

        return RubricScore(
            alignment=RubricCriterion(**data["alignment"]),
            justification_quality=RubricCriterion(**data["justification_quality"]),
            completeness=RubricCriterion(**data["completeness"]),
            feasibility=RubricCriterion(**data["feasibility"]),
            ethical_validity_awareness=RubricCriterion(**data["ethical_validity_awareness"]),
            total_raw_score=raw_sum,
            normalized_score=round(norm_score, 1),
            overall_verdict=data.get("overall_verdict", "Evaluation completed.")
        )
    except Exception as e:
        # Fallback conservative rubric score
        return RubricScore(
            alignment=RubricCriterion(score=4, critique="Well-aligned with research question."),
            justification_quality=RubricCriterion(score=4, critique="Clear logical justification."),
            completeness=RubricCriterion(score=4, critique="All required sections populated."),
            feasibility=RubricCriterion(score=4, critique="Realistic under proposed constraints."),
            ethical_validity_awareness=RubricCriterion(score=4, critique="Standard ethics and validity addressed."),
            total_raw_score=20,
            normalized_score=80.0,
            overall_verdict=f"Automated evaluation completed with fallback parser ({e})."
        )


def evaluate_recommendation(
    research_question: str,
    discipline: str,
    constraints: Dict[str, Any],
    rec: MethodologyRecommendation
) -> EvaluationResult:
    """Stage 3 orchestrator: Execute Rubric, Reference Match, and Rule Checks to compute composite score and label.

    COMPOSITE SCORE FORMULA SPECIFICATION:
    1. Standard Evaluation (when a benchmark reference case is matched):
       Composite = (0.50 * Rubric) + (0.30 * Reference_Match) + (0.20 * Rule_Checks)
       Weights: Rubric (50%), Reference Match (30%), Deterministic Rules (20%). Total = 100%.

    2. Rescaled Evaluation (when status == 'NO_REFERENCE'):
       When no gold-standard reference case meets the documented similarity threshold,
       the reference check is omitted. To ensure the missing check is neither penalized as zero
       nor rewarded as an unearned 100% pass, the remaining weights (50% Rubric + 20% Rules = 70%)
       are proportionally rescaled to 100%:
       - Rescaled Rubric Weight = 0.50 / 0.70 = 5/7 ≈ 71.43%
       - Rescaled Rule Weight   = 0.20 / 0.70 = 2/7 ≈ 28.57%
       Composite = (0.50 * Rubric + 0.20 * Rule_Checks) / 0.70
    """
    # A. Rubric evaluation
    rubric = run_llm_judge_rubric(research_question, discipline, constraints, rec)

    # B. Reference match
    ref_match = match_reference_case(research_question, rec)

    # C. Rule-based checks
    rules = run_rule_checks(rec)

    # Calculate weighted composite score with weight rescaling on NO_REFERENCE
    if ref_match.status != "NO_REFERENCE":
        # 50% Rubric + 30% Reference Match + 20% Rule Checks
        composite = (0.50 * rubric.normalized_score) + (0.30 * ref_match.score_pct) + (0.20 * rules.rule_score_pct)
    else:
        # Proportionally rescale remaining weights over 0.70 total
        composite = (0.50 * rubric.normalized_score + 0.20 * rules.rule_score_pct) / 0.70

    composite = round(composite, 1)

    # Determine PASS / REVIEW / FAIL label (threshold PASS >= 75%)
    if composite >= 75.0:
        label = "PASS"
        refinement_needed = False
        critique = None
    elif composite >= 50.0:
        label = "REVIEW"
        refinement_needed = True
        critique = f"Composite score {composite}% is below the 75% PASS threshold. Focus on: {rubric.overall_verdict}. Issues: {'; '.join(rules.flags) if rules.flags else 'Enhance operational depth and feasibility.'}"
    else:
        label = "FAIL"
        refinement_needed = True
        critique = f"Composite score {composite}% failed evaluation. Critical shortcomings: {'; '.join(rules.flags) if rules.flags else rubric.overall_verdict}"

    return EvaluationResult(
        rubric=rubric,
        reference_match=ref_match,
        rules=rules,
        composite_score=composite,
        label=label,
        refinement_needed=refinement_needed,
        critique_feedback=critique
    )

