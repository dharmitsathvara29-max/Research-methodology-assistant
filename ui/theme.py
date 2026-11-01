"""Design System Tokens, Typography, and Global CSS for MethodWise Research Assistant.
Aesthetic Direction: Scholarly Editorial (Typeset Research Journal × Modern Dashboard).
Supports dynamic Light and Dark mode with CSS Variables and WCAG 2.1 AA verified contrast.
"""

from typing import Dict, Any
import streamlit as st

# --- TOKEN SETS (WCAG 2.1 AA Compliant) ---
LIGHT_TOKENS = {
    "bg": "#FAF7F2",              # Warm scholarly paper canvas
    "surface": "#FFFFFF",         # Pure white card surface
    "surface_2": "#F3EFE8",       # Subtle warm secondary surface / table header
    "border": "#E7E2D9",          # Hairline card border
    "border_subtle": "#EFECE6",   # Row divider
    "text": "#0F172A",            # Deep ink for headings & high contrast (16.7:1)
    "muted": "#475569",           # Body slate (7.1:1)
    "text_faint": "#94A3B8",      # Disabled/faint metadata
    "primary": "#3730A3",         # Deep Indigo (actions, primary CTA, active navigation)
    "primary_contrast": "#FFFFFF",# Text on primary button
    "primary_subtle": "#EEF2FF",  # Tinted indigo badge background
    "primary_border": "#C7D2FE",  # Tinted indigo badge border
    "accent": "#B45309",          # Scholarly Ochre / Citation Gold (highlights)
    "accent_contrast": "#FFFFFF", # Text on accent
    "accent_subtle": "#FEF3C7",   # Soft ochre surface / badge background
    "accent_border": "#FDE68A",   # Soft ochre boundary
    "success": "#0F766E",         # Scholarly Teal (verified, rubric pass, reference match)
    "success_subtle": "#F0FDFA",  # Teal subtle surface
    "success_border": "#99F6E4",  # Teal hairline border
    "warning": "#B45309",         # Warm Amber (advisory notices, parameter review)
    "warning_subtle": "#FFFBEB",  # Amber subtle surface
    "warning_border": "#FDE68A",  # Amber hairline border
    "danger": "#B91C1C",          # Editorial Red (rejection, vulnerable cohort warning)
    "danger_subtle": "#FEF2F2",   # Red subtle surface
    "danger_border": "#FECACA",   # Red hairline border
    "sidebar_bg": "#0F172A",      # Midnight sidebar background
    "sidebar_surface": "#1E293B", # Sidebar elevated card
    "sidebar_text": "#F8FAFC",    # Sidebar primary text
    "sidebar_border": "#334155",  # Sidebar border
}

DARK_TOKENS = {
    "bg": "#0B1220",              # Deep navy slate canvas (avoids pure black #000000)
    "surface": "#121A2B",         # Elevated dark card surface
    "surface_2": "#1A2438",       # Secondary dark surface / table headers
    "border": "#2A3550",          # Visible dark component boundary (>= 3:1)
    "border_subtle": "#1E293B",   # Dark row divider
    "text": "#E6EAF2",            # High-contrast readable off-white (15.5:1)
    "muted": "#A3AEC2",           # Accessible muted silver text (7.8:1)
    "text_faint": "#64748B",      # Faint metadata
    "primary": "#818CF8",         # Accessible Periwinkle Indigo (6.3:1)
    "primary_contrast": "#0B1220",# Dark text on bright primary
    "primary_subtle": "rgba(129, 140, 248, 0.15)",
    "primary_border": "rgba(129, 140, 248, 0.35)",
    "accent": "#FBBF24",          # Luminous Amber / Gold (11.2:1)
    "accent_contrast": "#0B1220", # Dark text on accent
    "accent_subtle": "rgba(251, 191, 36, 0.15)",
    "accent_border": "rgba(251, 191, 36, 0.35)",
    "success": "#2DD4BF",         # Luminous Mint Teal (10.1:1)
    "success_subtle": "rgba(45, 212, 191, 0.15)",
    "success_border": "rgba(45, 212, 191, 0.35)",
    "warning": "#FBBF24",         # Warm Amber warning
    "warning_subtle": "rgba(251, 191, 36, 0.15)",
    "warning_border": "rgba(251, 191, 36, 0.35)",
    "danger": "#F87171",          # Coral Red (6.8:1)
    "danger_subtle": "rgba(248, 113, 113, 0.15)",
    "danger_border": "rgba(248, 113, 113, 0.35)",
    "sidebar_bg": "#0B1220",      # Matching dark slate sidebar
    "sidebar_surface": "#121A2B", # Elevated sidebar surface
    "sidebar_text": "#E6EAF2",    # Sidebar text
    "sidebar_border": "#2A3550",  # Sidebar divider
}


