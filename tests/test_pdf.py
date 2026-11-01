"""Automated Test Suite for ReportLab PDF Generation (src/pdf_report.py)."""

import os
import sys
import io
import pypdf

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.pdf_report import build_pdf, save_pdf
from src.schemas import (
    MethodologyRecommendation, AlternativeMethodology, RoadmapStep,
    RubricCriterion, RubricScore, RuleCheckResult, ReferenceMatchResult, EvaluationResult
)


def create_test_fixtures():
    """Create comprehensive test fixture with edge-case characters (<, &, quotes, unicode)."""
    rec = MethodologyRecommendation(
        parsed_question_summary='Evaluates sleep duration & exam performance under randomized conditions: α < 0.05 and power → 80% with "strict" controls & <escaped tags>.',
        recommended_paradigm='Quantitative',
        paradigm_justification='Positivist paradigm requiring empirical & numerical falsification with significance level α = 0.05.',
        research_design='Randomized Controlled Trial',
        design_rationale='Two-arm pre-test/post-test randomized design with baseline GPA ANCOVA adjustment & control group.',
        sampling_strategy='Stratified cluster sampling across undergraduate departments (Science, Arts, Engineering).',
        sample_size_rationale='G*Power v3.1 calculation: N=128 participants required for medium effect size (f=0.25) at α=0.05 and power=0.80.',
        data_collection_instruments=[
            'Standardized Cognitive Examination <Form A & B>',
            'ActiGraph GT9X Link Accelerometer Watch',
            'Pittsburgh Sleep Quality Index (PSQI) Questionnaire'
        ],
        data_collection_procedures='Continuous 14-day actigraphy tracking followed by standardized proctored exam.',
        data_analysis_techniques=['Analysis of Covariance (ANCOVA)', 'Paired-samples t-test', 'Multiple Linear Regression'],
        analysis_rationale='ANCOVA controls for pre-existing baseline GPA variability and sleep history.',
        validity_and_reliability_considerations='Internal validity guarded via double-blind scoring; test-retest reliability r = 0.88.',
        ethical_considerations=[
            'Institutional Review Board (IRB) approved protocol #2026-PSY-104',
            'Written digital informed consent & de-identified participant IDs',
            'Full psychological debriefing & circadian health counseling offered'
        ],
        vulnerable_population_flag=True,
        irb_ethics_board_required=True,
        limitations_and_risks=[
            'Potential student attrition during high-stress final exam periods',
            'Device non-compliance during sleep monitoring'
        ],
        alternative_methodologies=[
            AlternativeMethodology(
                paradigm='Qualitative',
                design='Phenomenology',
                rationale_for_rejection='Cannot isolate direction of causality or compute numerical effect sizes.'
            ),
            AlternativeMethodology(
                paradigm='Quantitative Observational',
                design='Cross-Sectional Survey',
                rationale_for_rejection='Susceptible to severe unmeasured confounding and reverse causation.'
            )
        ],
        step_by_step_roadmap=[
            RoadmapStep(step_number=1, title='Protocol & IRB Submission', description='File comprehensive institutional ethics application.', estimated_duration='Month 1'),
            RoadmapStep(step_number=2, title='Participant Recruitment', description='Randomized screening and baseline sleep diary.', estimated_duration='Month 2'),
            RoadmapStep(step_number=3, title='Trial Execution & Testing', description='14-day actigraphy deployment and proctored exam administration.', estimated_duration='Month 3'),
            RoadmapStep(step_number=4, title='Statistical Analysis & Report', description='ANCOVA modeling, hypothesis testing, and manuscript draft.', estimated_duration='Month 4')
        ],
        confidence_level='High',
        confidence_rationale='Standard gold standard clinical trial methodology with verified statistical power.',
        academic_disclaimer='Decision support only, not a replacement for supervisor or ethics-board approval.'
    )

    rubric = RubricScore(
        alignment=RubricCriterion(score=5, critique='Flawless causal alignment between question and RCT design.'),
        justification_quality=RubricCriterion(score=5, critique='Rigorous mathematical and epistemological reasoning.'),
        completeness=RubricCriterion(score=5, critique='All 10 required clauses populated with comprehensive detail.'),
        feasibility=RubricCriterion(score=4, critique='Demanding actigraphy protocol; requires student compliance incentives.'),
        ethical_validity_awareness=RubricCriterion(score=5, critique='Exemplary IRB protocols and vulnerable cohort alerts.'),
        total_raw_score=24,
        normalized_score=96.0,
        overall_verdict='PASS: Publication-grade causal methodology specification.'
    )

    evaluation = EvaluationResult(
        rubric=rubric,
        reference_match=ReferenceMatchResult(
            matched_reference_id='REF-001',
            similarity_score=1.0,
            status='MATCH',
            notes='Direct match with gold standard causal sleep study benchmark.'
        ),
        rules=RuleCheckResult(passed=True, flags=[]),
        composite_score=96.0,
        label='PASS'
    )

    run_record = {
        'run_id': 'test-run-pdf-unit-001',
        'timestamp': '2026-11-01 12:30:00 UTC',
        'research_question': 'Does daily sleep duration affect exam performance among undergraduate students? <test inquiry & special chars>',
        'discipline': 'Psychology & Behavioral Sciences',
        'prompt_version': 'v3_decomposed',
        'constraints': {
            'time': 'Semester (3-5 months)',
            'budget': 'Moderate ($500 - $3,000)',
            'sample_access': 'University Subject Pool',
            'ethical_sensitivity': 'High (Protected students)',
            'skill_level': 'Intermediate'
        }
    }

    return run_record, rec, evaluation


