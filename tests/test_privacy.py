"""Unit & Integration Tests for User Data Isolation, Privacy, and Security Controls.
Verifies multi-owner isolation, directory traversal prevention, on-demand CSV isolation,
data deletion sovereignty, legacy data exclusion, and admin mode access.
"""

import os
import sys
import json
import tempfile
import unittest
from datetime import datetime

# Path setup
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.storage import (
    init_db,
    save_run,
    save_evaluation,
    log_execution,
    get_all_runs,
    get_execution_logs,
    get_aggregate_stats,
    generate_owner_csv,
    delete_owner_data,
    delete_run,
    cleanup_old_records,
    sanitize_owner_id,
    is_safe_owner_path,
    REPORTS_DIR
)
from src.pdf_report import save_pdf


class TestPrivacyAndIsolation(unittest.TestCase):
    """Test suite asserting user data isolation per session."""

    def setUp(self):
        """Prepare database and clean test identifiers."""
        init_db()
        self.owner_a = "test_user_alpha_123"
        self.owner_b = "test_user_beta_456"

        # Clean prior test state for these test owners
        delete_owner_data(self.owner_a)
        delete_owner_data(self.owner_b)

    def tearDown(self):
        """Clean test data after runs."""
        delete_owner_data(self.owner_a)
        delete_owner_data(self.owner_b)

    def test_sanitize_owner_id(self):
        """Ensure malicious characters (slashes, dots, path traversal) are stripped from owner_id."""
        self.assertEqual(sanitize_owner_id("../../etc/passwd"), "etcpasswd")
        self.assertEqual(sanitize_owner_id("user@#$123!"), "user123")
        self.assertEqual(sanitize_owner_id("valid_owner-456"), "valid_owner-456")
        self.assertEqual(sanitize_owner_id(""), "legacy")
        self.assertEqual(sanitize_owner_id(None), "legacy")

    def test_directory_traversal_prevention(self):
        """Ensure path validation strictly prevents escaping reports/<owner_id>/."""
        owner = "safe_user_789"
        valid_path = os.path.join(REPORTS_DIR, owner, "report.pdf")
        traversal_attack_1 = os.path.join(REPORTS_DIR, owner, "..", "other_user", "report.pdf")
        traversal_attack_2 = os.path.join(REPORTS_DIR, owner, "..", "..", "etc", "passwd")
        traversal_attack_3 = "/etc/passwd"
        other_owner_path = os.path.join(REPORTS_DIR, "other_user", "report.pdf")

        # Valid owner path should pass
        self.assertTrue(is_safe_owner_path(valid_path, owner_id=owner))

        # Traversal attacks must fail
        self.assertFalse(is_safe_owner_path(traversal_attack_1, owner_id=owner))
        self.assertFalse(is_safe_owner_path(traversal_attack_2, owner_id=owner))
        self.assertFalse(is_safe_owner_path(traversal_attack_3, owner_id=owner))
        self.assertFalse(is_safe_owner_path(other_owner_path, owner_id=owner))

        # Admin can access safe reports paths
        self.assertTrue(is_safe_owner_path(other_owner_path, owner_id=owner, is_admin=True))
        # But even admin cannot traverse outside reports directory root
        self.assertFalse(is_safe_owner_path("/etc/passwd", is_admin=True))

    def test_owner_data_isolation_runs(self):
        """Assert Owner A cannot see Owner B's runs and vice versa."""
        run_a = "run_alpha_001"
        run_b = "run_beta_002"

        save_run(
            run_id=run_a,
            timestamp=datetime.now().isoformat(),
            research_question="Question Alpha: Machine learning impact on pedagogy",
            discipline="Computer Science",
            constraints={"budget": "Low"},
            prompt_version="v3_decomposed",
            parsed_json={"target": "Students"},
            recommendation_json={"recommended_paradigm": "Quantitative", "research_design": "Quasi-Experimental"},
            latency_ms=1200,
            owner_id=self.owner_a
        )

        save_run(
            run_id=run_b,
            timestamp=datetime.now().isoformat(),
            research_question="Question Beta: Lived experience of medical trauma",
            discipline="Psychology",
            constraints={"budget": "High"},
            prompt_version="v3_decomposed",
            parsed_json={"target": "Patients"},
            recommendation_json={"recommended_paradigm": "Qualitative", "research_design": "Phenomenological"},
            latency_ms=1400,
            owner_id=self.owner_b
        )

        # Owner A query
        runs_a = get_all_runs(owner_id=self.owner_a)
        runs_a_ids = [r["id"] for r in runs_a]
        self.assertIn(run_a, runs_a_ids)
        self.assertNotIn(run_b, runs_a_ids)
        self.assertEqual(runs_a[0]["research_question"], "Question Alpha: Machine learning impact on pedagogy")

        # Owner B query
        runs_b = get_all_runs(owner_id=self.owner_b)
        runs_b_ids = [r["id"] for r in runs_b]
        self.assertIn(run_b, runs_b_ids)
        self.assertNotIn(run_a, runs_b_ids)
        self.assertEqual(runs_b[0]["research_question"], "Question Beta: Lived experience of medical trauma")

        # Unauthenticated / empty query must return nothing
        self.assertEqual(get_all_runs(owner_id=""), [])
        self.assertEqual(get_all_runs(owner_id=None), [])

    def test_legacy_data_exclusion(self):
        """Assert historical/legacy records are excluded from normal user views."""
        legacy_id = "run_legacy_999"
        save_run(
            run_id=legacy_id,
            timestamp=datetime.now().isoformat(),
            research_question="Legacy Question from previous version",
            discipline="Sociology",
            constraints={},
            prompt_version="v1_basic",
            parsed_json=None,
            recommendation_json={"recommended_paradigm": "Mixed Methods"},
            latency_ms=800,
            owner_id="legacy"
        )

        # Normal user query cannot see legacy rows
        runs_user = get_all_runs(owner_id=self.owner_a)
        self.assertNotIn(legacy_id, [r["id"] for r in runs_user])

        # Direct legacy owner query is blocked for non-admin
        self.assertEqual(get_all_runs(owner_id="legacy"), [])

        # Admin query can see legacy records
        admin_runs = get_all_runs(is_admin=True)
        self.assertIn(legacy_id, [r["id"] for r in admin_runs])

    def test_execution_log_isolation(self):
        """Assert trigger-action logs are isolated per owner."""
        log_a = "run_log_alpha"
        log_b = "run_log_beta"

        log_execution(
            run_id=log_a,
            trigger_event="STAGE_3_COMPLETE",
            action_taken="GENERATE_PDF",
            status="DELIVERED",
            output_file_path=f"reports/{self.owner_a}/doc_a.pdf",
            duration_ms=250,
            action_type="PDF_GENERATED",
            owner_id=self.owner_a
        )

        log_execution(
            run_id=log_b,
            trigger_event="STAGE_3_COMPLETE",
            action_taken="GENERATE_PDF",
            status="DELIVERED",
            output_file_path=f"reports/{self.owner_b}/doc_b.pdf",
            duration_ms=290,
            action_type="PDF_GENERATED",
            owner_id=self.owner_b
        )

        logs_a = get_execution_logs(owner_id=self.owner_a)
        self.assertTrue(all(l.get("owner_id") == self.owner_a for l in logs_a))
        self.assertIn(log_a, [l["run_id"] for l in logs_a])
        self.assertNotIn(log_b, [l["run_id"] for l in logs_a])

        logs_b = get_execution_logs(owner_id=self.owner_b)
        self.assertTrue(all(l.get("owner_id") == self.owner_b for l in logs_b))
        self.assertIn(log_b, [l["run_id"] for l in logs_b])
        self.assertNotIn(log_a, [l["run_id"] for l in logs_b])

    def test_csv_export_isolation(self):
        """Assert in-memory CSV export contains strictly the requesting owner's rows."""
        run_a = "csv_run_alpha"
        run_b = "csv_run_beta"

        save_run(
            run_id=run_a,
            timestamp=datetime.now().isoformat(),
            research_question="Unique Secret Question Alpha for CSV",
            discipline="Computer Science",
            constraints={},
            prompt_version="v3_decomposed",
            parsed_json=None,
            recommendation_json={"recommended_paradigm": "Quantitative"},
            latency_ms=900,
            owner_id=self.owner_a
        )

        save_run(
            run_id=run_b,
            timestamp=datetime.now().isoformat(),
            research_question="Confidential Question Beta for CSV",
            discipline="Psychology",
            constraints={},
            prompt_version="v3_decomposed",
            parsed_json=None,
            recommendation_json={"recommended_paradigm": "Qualitative"},
            latency_ms=950,
            owner_id=self.owner_b
        )

        csv_a = generate_owner_csv(owner_id=self.owner_a)
        self.assertIn("Unique Secret Question Alpha", csv_a)
        self.assertNotIn("Confidential Question Beta", csv_a)

        csv_b = generate_owner_csv(owner_id=self.owner_b)
        self.assertIn("Confidential Question Beta", csv_b)
        self.assertNotIn("Unique Secret Question Alpha", csv_b)

    def test_delete_my_data_purges_rows_and_files(self):
        """Assert 'Delete My Data' purges owner records and disk files without affecting other owners."""
        run_a = "del_test_alpha"
        run_b = "del_test_beta"

        save_run(
            run_id=run_a,
            timestamp=datetime.now().isoformat(),
            research_question="To Be Deleted: Question Alpha",
            discipline="Medicine",
            constraints={},
            prompt_version="v3_decomposed",
            parsed_json=None,
            recommendation_json={"recommended_paradigm": "Quantitative"},
            latency_ms=1000,
            owner_id=self.owner_a
        )

        save_run(
            run_id=run_b,
            timestamp=datetime.now().isoformat(),
            research_question="To Be Kept: Question Beta",
            discipline="Sociology",
            constraints={},
            prompt_version="v3_decomposed",
            parsed_json=None,
            recommendation_json={"recommended_paradigm": "Qualitative"},
            latency_ms=1100,
            owner_id=self.owner_b
        )

        # Create physical report files
        owner_a_dir = os.path.join(REPORTS_DIR, self.owner_a)
        owner_b_dir = os.path.join(REPORTS_DIR, self.owner_b)
        os.makedirs(owner_a_dir, exist_ok=True)
        os.makedirs(owner_b_dir, exist_ok=True)

        file_a = os.path.join(owner_a_dir, "report_a.pdf")
        file_b = os.path.join(owner_b_dir, "report_b.pdf")
        with open(file_a, "wb") as f:
            f.write(b"%PDF-1.4 test file a")
        with open(file_b, "wb") as f:
            f.write(b"%PDF-1.4 test file b")

        self.assertTrue(os.path.exists(file_a))
        self.assertTrue(os.path.exists(file_b))

        # Perform deletion for Owner A
        result = delete_owner_data(self.owner_a)
        self.assertGreaterEqual(result["runs_deleted"], 1)
        self.assertGreaterEqual(result["files_deleted"], 1)

        # Verify Owner A rows and files are deleted
        self.assertEqual(get_all_runs(owner_id=self.owner_a), [])
        self.assertFalse(os.path.exists(file_a))
        self.assertFalse(os.path.exists(owner_a_dir))

        # Verify Owner B rows and files are intact!
        runs_b = get_all_runs(owner_id=self.owner_b)
        self.assertEqual(len(runs_b), 1)
        self.assertEqual(runs_b[0]["id"], run_b)
        self.assertTrue(os.path.exists(file_b))

    def test_pdf_saved_in_owner_directory(self):
        """Assert save_pdf stores the file under reports/<owner_id>/."""
        run_record = {
            "run_id": "pdf_test_run_101",
            "research_question": "Does music improve memory retention in adolescents?",
            "discipline": "Psychology",
            "prompt_version": "v3_decomposed",
            "owner_id": self.owner_a
        }
        pdf_path = save_pdf(run_record, recommendation=None, evaluation=None, owner_id=self.owner_a)

        self.assertTrue(os.path.exists(pdf_path))
        self.assertIn(self.owner_a, pdf_path)
        self.assertTrue(is_safe_owner_path(pdf_path, self.owner_a))

    def test_aggregate_stats_has_no_question_leakage(self):
        """Assert get_aggregate_stats returns counts and average score only (no strings/questions)."""
        stats = get_aggregate_stats()
        self.assertIn("total_runs", stats)
        self.assertIn("avg_score", stats)
        self.assertIsInstance(stats["total_runs"], int)
        self.assertIsInstance(stats["avg_score"], float)
        # Ensure no text keys or questions are in the dictionary
        self.assertNotIn("research_question", stats)
        self.assertNotIn("runs", stats)


if __name__ == "__main__":
    unittest.main()