def get_theme_tokens(theme: str = "light") -> Dict[str, str]:
    """Retrieve color token dictionary for the requested theme."""
    if str(theme).lower() == "dark":
        return DARK_TOKENS.copy()
    return LIGHT_TOKENS.copy()


class ThemeColorProxy(dict):
    """Dynamically resolves token colors based on active theme in session_state.
    Provides complete backwards-compatibility for components importing COLORS.
    """
    def __getitem__(self, key: str) -> str:
        try:
            active_theme = st.session_state.get("theme", "light")
        except Exception:
            active_theme = "light"
        tokens = get_theme_tokens(active_theme)
        if key in tokens:
            return tokens[key]
        legacy_map = {
            "primary_hover": tokens["primary"],
            "primary_light": tokens["primary"],
            "accent_hover": tokens["accent"],
            "success_bg": tokens["success_subtle"],
            "warning_bg": tokens["warning_subtle"],
            "danger_bg": tokens["danger_subtle"],
            "bg_paper": tokens["bg"],
            "bg_light": tokens["bg"],
            "card_bg": tokens["surface"],
            "surface_subtle": tokens["surface_2"],
            "ink": tokens["text"],
            "ink_body": tokens["text"],
            "ink_muted": tokens["muted"],
            "ink_faint": tokens["text_faint"],
            "slate_900": tokens["text"],
            "slate_800": tokens["text"],
            "slate_700": tokens["text"],
            "slate_600": tokens["muted"],
            "slate_500": tokens["muted"],
            "slate_400": tokens["text_faint"],
            "slate_300": tokens["border"],
            "slate_200": tokens["border_subtle"],
            "slate_100": tokens["surface_2"],
        }
        return legacy_map.get(key, tokens.get(key, "#3730A3"))

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default


COLORS = ThemeColorProxy()


@st.cache_data
def get_theme_css(theme: str = "light") -> str:
    """Generate complete global CSS with CSS variables and dark mode widget overrides."""
    tokens = get_theme_tokens(theme)
    is_dark = (str(theme).lower() == "dark")

    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:ital,wght@0,400;0,700;1,400&family=Crimson+Pro:ital,wght@0,500;0,600;0,700;1,500;1,600&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {{
    --bg: {tokens['bg']};
    --surface: {tokens['surface']};
    --surface-2: {tokens['surface_2']};
    --border: {tokens['border']};
    --border-subtle: {tokens['border_subtle']};
    --text: {tokens['text']};
    --muted: {tokens['muted']};
    --text-faint: {tokens['text_faint']};
    --primary: {tokens['primary']};
    --primary-contrast: {tokens['primary_contrast']};
    --primary-subtle: {tokens['primary_subtle']};
    --primary-border: {tokens['primary_border']};
    --accent: {tokens['accent']};
    --accent-contrast: {tokens['accent_contrast']};
    --accent-subtle: {tokens['accent_subtle']};
    --accent-border: {tokens['accent_border']};
    --success: {tokens['success']};
    --success-subtle: {tokens['success_subtle']};
    --success-border: {tokens['success_border']};
    --warning: {tokens['warning']};
    --warning-subtle: {tokens['warning_subtle']};
    --warning-border: {tokens['warning_border']};
    --danger: {tokens['danger']};
    --danger-subtle: {tokens['danger_subtle']};
    --danger-border: {tokens['danger_border']};
    --sidebar-bg: {tokens['sidebar_bg']};
    --sidebar-surface: {tokens['sidebar_surface']};
    --sidebar-text: {tokens['sidebar_text']};
    --sidebar-border: {tokens['sidebar_border']};
}}

