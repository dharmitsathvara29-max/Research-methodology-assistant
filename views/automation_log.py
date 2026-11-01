"""Automation Execution Log View for MethodWise: Verifiable Trigger-Action Audit Trail.
Aesthetic Direction: Scholarly Editorial (Typeset Research Journal × Modern Dashboard).
"""

import os
import pandas as pd
import streamlit as st

from ui.components import (
    render_page_header, render_footer, render_empty_state,
    render_badge, render_html, get_svg_icon
)
from src.storage import get_execution_logs, is_safe_owner_path

render_page_header(
    title="Automation & Execution Audit Log",
    description="For system administrators and compliance auditors: verifiable trigger-action audit trail documenting automated validation triggers, PDF generation, and Gmail dispatches.",
    breadcrumb="Automation Engine"
)

# 5-Step Visual Flow Graphic: Trigger → Validation → Generate PDF → Send Gmail → Log
render_html(f"""
<div class="rm-card" style="margin-bottom: 24px;">
    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 14px;">
        <span style="color: var(--primary);">{get_svg_icon('sparkles', size=20, color='var(--primary)')}</span>
        <h4 style="font-family: 'Crimson Pro', Georgia, serif; font-size: 1.25rem; font-weight: 700; color: var(--text); margin: 0;">
            Autonomous 5-Step Trigger-Action Pipeline
        </h4>
    </div>
    <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; text-align: center;">
        <div style="background: var(--surface); border: 1px solid var(--border); padding: 12px 8px; border-radius: 8px;">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; font-weight: 700; color: var(--muted); text-transform: uppercase;">1. Trigger</div>
            <div style="font-family: 'Crimson Pro', Georgia, serif; font-weight: 700; color: var(--text); font-size: 0.95rem; margin-top: 4px;">Stage 3 Complete</div>
            <div style="font-size: 0.78rem; color: var(--muted); margin-top: 2px;">Evaluation finishes</div>
        </div>
        <div style="background: var(--surface); border: 1px solid var(--border); padding: 12px 8px; border-radius: 8px;">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; font-weight: 700; color: var(--accent); text-transform: uppercase;">2. Validation</div>
            <div style="font-family: 'Crimson Pro', Georgia, serif; font-weight: 700; color: var(--text); font-size: 0.95rem; margin-top: 4px;">Score ≥ 75%?</div>
            <div style="font-size: 0.78rem; color: var(--muted); margin-top: 2px;">Threshold evaluated</div>
        </div>
        <div style="background: var(--primary-subtle); border: 1.5px solid var(--primary-border); padding: 12px 8px; border-radius: 8px;">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; font-weight: 700; color: var(--primary); text-transform: uppercase;">3. Generate PDF</div>
            <div style="font-family: 'Crimson Pro', Georgia, serif; font-weight: 700; color: var(--primary); font-size: 0.95rem; margin-top: 4px;">ReportLab Build</div>
            <div style="font-size: 0.78rem; color: var(--primary); margin-top: 2px;">Saved to reports/</div>
        </div>
        <div style="background: var(--surface-2); border: 1px solid var(--accent); padding: 12px 8px; border-radius: 8px;">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; font-weight: 700; color: var(--accent); text-transform: uppercase;">4. Send Gmail</div>
            <div style="font-family: 'Crimson Pro', Georgia, serif; font-weight: 700; color: var(--accent); font-size: 0.95rem; margin-top: 4px;">SMTP_SSL:465</div>
            <div style="font-size: 0.78rem; color: var(--muted); margin-top: 2px;">Attached PDF email</div>
        </div>
        <div style="background: var(--surface-2); border: 1px solid var(--success); padding: 12px 8px; border-radius: 8px;">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; font-weight: 700; color: var(--success); text-transform: uppercase;">5. Audit Log</div>
            <div style="font-family: 'Crimson Pro', Georgia, serif; font-weight: 700; color: var(--success); font-size: 0.95rem; margin-top: 4px;">SQLite & CSV</div>
            <div style="font-size: 0.78rem; color: var(--muted); margin-top: 2px;">Masked privacy log</div>
        </div>
    </div>
</div>
""")

owner_id = st.session_state.get("owner_id", "")
is_admin = st.session_state.get("is_admin", False)

# Query Execution Logs from Database (filtered strictly by owner_id)
exec_logs = get_execution_logs(owner_id=owner_id, is_admin=is_admin)

if not exec_logs:
    render_empty_state(
        icon_name="sparkles",
        title="No Automation Events Recorded",
        message="The trigger-action engine logs every completed recommendation run. Generate a recommendation to inspect verifiable audit entries.",
        cta_text="Generate a Recommendation",
        cta_page="views/recommend.py"
    )
