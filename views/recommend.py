"""Methodology Recommendation Engine View for MethodWise.
Presents the complete 4-Stage Pipeline, Scholarly Editorial 'Methodology Brief', PDF Export, and Gmail Automation.
"""

import os
import json
import time
import html
import secrets
import pandas as pd
import streamlit as st

from ui.components import (
    render_page_header, render_badge, render_footer,
    render_evidence_ribbon, render_confidence_meter,
    render_ethics_callout, render_roadmap_timeline,
    render_html, clean_html,
    get_svg_icon
)
from ui.charts import create_score_gauge, create_rubric_horizontal_bar
from ui.theme import COLORS
from src.config import is_api_configured, is_gmail_configured
from src.pipeline import run_methodology_pipeline
from src.prompts import get_available_prompt_versions, PROMPT_DESCRIPTIONS
from src.pdf_report import build_pdf
from src.storage import get_execution_logs, mask_email, hash_email, is_safe_owner_path, sanitize_owner_id
from src.emailer import (
    validate_recipient,
    generate_otp_code,
    create_otp_record,
    verify_otp_code,
    send_otp_email
)

# Ensure persistent owner_id for privacy isolation
if "owner_id" not in st.session_state:
    st.session_state["owner_id"] = secrets.token_urlsafe(16)

owner_id = st.session_state["owner_id"]
session_id = owner_id

render_page_header(
    title="Methodology Recommendation Engine",
    description="Formulate an epistemologically defensible, publication-grade research design calibrated to your inquiry and practical constraints.",
    breadcrumb="Recommendation Generator"
)

# Check API Configuration
api_ready = is_api_configured()
if not api_ready:
    render_html("""
    <div class="rm-alert-warning" style="margin-bottom: 24px;">
        <h4 style="margin: 0 0 6px 0; font-family: 'Crimson Pro', Georgia, serif; font-size: 1.25rem; font-weight: 700; color: var(--warning);">
            Gemini API Key Required
        </h4>
        <p style="margin: 0 0 12px 0; font-size: 0.95rem; color: var(--text); line-height: 1.5;">
            To generate methodologies and execute automated rubric validation, configure your Google Gemini API key.
        </p>
        <ol style="margin: 0; padding-left: 20px; font-size: 0.9rem; color: var(--muted); line-height: 1.6;">
            <li>Acquire an API key from <a href="https://aistudio.google.com/" target="_blank" style="color: var(--primary); font-weight: 600;">Google AI Studio</a>.</li>
            <li>Add <code>GEMINI_API_KEY=your_key_here</code> to your local <code>.env</code> file.</li>
            <li>Or enter your key temporarily in the sidebar configuration panel.</li>
        </ol>
    </div>
    """)

# Pre-filled values from Home page or session state
prefill_q = st.session_state.pop("prefill_question", "")
prefill_d = st.session_state.pop("prefill_discipline", "Psychology & Behavioral Sciences")
prefill_c = st.session_state.pop("prefill_constraints", {})

# Two-column layout: Form vs "What you'll receive" preview
col_form, col_guide = st.columns([1.18, 0.82], gap="large")

