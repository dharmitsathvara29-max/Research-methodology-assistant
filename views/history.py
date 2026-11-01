"""History View for MethodWise: Browse, Search, Filter, Export, and Manage Past Runs.
Aesthetic Direction: Scholarly Editorial (Typeset Research Journal × Modern Dashboard).
"""

import os
import json
import pandas as pd
import streamlit as st

from ui.components import (
    render_page_header, render_footer, render_empty_state,
    render_badge, render_html, get_svg_icon
)
from src.storage import (
    get_all_runs, delete_run, generate_owner_csv, delete_owner_data,
    is_safe_owner_path
)

render_page_header(
    title="Recommendation History & Data Storage",
    description="Browse, filter, and inspect past research methodology specifications stored locally in SQLite (data/app.db).",
    breadcrumb="Persistent Data Storage"
)

# Session Privacy Notice
render_html("""
<div style="background: var(--surface-2); border: 1px solid var(--border); border-radius: 6px; padding: 10px 14px; margin-bottom: 16px; font-size: 0.88rem; color: var(--muted);">
    🔒 <strong>Session Privacy Notice:</strong> Your history is private to this browser session and may be cleared when the session ends.
</div>
""")

owner_id = st.session_state.get("owner_id", "")
is_admin = st.session_state.get("is_admin", False)

# Search & Filter Controls
col_s1, col_s2, col_s3 = st.columns([1.5, 1, 1], gap="medium")
with col_s1:
    search_q = st.text_input("Search Inquiries", placeholder="Search keywords...")
with col_s2:
    all_disciplines = [
        "All",
        "Psychology & Behavioral Sciences",
        "Education & Educational Technology",
        "Medicine, Nursing & Public Health",
        "Sociology & Anthropology",
        "Business, Economics & Management",
        "Computer Science, Data Science & AI",
        "General Social Science"
    ]
    selected_disc = st.selectbox("Discipline Filter", all_disciplines)
with col_s3:
    selected_label = st.selectbox("Validation Outcome", ["All", "PASS", "REVIEW", "FAIL"])

# Fetch Runs strictly filtered by owner_id (parameterised query)
runs = get_all_runs(owner_id=owner_id, search=search_q, discipline=selected_disc, is_admin=is_admin)

if selected_label != "All":
    runs = [r for r in runs if r.get("label") == selected_label]

# CSV Export Row (Generated on demand from owner's rows only)
col_count, col_exp = st.columns([2, 1], vertical_alignment="center")
with col_count:
    st.markdown(f"**Showing {len(runs)} Historical Recommendations**" + (" *(Admin View)*" if is_admin else ""))
with col_exp:
    owner_csv_data = generate_owner_csv(owner_id=owner_id, is_admin=is_admin)
    st.download_button(
        "Export My CSV Audit Log",
        data=owner_csv_data,
        file_name="my_methodology_runs.csv",
        mime="text/csv",
        width="stretch"
    )

render_html("<div style='margin-bottom: 16px;'></div>")

if not runs:
    render_empty_state(
        icon_name="database",
        title="No Methodology Records Found",
        message="No historical records match your current search and filter criteria. Try clearing filters or run a new recommendation.",
        cta_text="Generate a Recommendation",
        cta_page="views/recommend.py"
    )
