"""PDF Report Generator for MethodWise using ReportLab Platypus.
Produces publication-grade, styled academic methodology reports (A4) matching the scholarly editorial palette.
"""

import os
import io
from datetime import datetime
from typing import Dict, Any, Optional, List

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    KeepTogether, PageBreak, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from src.schemas import MethodologyRecommendation, EvaluationResult, ParsedQuestion
from src.storage import sanitize_owner_id

REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")

# --- COLOR PALETTE (Scholarly Editorial Tokens) ---
PRIMARY = colors.HexColor("#3730A3")         # Deep Indigo
PRIMARY_LIGHT = colors.HexColor("#EEF2FF")   # Subtle Indigo
PRIMARY_BORDER = colors.HexColor("#C7D2FE")  # Tinted Indigo Border
ACCENT = colors.HexColor("#B45309")          # Scholarly Ochre
ACCENT_LIGHT = colors.HexColor("#FEF3C7")
SUCCESS = colors.HexColor("#0F766E")         # Scholarly Teal
SUCCESS_LIGHT = colors.HexColor("#F0FDFA")
SUCCESS_BORDER = colors.HexColor("#99F6E4")
DANGER = colors.HexColor("#B91C1C")          # Editorial Red
DANGER_LIGHT = colors.HexColor("#FEF2F2")
DANGER_BORDER = colors.HexColor("#FECACA")
BORDER = colors.HexColor("#E7E2D9")          # Hairline Card Border
BORDER_SUBTLE = colors.HexColor("#F1EFEA")
INK = colors.HexColor("#0F172A")             # Deep Charcoal
INK_MUTED = colors.HexColor("#475569")       # Muted Slate
BG_PAPER = colors.HexColor("#FAF7F2")        # Paper Canvas
WHITE = colors.HexColor("#FFFFFF")

# Register Unicode Font if available on host, else fallback to standard Helvetica/Times
FONT_BODY = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
FONT_ITALIC = "Helvetica-Oblique"
FONT_HEADING = "Helvetica-Bold"

UNICODE_FONT_CANDIDATES = [
    ("/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf", "Arial"),
    ("/System/Library/Fonts/Supplemental/Times New Roman.ttf", "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf", "TimesNewRoman"),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "DejaVuSans")
]

for norm_path, bold_path, family_name in UNICODE_FONT_CANDIDATES:
    if os.path.exists(norm_path):
        try:
            pdfmetrics.registerFont(TTFont(f"{family_name}", norm_path))
            if bold_path and os.path.exists(bold_path):
                pdfmetrics.registerFont(TTFont(f"{family_name}-Bold", bold_path))
                FONT_BOLD = f"{family_name}-Bold"
            else:
                FONT_BOLD = family_name
            FONT_BODY = family_name
            FONT_HEADING = FONT_BOLD
            break
        except Exception:
            pass


def escape_xml(text: Any) -> str:
    """Escape text for safe inclusion in ReportLab Paragraph XML."""
    if text is None:
        return "Not provided"
    if not isinstance(text, str):
        text = str(text)
    # XML escaping
    escaped = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # Normalize Greek & math characters for standard font compatibility if needed
    escaped = escaped.replace("α", "&alpha;").replace("β", "&beta;").replace("→", "-&gt;")
    return escaped.replace("\n", "<br/>")


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas that computes total page count and prints scholarly headers & footers."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(INK_MUTED)

        # Running Header on page 2 and beyond
        if self._pageNumber > 1:
            self.drawString(36, 810, "MethodWise • Academic Research Methodology Recommendation Report")
            self.setStrokeColor(BORDER)
            self.setLineWidth(0.5)
            self.line(36, 804, 559, 804)

        # Running Footer on EVERY page
        self.setStrokeColor(BORDER)
        self.setLineWidth(0.5)
        self.line(36, 38, 559, 38)

        disclaimer = "Decision support only, not a replacement for supervisor or ethics-board approval."
        self.drawString(36, 26, disclaimer)
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(559, 26, page_str)
        self.restoreState()


