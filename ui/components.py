"""Reusable Scholarly UI Component library for MethodWise Research Assistant."""

import os
import html
import textwrap
import streamlit as st
from ui.theme import COLORS

# --- SEMANTIC SVG ICON LIBRARY (Phosphor / Lucide Style) ---
ICONS = {
    "check": '<svg width="{size}" height="{size}" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M16.6667 5L7.5 14.1667L3.33333 10" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "check-circle": '<svg width="{size}" height="{size}" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="10" cy="10" r="8" stroke="{color}" stroke-width="1.75"/><path d="M6.5 10L9 12.5L13.5 7.5" stroke="{color}" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "document": '<svg width="{size}" height="{size}" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M11.6667 2.5H5C4.07953 2.5 3.33333 3.2457 3.33333 4.16667V15.8333C3.33333 16.7543 4.07953 17.5 5 17.5H15C15.9205 17.5 16.6667 16.7543 16.6667 15.8333V7.5L11.6667 2.5Z" stroke="{color}" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"/><path d="M11.6667 2.5V7.5H16.6667" stroke="{color}" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "book": '<svg width="{size}" height="{size}" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M3.33333 4.16667C3.33333 3.2457 4.07953 2.5 5 2.5H15C15.9205 2.5 16.6667 3.2457 16.6667 4.16667V15.8333C16.6667 16.7543 15.9205 17.5 15 17.5H5C4.07953 17.5 3.33333 16.7543 3.33333 15.8333V4.16667Z" stroke="{color}" stroke-width="1.75"/><path d="M7.5 6.66667H12.5M7.5 10H12.5M7.5 13.3333H10.5" stroke="{color}" stroke-width="1.75" stroke-linecap="round"/></svg>',
    "scale": '<svg width="{size}" height="{size}" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M10 2.5V17.5M5 17.5H15M2.5 6.66667L6.66667 12.5H1.66667L5 6.66667ZM15 6.66667L18.3333 12.5H13.3333L16.6667 6.66667Z" stroke="{color}" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "alert": '<svg width="{size}" height="{size}" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M10 3.33333L2.5 16.6667H17.5L10 3.33333Z" stroke="{color}" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"/><path d="M10 8.33333V11.6667M10 14.1667H10.0083" stroke="{color}" stroke-width="1.75" stroke-linecap="round"/></svg>',
    "shield": '<svg width="{size}" height="{size}" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M10 2.5L3.33333 5.83333V10C3.33333 14.1667 6.66667 17.0833 10 17.5C13.3333 17.0833 16.6667 14.1667 16.6667 10V5.83333L10 2.5Z" stroke="{color}" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "chart": '<svg width="{size}" height="{size}" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M15 16.6667V8.33333M10 16.6667V3.33333M5 16.6667V11.6667" stroke="{color}" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "crown": '<svg width="{size}" height="{size}" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M2.5 15H17.5L15.8333 6.66667L10 11.6667L4.16667 6.66667L2.5 15Z" stroke="{color}" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "clock": '<svg width="{size}" height="{size}" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="10" cy="10" r="8" stroke="{color}" stroke-width="1.75"/><path d="M10 5.83333V10L13.3333 11.6667" stroke="{color}" stroke-width="1.75" stroke-linecap="round"/></svg>',
    "compass": '<svg width="{size}" height="{size}" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="10" cy="10" r="8" stroke="{color}" stroke-width="1.75"/><path d="M13.5 6.5L11.5 11.5L6.5 13.5L8.5 8.5L13.5 6.5Z" stroke="{color}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "database": '<svg width="{size}" height="{size}" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><ellipse cx="10" cy="5" rx="7" ry="2.5" stroke="{color}" stroke-width="1.75"/><path d="M3 5V15C3 16.38 6.13 17.5 10 17.5C13.87 17.5 17 16.38 17 15V5" stroke="{color}" stroke-width="1.75"/><path d="M3 10C3 11.38 6.13 12.5 10 12.5C13.87 12.5 17 11.38 17 10" stroke="{color}" stroke-width="1.75"/></svg>',
    "arrow-right": '<svg width="{size}" height="{size}" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M4.16667 10H15.8333M15.8333 10L10.8333 5M15.8333 10L10.8333 15" stroke="{color}" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "download": '<svg width="{size}" height="{size}" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M10 3.33333V13.3333M10 13.3333L6.66667 10M10 13.3333L13.3333 10M3.33333 16.6667H16.6667" stroke="{color}" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "info": '<svg width="{size}" height="{size}" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="10" cy="10" r="8" stroke="{color}" stroke-width="1.75"/><path d="M10 9.16667V14.1667M10 6.66667H10.0083" stroke="{color}" stroke-width="2" stroke-linecap="round"/></svg>',
    "sparkles": '<svg width="{size}" height="{size}" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M10 2.5L11.5 7.5L16.5 9L11.5 10.5L10 15.5L8.5 10.5L3.5 9L8.5 7.5L10 2.5Z" stroke="{color}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "search": '<svg width="{size}" height="{size}" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="9" cy="9" r="6" stroke="{color}" stroke-width="1.75"/><path d="M13.5 13.5L17.5 17.5" stroke="{color}" stroke-width="1.75" stroke-linecap="round"/></svg>',
    "trash": '<svg width="{size}" height="{size}" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M3.33333 5H16.6667M8.33333 5V3.33333C8.33333 2.8731 8.70643 2.5 9.16667 2.5H10.8333C11.2936 2.5 11.6667 2.8731 11.6667 3.33333V5M15 5V16.6667C15 17.1269 14.6269 17.5 14.1667 17.5H5.83333C5.3731 17.5 5 17.1269 5 16.6667V5H15Z" stroke="{color}" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "refresh": '<svg width="{size}" height="{size}" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M17.5 10C17.5 14.1421 14.1421 17.5 10 17.5C5.85786 17.5 2.5 14.1421 2.5 10C2.5 5.85786 5.85786 2.5 10 2.5C13.0641 2.5 15.6987 4.33642 16.8529 7M17.5 2.5V7H13" stroke="{color}" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "flask": '<svg width="{size}" height="{size}" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M7.5 2.5H12.5M10 2.5V7.5L5 15.8333C4.46087 16.7319 5.10915 17.5 6.16667 17.5H13.8333C14.8909 17.5 15.5391 16.7319 15 15.8333L10 7.5" stroke="{color}" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"/><path d="M6.5 13.5H13.5" stroke="{color}" stroke-width="1.5"/></svg>',
    "layers": '<svg width="{size}" height="{size}" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M10 2.5L2.5 6.25L10 10L17.5 6.25L10 2.5Z" stroke="{color}" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"/><path d="M2.5 10L10 13.75L17.5 10" stroke="{color}" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"/><path d="M2.5 13.75L10 17.5L17.5 13.75" stroke="{color}" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "star": '<svg width="{size}" height="{size}" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M10 2.5L12.3175 7.19526L17.5 7.94975L13.75 11.6047L14.635 16.7645L10 14.325L5.365 16.7645L6.25 11.6047L2.5 7.94975L7.6825 7.19526L10 2.5Z" stroke="{color}" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "lightbulb": '<svg width="{size}" height="{size}" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M7.5 15H12.5M8.33333 17.5H11.6667M10 2.5C6.3181 2.5 3.33333 5.48477 3.33333 9.16667C3.33333 11.5833 4.6181 13.7083 6.66667 14.8333V15.8333H13.3333V14.8333C15.3819 13.7083 16.6667 11.5833 16.6667 9.16667C16.6667 5.48477 13.6819 2.5 10 2.5Z" stroke="{color}" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"/></svg>'
}