/* Typography & Layout Defaults */
html, body, [class*="css"], .stApp {{
    font-family: 'Atkinson Hyperlegible', -apple-system, BlinkMacSystemFont, sans-serif !important;
    background-color: var(--bg) !important;
    color: var(--text) !important;
    -webkit-font-smoothing: antialiased;
    transition: background-color 180ms ease, color 180ms ease, border-color 180ms ease;
}}

/* Scholarly Editorial Headings */
h1, h2, h3, h4, .serif-font, .rm-page-title, .rm-brief-title {{
    font-family: 'Crimson Pro', Georgia, serif !important;
    letter-spacing: -0.015em;
    color: var(--text) !important;
}}

p, span, label, div {{
    color: var(--text);
}}

.stCaption, small, [data-testid="stCaptionContainer"] {{
    color: var(--muted) !important;
}}

/* Tabular Numerals & Monospace */
code, pre, .tabular-num, .rm-stat-value {{
    font-family: 'JetBrains Mono', monospace !important;
    font-variant-numeric: tabular-nums;
}}

/* Hide Default Streamlit Clutter without hiding sidebar controls */
#MainMenu {{ visibility: hidden; }}
footer {{ visibility: hidden; }}
[data-testid="stAppDeployButton"] {{ display: none !important; }}
div[data-testid="stDecoration"] {{ display: none; }}
div[data-testid="stStatusWidget"] {{ visibility: hidden; }}

/* Ensure Header and Sidebar Toggle are ALWAYS visible and functional */
header[data-testid="stHeader"] {{
    background: transparent !important;
    visibility: visible !important;
}}

[data-testid="stToolbar"] {{
    visibility: visible !important;
}}

[data-testid="stExpandSidebarButton"],
button[aria-label="Expand sidebar"],
button[data-testid="stSidebarCollapseButton"] {{
    visibility: visible !important;
    display: inline-flex !important;
    opacity: 1 !important;
    z-index: 999999 !important;
    background: var(--surface) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    padding: 6px 10px !important;
    box-shadow: 0 2px 6px rgba(15, 23, 42, 0.12) !important;
}}

[data-testid="stExpandSidebarButton"]:hover {{
    background: var(--surface-2) !important;
    border-color: var(--primary) !important;
}}

/* Interactive Cursor Polish */
button, [role="button"], input[type="submit"], select, .clickable-card {{
    cursor: pointer !important;
}}

/* Accessible Focus States */
button:focus-visible, input:focus-visible, textarea:focus-visible, select:focus-visible, [tabindex="0"]:focus-visible {{
    outline: 2px solid var(--primary) !important;
    outline-offset: 2px !important;
}}

/* Editorial Card Container */
.rm-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 20px;
    box-shadow: {'0 1px 3px rgba(15, 23, 42, 0.04), 0 1px 2px rgba(15, 23, 42, 0.02)' if not is_dark else 'none'};
    transition: transform 180ms ease, box-shadow 180ms ease, background-color 180ms ease;
}}

.rm-card:hover {{
    transform: translateY(-1.5px);
    box-shadow: {'0 4px 6px -1px rgba(15, 23, 42, 0.07), 0 2px 4px -2px rgba(15, 23, 42, 0.04)' if not is_dark else '0 0 0 1px var(--primary)'};
}}

.rm-card-highlight {{
    background: var(--surface);
    border: 1.5px solid var(--primary);
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 20px;
    box-shadow: {'0 4px 12px rgba(55, 48, 163, 0.06)' if not is_dark else 'none'};
}}

/* Bento Box Grid */
.rm-bento-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    margin-bottom: 24px;
}}

.rm-bento-card-span2 {{
    grid-column: span 2;
}}