def get_report_styles() -> Dict[str, ParagraphStyle]:
    """Define comprehensive, high-contrast academic typography styles."""
    styles = getSampleStyleSheet()

    custom_styles = {
        "ReportTitle": ParagraphStyle(
            "ReportTitle",
            fontName=FONT_HEADING,
            fontSize=20,
            leading=24,
            textColor=PRIMARY,
            spaceAfter=4
        ),
        "ReportSubtitle": ParagraphStyle(
            "ReportSubtitle",
            fontName=FONT_BODY,
            fontSize=10,
            leading=14,
            textColor=INK_MUTED,
            spaceAfter=12
        ),
        "SectionHeading": ParagraphStyle(
            "SectionHeading",
            fontName=FONT_HEADING,
            fontSize=12,
            leading=16,
            textColor=PRIMARY,
            spaceBefore=14,
            spaceAfter=6,
            keepWithNext=True
        ),
        "SubSectionHeading": ParagraphStyle(
            "SubSectionHeading",
            fontName=FONT_HEADING,
            fontSize=10,
            leading=14,
            textColor=INK,
            spaceBefore=8,
            spaceAfter=4,
            keepWithNext=True
        ),
        "Body": ParagraphStyle(
            "Body",
            fontName=FONT_BODY,
            fontSize=9,
            leading=13.5,
            textColor=INK,
            spaceAfter=6
        ),
        "BodyMuted": ParagraphStyle(
            "BodyMuted",
            fontName=FONT_BODY,
            fontSize=8.5,
            leading=12,
            textColor=INK_MUTED,
            spaceAfter=4
        ),
        "BulletItem": ParagraphStyle(
            "BulletItem",
            fontName=FONT_BODY,
            fontSize=8.5,
            leading=12.5,
            textColor=INK,
            leftIndent=14,
            spaceAfter=3
        ),
        "QuestionQuote": ParagraphStyle(
            "QuestionQuote",
            fontName=FONT_HEADING if FONT_BOLD != "Helvetica-Bold" else FONT_BODY,
            fontSize=10,
            leading=14,
            textColor=INK,
            spaceAfter=4
        ),
        "WarningBanner": ParagraphStyle(
            "WarningBanner",
            fontName=FONT_HEADING,
            fontSize=9.5,
            leading=13.5,
            textColor=DANGER,
            alignment=TA_CENTER
        ),
        "TableHeader": ParagraphStyle(
            "TableHeader",
            fontName=FONT_HEADING,
            fontSize=8.5,
            leading=11.5,
            textColor=WHITE,
            alignment=TA_LEFT
        ),
        "TableCell": ParagraphStyle(
            "TableCell",
            fontName=FONT_BODY,
            fontSize=8,
            leading=11,
            textColor=INK
        ),
        "TableCellBold": ParagraphStyle(
            "TableCellBold",
            fontName=FONT_HEADING,
            fontSize=8,
            leading=11,
            textColor=INK
        ),
        "BadgeText": ParagraphStyle(
            "BadgeText",
            fontName=FONT_HEADING,
            fontSize=8,
            leading=10,
            textColor=PRIMARY,
            alignment=TA_CENTER
        )
    }
    return custom_styles