def get_svg_icon(name: str, size: int = 16, color: str = "currentColor") -> str:
    """Return inline SVG string for the specified icon name with accessible currentColor default."""
    template = ICONS.get(name, ICONS["info"])
    return template.format(size=size, color=color)


# --- HTML SANITIZATION & SAFE RENDERING HELPERS ---

def clean_html(html_str: str) -> str:
    """Clean HTML string: dedent, strip each line, drop empty lines, and join into a single string.
    Guarantees no lines begin with 4+ spaces and no blank lines exist (which trigger Markdown code blocks).
    """
    if not html_str:
        return ""
    dedented = textwrap.dedent(html_str)
    lines = [line.strip() for line in dedented.splitlines() if line.strip()]
    return " ".join(lines)


def render_html(html_str: str) -> None:
    """Render HTML string cleanly using st.html (if available) or st.markdown(unsafe_allow_html=True)."""
    cleaned = clean_html(html_str)
    if not cleaned:
        return
    if hasattr(st, "html"):
        st.html(cleaned)
    else:
        st.markdown(cleaned, unsafe_allow_html=True)


# --- COMPONENT BUILDERS (Clean Strings) & RENDERERS ---

def build_page_header_html(title: str, description: str, breadcrumb: str = "Research Assistant") -> str:
    raw = f"""
    <div class="rm-page-header">
        <div class="rm-breadcrumb" style="font-size: 0.8rem; font-weight: 700; color: var(--primary); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;">
            {html.escape(breadcrumb)}
        </div>
        <h1 class="rm-page-title" style="margin: 0 0 6px 0; font-family: 'Crimson Pro', Georgia, serif; font-size: 2.1rem; font-weight: 700; color: var(--text);">
            {html.escape(title)}
        </h1>
        <p class="rm-page-desc" style="font-size: 1rem; color: var(--muted); margin: 0 0 20px 0; line-height: 1.55;">
            {html.escape(description)}
        </p>
    </div>
    """
    return clean_html(raw)