@media (max-width: 992px) {{
    .rm-bento-grid {{
        grid-template-columns: 1fr;
    }}
    .rm-bento-card-span2 {{
        grid-column: span 1;
    }}
}}

/* Editorial Metric Box */
.rm-stat-box {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px 18px;
    text-align: left;
    box-shadow: {'0 1px 2px rgba(15, 23, 42, 0.03)' if not is_dark else 'none'};
    transition: transform 150ms ease, background-color 180ms ease;
}}

.rm-stat-box:hover {{
    transform: translateY(-1px);
}}

.rm-stat-label {{
    font-size: 0.75rem;
    font-weight: 700;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 6px;
}}

.rm-stat-value {{
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 1.85rem;
    font-weight: 600;
    color: var(--text);
    line-height: 1.1;
    font-variant-numeric: tabular-nums;
}}

.rm-stat-subtext {{
    font-size: 0.8rem;
    color: var(--muted);
    margin-top: 4px;
}}

/* Connected Horizontal Step Flow ("How It Works") */
.rm-step-flow {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin: 20px 0 32px 0;
}}

@media (max-width: 900px) {{
    .rm-step-flow {{
        grid-template-columns: 1fr 1fr;
    }}
}}

@media (max-width: 600px) {{
    .rm-step-flow {{
        grid-template-columns: 1fr;
    }}
}}

.rm-step-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 20px;
    position: relative;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}}

.rm-step-num {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
    font-weight: 700;
    color: var(--primary);
    background: var(--primary-subtle);
    border: 1px solid var(--primary-border);
    border-radius: 6px;
    padding: 2px 8px;
    display: inline-block;
    margin-bottom: 12px;
    width: fit-content;
}}

.rm-step-title {{
    font-family: 'Crimson Pro', Georgia, serif;
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--text);
    margin: 0 0 6px 0;
}}

.rm-step-desc {{
    font-size: 0.88rem;
    color: var(--muted);
    line-height: 1.5;
    margin: 0;
}}

/* Semantic Badges & Chips */
.rm-badge {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 3px 10px;
    border-radius: 6px;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.02em;
    line-height: 1.3;
}}

.rm-badge-indigo {{
    background-color: var(--primary-subtle);
    color: var(--primary);
    border: 1px solid var(--primary-border);
}}

.rm-badge-ochre {{
    background-color: var(--accent-subtle);
    color: var(--accent);
    border: 1px solid var(--accent-border);
}}

.rm-badge-teal, .rm-badge-pass {{
    background-color: var(--success-subtle);
    color: var(--success);
    border: 1px solid var(--success-border);
}}

.rm-badge-review, .rm-badge-amber {{
    background-color: var(--warning-subtle);
    color: var(--warning);
    border: 1px solid var(--warning-border);
}}

.rm-badge-fail, .rm-badge-danger {{
    background-color: var(--danger-subtle);
    color: var(--danger);
    border: 1px solid var(--danger-border);
}}

.rm-badge-grey, .rm-badge-neutral {{
    background-color: var(--surface-2);
    color: var(--muted);
    border: 1px solid var(--border);
}}

/* Signature "Evidence Ribbon" */
.rm-evidence-ribbon {{
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px 16px;
    margin: 16px 0;
    align-items: center;
}}

.rm-evidence-item {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--text);
}}

/* Segmented Confidence Meter */
.rm-confidence-meter {{
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 3px 6px;
}}

.rm-meter-step {{
    font-size: 0.72rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 4px;
    color: var(--muted);
    background: transparent;
}}

.rm-meter-step-active {{
    background: var(--primary);
    color: var(--primary-contrast);
}}

.rm-meter-step-active-teal {{
    background: var(--success);
    color: var(--primary-contrast);
}}

.rm-meter-step-active-amber {{
    background: var(--warning);
    color: var(--accent-contrast);
}}

/* Phased Roadmap Timeline Nodes */
.rm-timeline-node {{
    display: flex;
    gap: 14px;
    position: relative;
    padding-bottom: 20px;
}}