def build_pdf(
    run_record: Dict[str, Any],
    recommendation: Optional[MethodologyRecommendation],
    evaluation: Optional[EvaluationResult]
) -> bytes:
    """Build PDF document in-memory and return raw bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=46,
        bottomMargin=48
    )

    styles = get_report_styles()
    story = []

    # Safe data extraction
    run_id = run_record.get("run_id") or run_record.get("id") or "RUN-N/A"
    timestamp = run_record.get("timestamp") or datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    research_question = run_record.get("research_question") or "Not provided"
    discipline = run_record.get("discipline") or "General Scholarship"
    prompt_version = run_record.get("prompt_version") or "v3_decomposed"
    constraints = run_record.get("constraints") or {}
    if isinstance(constraints, str):
        try:
            import json
            constraints = json.loads(constraints)
        except Exception:
            constraints = {}

    eval_label = evaluation.label if evaluation else "UNCHECKED"
    composite_score = evaluation.composite_score if evaluation else 0.0

    # 1. Header Section
    story.append(Paragraph("MethodWise", ParagraphStyle("Brand", fontName=FONT_HEADING, fontSize=11, leading=13, textColor=ACCENT)))
    story.append(Paragraph("Methodology Recommendation Report", styles["ReportTitle"]))
    meta_str = f"Document ID: <b>{escape_xml(run_id[:12])}</b> | Date: <b>{escape_xml(timestamp[:19])}</b> | Engine: <b>{escape_xml(prompt_version)}</b>"
    story.append(Paragraph(meta_str, styles["ReportSubtitle"]))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceBefore=0, spaceAfter=10))

    # Review/Fail Warning Banner if applicable
    if eval_label in ("REVIEW", "FAIL") or run_record.get("status") == "FLAGGED_FOR_HUMAN_REVIEW":
        warn_text = (
            "<b>ATTENTION: FACULTY / SUPERVISOR REVIEW REQUIRED</b><br/>"
            "This methodology scored below the 75% validation threshold. Review parameter trade-offs and faculty guidance prior to execution."
        )
        warn_table = Table(
            [[Paragraph(warn_text, styles["WarningBanner"])]],
            colWidths=[523]
        )
        warn_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), DANGER_LIGHT),
            ('BOX', (0, 0), (-1, -1), 1, DANGER_BORDER),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ]))
        story.append(warn_table)
        story.append(Spacer(1, 10))

    # 2. Research Inquiry Callout Box
    constraints_text = ", ".join([f"{k.replace('_', ' ').title()}: {v}" for k, v in constraints.items()]) if constraints else "Standard academic constraints"
    inquiry_content = [
        Paragraph(f"<b>Primary Research Question:</b> &ldquo;{escape_xml(research_question)}&rdquo;", styles["QuestionQuote"]),
        Spacer(1, 3),
        Paragraph(f"<b>Discipline / Field:</b> {escape_xml(discipline)}", styles["Body"]),
        Paragraph(f"<b>Operational Constraints:</b> {escape_xml(constraints_text)}", styles["BodyMuted"])
    ]
    inquiry_table = Table([[inquiry_content]], colWidths=[523])
    inquiry_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_PAPER),
        ('BOX', (0, 0), (-1, -1), 1, BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(inquiry_table)
    story.append(Spacer(1, 10))

    if not recommendation:
        # Edge case / rejected input report
        story.append(Paragraph("<b>Input Screening Status:</b> REJECTED_INPUT", styles["SectionHeading"]))
        story.append(Paragraph("This inquiry was screened out at Stage 1 input guardrails (insufficient academic clarity, gibberish, or adversarial injection). No methodology was formulated to avoid hallucinations.", styles["Body"]))
        doc.build(story, canvasmaker=NumberedCanvas)
        return buffer.getvalue()

    # 3. Executive Summary Block (KPI Table)
    score_color = SUCCESS if eval_label == "PASS" else (ACCENT if eval_label == "REVIEW" else DANGER)
    kpi_data = [
        [
            Paragraph("<b>Recommended Paradigm</b>", styles["BodyMuted"]),
            Paragraph("<b>Specific Research Design</b>", styles["BodyMuted"]),
            Paragraph("<b>Confidence Level</b>", styles["BodyMuted"]),
            Paragraph("<b>Validation Score</b>", styles["BodyMuted"])
        ],
        [
            Paragraph(f"<font color='{PRIMARY.hexval()}'><b>{escape_xml(recommendation.recommended_paradigm)}</b></font>", styles["Body"]),
            Paragraph(f"<b>{escape_xml(recommendation.research_design)}</b>", styles["Body"]),
            Paragraph(f"<b>{escape_xml(recommendation.confidence_level)}</b>", styles["Body"]),
            Paragraph(f"<font color='{score_color.hexval()}'><b>{composite_score:.1f}% ({eval_label})</b></font>", styles["Body"])
        ]
    ]
    kpi_table = Table(kpi_data, colWidths=[120, 190, 105, 108])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), WHITE),
        ('BOX', (0, 0), (-1, -1), 1, BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_SUBTLE),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 12))

    # 4. Detailed Clauses
    # Clause 1: Question Analysis & Epistemological Scope
    story.append(Paragraph("1. Epistemological Scope & Problem Formulation", styles["SectionHeading"]))
    story.append(Paragraph(escape_xml(recommendation.parsed_question_summary), styles["Body"]))

    # Clause 2: Paradigm & Design Justification
    story.append(Paragraph("2. Paradigm & Design Justification", styles["SectionHeading"]))
    story.append(Paragraph(f"<b>Epistemological Stance:</b> {escape_xml(recommendation.paradigm_justification)}", styles["Body"]))
    story.append(Paragraph(f"<b>Design Rationale:</b> {escape_xml(recommendation.design_rationale)}", styles["Body"]))

    # Clause 3: Target Population & Sampling Framework
    story.append(Paragraph("3. Target Population & Sampling Framework", styles["SectionHeading"]))
    story.append(Paragraph(f"<b>Sampling Strategy:</b> {escape_xml(recommendation.sampling_strategy)}", styles["Body"]))
    story.append(Paragraph(f"<b>Sample Size & Power / Saturation Rationale:</b> {escape_xml(recommendation.sample_size_rationale)}", styles["Body"]))

    # Clause 4: Data Collection Instruments & Protocol
    story.append(Paragraph("4. Data Collection Instruments & Protocol", styles["SectionHeading"]))
    story.append(Paragraph("<b>Instruments & Measurement Tools:</b>", styles["SubSectionHeading"]))
    for inst in recommendation.data_collection_instruments:
        story.append(Paragraph(f"&bull; {escape_xml(inst)}", styles["BulletItem"]))
    story.append(Spacer(1, 3))
    story.append(Paragraph(f"<b>Collection Procedures:</b> {escape_xml(recommendation.data_collection_procedures)}", styles["Body"]))

    # Clause 5: Analytical Framework & Statistical Modeling
    story.append(Paragraph("5. Prescribed Analytical Framework & Modeling", styles["SectionHeading"]))
    story.append(Paragraph("<b>Analytical Techniques:</b>", styles["SubSectionHeading"]))
    for tech in recommendation.data_analysis_techniques:
        story.append(Paragraph(f"&bull; <code>{escape_xml(tech)}</code>", styles["BulletItem"]))
    story.append(Spacer(1, 3))
    story.append(Paragraph(f"<b>Analytical Rationale:</b> {escape_xml(recommendation.analysis_rationale)}", styles["Body"]))

    # Clause 6: Validity, Reliability & Trustworthiness
    story.append(Paragraph("6. Validity, Reliability & Qualitative Trustworthiness", styles["SectionHeading"]))
    story.append(Paragraph(escape_xml(recommendation.validity_and_reliability_considerations), styles["Body"]))

    # Clause 7: Ethical Governance & Participant Protections
    story.append(Paragraph("7. Ethical Governance & Participant Safeguards", styles["SectionHeading"]))
    
    # Conditional Ethics Alert
    if recommendation.vulnerable_population_flag or recommendation.irb_ethics_board_required:
        eth_box_title = "⚠️ VULNERABLE POPULATION SAFEGUARDS ACTIVATED" if recommendation.vulnerable_population_flag else "🏛️ INSTITUTIONAL REVIEW BOARD (IRB / REC) CLEARANCE MANDATORY"
        eth_box_desc = (
            f"<b>{eth_box_title}</b><br/>"
            "This study involves sensitive, protected, or traumatized cohorts. Institutional Review Board (IRB) / Research Ethics Committee (REC) approval is required before participant engagement."
        )
        eth_box = Table([[Paragraph(eth_box_desc, styles["Body"])]], colWidths=[523])
        eth_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), DANGER_LIGHT),
            ('BOX', (0, 0), (-1, -1), 1, DANGER_BORDER),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(eth_box)
        story.append(Spacer(1, 6))

    for eth in recommendation.ethical_considerations:
        story.append(Paragraph(f"&bull; {escape_xml(eth)}", styles["BulletItem"]))

    # Clause 8: Methodological Limitations & Risks
    story.append(Paragraph("8. Methodological Limitations & Risk Mitigation", styles["SectionHeading"]))
    for lim in recommendation.limitations_and_risks:
        story.append(Paragraph(f"&bull; {escape_xml(lim)}", styles["BulletItem"]))

    # Clause 9: Alternative Methodologies Comparison Table
    story.append(Paragraph("9. Comparative Evaluation of Alternative Designs", styles["SectionHeading"]))
    alt_table_data = [
        [
            Paragraph("<b>Alternative Design</b>", styles["TableHeader"]),
            Paragraph("<b>Paradigm</b>", styles["TableHeader"]),
            Paragraph("<b>Rationale for Exclusion</b>", styles["TableHeader"])
        ]
    ]
    for alt in recommendation.alternative_methodologies:
        alt_table_data.append([
            Paragraph(f"<b>{escape_xml(alt.design)}</b>", styles["TableCellBold"]),
            Paragraph(escape_xml(alt.paradigm), styles["TableCell"]),
            Paragraph(escape_xml(alt.rationale_for_rejection), styles["TableCell"])
        ])

    alt_table = Table(alt_table_data, colWidths=[140, 95, 288])
    alt_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_SUBTLE),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(alt_table)
    story.append(Spacer(1, 8))

    # Clause 10: Step-by-Step Execution Roadmap
    story.append(Paragraph("10. Phased Execution Roadmap", styles["SectionHeading"]))
    road_table_data = [
        [
            Paragraph("<b>Phase</b>", styles["TableHeader"]),
            Paragraph("<b>Milestone Title</b>", styles["TableHeader"]),
            Paragraph("<b>Actionable Tasks</b>", styles["TableHeader"]),
            Paragraph("<b>Timeline</b>", styles["TableHeader"])
        ]
    ]
    for step in recommendation.step_by_step_roadmap:
        road_table_data.append([
            Paragraph(f"<b>Phase {step.step_number}</b>", styles["TableCellBold"]),
            Paragraph(f"<b>{escape_xml(step.title)}</b>", styles["TableCellBold"]),
            Paragraph(escape_xml(step.description), styles["TableCell"]),
            Paragraph(escape_xml(step.estimated_duration), styles["TableCell"])
        ])

    road_table = Table(road_table_data, colWidths=[55, 125, 255, 88])
    road_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_SUBTLE),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(road_table)
    story.append(Spacer(1, 10))

    # 5. Independent Quality Validation Scorecard
    if evaluation:
        story.append(Paragraph("11. Triple-Validation Scorecard", styles["SectionHeading"]))
        rub = evaluation.rubric
        rub_data = [
            [
                Paragraph("<b>Quality Dimension</b>", styles["TableHeader"]),
                Paragraph("<b>Score</b>", styles["TableHeader"]),
                Paragraph("<b>Evaluator Critique & Justification</b>", styles["TableHeader"])
            ],
            [Paragraph("Alignment", styles["TableCellBold"]), Paragraph(f"{rub.alignment.score}/5", styles["TableCell"]), Paragraph(escape_xml(rub.alignment.critique), styles["TableCell"])],
            [Paragraph("Justification Quality", styles["TableCellBold"]), Paragraph(f"{rub.justification_quality.score}/5", styles["TableCell"]), Paragraph(escape_xml(rub.justification_quality.critique), styles["TableCell"])],
            [Paragraph("Completeness", styles["TableCellBold"]), Paragraph(f"{rub.completeness.score}/5", styles["TableCell"]), Paragraph(escape_xml(rub.completeness.critique), styles["TableCell"])],
            [Paragraph("Feasibility", styles["TableCellBold"]), Paragraph(f"{rub.feasibility.score}/5", styles["TableCell"]), Paragraph(escape_xml(rub.feasibility.critique), styles["TableCell"])],
            [Paragraph("Ethical / Validity", styles["TableCellBold"]), Paragraph(f"{rub.ethical_validity_awareness.score}/5", styles["TableCell"]), Paragraph(escape_xml(rub.ethical_validity_awareness.critique), styles["TableCell"])],
        ]
        rub_table = Table(rub_data, colWidths=[120, 48, 355])
        rub_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
            ('BOX', (0, 0), (-1, -1), 0.5, BORDER),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_SUBTLE),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(rub_table)
        story.append(Spacer(1, 6))

        ref = evaluation.reference_match
        ref_id_str = ref.matched_reference_id or "REF-BENCHMARK"
        story.append(Paragraph(f"<b>Reference Case Alignment:</b> {escape_xml(ref.status)} ({escape_xml(ref_id_str)}) &mdash; {escape_xml(ref.notes)}", styles["Body"]))
        rules_str = "Zero rule violations (no fabricated citations, power rationale verified)" if not evaluation.rules.flags else "; ".join(evaluation.rules.flags)
        story.append(Paragraph(f"<b>Deterministic Integrity:</b> {escape_xml(rules_str)}", styles["Body"]))

    # Build the document
    doc.build(story, canvasmaker=NumberedCanvas)
    return buffer.getvalue()


def save_pdf(
    run_record: Dict[str, Any],
    recommendation: Optional[MethodologyRecommendation],
    evaluation: Optional[EvaluationResult],
    output_path: Optional[str] = None,
    owner_id: Optional[str] = None
) -> str:
    """Build and save PDF to file path under reports/<owner_id>/."""
    if not output_path:
        owner = sanitize_owner_id(owner_id or run_record.get("owner_id") or "legacy")
        owner_dir = os.path.join(REPORTS_DIR, owner)
        os.makedirs(owner_dir, exist_ok=True)
        run_id = run_record.get("run_id") or run_record.get("id") or "RUN"
        timestamp_slug = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp_slug}_{run_id[:8]}_methodology_report.pdf"
        output_path = os.path.join(owner_dir, filename)
    else:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    pdf_bytes = build_pdf(run_record, recommendation, evaluation)
    with open(output_path, "wb") as f:
        f.write(pdf_bytes)

    return output_path