def render_page_header(title: str, description: str, breadcrumb: str = "Research Assistant"):
    """Render a consistent academic-tech page header."""
    render_html(build_page_header_html(title, description, breadcrumb))


def build_section_header_html(title: str, subtitle: str = None, icon_name: str = None) -> str:
    icon_html = f"<span style='color: var(--primary); display: inline-flex; align-items: center; margin-right: 8px;'>{get_svg_icon(icon_name, size=20, color='var(--primary)')}</span>" if icon_name and icon_name in ICONS else ""
    sub_html = f'<p style="font-size: 0.95rem; color: var(--muted); margin: 0;">{html.escape(subtitle)}</p>' if subtitle else ''
    raw = f"""
    <div style="margin: 28px 0 18px 0;">
        <h3 style="font-family: 'Crimson Pro', Georgia, serif; font-size: 1.65rem; font-weight: 700; color: var(--text); margin: 0 0 4px 0; display: flex; align-items: center;">
            {icon_html}<span>{html.escape(title)}</span>
        </h3>
        {sub_html}
    </div>
    """
    return clean_html(raw)


def render_section_header(title: str, subtitle: str = None, icon_name: str = None):
    """Render a clean editorial section header with optional SVG icon."""
    render_html(build_section_header_html(title, subtitle, icon_name))