with col_form:
    st.markdown("### 1. Research Question & Parameters")
    
    rq_input = st.text_area(
        "Research Question *",
        value=prefill_q,
        placeholder="e.g., Does daily sleep duration affect exam performance among undergraduate students?",
        height=105,
        help="Formulate a clear academic inquiry identifying the core relationship or phenomenon."
    )
    st.caption("Identify independent/dependent variables or qualitative phenomena explicitly.")

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        discipline_list = [
            "Psychology & Behavioral Sciences",
            "Education & Educational Technology",
            "Medicine, Nursing & Public Health",
            "Sociology & Anthropology",
            "Business, Economics & Management",
            "Computer Science, Data Science & AI",
            "Environmental & Biological Sciences",
            "Political Science & International Relations",
            "Engineering & Physical Sciences",
            "Other"
        ]
        default_d_idx = discipline_list.index(prefill_d) if prefill_d in discipline_list else 0
        discipline_choice = st.selectbox("Discipline / Field", discipline_list, index=default_d_idx)
        other_discipline = ""
        if discipline_choice == "Other":
            other_discipline = st.text_input("Specify Discipline", placeholder="e.g., Media Studies")

    with col_f2:
        prompt_versions = get_available_prompt_versions()
        selected_prompt = st.selectbox(
            "Prompt Engine",
            prompt_versions,
            index=0,
            format_func=lambda x: f"{x} (Recommended)" if "v3" in x else x,
            help=PROMPT_DESCRIPTIONS.get("v3_decomposed", "")
        )

    with st.expander("Optional Research Constraints", expanded=bool(prefill_c)):
        st.caption("Specify boundaries to calibrate sampling feasibility, power, and milestones.")
        c1, c2 = st.columns(2)
        with c1:
            time_opts = ["Standard (6-12 months)", "Short (< 3 months)", "Semester (3-5 months)", "Multi-year (2+ years)"]
            time_idx = time_opts.index(prefill_c["time"]) if prefill_c.get("time") in time_opts else 0
            time_constraint = st.selectbox("Timeframe", time_opts, index=time_idx)

            budget_opts = ["Minimal / Zero (< $500)", "Moderate ($500 - $3,000)", "Grant Funded ($5,000+)"]
            budget_idx = budget_opts.index(prefill_c["budget"]) if prefill_c.get("budget") in budget_opts else 0
            budget_constraint = st.selectbox("Budgetary Resources", budget_opts, index=budget_idx)

            sample_constraint = st.selectbox(
                "Sample Access",
                ["University Subject Pool", "General Public (Online / Prolific)", "Clinical / Hospital Cohort", "K-12 School Classrooms", "Corporate Professionals", "Protected / Vulnerable Group"]
            )
        with c2:
            ethical_constraint = st.selectbox(
                "Ethical Sensitivity",
                ["Standard / Low Risk", "Moderate (Workplace attitudes/personal)", "High (Trauma, minors, patients)"]
            )
            data_constraint = st.selectbox(
                "Data Collection Type",
                ["Primary Collection Required", "Secondary Data Available", "Hybrid Collection"]
            )
            skill_opts = ["Intermediate (Mixed / General)", "Novice Researcher", "Advanced Quantitative", "Advanced Qualitative"]
            skill_idx = skill_opts.index(prefill_c["skill_level"]) if prefill_c.get("skill_level") in skill_opts else 0
            skill_constraint = st.selectbox("Researcher Skillset", skill_opts, index=skill_idx)

    # Multi-User Email Delivery & OTP Verification Section
    render_html("<div style='margin-top: 14px;'></div>")
    email_opt_in = st.checkbox(
        "Email me the PDF report",
        value=False,
        help="Automatically deliver publication-grade PDF methodology brief directly to any verified recipient address."
    )
    
    recipient_email = ""
    is_verified = False
    
    if email_opt_in:
        render_html("""
        <div style="background: var(--surface-2); border: 1px solid var(--border); border-radius: 6px; padding: 10px 14px; margin-bottom: 12px; font-size: 0.85rem; color: var(--muted); line-height: 1.5;">
            <strong>Automated Multi-User Dispatch:</strong> The app delivers from our configured sender account directly to your entered address. End users never need Gmail credentials.
        </div>
        """)

        recipient_email = st.text_input(
            "Recipient Email Address *",
            placeholder="e.g., researcher@university.edu",
            help="Enter your personal or university address to receive the PDF report."
        )

        render_html("""
        <div style="font-size: 0.82rem; color: var(--muted); margin-top: -6px; margin-bottom: 12px;">
            🔒 <em>Consent & Privacy:</em> Your email is used only to send this report and is not stored. We only record a masked address and an irreversible cryptographic hash for rate limiting.
        </div>
        """)

        norm_email = recipient_email.strip().lower()
        verified_session_email = st.session_state.get("verified_email")
        is_verified = bool(norm_email and verified_session_email == norm_email)

        if not is_gmail_configured():
            render_html("""
            <div style="background: var(--surface-2); border: 1px solid var(--border); border-left: 4px solid var(--accent); border-radius: 6px; padding: 10px 12px; margin: 8px 0; font-size: 0.85rem; color: var(--text); line-height: 1.5;">
                <strong style="color: var(--accent);">Sender Notice:</strong> System sender credentials (<code>GMAIL_ADDRESS</code> + <code>GMAIL_APP_PASSWORD</code>) are not yet configured in <code>.env</code>.
                You can test locally using simulated verification below, or uncheck the email option to download your PDF report directly on-screen.
            </div>
            """)
            with st.expander("ℹ️ Setup Guide: How to connect Gmail in .env (1 minute)", expanded=False):
                st.markdown("""
                MethodWise sends from **one** centralized sender account to any researcher:
                1. Open your **Google Account Security** settings (`https://myaccount.google.com/security`).
                2. Ensure **2-Step Verification** is turned ON.
                3. Go to **App Passwords** (`https://myaccount.google.com/apppasswords`).
                4. Enter app name `MethodWise` and click **Create** to receive a 16-character password (e.g. `abcd efgh ijkl mnop`).
                5. Add to your `.env` file:
                ```env
                GMAIL_ADDRESS=your.email@gmail.com
                GMAIL_APP_PASSWORD=abcdefghijklmnop
                ```
                6. Once added, automated emails will dispatch to any verified recipient inbox!
                """)

        if norm_email:
            if is_verified:
                render_html(f"""
                <div style="background: var(--surface-2); border: 1px solid var(--success); border-radius: 6px; padding: 8px 12px; margin-bottom: 14px; display: flex; align-items: center; justify-content: space-between;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="color: var(--success);">{get_svg_icon('check-circle', size=16, color='var(--success)')}</span>
                        <span style="color: var(--text); font-size: 0.88rem; font-weight: 600;">Verified: <code>{html.escape(mask_email(norm_email))}</code></span>
                    </div>
                    <span style="background: var(--surface); color: var(--success); border: 1px solid var(--success); font-size: 0.75rem; padding: 2px 8px; border-radius: 4px; font-weight: 700;">VERIFIED</span>
                </div>
                """)
            else:
                col_otp_btn, col_otp_stat = st.columns([1.2, 1], vertical_alignment="center")
                with col_otp_btn:
                    if st.button("Send verification code", key="btn_send_otp_code", type="secondary", width="stretch"):
                        valid_e, err_e = validate_recipient(norm_email)
                        if not valid_e:
                            st.error(err_e)
                        else:
                            with st.spinner("Dispatching 6-digit verification code..."):
                                otp_val = generate_otp_code()
                                st.session_state["otp_store"] = create_otp_record(norm_email, otp_val)
                                send_res = send_otp_email(norm_email, otp_val, session_id=session_id)
                                if send_res.get("status") == "SENT":
                                    st.success(f"Verification code sent to {mask_email(norm_email)}! Valid for 10 minutes.")
                                    st.session_state.pop("dev_sim_code", None)
                                    st.rerun()
                                elif send_res.get("status") == "RATE_LIMITED_OTP":
                                    st.warning(send_res.get("error"))
                                elif send_res.get("status") == "SKIPPED_NO_CREDENTIALS":
                                    st.session_state["dev_sim_code"] = otp_val
                                    st.rerun()
                                else:
                                    st.error(f"Dispatch notice: {send_res.get('error')}")

                dev_code = st.session_state.get("dev_sim_code")
                if dev_code and not is_gmail_configured():
                    render_html(f"""
                    <div style="background: var(--surface-2); border: 1px solid var(--border); border-left: 4px solid var(--primary); border-radius: 6px; padding: 10px 14px; margin: 10px 0;">
                        <strong style="color: var(--primary); font-size: 0.9rem;">🧪 Local Development / Testing Mode:</strong><br>
                        <span style="font-size: 0.85rem; color: var(--text); line-height: 1.5;">
                            Gmail credentials are not configured in <code>.env</code>. For immediate local testing, your verification code is:
                            <strong style="font-family: monospace; font-size: 1.15rem; color: var(--primary); letter-spacing: 2px;">{html.escape(str(dev_code))}</strong>.
                            Enter this code below to proceed, or uncheck the email option to download your PDF report on-screen.
                        </span>
                    </div>
                    """)

                otp_rec = st.session_state.get("otp_store")
                if otp_rec and otp_rec.get("email_hash") == hash_email(norm_email):
                    render_html("<div style='margin-top: 8px;'></div>")
                    c_code, c_vbtn = st.columns([1.2, 1], vertical_alignment="bottom")
                    with c_code:
                        entered_code = st.text_input("Enter 6-Digit Code", max_chars=6, placeholder="123456", key="input_otp_code")
                    with c_vbtn:
                        if st.button("Verify Code", key="btn_verify_otp_submit", type="primary", width="stretch"):
                            ok_v, msg_v = verify_otp_code(otp_rec, entered_code, norm_email)
                            if ok_v:
                                st.session_state["verified_email"] = norm_email
                                st.session_state.pop("otp_store", None)
                                st.session_state.pop("dev_sim_code", None)
                                st.success("Verification successful! You can now generate and receive your report.")
                                st.rerun()
                            else:
                                st.error(msg_v)

    render_html("<div style='margin-top: 16px;'></div>")
    submit_btn = st.button("Generate Methodology Specification", type="primary", width="stretch", key="btn_submit_recommend")

