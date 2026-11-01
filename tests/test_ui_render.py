"""Unit tests for clean UI HTML rendering (tests/test_ui_render.py).
Asserts that every component's output has:
1. No lines starting with 4 or more spaces.
2. No blank lines.
This guarantees st.markdown / st.html never treats HTML as Markdown indented code blocks.
"""

import os
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ui.components import (
    clean_html,
    render_badge,
    render_evidence_ribbon,
    render_confidence_meter,
    build_roadmap_timeline_html,
    build_page_header_html,
    build_section_header_html,
    build_stat_card_html,
    build_step_card_html,
    build_feature_card_html,
    build_ethics_callout_html,
    build_empty_state_html,
    build_footer_html
)


def assert_clean_html_structure(html_output: str, component_name: str):
    """Assert that html_output has no lines starting with 4+ spaces and no blank lines."""
    assert html_output, f"[{component_name}] Output must not be empty"
    lines = html_output.splitlines()
    for idx, line in enumerate(lines):
        assert not line.startswith("    "), (
            f"[{component_name}] Line {idx} starts with 4+ spaces: {repr(line)}"
        )
        assert not line.startswith("\t"), (
            f"[{component_name}] Line {idx} starts with tab: {repr(line)}"
        )
        assert line.strip() != "", (
            f"[{component_name}] Line {idx} is a blank line"
        )


def test_clean_html_utility():
    sample_raw = """
        <div class="test-parent">
            <div class="test-child">
                <p>Paragraph with text</p>
            </div>

            <span>After blank line</span>
        </div>
    """
    cleaned = clean_html(sample_raw)
    assert_clean_html_structure(cleaned, "clean_html")
    assert "<pre>" not in cleaned
    assert "Paragraph with text" in cleaned
    print("test_clean_html_utility: PASS")


def test_roadmap_timeline_no_code_blocks():
    """Assert roadmap with multiple steps produces no code blocks or 4+ space indentations."""
    class DummyStep:
        def __init__(self, num, title, desc, dur):
            self.step_number = num
            self.title = title
            self.description = desc
            self.estimated_duration = dur

    steps = [
        DummyStep(1, "Phase 1: Institutional Approvals", "Secure IRB clearance and consent forms.", "Weeks 1-4"),
        DummyStep(2, "Phase 2: Pilot Testing", "Administer preliminary instrumentation to cohort.", "Weeks 5-8"),
        DummyStep(3, "Phase 3: Primary Data Collection", "Execute cross-sectional survey sampling.", "Weeks 9-14"),
        DummyStep(4, "Phase 4: Statistical Modeling", "Run ANCOVA and regression models.", "Weeks 15-18")
    ]

    html_out = build_roadmap_timeline_html(steps)
    assert_clean_html_structure(html_out, "build_roadmap_timeline_html")
    # Must contain all 4 step titles
    for s in steps:
        assert s.title in html_out
    print("test_roadmap_timeline_no_code_blocks: PASS")


def test_evidence_ribbon_colors_and_no_code_blocks():
    """Assert evidence ribbon variants: neutral grey for no case, amber for partial, teal for match, red for mismatch."""
    # 1. No matching case -> neutral grey badge
    ribbon_none = render_evidence_ribbon(
        rubric_score=94.0,
        rubric_label="PASS",
        ref_case_id="REF-NONE",
        ref_status="UNCHECKED",
        rule_violations_count=0
    )
    assert_clean_html_structure(ribbon_none, "evidence_ribbon_none")
    assert "Reference: no matching case (n/a)" in ribbon_none
    assert "rm-badge-neutral" in ribbon_none or "rm-badge-grey" in ribbon_none

    # 2. Match -> teal badge
    ribbon_match = render_evidence_ribbon(
        rubric_score=95.0,
        rubric_label="PASS",
        ref_case_id="REF-01",
        ref_status="MATCH",
        rule_violations_count=0
    )
    assert_clean_html_structure(ribbon_match, "evidence_ribbon_match")
    assert "Reference: REF-01 (MATCH)" in ribbon_match
    assert "rm-badge-teal" in ribbon_match

    # 3. Partial -> amber badge
    ribbon_partial = render_evidence_ribbon(
        rubric_score=85.0,
        rubric_label="REVIEW",
        ref_case_id="REF-03",
        ref_status="PARTIAL",
        rule_violations_count=0
    )
    assert_clean_html_structure(ribbon_partial, "evidence_ribbon_partial")
    assert "Reference: REF-03 (PARTIAL)" in ribbon_partial
    assert "rm-badge-amber" in ribbon_partial

    # 4. Mismatch -> red badge (fail)
    ribbon_mismatch = render_evidence_ribbon(
        rubric_score=40.0,
        rubric_label="FAIL",
        ref_case_id="REF-02",
        ref_status="MISMATCH",
        rule_violations_count=2
    )
    assert_clean_html_structure(ribbon_mismatch, "evidence_ribbon_mismatch")
    assert "Reference: REF-02 (MISMATCH)" in ribbon_mismatch
    assert "rm-badge-fail" in ribbon_mismatch

    print("test_evidence_ribbon_colors_and_no_code_blocks: PASS")


def test_badges_and_confidence_meter():
    b_pass = render_badge("94.5%", "pass", icon_name="check-circle")
    assert_clean_html_structure(b_pass, "render_badge_pass")

    b_neutral = render_badge("Reference: no matching case (n/a)", "neutral", icon_name="book")
    assert_clean_html_structure(b_neutral, "render_badge_neutral")

    meter_high = render_confidence_meter("High")
    assert_clean_html_structure(meter_high, "render_confidence_meter")
    print("test_badges_and_confidence_meter: PASS")


def test_all_custom_components_structure():
    assert_clean_html_structure(
        build_page_header_html("Title", "Description", "Breadcrumb"),
        "build_page_header_html"
    )
    assert_clean_html_structure(
        build_section_header_html("Section Title", "Section Subtitle", "refresh"),
        "build_section_header_html"
    )
    assert_clean_html_structure(
        build_stat_card_html("Metric", "98%", "Subtext", "chart"),
        "build_stat_card_html"
    )
    assert_clean_html_structure(
        build_step_card_html(1, "Step Title", "Step Description"),
        "build_step_card_html"
    )
    assert_clean_html_structure(
        build_feature_card_html("scale", "Feature Title", "Feature Description"),
        "build_feature_card_html"
    )
    assert_clean_html_structure(
        build_ethics_callout_html("Ethical warning message", is_vulnerable=True, is_irb_required=True),
        "build_ethics_callout_html"
    )
    assert_clean_html_structure(
        build_empty_state_html("flask", "Empty Title", "Empty Message"),
        "build_empty_state_html"
    )
    assert_clean_html_structure(
        build_footer_html(),
        "build_footer_html"
    )
    print("test_all_custom_components_structure: PASS")


if __name__ == "__main__":
    test_clean_html_utility()
    test_roadmap_timeline_no_code_blocks()
    test_evidence_ribbon_colors_and_no_code_blocks()
    test_badges_and_confidence_meter()
    test_all_custom_components_structure()
    print("\nALL UI RENDER TESTS PASSED!")