def build_method_map_fallback_html() -> str:
    """Styled 3-card fallback when assets/method_map.svg is missing."""
    raw = """
    <div class="rm-hero-map-container" style="display: flex; flex-direction: column; gap: 12px; width: 100%;">
        <div style="background: var(--surface); border: 1px solid var(--primary-border); border-left: 4px solid var(--primary); border-radius: 8px; padding: 14px 16px;">
            <div style="font-family: 'Crimson Pro', Georgia, serif; font-size: 1.1rem; font-weight: 700; color: var(--primary);">Quantitative Paradigm</div>
            <div style="font-size: 0.85rem; color: var(--muted); margin-top: 2px;">Causal &amp; Deductive • RCT, Quasi-Experimental • G*Power Calculation</div>
        </div>
        <div style="background: var(--surface); border: 1px solid var(--accent-border); border-left: 4px solid var(--accent); border-radius: 8px; padding: 14px 16px;">
            <div style="font-family: 'Crimson Pro', Georgia, serif; font-size: 1.1rem; font-weight: 700; color: var(--accent);">Qualitative Paradigm</div>
            <div style="font-size: 0.85rem; color: var(--muted); margin-top: 2px;">Lived &amp; Inductive • IPA, Thematic • Theoretical Saturation</div>
        </div>
        <div style="background: var(--surface); border: 1px solid var(--success-border); border-left: 4px solid var(--success); border-radius: 8px; padding: 14px 16px;">
            <div style="font-family: 'Crimson Pro', Georgia, serif; font-size: 1.1rem; font-weight: 700; color: var(--success);">Mixed Methods Paradigm</div>
            <div style="font-size: 0.85rem; color: var(--muted); margin-top: 2px;">Pragmatic &amp; Dialectical • Explanatory Sequential • Joint Display Matrix</div>
        </div>
    </div>
    """
    return clean_html(raw)


def render_hero(
    headline: str = "Choose the right research method, with confidence",
    subheadline: str = "Empowering researchers, doctoral scholars, and academics to formulate epistemologically rigorous, feasible, and defensible research designs.",
    trust_line: str = "Triple-validated: LLM-as-Judge Rubric + 26 Gold Standard Reference Cases + Deterministic Rule Verification"
):
    """Render the landing page hero section with inline Method Map illustration."""
    active_theme = st.session_state.get("theme", "light")
    method_map_filename = "method_map_dark.svg" if str(active_theme).lower() == "dark" else "method_map.svg"
    method_map_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", method_map_filename)

    col1, col2 = st.columns([1.22, 1.0], vertical_alignment="center")
    with col1:
        raw_text_block = f"""
        <div style="padding: 10px 0 16px 0;">
            <div class="rm-badge rm-badge-indigo" style="margin-bottom: 16px;">
                {get_svg_icon("sparkles", size=14, color="var(--primary)")}
                <span>MethodWise AI • Academic Decision Support</span>
            </div>
            <h1 style="font-family: 'Crimson Pro', Georgia, serif; font-size: 2.85rem; font-weight: 700; line-height: 1.15; color: var(--text); margin: 0 0 16px 0;">
                {html.escape(headline)}
            </h1>
            <p style="font-size: 1.1rem; line-height: 1.6; color: var(--muted); margin: 0 0 20px 0;">
                {html.escape(subheadline)}
            </p>
            <div style="font-size: 0.88rem; color: var(--muted); display: flex; align-items: center; gap: 8px; margin-bottom: 24px;">
                <span style="color: var(--success);">{get_svg_icon('check-circle', size=16, color='var(--success)')}</span>
                <span>{html.escape(trust_line)}</span>
            </div>
        </div>
        """
        render_html(raw_text_block)

        btn_c1, btn_c2 = st.columns([1.1, 1], gap="medium")
        with btn_c1:
            if st.button("Get a Recommendation", type="primary", width="stretch", key="hero_cta_rec"):
                st.switch_page("views/recommend.py")
        with btn_c2:
            if st.button("See How It Works", type="secondary", width="stretch", key="hero_cta_about"):
                st.switch_page("views/about.py")

    with col2:
        if os.path.exists(method_map_path):
            render_html('<div class="rm-hero-map-container">')
            st.image(
                method_map_path,
                use_container_width=True,
                alt="Method Map: Branching decision tree connecting research questions to Quantitative, Qualitative, and Mixed Methods paradigms with design, sampling, and analysis specifications"
            )
            render_html('</div>')
        else:
            render_html(build_method_map_fallback_html())


