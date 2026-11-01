"""Scholarly Editorial Chart Components for MethodWise.
Crafted with high-contrast palette, academic typography (Crimson Pro & Atkinson Hyperlegible),
tabular JetBrains Mono numerals, and full dynamic Light/Dark theme responsiveness.
"""

from typing import Dict, Any, List
import streamlit as st
import plotly.graph_objects as go
from ui.theme import get_theme_tokens


def get_current_tokens() -> Dict[str, str]:
    """Retrieve color tokens corresponding to the active session theme."""
    try:
        active_theme = st.session_state.get("theme", "light")
    except Exception:
        active_theme = "light"
    return get_theme_tokens(active_theme)


def create_score_gauge(score: float = None, label: str = None) -> go.Figure:
    """Semi-circular editorial gauge chart for composite validation score."""
    tokens = get_current_tokens()
    is_dark = st.session_state.get("theme", "light") == "dark"

    score_val = float(score) if score is not None else 0.0
    label_val = str(label or "EVALUATED")

    if score_val >= 75.0:
        bar_color = tokens["success"]
    elif score_val >= 50.0:
        bar_color = tokens["warning"]
    else:
        bar_color = tokens["danger"]

    step_colors = [
        {"range": [0, 50], "color": "rgba(248, 113, 113, 0.22)" if is_dark else "#FEE2E2"},
        {"range": [50, 75], "color": "rgba(251, 191, 36, 0.22)" if is_dark else "#FEF3C7"},
        {"range": [75, 100], "color": "rgba(45, 212, 191, 0.22)" if is_dark else "#CCFBF1"}
    ]

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score_val,
        number={
            "suffix": "%",
            "font": {"family": "JetBrains Mono, monospace", "size": 36, "color": tokens["text"]}
        },
        title={
            "text": f"<b>{label_val}</b>",
            "font": {"family": "Crimson Pro, Georgia, serif", "size": 16, "color": tokens["text"]}
        },
        gauge={
            "axis": {
                "range": [0, 100],
                "tickwidth": 1,
                "tickcolor": tokens["border"],
                "tickfont": {"family": "JetBrains Mono, monospace", "size": 11, "color": tokens["muted"]}
            },
            "bar": {"color": bar_color, "thickness": 0.28},
            "bgcolor": tokens["surface_2"],
            "borderwidth": 1,
            "bordercolor": tokens["border"],
            "steps": step_colors,
            "threshold": {
                "line": {"color": tokens["primary"], "width": 3},
                "thickness": 0.75,
                "value": 75.0
            }
        }
    ))

    fig.update_layout(
        height=210,
        margin=dict(l=15, r=15, t=30, b=15),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Atkinson Hyperlegible, sans-serif", "color": tokens["text"]}
    )
    return fig


