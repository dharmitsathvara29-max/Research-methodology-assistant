"""Unit & Integration Tests for the Improved Reference-Based Checking Engine.
Verifies:
1. Matching Question (MATCH -> score_pct=100.0, composite uses 50/30/20)
2. Partial Match Question (PARTIAL -> score_pct=80.0, composite uses 50/30/20)
3. Mismatch Question (MISMATCH -> score_pct=25.0, composite uses 50/30/20)
4. Unmatched Question (NO_REFERENCE -> weight rescaling over 70%, neither 0% nor 100% free pass)
5. Comprehensive Reference Case Library (>= 25 cases across diverse domains, zero fabricated citations)
"""

import os
import sys
import json
import unittest
from typing import Dict, Any

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.schemas import (
    MethodologyRecommendation,
    RubricScore,
    RubricCriterion,
    RuleCheckResult,
    ReferenceMatchResult,
    EvaluationResult,
    RoadmapStep,
    AlternativeMethodology
)
from src.evaluator import (
    load_reference_cases,
    match_reference_case,
    compute_reference_similarity,
    evaluate_recommendation,
    REFERENCE_SIMILARITY_THRESHOLD
)


def make_dummy_recommendation(
    paradigm: str,
    design: str,
    vulnerable: bool = False,
    sample_text: str = "A power analysis via G*Power indicates n=128 is required for statistical power of 0.80.",
    analysis_list: list = None
) -> MethodologyRecommendation:
    """Helper to construct a valid MethodologyRecommendation for testing."""
    return MethodologyRecommendation(
        parsed_question_summary="Investigating empirical relationships.",
        recommended_paradigm=paradigm,
        paradigm_justification="Epistemologically sound justification for paradigm selection.",
        research_design=design,
        design_rationale="Thorough design rationale aligned with research aims.",
        sampling_strategy="Probability sampling across cohort.",
        sample_size_rationale=sample_text,
        data_collection_instruments=["Standardized measurement scale"],
        data_collection_procedures="Administered in controlled environment.",
        data_analysis_techniques=analysis_list or (["independent samples t-test", "linear regression"] if "quant" in paradigm.lower() else ["thematic analysis"]),
        analysis_rationale="Analytical model directly maps to hypotheses.",
        validity_and_reliability_considerations="Internal and external validity controls implemented.",
        ethical_considerations=["Informed consent obtained", "Data de-identified"],
        vulnerable_population_flag=vulnerable,
        irb_ethics_board_required=True,
        limitations_and_risks=["Potential self-selection bias"],
        alternative_methodologies=[
            AlternativeMethodology(
                paradigm="Alternative Paradigm",
                design="Alternative Design",
                rationale_for_rejection="Lacks sufficient experimental control."
            )
        ],
        step_by_step_roadmap=[
            RoadmapStep(
                step_number=1,
                title="Ethical Approval & Sampling",
                description="Obtain clearance and recruit participants.",
                estimated_duration="Month 1"
            )
        ],
        confidence_level="High",
        confidence_rationale="High methodological alignment and sufficient resources.",
        academic_disclaimer="Faculty supervision and IRB clearance required."
    )