def build_stat_card_html(label: str, value: str, subtext: str = None, icon_name: str = None) -> str:
    subtext_html = f'<div class="rm-stat-subtext">{html.escape(subtext)}</div>' if subtext else ""
    icon_html = f'<div style="margin-bottom: 6px; color: var(--accent);">{get_svg_icon(icon_name, size=18, color="var(--accent)")}</div>' if icon_name else ""
    raw = f"""
    <div class="rm-stat-box">
        {icon_html}
        <div class="rm-stat-label">{html.escape(label)}</div>
        <div class="rm-stat-value">{html.escape(value)}</div>
        {subtext_html}
    </div>
    """
    return clean_html(raw)


def render_stat_card(label: str, value: str, subtext: str = None, icon_name: str = None):
    """Render a modern stat metric card."""
    render_html(build_stat_card_html(label, value, subtext, icon_name))


def build_step_card_html(step_num: int, title: str, description: str) -> str:
    step_str = f"0{step_num}" if step_num < 10 else str(step_num)
    raw = f"""
    <div class="rm-step-card" style="height: 100%;">
        <div>
            <div class="rm-step-num">Step {step_str}</div>
            <h4 class="rm-step-title">{html.escape(title)}</h4>
            <p class="rm-step-desc">{html.escape(description)}</p>
        </div>
    </div>
    """
    return clean_html(raw)


def render_step_card(step_num: int, title: str, description: str):
    """Render a step card in the connected horizontal flow."""
    render_html(build_step_card_html(step_num, title, description))


def build_feature_card_html(icon_name: str, title: str, description: str, is_span2: bool = False) -> str:
    span_class = "rm-bento-card-span2" if is_span2 else ""
    icon_html = get_svg_icon(icon_name, size=24, color="var(--primary)")
    raw = f"""
    <div class="rm-card {span_class}" style="height: 100%;">
        <div style="margin-bottom: 14px; background: var(--primary-subtle); border: 1px solid var(--primary-border); border-radius: 8px; width: 42px; height: 42px; display: flex; align-items: center; justify-content: center;">
            {icon_html}
        </div>
        <h4 style="font-family: 'Crimson Pro', Georgia, serif; font-size: 1.25rem; font-weight: 700; color: var(--text); margin: 0 0 8px 0;">
            {html.escape(title)}
        </h4>
        <p style="font-size: 0.92rem; line-height: 1.55; color: var(--muted); margin: 0;">
            {html.escape(description)}
        </p>
    </div>
    """
    return clean_html(raw)


def render_feature_card(icon_name: str, title: str, description: str, is_span2: bool = False):
    """Render a bento box feature card with SVG icon."""
    render_html(build_feature_card_html(icon_name, title, description, is_span2))


def render_badge(text: str, variant: str = "indigo", icon_name: str = None, tooltip: str = None) -> str:
    """Return clean HTML string for a styled badge with optional SVG icon and tooltip."""
    escaped_text = html.escape(str(text))
    variant_class = f"rm-badge-{variant}"
    color_map = {
        "indigo": "var(--primary)",
        "ochre": "var(--accent)",
        "amber": "var(--warning)",
        "teal": "var(--success)",
        "pass": "var(--success)",
        "review": "var(--warning)",
        "fail": "var(--danger)",
        "danger": "var(--danger)",
        "grey": "var(--muted)",
        "neutral": "var(--muted)",
    }
    icon_color = color_map.get(variant, "var(--primary)")
    icon_html = f"<span>{get_svg_icon(icon_name, size=13, color=icon_color)}</span>" if icon_name else ""
    title_attr = f' title="{html.escape(tooltip)}"' if tooltip else ""
    raw = f'<span class="rm-badge {variant_class}"{title_attr}>{icon_html}<span>{escaped_text}</span></span>'
    return clean_html(raw)


