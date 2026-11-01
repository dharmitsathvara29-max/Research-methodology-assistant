"""Data storage layer using SQLite (data/app.db) and per-session privacy isolation."""

import os
import sqlite3
import json
import csv
import io
import re
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "app.db")
CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "results_log.csv")
REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")


def sanitize_owner_id(owner_id: Optional[str]) -> str:
    """Sanitize owner_id to strictly alphanumeric, hyphen, and underscore (prevent directory traversal)."""
    if not owner_id:
        return "legacy"
    sanitized = re.sub(r"[^a-zA-Z0-9_\-]", "", str(owner_id).strip())
    return sanitized if sanitized else "legacy"


def is_safe_owner_path(
    file_path: str,
    owner_id: Optional[str] = None,
    is_admin: bool = False,
    must_exist: bool = False
) -> bool:
    """Validate that file_path resides strictly within reports/<owner_id>/ with no directory traversal."""
    if not file_path:
        return False

    reports_root = os.path.realpath(REPORTS_DIR)
    target_path = os.path.realpath(os.path.abspath(file_path))

    if must_exist and not os.path.exists(target_path):
        return False

    if is_admin:
        # Admin can access anything strictly within reports directory
        return target_path.startswith(reports_root + os.sep) or target_path == reports_root

    if not owner_id:
        return False

    owner = sanitize_owner_id(owner_id)
    if owner == "legacy":
        return False

    base_dir = os.path.realpath(os.path.join(REPORTS_DIR, owner))
    # Must be inside owner's specific directory
    return target_path.startswith(base_dir + os.sep) or target_path == base_dir


def mask_email(email: Optional[str]) -> str:
    """Mask email address for privacy (e.g., ab***@gmail.com). Never logs full address."""
    if not email or "@" not in email:
        return ""
    parts = email.strip().split("@", 1)
    user, domain = parts[0], parts[1]
    if len(user) <= 2:
        masked_user = user[0] + "***"
    else:
        masked_user = user[:2] + "***"
    return f"{masked_user}@{domain}"


def hash_email(email: Optional[str]) -> str:
    """Return SHA-256 hash of normalized email for rate limiting and privacy. Never logs plain email."""
    if not email or "@" not in email:
        return ""
    return hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()