with col_guide:
    st.markdown("### 2. What You'll Receive")
    render_html(f"""
    <div class="rm-card" style="background: var(--surface); border: 1px solid var(--border);">
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
            <span style="color: var(--primary);">{get_svg_icon('document', size=20, color='var(--primary)')}</span>
            <h4 style="font-family: 'Crimson Pro', Georgia, serif; font-size: 1.25rem; font-weight: 700; color: var(--text); margin: 0;">
                Publication-Grade Specification
            </h4>
        </div>
        <ul style="padding-left: 20px; font-size: 0.9rem; color: var(--muted); line-height: 1.65; margin: 0;">
            <li><strong>Parsed Scope:</strong> Categorizes inquiry type & extracts operational variables.</li>
            <li><strong>Paradigm & Design:</strong> Epistemologically justified design (RCT, IPA, Convergent, etc.).</li>
            <li><strong>Power Rationale:</strong> Statistical power (G*Power) or saturation criteria.</li>
            <li><strong>Analytical Framework:</strong> Exact statistical models or qualitative coding strategies.</li>
            <li><strong>Ethics & Oversight:</strong> Mandatory IRB/REC evaluation & vulnerable population alerts.</li>
            <li><strong>Alternative Designs:</strong> 1-2 realistic alternatives with exclusion trade-offs.</li>
            <li><strong>Phased Roadmap:</strong> Actionable milestone-by-milestone schedule.</li>
            <li><strong>Validation Scorecard:</strong> Independent LLM judge rubric + reference verification.</li>
            <li><strong>Multi-Format Deliverables:</strong> Downloadable PDF report, Markdown summary, and JSON specification.</li>
        </ul>
    </div>
    """)