def render_evidence_ribbon(
    rubric_score: float,
    rubric_label: str,
    ref_case_id: str,
    ref_status: str,
    rule_violations_count: int = 0
) -> str:
    """Render the signature Evidence Ribbon under the brief abstract."""
    rubric_variant = "pass" if rubric_label == "PASS" else ("review" if rubric_label == "REVIEW" else "fail")
    rubric_chip = render_badge(
        f"Rubric: {rubric_score:.1f}% ({rubric_label})",
        rubric_variant,
        icon_name="chart",
        tooltip="LLM-as-judge academic rubric evaluation across 5 methodological criteria (0-25 scale)."
    )

    norm_status = (ref_status or "").upper().strip()
    norm_ref_id = (ref_case_id or "").strip()
    is_no_case = (
        not norm_ref_id
        or norm_ref_id in ("REF-NONE", "NONE", "N/A", "NO_CASE", "NO_MATCH", "NO_REFERENCE")
        or norm_status in ("UNCHECKED", "NO_MATCH", "NO_CASE", "NONE", "N/A", "NO_REFERENCE", "")
    )

    ref_tooltip = "Reference check: evaluates paradigm and design alignment against expert gold-standard methodological benchmark cases."

    if norm_status == "MATCH" and not is_no_case:
        ref_variant = "teal"
        ref_label = f"Reference: {norm_ref_id} (MATCH)"
    elif norm_status in ("PARTIAL", "PARTIAL_MATCH") and not is_no_case:
        ref_variant = "amber"
        ref_label = f"Reference: {norm_ref_id} (PARTIAL)"
    elif norm_status == "MISMATCH" and not is_no_case:
        ref_variant = "fail"
        ref_label = f"Reference: {norm_ref_id} (MISMATCH)"
    else:
        ref_variant = "neutral"
        ref_label = "Reference: no matching case (n/a)"

    ref_chip = render_badge(ref_label, ref_variant, icon_name="book", tooltip=ref_tooltip)

    rule_variant = "teal" if rule_violations_count == 0 else "danger"
    rule_text = "Integrity: Zero Violations" if rule_violations_count == 0 else f"Integrity: {rule_violations_count} Flags"
    rule_chip = render_badge(
        rule_text,
        rule_variant,
        icon_name="shield",
        tooltip="Deterministic integrity checks: anti-hallucinated citations, statistical power calculations, and paradigm consistency."
    )

    raw = f"""
    <div class="rm-evidence-ribbon">
        <span style="font-size: 0.78rem; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; margin-right: 4px;">
            Evidence Ribbon:
        </span>
        {rubric_chip}
        {ref_chip}
        {rule_chip}
    </div>
    """
    return clean_html(raw)


def render_confidence_meter(level: str) -> str:
    """Render a discrete 3-step segmented confidence meter (Low | Medium | High)."""
    norm_level = (level or "").capitalize().strip()
    low_class = "rm-meter-step-active-amber" if norm_level == "Low" else ""
    med_class = "rm-meter-step-active-amber" if norm_level == "Medium" else ""
    high_class = "rm-meter-step-active-teal" if norm_level == "High" else ""

    raw = f"""
    <div style="display: inline-flex; align-items: center; gap: 8px;">
        <span style="font-size: 0.8rem; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: 0.04em;">Confidence:</span>
        <div class="rm-confidence-meter">
            <span class="rm-meter-step {low_class}">Low</span>
            <span class="rm-meter-step {med_class}">Medium</span>
            <span class="rm-meter-step {high_class}">High</span>
        </div>
    </div>
    """
    return clean_html(raw)


def build_ethics_callout_html(message: str, is_vulnerable: bool = False, is_irb_required: bool = False) -> str:
    alert_icon = get_svg_icon("alert", size=20, color="var(--danger)")
    vulnerable_badge = render_badge("Vulnerable Population Safeguards Activated", "danger", icon_name="alert") if is_vulnerable else ""
    irb_badge = render_badge("IRB / REC Clearance Mandatory", "danger", icon_name="scale") if is_irb_required else ""
    escaped_msg = html.escape(str(message))

    raw = f"""
    <div class="rm-alert-danger" style="margin-bottom: 20px;">
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
            {alert_icon}
            <strong style="font-family: 'Crimson Pro', Georgia, serif; font-size: 1.15rem; color: var(--danger);">
                Research Ethics &amp; Governance Alert
            </strong>
        </div>
        <div style="margin-bottom: 8px; display: flex; gap: 8px; flex-wrap: wrap;">
            {vulnerable_badge}
            {irb_badge}
        </div>
        <div>{escaped_msg}</div>
    </div>
    """
    return clean_html(raw)


