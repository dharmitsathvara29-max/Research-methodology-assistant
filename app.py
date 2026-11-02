"""MethodWise — Research Methodology Recommendation Assistant.
Scholarly Editorial Multi-Page Streamlit Application.
"""

import os
import sys
import errno
import secrets
from dotenv import load_dotenv

# Project Root and Dotenv Path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

DOTENV_PATH = os.path.join(PROJECT_ROOT, ".env")

# Ensure OS file descriptors 0, 1, and 2 do not crash with EIO (Errno 5) when terminal is closed/detached
def ensure_safe_std_streams():
    """Ensure OS file descriptors 0, 1, 2 and Python std streams do not crash with EIO (Errno 5) when terminal is closed."""
    devnull_fd = None
    for fd in (0, 1, 2):
        try:
            os.write(fd, b'')
        except OSError as e:
            if e.errno in (errno.EIO, errno.EBADF, errno.EPIPE, errno.ENOTTY):
                if devnull_fd is None:
                    devnull_fd = os.open(os.devnull, os.O_RDWR)
                try:
                    os.dup2(devnull_fd, fd)
                except Exception:
                    pass
    if devnull_fd is not None:
        try:
            os.close(devnull_fd)
        except Exception:
            pass
        try:
            devnull_w = open(os.devnull, "w", encoding="utf-8")
            sys.stdout = devnull_w
            sys.stderr = devnull_w
            sys.__stdout__ = devnull_w
            sys.__stderr__ = devnull_w
        except Exception:
            pass

ensure_safe_std_streams()

# Ensure stdout and stderr do not crash with [Errno 5] EIO when running headless or with detached tty
class SafeTextIO:
    """Wrap a stream to safely ignore EIO (Errno 5) and EPIPE (Errno 32) when running headless or with detached tty."""
    def __init__(self, stream):
        self._stream = stream

    def write(self, data):
        try:
            return self._stream.write(data)
        except (OSError, IOError):
            return len(data) if data else 0

    def flush(self):
        try:
            return self._stream.flush()
        except (OSError, IOError):
            pass

    def isatty(self):
        try:
            return self._stream.isatty()
        except (OSError, IOError):
            return False

    def __getattr__(self, attr):
        return getattr(self._stream, attr)

if sys.stdout is not None and not isinstance(sys.stdout, SafeTextIO):
    sys.stdout = SafeTextIO(sys.stdout)
if sys.stderr is not None and not isinstance(sys.stderr, SafeTextIO):
    sys.stderr = SafeTextIO(sys.stderr)

# Ensure environment variables are loaded and refreshed on every rerun from project root
load_dotenv(DOTENV_PATH, override=True)

import streamlit as st

# Safe stream protection check on each run
ensure_safe_std_streams()

from ui.theme import get_theme_css
from ui.components import render_html
from src.config import is_api_configured
from src.storage import init_db, cleanup_old_records

# Initialize database schema
init_db()

# Run retention cleanup on startup once per session
if "retention_cleaned" not in st.session_state:
    try:
        retention_days = int(os.getenv("RETENTION_DAYS", "30"))
        cleanup_old_records(retention_days=retention_days)
    except Exception:
        pass
    st.session_state["retention_cleaned"] = True

# Anonymous Owner ID: isolate user data per session
if "owner_id" not in st.session_state:
    st.session_state["owner_id"] = secrets.token_urlsafe(16)