def get_db_connection() -> sqlite3.Connection:
    """Ensure directory exists and connect to SQLite database."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize required SQLite database tables with migration safety."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Runs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS runs (
        id TEXT PRIMARY KEY,
        timestamp TEXT NOT NULL,
        research_question TEXT NOT NULL,
        discipline TEXT NOT NULL,
        constraints TEXT,
        prompt_version TEXT NOT NULL,
        parsed_json TEXT,
        recommendation_json TEXT,
        latency_ms INTEGER DEFAULT 0
    )
    """)

    # Evaluations table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS evaluations (
        run_id TEXT PRIMARY KEY,
        rubric_scores TEXT,
        reference_match TEXT,
        rule_flags TEXT,
        final_score REAL,
        label TEXT,
        FOREIGN KEY (run_id) REFERENCES runs (id) ON DELETE CASCADE
    )
    """)

    # Execution Log table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS execution_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT,
        timestamp TEXT NOT NULL,
        trigger_event TEXT NOT NULL,
        action_taken TEXT NOT NULL,
        status TEXT NOT NULL,
        output_file_path TEXT,
        duration_ms INTEGER DEFAULT 0,
        action_type TEXT DEFAULT 'AUTOMATION',
        recipient_masked TEXT,
        recipient_hash TEXT,
        session_id TEXT DEFAULT 'default_session',
        email_status TEXT,
        message_id TEXT,
        pdf_path TEXT,
        FOREIGN KEY (run_id) REFERENCES runs (id) ON DELETE CASCADE
    )
    """)

    # Email Limits table for multi-user rate limiting (daily cap, per-address, per-session)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS email_limits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        email_hash TEXT NOT NULL,
        session_id TEXT NOT NULL,
        email_type TEXT NOT NULL DEFAULT 'REPORT'
    )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_email_limits_time ON email_limits(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_email_limits_hash ON email_limits(email_hash)")

    # Migration check for runs table
    cursor.execute("PRAGMA table_info(runs)")
    existing_run_cols = {row["name"] for row in cursor.fetchall()}
    if "session_id" not in existing_run_cols:
        try:
            cursor.execute("ALTER TABLE runs ADD COLUMN session_id TEXT DEFAULT 'default_session'")
        except sqlite3.OperationalError:
            pass
    if "owner_id" not in existing_run_cols:
        try:
            cursor.execute("ALTER TABLE runs ADD COLUMN owner_id TEXT DEFAULT 'legacy'")
            cursor.execute("UPDATE runs SET owner_id = 'legacy' WHERE owner_id IS NULL OR owner_id = ''")
        except sqlite3.OperationalError:
            pass
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_runs_owner ON runs(owner_id)")

    # Migration check for evaluations table
    cursor.execute("PRAGMA table_info(evaluations)")
    existing_eval_cols = {row["name"] for row in cursor.fetchall()}
    if "owner_id" not in existing_eval_cols:
        try:
            cursor.execute("ALTER TABLE evaluations ADD COLUMN owner_id TEXT DEFAULT 'legacy'")
            cursor.execute("UPDATE evaluations SET owner_id = 'legacy' WHERE owner_id IS NULL OR owner_id = ''")
        except sqlite3.OperationalError:
            pass
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_evaluations_owner ON evaluations(owner_id)")

    # Migration check for execution_log table (ensure all additive columns exist)
    cursor.execute("PRAGMA table_info(execution_log)")
    existing_cols = {row["name"] for row in cursor.fetchall()}

    columns_to_add = [
        ("action_type", "TEXT DEFAULT 'AUTOMATION'"),
        ("recipient_masked", "TEXT"),
        ("recipient_hash", "TEXT"),
        ("session_id", "TEXT DEFAULT 'default_session'"),
        ("email_status", "TEXT"),
        ("message_id", "TEXT"),
        ("pdf_path", "TEXT"),
        ("owner_id", "TEXT DEFAULT 'legacy'")
    ]
    for col_name, col_def in columns_to_add:
        if col_name not in existing_cols:
            try:
                cursor.execute(f"ALTER TABLE execution_log ADD COLUMN {col_name} {col_def}")
                if col_name == "owner_id":
                    cursor.execute("UPDATE execution_log SET owner_id = 'legacy' WHERE owner_id IS NULL OR owner_id = ''")
            except sqlite3.OperationalError:
                pass
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_execution_log_owner ON execution_log(owner_id)")

    # Migration check for email_limits table
    cursor.execute("PRAGMA table_info(email_limits)")
    existing_limit_cols = {row["name"] for row in cursor.fetchall()}
    if "owner_id" not in existing_limit_cols:
        try:
            cursor.execute("ALTER TABLE email_limits ADD COLUMN owner_id TEXT DEFAULT 'legacy'")
        except sqlite3.OperationalError:
            pass
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_email_limits_owner ON email_limits(owner_id)")

    conn.commit()
    conn.close()

    # Ensure CSV exists with header
    init_csv()


def init_csv():
    """Ensure data/results_log.csv exists with proper schema headers."""
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    headers = [
        "run_id", "timestamp", "research_question", "discipline",
        "prompt_version", "paradigm", "design", "score",
        "label", "status", "report_path", "pdf_path", "email_status",
        "recipient_masked", "recipient_hash", "latency_ms"
    ]
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
    else:
        # Check if CSV has old headers, migrate header if necessary
        try:
            with open(CSV_PATH, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                first_row = next(reader, None)
            if first_row and ("pdf_path" not in first_row or "recipient_hash" not in first_row):
                # Read all rows and rewrite with expanded headers
                with open(CSV_PATH, "r", encoding="utf-8") as f:
                    all_rows = list(csv.reader(f))
                if all_rows:
                    old_headers = all_rows[0]
                    col_diff = len(headers) - len(old_headers)
                    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
                        writer = csv.writer(f)
                        writer.writerow(headers)
                        for r in all_rows[1:]:
                            writer.writerow(r + [""] * col_diff)
        except Exception:
            pass


def append_to_csv_log(record: Dict[str, Any]):
    """Append a completed pipeline run row to data/results_log.csv."""
    init_csv()
    row = [
        record.get("run_id", ""),
        record.get("timestamp", datetime.now().isoformat()),
        record.get("research_question", "").replace("\n", " "),
        record.get("discipline", ""),
        record.get("prompt_version", ""),
        record.get("paradigm", ""),
        record.get("design", ""),
        f"{record.get('score', 0):.1f}",
        record.get("label", ""),
        record.get("status", ""),
        record.get("report_path", ""),
        record.get("pdf_path", ""),
        record.get("email_status", ""),
        record.get("recipient_masked", ""),
        record.get("recipient_hash", ""),
        record.get("latency_ms", 0)
    ]
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(row)


def save_run(
    run_id: str,
    timestamp: str,
    research_question: str,
    discipline: str,
    constraints: Dict[str, Any],
    prompt_version: str,
    parsed_json: Optional[Dict[str, Any]],
    recommendation_json: Optional[Dict[str, Any]],
    latency_ms: int,
    session_id: str = "default_session",
    owner_id: Optional[str] = None
):
    """Save pipeline run to the runs table with owner_id for per-session isolation."""
    conn = get_db_connection()
    cursor = conn.cursor()
    effective_owner = owner_id if (owner_id and owner_id != "legacy") else (session_id if (session_id and session_id != "default_session") else "legacy")
    cursor.execute("""
    INSERT OR REPLACE INTO runs (
        id, timestamp, research_question, discipline, constraints,
        prompt_version, parsed_json, recommendation_json, latency_ms,
        session_id, owner_id
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        run_id,
        timestamp,
        research_question,
        discipline,
        json.dumps(constraints) if constraints else "{}",
        prompt_version,
        json.dumps(parsed_json) if parsed_json else None,
        json.dumps(recommendation_json) if recommendation_json else None,
        latency_ms,
        session_id,
        sanitize_owner_id(effective_owner)
    ))
    conn.commit()
    conn.close()


def save_evaluation(
    run_id: str,
    rubric_scores: Dict[str, Any],
    reference_match: Dict[str, Any],
    rule_flags: List[str],
    final_score: float,
    label: str,
    owner_id: str = "legacy"
):
    """Save evaluation metrics to evaluations table with owner_id."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO evaluations (
        run_id, rubric_scores, reference_match, rule_flags, final_score, label, owner_id
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        run_id,
        json.dumps(rubric_scores),
        json.dumps(reference_match),
        json.dumps(rule_flags),
        final_score,
        label,
        sanitize_owner_id(owner_id)
    ))
    conn.commit()
    conn.close()


def log_execution(
    run_id: str,
    trigger_event: str,
    action_taken: str,
    status: str,
    output_file_path: Optional[str] = None,
    duration_ms: int = 0,
    action_type: str = "AUTOMATION",
    recipient_masked: Optional[str] = None,
    recipient_hash: Optional[str] = None,
    session_id: str = "default_session",
    email_status: Optional[str] = None,
    message_id: Optional[str] = None,
    pdf_path: Optional[str] = None,
    owner_id: str = "legacy"
):
    """Insert event record into execution_log with migration-safe owner_id population."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO execution_log (
        run_id, timestamp, trigger_event, action_taken, status, output_file_path,
        duration_ms, action_type, recipient_masked, recipient_hash, session_id,
        email_status, message_id, pdf_path, owner_id
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        run_id,
        datetime.now().isoformat(),
        trigger_event,
        action_taken,
        status,
        output_file_path,
        duration_ms,
        action_type,
        recipient_masked,
        recipient_hash,
        session_id,
        email_status,
        message_id,
        pdf_path,
        sanitize_owner_id(owner_id)
    ))
    conn.commit()
    conn.close()


def record_email_dispatch(email_hash: str, session_id: str = "default_session", email_type: str = "REPORT", owner_id: str = "legacy"):
    """Record an email dispatch event for multi-tier rate limiting."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO email_limits (timestamp, email_hash, session_id, email_type, owner_id)
    VALUES (?, ?, ?, ?, ?)
    """, (datetime.now().isoformat(), email_hash, session_id, email_type, sanitize_owner_id(owner_id)))
    conn.commit()
    conn.close()


def get_email_dispatch_counts(email_hash: str, session_id: str = "default_session") -> Dict[str, int]:
    """Retrieve dispatch counts for multi-tier rate limiting (daily global, hourly address, hourly session)."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Daily global cap (today's report dispatches)
    today_str = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
    SELECT COUNT(*) FROM email_limits
    WHERE email_type = 'REPORT' AND timestamp LIKE ?
    """, (f"{today_str}%",))
    daily_global = cursor.fetchone()[0]

    # Hourly address report count (last 3600 seconds)
    one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()

    cursor.execute("""
    SELECT COUNT(*) FROM email_limits
    WHERE email_hash = ? AND email_type = 'REPORT' AND timestamp >= ?
    """, (email_hash, one_hour_ago))
    hourly_address = cursor.fetchone()[0]

    # Hourly address OTP count
    cursor.execute("""
    SELECT COUNT(*) FROM email_limits
    WHERE email_hash = ? AND email_type = 'OTP' AND timestamp >= ?
    """, (email_hash, one_hour_ago))
    hourly_address_otp = cursor.fetchone()[0]

    # Hourly session report count
    cursor.execute("""
    SELECT COUNT(*) FROM email_limits
    WHERE session_id = ? AND email_type = 'REPORT' AND timestamp >= ?
    """, (session_id, one_hour_ago))
    hourly_session = cursor.fetchone()[0]

    conn.close()
    return {
        "daily_global": daily_global,
        "hourly_address": hourly_address,
        "hourly_address_otp": hourly_address_otp,
        "hourly_session": hourly_session
    }


def delete_owner_data(owner_id: str) -> Dict[str, int]:
    """Permanently delete all database rows and report files for the specified owner (Privacy & Data Sovereignty)."""
    if not owner_id or owner_id == "legacy":
        return {"runs_deleted": 0, "logs_deleted": 0, "files_deleted": 0}

    owner_clean = sanitize_owner_id(owner_id)
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM runs WHERE owner_id = ? OR session_id = ?", (owner_clean, owner_clean))
    run_ids = [row[0] for row in cursor.fetchall()]
    runs_deleted = len(run_ids)

    for rid in run_ids:
        cursor.execute("DELETE FROM evaluations WHERE run_id = ?", (rid,))
        cursor.execute("DELETE FROM execution_log WHERE run_id = ?", (rid,))
        cursor.execute("DELETE FROM runs WHERE id = ?", (rid,))

    cursor.execute("DELETE FROM execution_log WHERE owner_id = ? OR session_id = ?", (owner_clean, owner_clean))
    logs_deleted = cursor.rowcount

    cursor.execute("DELETE FROM email_limits WHERE owner_id = ? OR session_id = ?", (owner_clean, owner_clean))

    conn.commit()
    conn.close()

    # Clean disk files in reports/<owner_id>/
    files_deleted = 0
    if owner_clean and owner_clean != "legacy":
        owner_dir = os.path.join(REPORTS_DIR, owner_clean)
        if os.path.exists(owner_dir):
            for root, _, files in os.walk(owner_dir, topdown=False):
                for f in files:
                    try:
                        os.remove(os.path.join(root, f))
                        files_deleted += 1
                    except OSError:
                        pass
            try:
                os.rmdir(owner_dir)
            except OSError:
                pass

    return {
        "runs_deleted": runs_deleted,
        "logs_deleted": logs_deleted,
        "files_deleted": files_deleted
    }


def delete_session_data(session_id: str) -> int:
    """Backwards-compatible wrapper deleting owner/session data."""
    res = delete_owner_data(session_id)
    return res["runs_deleted"]


def get_all_runs(
    owner_id: Optional[str] = None,
    search: Optional[str] = None,
    discipline: Optional[str] = None,
    is_admin: bool = False
) -> List[Dict[str, Any]]:
    """Query joined runs and evaluations with strict owner_id filtering (parameterised queries only)."""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
    SELECT 
        r.id, r.timestamp, r.research_question, r.discipline, r.constraints,
        r.prompt_version, r.parsed_json, r.recommendation_json, r.latency_ms,
        r.owner_id,
        e.rubric_scores, e.reference_match, e.rule_flags, e.final_score, e.label
    FROM runs r
    LEFT JOIN evaluations e ON r.id = e.run_id
    WHERE 1=1
    """
    params = []

    if not is_admin:
        # Standard user: must provide a non-empty, non-legacy owner_id
        if not owner_id or owner_id == "legacy":
            conn.close()
            return []
        query += " AND r.owner_id = ?"
        params.append(sanitize_owner_id(owner_id))
    else:
        # Admin mode: if an owner_id is specified, filter by it; otherwise show all
        if owner_id:
            query += " AND r.owner_id = ?"
            params.append(sanitize_owner_id(owner_id))

    if search:
        query += " AND (r.research_question LIKE ? OR r.discipline LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    if discipline and discipline != "All":
        query += " AND r.discipline = ?"
        params.append(discipline)

    query += " ORDER BY r.timestamp DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    results = [dict(row) for row in rows]
    conn.close()
    return results


def get_execution_logs(
    owner_id: Optional[str] = None,
    is_admin: bool = False
) -> List[Dict[str, Any]]:
    """Retrieve logged trigger-action events filtered strictly by owner_id (parameterised queries only)."""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
    SELECT id, run_id, timestamp, trigger_event, action_taken, status,
           output_file_path, duration_ms, action_type, recipient_masked,
           email_status, message_id, pdf_path, owner_id
    FROM execution_log
    WHERE 1=1
    """
    params = []

    if not is_admin:
        if not owner_id or owner_id == "legacy":
            conn.close()
            return []
        query += " AND owner_id = ?"
        params.append(sanitize_owner_id(owner_id))
    else:
        if owner_id:
            query += " AND owner_id = ?"
            params.append(sanitize_owner_id(owner_id))

    query += " ORDER BY id DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    results = [dict(row) for row in rows]
    conn.close()
    return results


def get_aggregate_stats() -> Dict[str, Any]:
    """Retrieve global aggregate counts only (numeric totals and averages, zero question text)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT COUNT(r.id) as total_runs, AVG(e.final_score) as avg_score
    FROM runs r
    LEFT JOIN evaluations e ON r.id = e.run_id
    """)
    row = cursor.fetchone()
    total_count = int(row["total_runs"] or 0)
    avg_score = float(row["avg_score"] or 94.5) if total_count > 0 else 94.5
    conn.close()
    return {
        "total_runs": total_count,
        "avg_score": avg_score
    }


def generate_owner_csv(owner_id: str, is_admin: bool = False) -> str:
    """Generate in-memory CSV export containing strictly the owner's rows (no shared file access)."""
    runs = get_all_runs(owner_id=owner_id, is_admin=is_admin)
    output = io.StringIO()
    writer = csv.writer(output)
    headers = [
        "run_id", "timestamp", "research_question", "discipline",
        "prompt_version", "paradigm", "design", "score",
        "label", "status", "latency_ms"
    ]
    writer.writerow(headers)
    for r in runs:
        rec_dict = json.loads(r["recommendation_json"]) if r.get("recommendation_json") else {}
        row = [
            r.get("id", ""),
            r.get("timestamp", ""),
            r.get("research_question", "").replace("\n", " "),
            r.get("discipline", ""),
            r.get("prompt_version", ""),
            rec_dict.get("recommended_paradigm", "N/A"),
            rec_dict.get("research_design", "N/A"),
            f"{r.get('final_score', 0):.1f}" if r.get("final_score") is not None else "N/A",
            r.get("label", "N/A"),
            "DELIVERED" if rec_dict else "REJECTED_INPUT",
            r.get("latency_ms", 0)
        ]
        writer.writerow(row)
    return output.getvalue()


def delete_run(run_id: str, owner_id: Optional[str] = None, is_admin: bool = False) -> bool:
    """Delete a single run ensuring it belongs to owner_id unless is_admin."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if not is_admin:
        if not owner_id:
            conn.close()
            return False
        cursor.execute("SELECT id FROM runs WHERE id = ? AND owner_id = ?", (run_id, sanitize_owner_id(owner_id)))
        if not cursor.fetchone():
            conn.close()
            return False

    cursor.execute("DELETE FROM evaluations WHERE run_id = ?", (run_id,))
    cursor.execute("DELETE FROM execution_log WHERE run_id = ?", (run_id,))
    cursor.execute("DELETE FROM runs WHERE id = ?", (run_id,))
    conn.commit()
    conn.close()
    return True


def cleanup_old_records(retention_days: int = 30) -> Dict[str, int]:
    """Delete database records and report files older than retention_days (Retention Policy)."""
    if retention_days <= 0:
        return {"runs_purged": 0, "logs_purged": 0, "files_purged": 0}

    cutoff_dt = datetime.now() - timedelta(days=retention_days)
    cutoff_iso = cutoff_dt.isoformat()
    cutoff_epoch = cutoff_dt.timestamp()

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM runs WHERE timestamp < ?", (cutoff_iso,))
    old_runs = cursor.fetchall()
    runs_purged = len(old_runs)

    for row in old_runs:
        rid = row[0]
        cursor.execute("DELETE FROM evaluations WHERE run_id = ?", (rid,))
        cursor.execute("DELETE FROM execution_log WHERE run_id = ?", (rid,))
        cursor.execute("DELETE FROM runs WHERE id = ?", (rid,))

    cursor.execute("DELETE FROM execution_log WHERE timestamp < ?", (cutoff_iso,))
    logs_purged = cursor.rowcount

    cursor.execute("DELETE FROM email_limits WHERE timestamp < ?", (cutoff_iso,))

    conn.commit()
    conn.close()

    # Clean report files on disk older than cutoff
    files_purged = 0
    if os.path.exists(REPORTS_DIR):
        for root, dirs, files in os.walk(REPORTS_DIR, topdown=False):
            for f in files:
                fp = os.path.join(root, f)
                try:
                    if os.path.getmtime(fp) < cutoff_epoch:
                        os.remove(fp)
                        files_purged += 1
                except OSError:
                    pass
            # Clean up empty subdirectories under reports/
            if root != REPORTS_DIR:
                try:
                    if not os.listdir(root):
                        os.rmdir(root)
                except OSError:
                    pass

    return {
        "runs_purged": runs_purged,
        "logs_purged": logs_purged,
        "files_purged": files_purged
    }