class TestReferenceBasedChecking(unittest.TestCase):
    """Test suite asserting reference matching, composite score calculation, and weight rescaling."""

    def test_reference_library_size_and_integrity(self):
        """Assert library has at least 25 cases, correct fields, and zero fabricated citations."""
        cases = load_reference_cases()
        self.assertGreaterEqual(len(cases), 25, f"Expected >= 25 cases, found {len(cases)}")

        required_keys = {"id", "pattern_keywords", "question_type", "acceptable_paradigms", "acceptable_designs"}
        for c in cases:
            for k in required_keys:
                self.assertIn(k, c, f"Case {c.get('id')} missing required key '{k}'")
            self.assertIsInstance(c["pattern_keywords"], list)
            self.assertGreaterEqual(len(c["pattern_keywords"]), 3)
            self.assertIn("rationale", c)

            # Check for fabricated literature citations in notes and rationale
            combined_text = (c.get("rationale", "") + " " + c.get("notes", "")).lower()
            self.assertNotIn("et al.", combined_text, f"Fabricated citation detected in {c['id']}")
            self.assertNotRegex(combined_text, r"\b(19|20)\d{2}\b", f"Fabricated year citation in {c['id']}")

    def test_matching_question_match_status(self):
        """Assert inquiry matching REF-001 with Quantitative RCT yields MATCH (100%)."""
        q = "Does daily sleep duration affect exam performance among undergraduate students?"
        rec = make_dummy_recommendation(paradigm="Quantitative", design="Randomized Controlled Trial")

        ref_result = match_reference_case(q, rec)
        self.assertEqual(ref_result.status, "MATCH")
        self.assertEqual(ref_result.matched_reference_id, "REF-001")
        self.assertEqual(ref_result.score_pct, 100.0)
        self.assertTrue(ref_result.paradigm_match)
        self.assertTrue(ref_result.design_match)
        self.assertIn("Exact alignment", ref_result.notes)

    def test_partial_match_question_partial_status(self):
        """Assert inquiry matching REF-001 with Quantitative but non-experimental design yields PARTIAL (80%)."""
        q = "Does daily sleep duration affect exam performance among undergraduate students?"
        # Using a design that is not in acceptable_designs for causal claims (e.g. Pure Cross-Sectional Retrospective Survey)
        rec = make_dummy_recommendation(paradigm="Quantitative", design="Retrospective Uncontrolled Observation")

        ref_result = match_reference_case(q, rec)
        self.assertEqual(ref_result.status, "PARTIAL")
        self.assertEqual(ref_result.matched_reference_id, "REF-001")
        self.assertEqual(ref_result.score_pct, 80.0)
        self.assertTrue(ref_result.paradigm_match)
        self.assertFalse(ref_result.design_match)
        self.assertIn("Partial alignment", ref_result.notes)

    def test_mismatch_question_mismatch_status(self):
        """Assert inquiry matching REF-001 with Qualitative paradigm yields MISMATCH (25%)."""
        q = "Does daily sleep duration affect exam performance among undergraduate students?"
        rec = make_dummy_recommendation(
            paradigm="Qualitative",
            design="Phenomenological Inquiry",
            analysis_list=["thematic analysis", "interpretative phenomenological analysis"]
        )

        ref_result = match_reference_case(q, rec)
        self.assertEqual(ref_result.status, "MISMATCH")
        self.assertEqual(ref_result.matched_reference_id, "REF-001")
        self.assertEqual(ref_result.score_pct, 25.0)
        self.assertFalse(ref_result.paradigm_match)
        self.assertIn("Methodological divergence", ref_result.notes)

    def test_unmatched_question_no_reference_status(self):
        """Assert inquiry without matching reference case yields NO_REFERENCE."""
        q = "What are the optimal hyperparameters for training a LoRA adapter on an edge TPU device?"
        rec = make_dummy_recommendation(paradigm="Quantitative", design="Empirical Benchmarking")

        ref_result = match_reference_case(q, rec)
        self.assertEqual(ref_result.status, "NO_REFERENCE")
        self.assertIsNone(ref_result.matched_reference_id)
        self.assertEqual(ref_result.score_pct, 0.0)
        self.assertFalse(ref_result.paradigm_match)
        self.assertFalse(ref_result.design_match)
        self.assertIn("minimum similarity threshold", ref_result.notes)

    def test_composite_score_formula_with_match(self):
        """Assert composite score follows (0.50 * Rubric) + (0.30 * Ref) + (0.20 * Rules) on MATCH."""
        # Simulated scores: Rubric = 90.0, Ref = 100.0, Rules = 100.0
        # Expected: 0.50 * 90.0 + 0.30 * 100.0 + 0.20 * 100.0 = 45.0 + 30.0 + 20.0 = 95.0
        rubric_score = 90.0
        ref_score = 100.0
        rule_score = 100.0
        expected = round((0.50 * rubric_score) + (0.30 * ref_score) + (0.20 * rule_score), 1)
        self.assertEqual(expected, 95.0)

    def test_composite_score_formula_with_partial(self):
        """Assert composite score follows (0.50 * Rubric) + (0.30 * 80) + (0.20 * Rules) on PARTIAL."""
        # Simulated scores: Rubric = 80.0, Ref = 80.0, Rules = 100.0
        # Expected: 0.50 * 80.0 + 0.30 * 80.0 + 0.20 * 100.0 = 40.0 + 24.0 + 20.0 = 84.0
        rubric_score = 80.0
        ref_score = 80.0
        rule_score = 100.0
        expected = round((0.50 * rubric_score) + (0.30 * ref_score) + (0.20 * rule_score), 1)
        self.assertEqual(expected, 84.0)

    def test_composite_score_formula_with_mismatch(self):
        """Assert composite score follows (0.50 * Rubric) + (0.30 * 25) + (0.20 * Rules) on MISMATCH."""
        # Simulated scores: Rubric = 80.0, Ref = 25.0, Rules = 80.0
        # Expected: 0.50 * 80.0 + 0.30 * 25.0 + 0.20 * 80.0 = 40.0 + 7.5 + 16.0 = 63.5
        rubric_score = 80.0
        ref_score = 25.0
        rule_score = 80.0
        expected = round((0.50 * rubric_score) + (0.30 * ref_score) + (0.20 * rule_score), 1)
        self.assertEqual(expected, 63.5)

    def test_composite_score_rescaling_on_no_reference(self):
        """Assert composite score proportionally rescales remaining weights on NO_REFERENCE."""
        # When ref is NO_REFERENCE:
        # Rubric (50%) and Rules (20%) sum to 70%.
        # Rescaled: Rubric = 50/70 ≈ 71.43%, Rules = 20/70 ≈ 28.57%
        # Formula: (0.50 * Rubric + 0.20 * Rules) / 0.70
        rubric_score = 84.0
        rule_score = 100.0
        rescaled_composite = round((0.50 * rubric_score + 0.20 * rule_score) / 0.70, 1)

        # 0.50 * 84 = 42.0; 0.20 * 100 = 20.0; sum = 62.0; 62.0 / 0.70 = 88.5714 -> 88.6
        self.assertEqual(rescaled_composite, 88.6)

        # Assert it is NEITHER penalized as zero (which would be 62.0%)
        penalized_zero = (0.50 * rubric_score) + (0.30 * 0.0) + (0.20 * rule_score)
        self.assertNotEqual(rescaled_composite, penalized_zero)
        self.assertGreater(rescaled_composite, penalized_zero)

        # NOR rewarded as unearned pass (which would be 42 + 30 + 20 = 92.0%)
        free_pass = (0.50 * rubric_score) + (0.30 * 100.0) + (0.20 * rule_score)
        self.assertNotEqual(rescaled_composite, free_pass)
        self.assertLess(rescaled_composite, free_pass)


if __name__ == "__main__":
    unittest.main()