# Execute Recommendation Generation
if submit_btn:
    if not rq_input.strip():
        st.warning("Please provide a research question before generating a recommendation.")
    elif email_opt_in and not recipient_email.strip():
        st.warning("Please enter a recipient email address or uncheck the email option.")
    elif email_opt_in and not is_verified:
        st.warning(f"Please verify your email address ({mask_email(norm_email)}) using the 6-digit verification code above before requesting automated delivery, or uncheck the email option to download the PDF on-screen.")
    elif not api_ready:
        st.error("Cannot proceed: Please configure GEMINI_API_KEY in .env or the sidebar.")
    else:
        final_disc = other_discipline.strip() if discipline_choice == "Other" and other_discipline else discipline_choice
        owner_id = st.session_state.get("owner_id", "default_session")
        constraints_dict = {
            "owner_id": owner_id,
            "time": time_constraint,
            "budget": budget_constraint,
            "sample_access": sample_constraint,
            "ethical_sensitivity": ethical_constraint,
            "data_availability": data_constraint,
            "skill_level": skill_constraint,
            "email_opt_in": email_opt_in,
            "recipient_email": norm_email if email_opt_in else None,
            "email_verified": is_verified if email_opt_in else False,
            "session_id": owner_id
        }

        with st.status("Executing 4-Stage Methodology Pipeline...", expanded=True) as status_box:
            st.write("🔍 **Stage 1 of 4:** Validating question integrity & extracting variables...")
            time.sleep(0.3)
            
            def _apply_stream_protection():
                """Defensive OS stream and Python standard I/O protection against detached terminal EIO (Errno 5)."""
                devnull_fd = None
                for fd in (0, 1, 2):
                    try:
                        os.write(fd, b'')
                    except OSError as _oe:
                        if _oe.errno in (5, 9, 32, 25):  # EIO, EBADF, EPIPE, ENOTTY
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

            try:
                _apply_stream_protection()
                try:
                    pipeline_result = run_methodology_pipeline(
                        research_question=rq_input,
                        discipline=final_disc,
                        constraints=constraints_dict,
                        prompt_version=selected_prompt
                    )
                except OSError as _oe_run:
                    if _oe_run.errno in (5, 9, 32):
                        _apply_stream_protection()
                        pipeline_result = run_methodology_pipeline(
                            research_question=rq_input,
                            discipline=final_disc,
                            constraints=constraints_dict,
                            prompt_version=selected_prompt
                        )
                    else:
                        raise
                
                if getattr(pipeline_result, "status", None) == "REJECTED_INPUT":
                    st.write("⚠️ **Stage 1 (Screening):** Input question requires refinement before methodology generation.")
                    status_box.update(label="Input Screening: Refinement Required", state="complete", expanded=False)
                else:
                    st.write("📐 **Stage 2 of 4:** Formulating end-to-end design & sampling calculations...")
                    st.write("⚖️ **Stage 3 of 4:** Validating against LLM-as-judge rubric & reference cases...")
                    if getattr(pipeline_result, "refinement_iterations", 0) > 0:
                        st.write("🔄 **Stage 4 (Refinement):** Executing automated revision based on evaluator critique...")
                    st.write("📄 **Stage 4 (Export):** Generating publication-grade PDF report...")
                    if email_opt_in and is_verified:
                        st.write(f"✉️ **Stage 4 (Email):** Executing automated dispatch to {mask_email(norm_email)}...")
                    st.write("📦 **Stage 4 of 4:** Compiling deliverable report & persisting audit records...")
                    status_box.update(label="Methodology Analysis Completed Successfully", state="complete", expanded=False)
                st.session_state["active_result"] = pipeline_result
            except Exception as e:
                import traceback
                status_box.update(label="Pipeline Execution Encountered an Issue", state="error")
                st.error(f"Execution Error: {e}")
                with st.expander("Diagnostic Traceback & Actionable Guidance", expanded=False):
                    st.code(traceback.format_exc())
                    if "Errno 5" in str(e):
                        st.info("💡 **Terminal Detachment Notice:** The background terminal session running Streamlit was detached or closed. Automatic stdout/stderr redirection has now been applied. Please re-click Generate, or restart Streamlit (`streamlit run app.py`) in an active terminal.")