# Application Page Configuration
st.set_page_config(
    page_title="MethodWise — Research Methodology Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Theme State Resolution & Synchronization
query_theme = st.query_params.get("theme", None)
if query_theme in ("light", "dark"):
    st.session_state["theme"] = query_theme
elif "theme" not in st.session_state:
    st.session_state["theme"] = "light"

active_theme = st.session_state.get("theme", "light")
st.query_params["theme"] = active_theme

# Inject Global Styling & Typography for Active Theme
st.markdown(get_theme_css(active_theme), unsafe_allow_html=True)

# Ensure Sidebar is Expanded (auto-recover if collapsed in browser localStorage)
st.html("""
<script>
try {
    Object.keys(localStorage).forEach(function(k) {
        if (k.indexOf('stSidebarCollapsed') !== -1) {
            localStorage.setItem(k, 'false');
        }
    });
    setTimeout(function() {
        var expandBtn = document.querySelector('[data-testid="stExpandSidebarButton"]');
        if (expandBtn) {
            expandBtn.click();
        }
    }, 120);
} catch (e) {}
</script>
""", unsafe_allow_javascript=True)

# Shared Global Session State Initialization
if "active_result" not in st.session_state:
    st.session_state["active_result"] = None
if "active_lab_results" not in st.session_state:
    st.session_state["active_lab_results"] = None

# Multi-Page Navigation Definition
home_page = st.Page(
    "views/home.py",
    title="Home",
    icon=":material/home:",
    url_path="",
    default=True
)

recommend_page = st.Page(
    "views/recommend.py",
    title="Recommend",
    icon=":material/lightbulb:",
    url_path="recommend"
)

prompt_lab_page = st.Page(
    "views/prompt_lab.py",
    title="Prompt Lab",
    icon=":material/science:",
    url_path="prompt-lab"
)

test_results_page = st.Page(
    "views/test_results.py",
    title="Test Results",
    icon=":material/analytics:",
    url_path="test-results"
)

automation_log_page = st.Page(
    "views/automation_log.py",
    title="Automation Log",
    icon=":material/bolt:",
    url_path="automation-log"
)

history_page = st.Page(
    "views/history.py",
    title="History",
    icon=":material/history:",
    url_path="history"
)

about_page = st.Page(
    "views/about.py",
    title="About",
    icon=":material/info:",
    url_path="about"
)

# Navigation Structure & Evidence Mode Toggle
SHOW_EVIDENCE_PAGES = os.getenv("SHOW_EVIDENCE_PAGES", "true").strip().lower() not in ("false", "0", "no", "off")

nav_sections = {
    "Explore & Design": [home_page, recommend_page, prompt_lab_page],
    "My Work": [history_page],
}
if SHOW_EVIDENCE_PAGES:
    nav_sections["Evidence & Audit"] = [test_results_page, automation_log_page]

nav_sections["Reference"] = [about_page]

pg = st.navigation(nav_sections, position="sidebar")

# Shared Sidebar Chrome
with st.sidebar:
    # Logo & Product Title
    logo_path = os.path.join(PROJECT_ROOT, "assets", "logo.svg")
    col_l1, col_l2 = st.columns([0.28, 0.72], vertical_alignment="center")
    with col_l1:
        if os.path.exists(logo_path):
            st.image(logo_path, alt="MethodWise Logo", width=42)
    with col_l2:
        render_html("""
        <div style="line-height: 1.2;">
            <strong style="font-family: 'Crimson Pro', Georgia, serif; font-size: 1.25rem; color: var(--sidebar-text); font-weight: 700; letter-spacing: -0.01em;">MethodWise</strong><br>
            <span style="font-size: 0.75rem; color: var(--muted);">Research Assistant</span>
        </div>
        """)

    # Theme Switcher Segmented Control (Light / Dark)
    theme_options = ["☀️ Light", "🌙 Dark"]
    theme_default_idx = 1 if active_theme == "dark" else 0
    selected_theme_label = st.segmented_control(
        "Appearance",
        options=theme_options,
        default=theme_options[theme_default_idx],
        label_visibility="collapsed",
        key="theme_toggle_ctrl"
    )
    new_theme = "dark" if selected_theme_label == "🌙 Dark" else "light"
    if new_theme != active_theme:
        st.session_state["theme"] = new_theme
        st.query_params["theme"] = new_theme
        st.rerun()

    render_html("<div style='margin-bottom: 12px;'></div>")

    # API Status Indicator
    api_connected = is_api_configured()
    if api_connected:
        render_html("""
        <div style="background: var(--success-subtle); border: 1px solid var(--success-border); border-radius: 8px; padding: 8px 12px; margin-bottom: 12px;">
            <span style="color: var(--success); font-weight: 700; font-size: 0.85rem;">● Gemini Connected</span>
            <div style="font-size: 0.75rem; color: var(--muted); margin-top: 2px;">Flash Model Operational</div>
        </div>
        """)
    else:
        render_html("""
        <div style="background: var(--warning-subtle); border: 1px solid var(--warning-border); border-radius: 8px; padding: 8px 12px; margin-bottom: 12px;">
            <span style="color: var(--warning); font-weight: 700; font-size: 0.85rem;">▲ API Key Missing</span>
            <div style="font-size: 0.75rem; color: var(--muted); margin-top: 2px;">Enter key below or add to .env</div>
        </div>
        """)
        sidebar_key = st.text_input("Enter GEMINI_API_KEY", type="password", key="sidebar_gemini_key")
        if sidebar_key:
            os.environ["GEMINI_API_KEY"] = sidebar_key
            st.rerun()

    # Limitations & Academic Advisory Expander
    with st.expander("Advisory & Limitations", expanded=False):
        st.caption(
            "• Decision support system only; does not supersede faculty committee supervision.\n"
            "• Institutional Review Board (IRB) / REC approval remains mandatory.\n"
            "• Zero fabricated literature citations or statistics rule enforced.\n"
            "• Local data privacy: all queries can be purged in History."
        )

    # Session Privacy Status (masked owner_id, never shown in full)
    curr_owner = st.session_state.get("owner_id", "")
    masked_owner = f"{curr_owner[:4]}...{curr_owner[-4:]}" if len(curr_owner) >= 8 else "Private"
    render_html(f"""
    <div style="background: var(--sidebar-surface); border: 1px solid var(--border); border-radius: 6px; padding: 6px 10px; margin-bottom: 8px;">
        <span style="color: var(--muted); font-size: 0.72rem;">🔒 Session Isolated: <code>{masked_owner}</code></span>
    </div>
    """)

    # Admin Mode: Protected by ADMIN_PASSWORD from .env, never shown in normal navigation
    admin_mode_enabled = os.getenv("ADMIN_MODE", "false").strip().lower() in ("true", "1", "yes")
    if admin_mode_enabled:
        with st.expander("Admin Mode", expanded=False):
            if not st.session_state.get("is_admin", False):
                admin_pwd = st.text_input("Admin Password", type="password", key="sidebar_admin_pwd")
                if st.button("Unlock Admin", key="btn_sidebar_admin_unlock", width="stretch"):
                    expected_pwd = os.getenv("ADMIN_PASSWORD", "")
                    if expected_pwd and admin_pwd == expected_pwd:
                        st.session_state["is_admin"] = True
                        st.success("Admin mode unlocked.")
                        st.rerun()
                    else:
                        st.error("Invalid credentials.")
            else:
                st.success("Admin mode active.")
                
                # Internal diagnostic dispatch control (restricted to unlocked admin session only)
                from src.config import is_gmail_configured, get_gmail_address
                from src.storage import mask_email
                from src.emailer import send_report_email

                if is_gmail_configured():
                    gmail_addr = get_gmail_address()
                    render_html(f"""
                    <div style="background: var(--primary-subtle); border: 1px solid var(--primary-border); border-radius: 8px; padding: 8px 12px; margin-bottom: 8px;">
                        <span style="color: var(--primary); font-weight: 700; font-size: 0.85rem;">✉️ Gmail Automated</span>
                        <div style="font-size: 0.72rem; color: var(--muted); margin-top: 2px;">{mask_email(gmail_addr)}</div>
                    </div>
                    """)
                    if st.button("Send Test Email", key="sidebar_test_email", width="stretch"):
                        with st.spinner("Dispatching test email..."):
                            reports_dir = os.path.join(PROJECT_ROOT, "reports")
                            os.makedirs(reports_dir, exist_ok=True)
                            test_pdf_path = os.path.join(reports_dir, "test_verification_report.pdf")
                            from src.pdf_report import save_pdf
                            save_pdf(
                                {"run_id": "test-verif-01", "research_question": "System Verification: MethodWise Automated Dispatch", "discipline": "Computer Science"},
                                None, None, output_path=test_pdf_path
                            )
                            test_res = send_report_email(
                                recipient=gmail_addr,
                                run_record={"run_id": "test-verif-01", "research_question": "System Verification: MethodWise Automated Dispatch"},
                                pdf_path=test_pdf_path,
                                summary={"paradigm": "Quantitative", "design": "System Dispatch Test", "confidence": "High", "label": "PASS", "roadmap_preview": ["Verification Step 1: SMTP delivery"]},
                                session_id="sidebar_test"
                            )
                            if test_res["status"] == "SENT":
                                st.success(f"Sent! Check inbox ({mask_email(gmail_addr)}).")
                            else:
                                st.error(f"Dispatch notice: {test_res.get('error')}")

                if st.button("Lock / Exit Admin", key="btn_sidebar_admin_lock", width="stretch"):
                    st.session_state["is_admin"] = False
                    st.rerun()

# Execute the routed page
pg.run()