.rm-timeline-line {{
    position: absolute;
    left: 17px;
    top: 24px;
    bottom: 0;
    width: 2px;
    background: var(--border);
}}

.rm-timeline-marker {{
    width: 22px;
    height: 22px;
    border-radius: 50%;
    background: var(--surface);
    border: 2px solid var(--primary);
    color: var(--primary);
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    z-index: 1;
}}

.rm-timeline-content {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 14px 18px;
    flex-grow: 1;
}}

.rm-timeline-header {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 6px;
}}

.rm-timeline-title {{
    font-family: 'Crimson Pro', Georgia, serif;
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--text);
}}

.rm-timeline-duration, .rm-pill {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    font-weight: 600;
    color: var(--accent);
    background: var(--accent-subtle);
    border: 1px solid var(--accent-border);
    padding: 2px 8px;
    border-radius: 4px;
}}

.rm-pill-teal {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    font-weight: 600;
    color: var(--success);
    background: var(--success-subtle);
    border: 1px solid var(--success-border);
    padding: 2px 8px;
    border-radius: 4px;
}}

.rm-pill-indigo {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    font-weight: 600;
    color: var(--primary);
    background: var(--primary-subtle);
    border: 1px solid var(--primary-border);
    padding: 2px 8px;
    border-radius: 4px;
}}

.rm-timeline-desc {{
    font-size: 0.9rem;
    color: var(--muted);
    line-height: 1.55;
    margin: 0;
}}

/* Callout Alerts */
.rm-alert-info {{
    background-color: var(--primary-subtle);
    border-left: 4px solid var(--primary);
    border-radius: 8px;
    padding: 14px 18px;
    color: var(--text);
    margin-bottom: 18px;
    border-top: 1px solid var(--primary-border);
    border-right: 1px solid var(--primary-border);
    border-bottom: 1px solid var(--primary-border);
}}

.rm-alert-warning {{
    background-color: var(--warning-subtle);
    border-left: 4px solid var(--warning);
    border-radius: 8px;
    padding: 14px 18px;
    color: var(--text);
    margin-bottom: 18px;
    border-top: 1px solid var(--warning-border);
    border-right: 1px solid var(--warning-border);
    border-bottom: 1px solid var(--warning-border);
}}

.rm-alert-danger {{
    background-color: var(--danger-subtle);
    border-left: 4px solid var(--danger);
    border-radius: 8px;
    padding: 14px 18px;
    color: var(--text);
    margin-bottom: 18px;
    border-top: 1px solid var(--danger-border);
    border-right: 1px solid var(--danger-border);
    border-bottom: 1px solid var(--danger-border);
}}

/* Clean Empty State */
.rm-empty-state {{
    text-align: center;
    padding: 48px 24px;
    background: var(--surface);
    border: 1px dashed var(--border);
    border-radius: 12px;
    margin: 20px 0;
}}

.rm-empty-state-icon {{
    color: var(--muted);
    margin-bottom: 14px;
}}

.rm-empty-state-title {{
    font-family: 'Crimson Pro', Georgia, serif;
    font-size: 1.35rem;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 8px;
}}

.rm-empty-state-text {{
    font-size: 0.95rem;
    color: var(--muted);
    max-width: 480px;
    margin: 0 auto 20px auto;
    line-height: 1.6;
}}

/* Academic Footers */
.rm-footer {{
    border-top: 1px solid var(--border);
    padding: 24px 0 16px 0;
    margin-top: 48px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.82rem;
    color: var(--muted);
}}

/* Hero Method Map Container & Responsive Layout */
.rm-hero-map-container {{
    width: 100%;
    min-height: 280px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    position: relative;
    transition: transform 0.25s ease, box-shadow 0.25s ease;
}}

.rm-hero-map-container img {{
    width: 100% !important;
    height: auto !important;
    display: block;
    max-width: 560px;
    border-radius: 12px;
    border: 1px solid var(--border);
    box-shadow: {'0 4px 20px -2px rgba(15, 23, 42, 0.06)' if not is_dark else 'none'};
}}