def test_pdf_bytes_and_structure():
    """Verify PDF generates valid bytes starting with %PDF and has at least 2 pages."""
    run_rec, rec, eval_res = create_test_fixtures()
    pdf_bytes = build_pdf(run_rec, rec, eval_res)

    assert isinstance(pdf_bytes, bytes), "build_pdf must return bytes"
    assert pdf_bytes.startswith(b"%PDF"), "PDF bytes must start with %PDF magic header"
    assert len(pdf_bytes) > 5000, "PDF bytes must be substantively populated (> 5 KB)"

    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    page_count = len(reader.pages)
    print(f"Generated PDF page count: {page_count}")
    assert page_count >= 2, f"Expected at least 2 pages, got {page_count}"

    full_text = " ".join([page.extract_text() for page in reader.pages])

    # Assert question text and standard disclaimer are present
    assert "Does daily sleep duration affect exam performance" in full_text, "Research question text missing from PDF"
    assert "Decision support only" in full_text, "Academic disclaimer missing from PDF footer"
    assert "MethodWise" in full_text, "Brand name missing from PDF"
    assert "Page 1 of" in full_text, "Page numbering missing from PDF footer"
    assert "G*Power v3.1 calculation" in full_text, "Sample size rationale missing from PDF"
    print("test_pdf_bytes_and_structure: PASS")


def test_special_characters_no_crash():
    """Assert text containing <, &, quotes, and non-ASCII characters does not crash the build."""
    run_rec, rec, eval_res = create_test_fixtures()
    # Inject adversarial XML/HTML fragments and unicode
    rec.parsed_question_summary = "Adversarial test: <script>alert('xss')</script> & <b>bold</b> &amp; 'quotes' \"double\" & é, à, ç, α, β, →"
    rec.limitations_and_risks = ["Risk with <brackets> & unescaped & amp;", "Special chars: © 2026 ® ™"]
    run_rec['research_question'] = "Question with <tags> & symbols: 1 < 2 & 5 > 3?"

    pdf_bytes = build_pdf(run_rec, rec, eval_res)
    assert pdf_bytes.startswith(b"%PDF"), "Must build successfully even with raw < and &"

    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    full_text = " ".join([page.extract_text() for page in reader.pages])
    assert "Adversarial test" in full_text, "Text should be rendered safely"
    print("test_special_characters_no_crash: PASS")


def test_save_pdf_to_disk():
    """Assert save_pdf writes file to disk and returns accessible path."""
    run_rec, rec, eval_res = create_test_fixtures()
    output_path = save_pdf(run_rec, rec, eval_res)

    assert os.path.exists(output_path), f"Saved PDF file does not exist at {output_path}"
    assert os.path.getsize(output_path) > 5000, "Saved PDF file must be > 5 KB"
    print(f"test_save_pdf_to_disk: PASS (saved {os.path.getsize(output_path)} bytes to {output_path})")


if __name__ == "__main__":
    test_pdf_bytes_and_structure()
    test_special_characters_no_crash()
    test_save_pdf_to_disk()
    print("ALL PDF TESTS PASSED!")