else:
    # Filter Controls
    c_f1, c_f2 = st.columns([1, 2])
    with c_f1:
        action_filter = st.selectbox("Filter by Action Type", ["All", "PDF_GENERATED", "EMAIL_SENT", "PIPELINE_COMPLETE", "REJECTION"])

    filtered_logs = exec_logs
    if action_filter != "All":
        filtered_logs = [l for l in exec_logs if l.get("action_type") == action_filter]

    # Verification Note Card
    render_html("""
    <div style="background: var(--surface-2); border: 1px solid var(--border); border-radius: 6px; padding: 10px 14px; margin-bottom: 16px; font-size: 0.88rem; color: var(--muted);">
        <strong>Verification Tip:</strong> If an email was dispatched, you can confirm delivery by checking your Gmail <em>Sent</em> folder or recipient inbox for the attached PDF report.
    </div>
    """)

    # Render formatted table
    log_rows = []
    for l in filtered_logs:
        log_rows.append({
            "Run ID": l["run_id"][:8] if l.get("run_id") else "N/A",
            "Timestamp": l["timestamp"][:19].replace("T", " "),
            "Action Type": l.get("action_type") or "AUTOMATION",
            "Action Taken": l["action_taken"],
            "Recipient": l.get("recipient_masked") or "None",
            "Email Status": l.get("email_status") or "N/A",
            "Status": l["status"],
            "Duration (s)": f"{l.get('duration_ms', 0) / 1000:.2f}s",
            "Output File": os.path.basename(l["output_file_path"]) if l.get("output_file_path") else "None"
        })

    render_html(f"""
    <div style="margin: 20px 0 12px 0;">
        <h4 style="font-family: 'Crimson Pro', Georgia, serif; font-size: 1.35rem; font-weight: 700; color: var(--text); margin: 0 0 4px 0;">
            Execution Audit Trail ({len(filtered_logs)} Events)
        </h4>
        <p style="font-size: 0.88rem; color: var(--muted); margin: 0;">Immutable records of pipeline triggers, decisions, PDF generation, and Gmail dispatches.</p>
    </div>
    """)

    st.dataframe(pd.DataFrame(log_rows), width="stretch", hide_index=True)

    render_html("<div style='margin-top: 28px;'></div>")
    st.divider()

    # Interactive Deliverable Proof Inspector
    render_html("""
    <div style="margin: 20px 0 12px 0;">
        <h4 style="font-family: 'Crimson Pro', Georgia, serif; font-size: 1.35rem; font-weight: 700; color: var(--text); margin: 0 0 4px 0;">
            Inspect Generated Deliverable Proof (PDF & Markdown)
        </h4>
        <p style="font-size: 0.88rem; color: var(--muted); margin: 0;">Select any compiled methodology report to verify autonomous disk persistence and download directly.</p>
    </div>
    """)

    # Collect available reports (both markdown and pdf) ensuring safe owner path
    available_files = []
    for l in exec_logs:
        for path_key in ("output_file_path", "pdf_path"):
            p = l.get(path_key)
            if p and is_safe_owner_path(p, owner_id=owner_id, is_admin=is_admin) and os.path.exists(p) and p not in available_files:
                available_files.append(p)

    available_files = sorted(available_files, reverse=True)

    if available_files:
        selected_file_path = st.selectbox(
            "Select Deliverable Artifact",
            available_files,
            format_func=lambda x: f"[{'PDF' if x.endswith('.pdf') else 'MD'}] {os.path.basename(x)} ({os.path.getsize(x):,} bytes)"
        )

        if selected_file_path and is_safe_owner_path(selected_file_path, owner_id=owner_id, is_admin=is_admin) and os.path.exists(selected_file_path):
            c_down, c_path = st.columns([1, 2], vertical_alignment="center")
            is_pdf = selected_file_path.endswith(".pdf")
            
            with open(selected_file_path, "rb") as f:
                file_bytes = f.read()

            with c_down:
                st.download_button(
                    label=f"Download {os.path.basename(selected_file_path)}",
                    data=file_bytes,
                    file_name=os.path.basename(selected_file_path),
                    mime="application/pdf" if is_pdf else "text/markdown",
                    type="primary",
                    width="stretch",
                    key="btn_download_deliverable_proof"
                )
            with c_path:
                st.caption(f"Physical Path: `{selected_file_path}`")

            if not is_pdf:
                with st.expander("View Full Markdown Content", expanded=True):
                    st.markdown(file_bytes.decode("utf-8", errors="replace"))
            else:
                st.caption("PDF document verified on disk. Click the button above to download and inspect.")
    else:
        st.info("No report files currently available on disk.")

render_footer()