@media (max-width: 768px) {{
    .rm-hero-map-container {{
        min-height: 200px;
        margin-top: 16px;
    }}
}}

@media (prefers-reduced-motion: no-preference) {{
    .rm-hero-map-container:hover {{
        transform: translateY(-2px);
    }}
}}

/* ========================================================================= */
/* STREAMLIT NATIVE WIDGET OVERRIDES FOR SEAMLESS THEME COHESION             */
/* ========================================================================= */

/* Sidebar Background & Borders */
section[data-testid="stSidebar"] {{
    background-color: var(--sidebar-bg) !important;
    border-right: 1px solid var(--sidebar-border) !important;
}}

section[data-testid="stSidebar"] div.stMarkdown,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label {{
    color: var(--sidebar-text);
}}

/* Inputs, TextAreas & SelectBoxes */
.stTextInput input, .stTextArea textarea, .stNumberInput input {{
    background-color: var(--surface) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}}

.stTextInput input:focus, .stTextArea textarea:focus, .stNumberInput input:focus {{
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 1px var(--primary) !important;
}}

div[data-baseweb="select"] > div {{
    background-color: var(--surface) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}}

div[data-baseweb="select"] span {{
    color: var(--text) !important;
}}

div[data-baseweb="select"] svg {{
    fill: var(--text) !important;
}}

/* Dropdown Menus */
div[data-baseweb="popover"], div[data-baseweb="menu"], ul[role="listbox"] {{
    background-color: var(--surface) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}}

li[role="option"] {{
    color: var(--text) !important;
}}

li[role="option"]:hover, li[aria-selected="true"] {{
    background-color: var(--surface-2) !important;
    color: var(--primary) !important;
}}

/* Primary & Secondary Buttons */
button[kind="primary"], button[data-testid="baseButton-primary"] {{
    background-color: var(--primary) !important;
    color: var(--primary-contrast) !important;
    border: 1px solid var(--primary) !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}}

button[kind="primary"]:hover, button[data-testid="baseButton-primary"]:hover {{
    filter: brightness(1.1);
}}

button[kind="secondary"], button[data-testid="baseButton-secondary"] {{
    background-color: var(--surface) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}}

button[kind="secondary"]:hover, button[data-testid="baseButton-secondary"]:hover {{
    background-color: var(--surface-2) !important;
    border-color: var(--primary) !important;
}}

/* Segmented Control & Radio */
div[data-baseweb="segmented-control"] {{
    background-color: var(--surface-2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    padding: 3px !important;
}}

div[data-baseweb="segmented-control"] button {{
    color: var(--text) !important;
    font-weight: 600 !important;
    border-radius: 6px !important;
}}

div[data-baseweb="segmented-control"] button[aria-selected="true"] {{
    background-color: var(--surface) !important;
    color: var(--primary) !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
}}

/* Expanders */
details[data-testid="stExpander"] {{
    background-color: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}}

details[data-testid="stExpander"] summary {{
    color: var(--text) !important;
    font-weight: 600 !important;
}}

details[data-testid="stExpander"] summary:hover {{
    color: var(--primary) !important;
}}

/* Tabs */
button[data-baseweb="tab"] {{
    color: var(--muted) !important;
    font-weight: 600 !important;
}}

button[data-baseweb="tab"][aria-selected="true"] {{
    color: var(--primary) !important;
    border-bottom-color: var(--primary) !important;
}}

/* Code Blocks */
pre, code, div[data-testid="stCodeBlock"] {{
    background-color: var(--surface-2) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
}}

/* Dataframe & Tables */
div[data-testid="stDataFrame"], div[data-testid="stTable"] {{
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    background: var(--surface) !important;
}}

/* Status Alerts */
div[data-testid="stAlert"] {{
    background-color: var(--surface-2) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 8px !important;
}}

/* Respect Prefers Reduced Motion */
@media (prefers-reduced-motion: reduce) {{
    *, ::before, ::after {{
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
        scroll-behavior: auto !important;
    }}
    .rm-hero-map-container {{
        transition: none !important;
        transform: none !important;
    }}
}}
</style>
"""