else:
    # Summary Table
    table_rows = []
    for r in runs:
        score_val = f"{r['final_score']:.1f}%" if r.get("final_score") is not None else "N/A"
        label_val = r.get("label", "N/A")
        table_rows.append({
            "Run ID": r["id"][:8],
            "Timestamp": r["timestamp"][:19].replace("T", " "),
            "Research Question": r["research_question"][:70] + "...",
            "Discipline": r["discipline"],
            "Engine": r["prompt_version"],
            "Score": score_val,
            "Status": label_val,
            "Latency": f"{r.get('latency_ms', 0) / 1000:.2f}s"
        })

    st.dataframe(pd.DataFrame(table_rows), width="stretch", hide_index=True)

    render_html("<div style='margin-top: 28px;'></div>")
    st.divider()

    # Detailed Record Inspection & Deletion
    col_insp, col_del = st.columns([1.5, 1], gap="large")

    with col_insp:
        render_html("""
        <div style="margin: 0 0 12px 0;">
            <h4 style="font-family: 'Crimson Pro', Georgia, serif; font-size: 1.35rem; font-weight: 700; color: var(--text); margin: 0 0 4px 0;">
                Detailed Record Inspector
            </h4>
            <p style="font-size: 0.88rem; color: var(--muted); margin: 0;">Select a past run to examine full methodology specifications and parameters.</p>
        </div>
        """)

        run_ids = [r["id"] for r in runs]
        chosen_id = st.selectbox(
            "Select Run to View Specification Details",
            run_ids,
            format_func=lambda x: f"[{x[:8]}] {next((r['research_question'][:55] for r in runs if r['id'] == x), '')}..."
        )

        matched_run = next((r for r in runs if r["id"] == chosen_id), None)
        if matched_run:
            rec_json = json.loads(matched_run["recommendation_json"]) if matched_run.get("recommendation_json") else None
            if rec_json:
                st.markdown(f"**Recommended Paradigm:** `{rec_json.get('recommended_paradigm')}`")
                st.markdown(f"**Specific Design:** **{rec_json.get('research_design')}**")
                st.markdown(f"**Sampling Framework:** {rec_json.get('sampling_strategy')}")
                st.markdown(f"**Sample Size Rationale:** {rec_json.get('sample_size_rationale')}")

                # Provide PDF download button for historical record
                from src.pdf_report import build_pdf
                from src.schemas import MethodologyRecommendation, EvaluationResult, RubricScore, ReferenceMatchResult, RuleCheckResult

                try:
                    rec_obj = MethodologyRecommendation(**rec_json)
                    eval_obj = None
                    if matched_run.get("rubric_scores"):
                        rub_data = json.loads(matched_run["rubric_scores"])
                        ref_data = json.loads(matched_run.get("reference_match", "{}"))
                        eval_obj = EvaluationResult(
                            rubric=RubricScore(**rub_data),
                            reference_match=ReferenceMatchResult(**ref_data),
                            rules=RuleCheckResult(passed=True, flags=json.loads(matched_run.get("rule_flags", "[]"))),
                            composite_score=matched_run.get("final_score") or 90.0,
                            label=matched_run.get("label") or "DELIVERED"
                        )
                    hist_pdf_bytes = build_pdf(matched_run, rec_obj, eval_obj)
                    st.download_button(
                        label="📄 Download Historical PDF Report (.pdf)",
                        data=hist_pdf_bytes,
                        file_name=f"methodology_report_{matched_run['id'][:8]}.pdf",
                        mime="application/pdf",
                        type="primary",
                        width="stretch",
                        key=f"hist_pdf_{matched_run['id']}"
                    )
                except Exception as err:
                    pass

                with st.expander("View Complete Raw Recommendation JSON"):
                    st.json(rec_json)
            else:
                st.info("This run was rejected at Stage 1 input screening (no methodology generated).")

    with col_del:
        render_html("""
        <div style="margin: 0 0 12px 0;">
            <h4 style="font-family: 'Crimson Pro', Georgia, serif; font-size: 1.35rem; font-weight: 700; color: var(--text); margin: 0 0 4px 0;">
                Data Sovereignty & Deletion
            </h4>
            <p style="font-size: 0.88rem; color: var(--muted); margin: 0;">Permanently purge records from local SQLite storage to maintain privacy.</p>
        </div>
        """)
        
        del_target = st.selectbox(
            "Select Run ID to Permanently Purge",
            run_ids,
            format_func=lambda x: f"Run ID {x[:8]}..."
        )
        
        confirm_del = st.checkbox("Confirm permanent deletion of this record", key="confirm_del_box")
        if st.button("Delete Record", type="secondary", width="stretch", disabled=not confirm_del):
            ok = delete_run(del_target, owner_id=owner_id, is_admin=is_admin)
            if ok:
                st.success(f"Record {del_target[:8]} successfully purged.")
            else:
                st.error("Unable to delete record (permission denied).")
            st.rerun()

        render_html("<div style='margin-top: 18px; border-top: 1px solid var(--border); padding-top: 14px;'></div>")
        st.markdown("**Delete My Data:**")
        st.caption("Permanently remove all your inquiry records, evaluation scores, audit logs, and generated PDF/Markdown report files.")
        confirm_purge_all = st.checkbox("I confirm I want to permanently delete all my session data and reports", key="confirm_purge_all_box")
        if st.button("Delete My Data", type="secondary", width="stretch", disabled=not confirm_purge_all, key="btn_purge_owner_data"):
            purged = delete_owner_data(owner_id)
            st.session_state.pop("active_result", None)
            st.session_state.pop("verified_email", None)
            st.session_state.pop("otp_store", None)
            st.session_state.pop("dev_sim_code", None)
            st.success(f"All session data purged successfully ({purged.get('runs_deleted', 0)} runs, {purged.get('files_deleted', 0)} files deleted).")
            st.rerun()

render_footer()
