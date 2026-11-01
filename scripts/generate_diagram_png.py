"""Generate a publication-grade workflow diagram PNG using Pillow."""

import os
from PIL import Image, ImageDraw, ImageFont

OUTPUT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "workflow_diagram.png")
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

# Create 1400x950 image
width, height = 1400, 950
img = Image.new("RGBA", (width, height), "#F8FAFC")
draw = ImageDraw.Draw(img)

# Try loading system font, fallback to default
try:
    font_title = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
    font_stage = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
    font_body = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 15)
    font_sub = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 13)
except Exception:
    font_title = ImageFont.load_default()
    font_stage = font_title
    font_body = font_title
    font_sub = font_title

# Header
draw.text((width // 2, 45), "Research Methodology Recommendation Assistant: System Workflow", fill="#0F172A", font=font_title, anchor="mm")
draw.text((width // 2, 80), "End-to-End 4-Stage Architectural Pipeline with Autonomous Refinement & Trigger-Action Delivery", fill="#64748B", font=font_sub, anchor="mm")

# Define Stage Blocks
stages = [
    {
        "title": "STAGE 1: INPUT VALIDATION & PARSING",
        "color": "#EFF6FF",
        "border": "#3B82F6",
        "header_color": "#1D4ED8",
        "bbox": (80, 130, 1320, 240),
        "details": [
            "• Deterministic Guardrails: Length, keystroke spam, & prompt injection detection ('ignore instructions...')",
            "• Graceful Clarification Engine: Rejects invalid queries with actionable tips (Never crashes / hallucinates)",
            "• LLM Semantic Scope Parser: Classifies Question Type (Causal/Exploratory/etc.) & extracts Variables, Cohort, & Setting"
        ]
    },
    {
        "title": "STAGE 2: METHODOLOGY GENERATION",
        "color": "#F0FDF4",
        "border": "#22C55E",
        "header_color": "#15803D",
        "bbox": (80, 280, 1320, 420),
        "details": [
            "• Modular Strategy Selector: v1_basic (flat baseline), v2_structured (persona + schema), v3_decomposed (Default champion)",
            "• 8-Step Cognitive Decomposition: Deconstructs question -> Paradigm -> Design -> Power Analysis -> Instrumentation -> Analysis -> Ethics",
            "• Strict Pydantic JSON Contract: Enforces 15 mandatory academic fields with automated single retry on malformed outputs",
            "• Negative Guardrails: Explicit ban on invented citations (et al., fake years) and cross-paradigm method mismatch"
        ]
    },
    {
        "title": "STAGE 3: MULTI-DIMENSIONAL VALIDATION & SCORING",
        "color": "#FEFCE8",
        "border": "#EAB308",
        "header_color": "#A16207",
        "bbox": (80, 460, 1320, 610),
        "details": [
            "• A. LLM-as-Judge 5-Criteria Rubric (0-25 -> 100%): Alignment, Justification Quality, Completeness, Feasibility, Ethics/Validity",
            "• B. Reference-Based Ground Truth Alignment: Length-weighted pattern match against data/reference_cases.json (8+ gold standards)",
            "• C. Deterministic Rule Integrity Checks: Zero fake citations regex scanner, G*Power/saturation verification, paradigm consistency",
            "• Composite Scoring Matrix: Weighted synthesis -> PASS (>= 75.0%), REVIEW (50.0 - 74.9%), or FAIL (< 50.0%)"
        ]
    },
    {
        "title": "STAGE 4: AUTOMATED REFINEMENT & TRIGGER-ACTION DELIVERY",
        "color": "#FAF5FF",
        "border": "#A855F7",
        "header_color": "#7E22CE",
        "bbox": (80, 650, 1320, 800),
        "details": [
            "• Closed-Loop Refinement Trigger: If score < 75%, feeds evaluator critique back into Stage 2 for 1 targeted revision pass",
            "• Status Branching: DELIVERED (if PASS) or FLAGGED_FOR_HUMAN_REVIEW (with supervisor advisory note)",
            "• Report Generation Engine: Produces publication-grade reports in reports/<timestamp>_methodology_report.md",
            "• Verifiable Persistence: Logs all triggers, actions, and durations to SQLite (data/app.db) and synchronizes data/results_log.csv"
        ]
    }
]

def draw_rounded_rect(draw_obj, bbox, radius, fill, outline, width=2):
    x0, y0, x1, y1 = bbox
    draw_obj.rectangle([x0 + radius, y0, x1 - radius, y1], fill=fill)
    draw_obj.rectangle([x0, y0 + radius, x1, y1 - radius], fill=fill)
    draw_obj.pieslice([x0, y0, x0 + 2*radius, y0 + 2*radius], 180, 270, fill=fill)
    draw_obj.pieslice([x1 - 2*radius, y0, x1, y0 + 2*radius], 270, 360, fill=fill)
    draw_obj.pieslice([x0, y1 - 2*radius, x0 + 2*radius, y1], 90, 180, fill=fill)
    draw_obj.pieslice([x1 - 2*radius, y1 - 2*radius, x1, y1], 0, 90, fill=fill)
    # Borders
    draw_obj.line([x0 + radius, y0, x1 - radius, y0], fill=outline, width=width)
    draw_obj.line([x0 + radius, y1, x1 - radius, y1], fill=outline, width=width)
    draw_obj.line([x0, y0 + radius, x0, y1 - radius], fill=outline, width=width)
    draw_obj.line([x1, y0 + radius, x1, y1 - radius], fill=outline, width=width)
    draw_obj.arc([x0, y0, x0 + 2*radius, y0 + 2*radius], 180, 270, fill=outline, width=width)
    draw_obj.arc([x1 - 2*radius, y0, x1, y0 + 2*radius], 270, 360, fill=outline, width=width)
    draw_obj.arc([x0, y1 - 2*radius, x0 + 2*radius, y1], 90, 180, fill=outline, width=width)
    draw_obj.arc([x1 - 2*radius, y1 - 2*radius, x1, y1], 0, 90, fill=outline, width=width)

# Draw Stages and Details
for s in stages:
    draw_rounded_rect(draw, s["bbox"], 12, s["color"], s["border"], width=2)
    # Stage Title
    bx0, by0, bx1, by1 = s["bbox"]
    draw.text((bx0 + 20, by0 + 16), s["title"], fill=s["header_color"], font=font_stage)
    # Stage Details
    cur_y = by0 + 46
    for detail in s["details"]:
        draw.text((bx0 + 24, cur_y), detail, fill="#334155", font=font_body)
        cur_y += 24

# Connecting Arrows
arrows = [
    (width // 2, 240, width // 2, 280),
    (width // 2, 420, width // 2, 460),
    (width // 2, 610, width // 2, 650)
]

for ax0, ay0, ax1, ay1 in arrows:
    draw.line([ax0, ay0, ax1, ay1], fill="#64748B", width=3)
    draw.polygon([(ax1 - 6, ay1 - 10), (ax1 + 6, ay1 - 10), (ax1, ay1)], fill="#64748B")

# Footer: User Interface Tab Integration
draw_rounded_rect(draw, (80, 830, 1320, 910), 10, "#FFFFFF", "#CBD5E1", width=1)
draw.text((width // 2, 852), "Streamlit Interactive UI: Tab 1 (Recommend) | Tab 2 (Prompt Lab) | Tab 3 (Test Results) | Tab 4 (Automation Log) | Tab 5 (History) | Tab 6 (About)", fill="#0F172A", font=font_body, anchor="mm")
draw.text((width // 2, 882), "Storage & Governance: SQLite (data/app.db) • CSV Sync (data/results_log.csv) • Academic Disclaimers • Data Rights Deletion", fill="#64748B", font=font_sub, anchor="mm")

img.save(OUTPUT_PATH, "PNG")
print(f"Workflow diagram PNG generated successfully at: {OUTPUT_PATH}")