# Display Active Results
res = st.session_state.get("active_result")
if res is not None:
    render_html("<div style='margin-top: 36px;'></div>")
    st.divider()

    # --- Case 1: Rejected Input (Edge Case Refusal) ---
    if getattr(res, "status", None) == "REJECTED_INPUT":
        reason_text = getattr(res, "error_message", None) or "The input does not meet academic research criteria."
        render_html(f"""
        <div class="rm-alert-warning" style="margin-bottom: 20px;">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                <span style="color: var(--warning);">{get_svg_icon('alert', size=20, color='var(--warning)')}</span>
                <h4 style="margin: 0; font-family: 'Crimson Pro', Georgia, serif; font-size: 1.25rem; font-weight: 700; color: var(--warning);">
                    Research Question Requires Clarification
                </h4>
            </div>
            <p style="margin: 0; font-size: 0.95rem; color: var(--text); line-height: 1.5;">
                <strong>Reason:</strong> {html.escape(reason_text)}
            </p>
        </div>
        """)

        if getattr(res, "parsed_question", None) and getattr(res.parsed_question, "clarification_suggestions", None):
            st.markdown("#### Recommendations to Formulate an Actionable Academic Question:")
            for sug in res.parsed_question.clarification_suggestions:
                st.markdown(f"- {sug}")

        st.caption("The system gracefully refuses malformed inputs to prevent hallucinated methodologies.")

    # --- Case 2: Valid Recommendation (Methodology Brief) ---
    elif getattr(res, "recommendation", None) and getattr(res, "evaluation", None):
        rec = res.recommendation
        eval_res = res.evaluation

        # Email delivery confirmation badge if attempted
        exec_logs = get_execution_logs(
            owner_id=st.session_state.get("owner_id"),
            is_admin=st.session_state.get("is_admin", False)
        )
        res_run_id = getattr(res, "run_id", "")
        email_log = next((l for l in exec_logs if l.get("run_id") == res_run_id and l.get("action_type") == "EMAIL_SENT"), None)
        if email_log:
            e_status = email_log.get("email_status")
            if e_status == "SENT":
                render_html(f"""
                <div class="rm-card" style="background: var(--surface-2); border: 1px solid var(--success); padding: 12px 16px; margin-bottom: 20px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="color: var(--success);">{get_svg_icon('check-circle', size=18, color='var(--success)')}</span>
                        <strong style="color: var(--success); font-size: 0.95rem;">Automated Email Delivered:</strong>
                        <span style="color: var(--text); font-size: 0.9rem;">The PDF report was successfully dispatched to <code>{html.escape(str(email_log.get('recipient_masked')))}</code>. Status: <strong>SENT</strong>. Check your inbox and spam folder.</span>
                    </div>
                </div>
                """)
            elif e_status == "UNVERIFIED":
                render_html("""
                <div class="rm-card" style="background: var(--surface-2); border: 1px solid var(--accent); padding: 12px 16px; margin-bottom: 20px;">
                    <strong style="color: var(--accent); font-size: 0.95rem;">Email Dispatch Notice (UNVERIFIED):</strong>
                    <span style="color: var(--text); font-size: 0.9rem;">Recipient address was not verified via OTP code; automated email delivery was skipped. Download your PDF report directly below.</span>
                </div>
                """)
            elif e_status and "RATE_LIMITED" in str(e_status):
                render_html(f"""
                <div class="rm-card" style="background: var(--surface-2); border: 1px solid var(--accent); padding: 12px 16px; margin-bottom: 20px;">
                    <strong style="color: var(--accent); font-size: 0.95rem;">Email Rate Limit Notice:</strong>
                    <span style="color: var(--text); font-size: 0.9rem;">Dispatch rate limit reached ({html.escape(str(e_status))}). Your publication-grade PDF report is available for immediate download below.</span>
                </div>
                """)
            elif e_status == "FAILED":
                render_html("""
                <div class="rm-card" style="background: var(--surface-2); border: 1px solid var(--danger); padding: 12px 16px; margin-bottom: 20px;">
                    <strong style="color: var(--danger); font-size: 0.95rem;">Email Dispatch Notice:</strong>
                    <span style="color: var(--text); font-size: 0.9rem;">Automated delivery was not completed. Use the button below to download your PDF directly.</span>
                </div>
                """)

        # Conditional Ethics Marginal Callout
        is_vuln = getattr(rec, "vulnerable_population_flag", False)
        is_irb = getattr(rec, "irb_ethics_board_required", False)
        if is_vuln or is_irb:
            vuln_text = (
                "This study engages a sensitive cohort or collects high-risk data. "
                "Enhanced participant protections (de-identification, trauma-informed consent, psychological debriefing) "
                "and formal Institutional Review Board (IRB) / Research Ethics Committee (REC) review are required."
            )
            render_ethics_callout(
                message=vuln_text,
                is_vulnerable=is_vuln,
                is_irb_required=is_irb
            )

        # Signature Abstract Header Card
        rec_paradigm = getattr(rec, "recommended_paradigm", "Methodology")
        paradigm_badge = render_badge(rec_paradigm, "indigo", icon_name="compass")
        eval_label = getattr(eval_res, "label", "REVIEW")
        label_variant = "pass" if eval_label == "PASS" else ("review" if eval_label == "REVIEW" else "fail")
        label_badge = render_badge(eval_label, label_variant, icon_name="check-circle" if eval_label == "PASS" else "alert")
        conf_meter = render_confidence_meter(getattr(rec, "confidence_level", 0.8))

        render_html(f"""
        <div class="rm-card-highlight">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px; margin-bottom: 12px;">
                <div style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
                    {label_badge}
                    {paradigm_badge}
                </div>
                <div>{conf_meter}</div>
            </div>
            <h2 style="font-family: 'Crimson Pro', Georgia, serif; font-size: 2.1rem; font-weight: 700; color: var(--text); margin: 0 0 12px 0;">
                {html.escape(str(getattr(rec, 'research_design', 'Research Design')))}
            </h2>
            <div style="font-style: italic; font-size: 1.05rem; line-height: 1.6; color: var(--muted); margin-bottom: 16px; border-left: 3px solid var(--primary); padding-left: 14px;">
                "{html.escape(str(getattr(rec, 'parsed_question_summary', '')))}"
            </div>
            <div style="font-size: 0.88rem; color: var(--muted);">
                <strong style="color: var(--text);">Confidence Rationale:</strong> {html.escape(str(getattr(rec, 'confidence_rationale', '')))}
            </div>
        </div>
        """)

        # Signature Evidence Ribbon
        rules_obj = getattr(eval_res, "rules", None)
        violations_count = len(rules_obj.flags) if (rules_obj and getattr(rules_obj, "flags", None)) else 0
        ref_match = getattr(eval_res, "reference_match", None)
        ref_id = getattr(ref_match, "matched_reference_id", None) if ref_match else "REF-NONE"
        ref_status = getattr(ref_match, "status", "UNCHECKED") if ref_match else "UNCHECKED"
        comp_score = float(getattr(eval_res, "composite_score", 0.0) or 0.0)

        evidence_ribbon_html = render_evidence_ribbon(
            rubric_score=comp_score,
            rubric_label=eval_label,
            ref_case_id=ref_id,
            ref_status=ref_status,
            rule_violations_count=violations_count
        )
        render_html(evidence_ribbon_html)
        render_html("<div style='margin-bottom: 24px;'></div>")

        # Tabs for Methodological Breakdown & Scorecard
        tab_scope, tab_sampling, tab_data, tab_analysis, tab_ethics, tab_alts, tab_roadmap, tab_scorecard = st.tabs([
            "1. Stance & Design",
            "2. Sampling & Power",
            "3. Data Collection",
            "4. Analysis Plan",
            "5. Ethics & Validity",
            "6. Alternatives",
            "7. Phased Roadmap",
            "Validation Scorecard"
        ])

        with tab_scope:
            st.markdown("#### Clause 1: Epistemological Scope & Paradigm Justification")
            st.info(rec.paradigm_justification)

            st.markdown("#### Clause 2: Research Design & Empirical Rationale")
            st.write(rec.design_rationale)
            
            if getattr(res, "parsed_question", None):
                pq = res.parsed_question
                c_v1, c_v2 = st.columns(2)
                with c_v1:
                    st.markdown(f"**Inquiry Nature:** `{getattr(pq, 'question_type', 'N/A').upper()}`")
                    st.markdown(f"**Target Population:** {getattr(pq, 'target_population', 'N/A')}")
                    st.markdown(f"**Contextual Setting:** {getattr(pq, 'context_setting', 'N/A')}")
                with c_v2:
                    vb = getattr(pq, "variables_and_concepts", None)
                    if vb:
                        if getattr(vb, "independent_variables", None):
                            st.markdown(f"**Independent Variables:** {', '.join(vb.independent_variables)}")
                        if getattr(vb, "dependent_variables", None):
                            st.markdown(f"**Dependent Variables:** {', '.join(vb.dependent_variables)}")
                        if getattr(vb, "qualitative_phenomena_or_concepts", None):
                            st.markdown(f"**Qualitative Constructs:** {', '.join(vb.qualitative_phenomena_or_concepts)}")

        with tab_sampling:
            st.markdown("#### Clause 3: Target Population & Sampling Strategy")
            st.write(rec.sampling_strategy)

            st.markdown("#### Clause 4: Sample Size & Statistical Power / Saturation Rationale")
            st.success(rec.sample_size_rationale)

        with tab_data:
            st.markdown("#### Clause 5: Standardized Instruments & Measurement Protocols")
            for inst in rec.data_collection_instruments:
                st.markdown(f"- {inst}")

            st.markdown("#### Clause 6: Data Collection Procedures")
            st.write(rec.data_collection_procedures)

        with tab_analysis:
            st.markdown("#### Clause 7: Prescribed Analytical Techniques")
            for tech in rec.data_analysis_techniques:
                st.markdown(f"- `{tech}`")

            st.markdown("#### Analytical Modeling Rationale")
            st.write(rec.analysis_rationale)

        with tab_ethics:
            st.markdown("#### Clause 8: Validity, Reliability & Trustworthiness Protections")
            st.write(rec.validity_and_reliability_considerations)

            st.markdown("#### Clause 9: Ethical Governance & Participant Protections")
            c_e1, c_e2 = st.columns(2)
            with c_e1:
                st.markdown(f"**Vulnerable Cohort Flag:** `{'YES' if rec.vulnerable_population_flag else 'No'}`")
            with c_e2:
                st.markdown(f"**Institutional Review Board (IRB):** `{'MANDATORY' if rec.irb_ethics_board_required else 'Standard Departmental'}`")

            for eth in rec.ethical_considerations:
                st.markdown(f"- {eth}")

        with tab_alts:
            st.markdown("#### Comparative Evaluation of Alternative Designs")
            for idx, alt in enumerate(rec.alternative_methodologies, 1):
                st.markdown(f"**Alternative {idx}: {alt.design} ({alt.paradigm})**")
                st.markdown(f"*Reason for Exclusion:* {alt.rationale_for_rejection}")
                st.divider()

        with tab_roadmap:
            st.markdown("#### Clause 10: Phased Execution Roadmap")
            render_roadmap_timeline(rec.step_by_step_roadmap)

        with tab_scorecard:
            col_sc_chart, col_sc_notes = st.columns([1.1, 0.9])
            with col_sc_chart:
                st.markdown("##### Rubric Breakdown (0-5 Scale)")
                rubric_obj = getattr(eval_res, "rubric", None)
                if rubric_obj and hasattr(rubric_obj, "model_dump"):
                    fig_rubric = create_rubric_horizontal_bar(rubric_obj.model_dump())
                    st.plotly_chart(fig_rubric, width="stretch")
                    st.caption("Direct evaluation across 5 quality dimensions by the independent LLM judge.")
                else:
                    st.info("Rubric breakdown not available.")

            with col_sc_notes:
                st.markdown("##### Composite Validation Score")
                fig_gauge = create_score_gauge(comp_score, eval_label)
                st.plotly_chart(fig_gauge, width="stretch")
                
                rubric_obj = getattr(eval_res, "rubric", None)
                verdict_str = getattr(rubric_obj, "overall_verdict", "Evaluation completed.") if rubric_obj else "Evaluation completed."
                st.markdown(f"**Evaluator Verdict:** {verdict_str}")
                ref_id_str = getattr(ref_match, "matched_reference_id", None) if ref_match else "None"
                ref_status_str = getattr(ref_match, "status", "UNCHECKED") if ref_match else "UNCHECKED"
                ref_notes_str = getattr(ref_match, "notes", "") if ref_match else ""
                st.markdown(f"**Reference Benchmark:** `{ref_status_str}` ({ref_id_str or 'None'})")
                if ref_notes_str:
                    st.caption(ref_notes_str)
                if rules_obj and getattr(rules_obj, "flags", None):
                    st.warning(f"Integrity Flags: {', '.join(rules_obj.flags)}")
                else:
                    st.success("Integrity Verified: Zero fabricated citations, power rationale verified.")

        # Academic Disclaimer
        render_html(f"""
        <div class="rm-alert-info" style="margin-top: 24px;">
            <strong>Academic Advisory Notice:</strong> {html.escape(str(getattr(rec, 'academic_disclaimer', 'Recommended methodologies should be adapted to institutional requirements and vetted by academic advisors.')))}
        </div>
        """)

        # Download Deliverables Section (PDF, Markdown, JSON)
        st.markdown("#### Export Methodology Deliverables")
        
        # Build PDF bytes once per run and cache in session state to prevent regeneration
        res_run_id = getattr(res, "run_id", "active_run")
        pdf_cache_key = f"pdf_bytes_{res_run_id}"
        if pdf_cache_key not in st.session_state:
            run_record_for_pdf = {
                "run_id": res_run_id,
                "id": res_run_id,
                "timestamp": getattr(res, "timestamp", ""),
                "research_question": getattr(res, "research_question", ""),
                "discipline": getattr(res, "discipline", ""),
                "prompt_version": getattr(res, "prompt_version", "v3_decomposed"),
                "constraints": getattr(res, "constraints", {}),
                "status": getattr(res, "status", "COMPLETED")
            }
            try:
                st.session_state[pdf_cache_key] = build_pdf(run_record_for_pdf, rec, eval_res)
            except Exception as e:
                st.session_state[pdf_cache_key] = None

        pdf_bytes = st.session_state.get(pdf_cache_key)

        d1, d2, d3 = st.columns(3)
        with d1:
            if pdf_bytes:
                st.download_button(
                    label="📄 Download PDF Report (.pdf)",
                    data=pdf_bytes,
                    file_name=f"methodology_report_{res_run_id[:8]}.pdf",
                    mime="application/pdf",
                    type="primary",
                    width="stretch",
                    key="btn_download_pdf"
                )
            else:
                st.button("📄 PDF Unavailable", disabled=True, width="stretch", key="btn_no_pdf")
        with d2:
            rep_path = getattr(res, "report_path", None)
            curr_owner = st.session_state.get("owner_id")
            if rep_path and is_safe_owner_path(rep_path, curr_owner) and os.path.exists(rep_path):
                with open(rep_path, "r", encoding="utf-8") as f:
                    md_text = f.read()
            else:
                md_text = f"# Methodology Specification\n\nQuestion: {getattr(res, 'research_question', '')}\nDesign: {getattr(rec, 'research_design', '')}"
            st.download_button(
                label="📝 Download Report (.md)",
                data=md_text,
                file_name=os.path.basename(rep_path) if rep_path else f"methodology_report_{res_run_id[:8]}.md",
                mime="text/markdown",
                type="secondary",
                width="stretch",
                key="btn_download_md"
            )
        with d3:
            dump_dict = res.model_dump() if hasattr(res, "model_dump") else {}
            st.download_button(
                label="💾 Download Spec (.json)",
                data=json.dumps(dump_dict, indent=2),
                file_name=f"methodology_spec_{res_run_id[:8]}.json",
                mime="application/json",
                type="secondary",
                width="stretch",
                key="btn_download_json"
            )

    # --- Case 3: Other Pipeline Results (e.g. Failure or Partial) ---
    else:
        err_msg = getattr(res, "error_message", None) or "The pipeline was unable to complete methodology formulation. Please check your query or API configuration."
        render_html(f"""
        <div class="rm-alert-warning" style="margin-bottom: 20px;">
            <h4 style="margin: 0 0 6px 0; font-family: 'Crimson Pro', Georgia, serif; font-size: 1.25rem; font-weight: 700; color: var(--warning);">
                Pipeline Execution Incomplete
            </h4>
            <p style="margin: 0; font-size: 0.95rem; color: var(--text); line-height: 1.5;">
                <strong>Details:</strong> {html.escape(str(err_msg))}
            </p>
        </div>
        """)

render_footer()