def create_rubric_horizontal_bar(rubric_criteria: Dict[str, Any]) -> go.Figure:
    """Horizontal bar chart for 5 rubric criteria on a 0-5 scale with direct labels."""
    tokens = get_current_tokens()
    categories = [
        "Ethical Awareness",
        "Method Feasibility",
        "Schema Completeness",
        "Justification Quality",
        "Question Alignment"
    ]

    scores = [
        rubric_criteria.get("ethical_validity_awareness", {}).get("score", 0),
        rubric_criteria.get("feasibility", {}).get("score", 0),
        rubric_criteria.get("completeness", {}).get("score", 0),
        rubric_criteria.get("justification_quality", {}).get("score", 0),
        rubric_criteria.get("alignment", {}).get("score", 0)
    ]

    colors = []
    for s in scores:
        if s >= 4:
            colors.append(tokens["primary"])
        elif s >= 3:
            colors.append(tokens["accent"])
        else:
            colors.append(tokens["danger"])

    fig = go.Figure(go.Bar(
        x=scores,
        y=categories,
        orientation='h',
        marker=dict(
            color=colors,
            line=dict(color=tokens["border"], width=1)
        ),
        text=[f"{s}/5" for s in scores],
        textposition="outside",
        textfont=dict(family="JetBrains Mono, monospace", size=12, color=tokens["text"])
    ))

    fig.update_layout(
        xaxis=dict(
            range=[0, 5.5],
            dtick=1,
            showgrid=True,
            gridcolor=tokens["border"],
            title=dict(
                text="Score (out of 5)",
                font=dict(family="Atkinson Hyperlegible, sans-serif", size=12, color=tokens["muted"])
            ),
            tickfont=dict(family="JetBrains Mono, monospace", size=11, color=tokens["muted"])
        ),
        yaxis=dict(
            showgrid=False,
            tickfont=dict(family="Atkinson Hyperlegible, sans-serif", size=12, color=tokens["text"])
        ),
        height=240,
        margin=dict(l=10, r=35, t=10, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Atkinson Hyperlegible, sans-serif", "color": tokens["text"]}
    )
    return fig


def create_prompt_comparison_bar(version_scores: Dict[str, float]) -> go.Figure:
    """Bar chart comparing validation scores across prompt versions with high-contrast pairing."""
    tokens = get_current_tokens()
    is_dark = st.session_state.get("theme", "light") == "dark"

    version_scores = version_scores or {}
    versions = list(version_scores.keys())
    scores = [float(version_scores.get(v) or 0.0) for v in versions]

    colors = []
    for v in versions:
        if "v3" in v:
            colors.append(tokens["primary"])
        elif "v2" in v:
            colors.append("#818CF8" if not is_dark else "#A5B4FC")
        else:
            colors.append(tokens["muted"])

    fig = go.Figure(go.Bar(
        x=versions,
        y=scores,
        marker=dict(color=colors, line=dict(color=tokens["border"], width=1)),
        text=[f"{s:.1f}%" for s in scores],
        textposition="outside",
        textfont=dict(family="JetBrains Mono, monospace", size=12, color=tokens["text"])
    ))

    # Add 75% threshold line
    fig.add_hline(
        y=75,
        line_dash="dash",
        line_color=tokens["success"],
        annotation_text="Pass Threshold (75%)",
        annotation_position="bottom right",
        annotation_font=dict(family="Atkinson Hyperlegible, sans-serif", size=11, color=tokens["success"])
    )

    fig.update_layout(
        yaxis=dict(
            range=[0, 115],
            dtick=20,
            showgrid=True,
            gridcolor=tokens["border"],
            title=dict(
                text="Validation Score (%)",
                font=dict(family="Atkinson Hyperlegible, sans-serif", size=12, color=tokens["muted"])
            ),
            tickfont=dict(family="JetBrains Mono, monospace", size=11, color=tokens["muted"])
        ),
        xaxis=dict(
            showgrid=False,
            tickfont=dict(family="Atkinson Hyperlegible, sans-serif", size=12, color=tokens["text"])
        ),
        height=270,
        margin=dict(l=10, r=10, t=25, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Atkinson Hyperlegible, sans-serif", "color": tokens["text"]}
    )
    return fig


def create_latency_bar(latencies: Dict[str, float]) -> go.Figure:
    """Bar chart comparing latency in seconds across prompt versions."""
    tokens = get_current_tokens()
    latencies = latencies or {}
    versions = list(latencies.keys())
    values = [float(latencies.get(v) or 0.0) for v in versions]

    fig = go.Figure(go.Bar(
        x=versions,
        y=values,
        marker=dict(color=tokens["accent"], line=dict(color=tokens["border"], width=1)),
        text=[f"{v:.1f}s" for v in values],
        textposition="outside",
        textfont=dict(family="JetBrains Mono, monospace", size=12, color=tokens["text"])
    ))

    fig.update_layout(
        yaxis=dict(
            showgrid=True,
            gridcolor=tokens["border"],
            title=dict(
                text="Latency (seconds)",
                font=dict(family="Atkinson Hyperlegible, sans-serif", size=12, color=tokens["muted"])
            ),
            tickfont=dict(family="JetBrains Mono, monospace", size=11, color=tokens["muted"])
        ),
        xaxis=dict(
            showgrid=False,
            tickfont=dict(family="Atkinson Hyperlegible, sans-serif", size=12, color=tokens["text"])
        ),
        height=250,
        margin=dict(l=10, r=10, t=20, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Atkinson Hyperlegible, sans-serif", "color": tokens["text"]}
    )
    return fig


def create_test_score_chart(test_results: List[Dict[str, Any]]) -> go.Figure:
    """Plotly grouped bar chart showing test case scores across prompt versions."""
    tokens = get_current_tokens()
    is_dark = st.session_state.get("theme", "light") == "dark"

    test_ids = sorted(list(set(r["test_id"] for r in test_results if r["test_id"] != "TC-05")))
    versions = ["v1_basic", "v2_structured", "v3_decomposed"]

    data_by_ver = {v: [] for v in versions}
    for tid in test_ids:
        for v in versions:
            match = next((r for r in test_results if r["test_id"] == tid and r["prompt_version"] == v), None)
            score = match["score"] if match else 0.0
            data_by_ver[v].append(score)

    palette = {
        "v1_basic": tokens["muted"],
        "v2_structured": "#818CF8" if not is_dark else "#A5B4FC",
        "v3_decomposed": tokens["primary"]
    }

    fig = go.Figure()
    for v in versions:
        fig.add_trace(go.Bar(
            name=v,
            x=test_ids,
            y=data_by_ver[v],
            marker_color=palette[v],
            marker_line=dict(color=tokens["border"], width=1),
            text=[f"{s:.0f}%" for s in data_by_ver[v]],
            textposition="auto",
            textfont=dict(family="JetBrains Mono, monospace", size=11, color=tokens["text"])
        ))

    fig.add_hline(
        y=75,
        line_dash="dash",
        line_color=tokens["success"],
        annotation_text="Pass (75%)",
        annotation_position="top left",
        annotation_font=dict(family="Atkinson Hyperlegible, sans-serif", size=11, color=tokens["success"])
    )

    fig.update_layout(
        barmode='group',
        yaxis=dict(
            range=[0, 115],
            dtick=20,
            showgrid=True,
            gridcolor=tokens["border"],
            title=dict(
                text="Score (%)",
                font=dict(family="Atkinson Hyperlegible, sans-serif", size=12, color=tokens["muted"])
            ),
            tickfont=dict(family="JetBrains Mono, monospace", size=11, color=tokens["muted"])
        ),
        xaxis=dict(
            title=dict(
                text="Benchmark Test Cases",
                font=dict(family="Atkinson Hyperlegible, sans-serif", size=12, color=tokens["muted"])
            ),
            tickfont=dict(family="JetBrains Mono, monospace", size=11, color=tokens["text"])
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(family="Atkinson Hyperlegible, sans-serif", size=12, color=tokens["text"])
        ),
        height=320,
        margin=dict(l=10, r=10, t=30, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Atkinson Hyperlegible, sans-serif", "color": tokens["text"]}
    )
    return fig