def render_ethics_callout(message: str, is_vulnerable: bool = False, is_irb_required: bool = False):
    """Render a high-contrast editorial ethics marginal callout."""
    render_html(build_ethics_callout_html(message, is_vulnerable, is_irb_required))


def build_roadmap_timeline_html(roadmap_steps: list) -> str:
    """Build the vertical scholarly timeline HTML string with clean classes and escaped text."""
    nodes_html_parts = []
    for s in (roadmap_steps or []):
        num = html.escape(str(s.step_number if hasattr(s, "step_number") else s.get("step_number", 1)))
        title = html.escape(str(s.title if hasattr(s, "title") else s.get("title", "")))
        desc = html.escape(str(s.description if hasattr(s, "description") else s.get("description", "")))
        duration = html.escape(str(s.estimated_duration if hasattr(s, "estimated_duration") else s.get("estimated_duration", "")))

        node = f"""
        <div class="rm-timeline-node">
            <div class="rm-timeline-marker">{num}</div>
            <div class="rm-timeline-content">
                <div class="rm-timeline-header">
                    <strong class="rm-timeline-title">{title}</strong>
                    <span class="rm-timeline-duration">{duration}</span>
                </div>
                <p class="rm-timeline-desc">{desc}</p>
            </div>
        </div>
        """
        nodes_html_parts.append(clean_html(node))

    full_html = f'<div class="rm-timeline">{" ".join(nodes_html_parts)}</div>'
    return clean_html(full_html)


def render_roadmap_timeline(roadmap_steps: list):
    """Render the execution roadmap as a vertical scholarly timeline."""
    render_html(build_roadmap_timeline_html(roadmap_steps))


def build_empty_state_html(icon_name: str, title: str, message: str) -> str:
    icon_svg = get_svg_icon(icon_name, size=38, color="var(--accent)")
    raw = f"""
    <div class="rm-card" style="text-align: center; padding: 48px 24px; margin: 24px 0;">
        <div style="margin-bottom: 12px; display: inline-flex; align-items: center; justify-content: center; width: 64px; height: 64px; background: var(--surface-2); border: 1px solid var(--border); border-radius: 50%;">
            {icon_svg}
        </div>
        <h3 style="font-family: 'Crimson Pro', Georgia, serif; font-size: 1.45rem; font-weight: 700; color: var(--text); margin: 0 0 8px 0;">
            {html.escape(title)}
        </h3>
        <p style="color: var(--muted); font-size: 0.95rem; max-width: 480px; margin: 0 auto 20px auto; line-height: 1.6;">
            {html.escape(message)}
        </p>
    </div>
    """
    return clean_html(raw)


def render_empty_state(icon_name: str, title: str, message: str, cta_text: str = None, cta_page: str = None):
    """Render a clean empty state card with optional action button."""
    render_html(build_empty_state_html(icon_name, title, message))
    if cta_text and cta_page:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button(cta_text, width="stretch", type="primary"):
                st.switch_page(cta_page)


def build_footer_html() -> str:
    raw = """
    <div class="rm-footer">
        <strong>MethodWise • Research Methodology Recommendation Assistant</strong><br>
        <span style="font-size: 0.82rem; color: var(--muted);">
            Academic Advisory: This tool provides algorithmic decision support to guide methodological planning. It does not supersede doctoral faculty supervision or mandatory Institutional Review Board (IRB / REC) oversight.
        </span>
    </div>
    """
    return clean_html(raw)


def render_footer():
    """Render consistent scholarly footer across all pages."""
    render_html(build_footer_html())
