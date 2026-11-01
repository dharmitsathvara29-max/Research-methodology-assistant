"""Pydantic schemas for Research Methodology Recommendation Assistant.

Defines strict data contracts for:
- Input parsing and validation
- Comprehensive methodology recommendations
- Multi-dimensional evaluation (Rubric, Reference, Rule-based)
- Trigger-action pipeline results
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class VariableBreakdown(BaseModel):
    independent_variables: List[str] = Field(default_factory=list, description="Independent or predictor variables")
    dependent_variables: List[str] = Field(default_factory=list, description="Dependent or outcome variables")
    control_or_confounding_variables: List[str] = Field(default_factory=list, description="Control, moderating, or confounding variables")
    qualitative_phenomena_or_concepts: List[str] = Field(default_factory=list, description="Core lived experiences, cultural phenomena, or concepts")


class ParsedQuestion(BaseModel):
    is_valid_research_question: bool = Field(description="True if the input is a genuine academic/research question")
    rejection_reason: Optional[str] = Field(default=None, description="Explanation if rejected as invalid, gibberish, or prompt injection")
    question_type: Literal["descriptive", "exploratory", "explanatory", "causal", "evaluative", "invalid"] = Field(
        default="invalid",
        description="Methodological nature of the research question"
    )
    variables_and_concepts: VariableBreakdown = Field(default_factory=VariableBreakdown)
    target_population: str = Field(default="", description="The specific demographic or unit of analysis under study")
    context_setting: str = Field(default="", description="The geographic, organizational, or academic context")
    clarification_suggestions: List[str] = Field(
        default_factory=list,
        description="Helpful recommendations to improve the question if vague or invalid"
    )


class AlternativeMethodology(BaseModel):
    paradigm: str = Field(description="Alternative research paradigm (e.g. Quantitative, Qualitative, Mixed)")
    design: str = Field(description="Specific design name (e.g. Cross-sectional Survey, Case Study)")
    rationale_for_rejection: str = Field(description="Why this alternative was deemed inferior to the primary recommendation")


class RoadmapStep(BaseModel):
    step_number: int = Field(description="Sequential phase index (1 to N)")
    title: str = Field(description="Phase title (e.g., IRB Submission, Pilot Testing, Main Data Collection)")
    description: str = Field(description="Specific actionable tasks in this phase")
    estimated_duration: str = Field(description="Realistic timeframe (e.g., 2-3 weeks, Month 2)")


class MethodologyRecommendation(BaseModel):
    parsed_question_summary: str = Field(description="Concise summary of the research question and its analytical scope")
    recommended_paradigm: Literal["Quantitative", "Qualitative", "Mixed Methods"] = Field(
        description="High-level research paradigm"
    )
    paradigm_justification: str = Field(description="Epistemological and practical justification for this paradigm")
    research_design: str = Field(description="Specific design (e.g., Randomized Experiment, Phenomenology, Convergent Parallel)")
    design_rationale: str = Field(description="Detailed rationale tying the design directly to the research question")
    sampling_strategy: str = Field(description="Specific sampling technique (e.g., Purposive, Stratified Random, Snowball)")
    sample_size_rationale: str = Field(description="Empirically or theoretically grounded sample size rationale (power analysis, saturation)")
    data_collection_instruments: List[str] = Field(description="Specific tools, questionnaires, scales, interview protocols")
    data_collection_procedures: str = Field(description="Step-by-step procedure for gathering data from participants")
    data_analysis_techniques: List[str] = Field(description="Specific statistical models (e.g., ANCOVA, Multiple Regression) or qualitative coding methods (e.g., Reflexive Thematic Analysis)")
    analysis_rationale: str = Field(description="Why these analytical techniques match the data structure and question")
    validity_and_reliability_considerations: str = Field(description="Internal/external validity, construct validity, or qualitative trustworthiness (credibility, transferability, dependability, confirmability)")
    ethical_considerations: List[str] = Field(description="Specific ethical safeguards: informed consent, privacy/confidentiality, data protection")
    vulnerable_population_flag: bool = Field(description="True if research involves protected or vulnerable groups (minors, trauma survivors, patients, refugees)")
    irb_ethics_board_required: bool = Field(description="Whether Institutional Review Board / Research Ethics Committee approval is mandatory")
    limitations_and_risks: List[str] = Field(description="Key methodological, logistical, and inferential limitations")
    alternative_methodologies: List[AlternativeMethodology] = Field(description="1-2 plausible alternatives with trade-off justification")
    step_by_step_roadmap: List[RoadmapStep] = Field(description="Phased execution plan from preparation to dissemination")
    confidence_level: Literal["Low", "Medium", "High"] = Field(description="Confidence in this methodological recommendation")
    confidence_rationale: str = Field(description="Justification for confidence rating considering constraints and question clarity")
    academic_disclaimer: str = Field(
        default="Decision Support Notice: This AI-generated methodology recommendation provides preliminary structural guidance and does not replace formal consultation with an academic advisor, supervisory committee, or institutional ethics review board (IRB/REC).",
        description="Standard mandatory academic disclaimer"
    )


class RubricCriterion(BaseModel):
    score: int = Field(ge=0, le=5, description="Rubric score 0 to 5")
    critique: str = Field(description="Constructive critique detailing justification for the score")


class RubricScore(BaseModel):
    alignment: RubricCriterion = Field(description="Alignment between research question and chosen method")
    justification_quality: RubricCriterion = Field(description="Quality and depth of logical reasoning")
    completeness: RubricCriterion = Field(description="Completeness across all required methodological sections")
    feasibility: RubricCriterion = Field(description="Feasibility under user constraints (time, budget, access, skills)")
    ethical_validity_awareness: RubricCriterion = Field(description="Depth of ethics, vulnerable group safeguards, and validity/trustworthiness")
    total_raw_score: int = Field(ge=0, le=25, description="Sum of 5 criteria (max 25)")
    normalized_score: float = Field(ge=0.0, le=100.0, description="Normalized percentage (total_raw_score / 25 * 100)")
    overall_verdict: str = Field(description="Summary evaluative remarks")


class RuleCheckResult(BaseModel):
    all_required_fields_present: bool = True
    has_sample_size_rationale: bool = True
    paradigm_analysis_consistent: bool = True
    invented_citations_detected: List[str] = Field(default_factory=list)
    rule_score_pct: float = 100.0
    flags: List[str] = Field(default_factory=list)


class ReferenceMatchResult(BaseModel):
    matched_reference_id: Optional[str] = None
    matched_pattern: Optional[str] = None
    paradigm_match: bool = False
    design_match: bool = False
    status: Literal["MATCH", "PARTIAL", "MISMATCH", "NO_REFERENCE"] = "NO_REFERENCE"
    score_pct: float = 100.0
    notes: str = ""


class EvaluationResult(BaseModel):
    rubric: RubricScore
    reference_match: ReferenceMatchResult
    rules: RuleCheckResult
    composite_score: float = Field(ge=0.0, le=100.0, description="Weighted composite score")
    label: Literal["PASS", "REVIEW", "FAIL"] = "REVIEW"
    refinement_needed: bool = False
    critique_feedback: Optional[str] = None


class PipelineResult(BaseModel):
    run_id: str
    timestamp: str
    research_question: str
    discipline: str
    constraints: Dict[str, Any]
    prompt_version: str
    parsed_question: Optional[ParsedQuestion] = None
    recommendation: Optional[MethodologyRecommendation] = None
    evaluation: Optional[EvaluationResult] = None
    latency_ms: int = 0
    status: Literal["DELIVERED", "FLAGGED_FOR_HUMAN_REVIEW", "REJECTED_INPUT", "ERROR"] = "DELIVERED"
    report_path: Optional[str] = None
    refinement_iterations: int = 0
    error_message: Optional[str] = None

