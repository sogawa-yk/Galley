"""Tests for reporter module."""

from src.reporter import generate_summary, report_error, report_progress


class TestReportProgress:
    def test_appends_progress(self, tmp_path):
        path = str(tmp_path / "progress.md")
        report_progress("Hearing", "completed", "5 questions answered", path)
        report_progress("TF Generation", "completed", "8 files generated", path)

        with open(path) as f:
            content = f.read()
        assert "Hearing" in content
        assert "TF Generation" in content
        assert "completed" in content


class TestGenerateSummary:
    def test_generates_summary(self, tmp_path):
        path = str(tmp_path / "summary.md")
        result = generate_summary(
            project_name="test-demo",
            stack_id="ocid1.stack.test",
            endpoints={"url": "http://1.2.3.4:8080", "health_url": "http://1.2.3.4:8080/health", "compute_type": "oke"},
            test_results={"total": 5, "passed": 5, "failed": 0},
            output_path=path,
        )

        with open(result) as f:
            content = f.read()
        assert "test-demo" in content
        assert "ALL PASSED" in content
        assert "ocid1.stack.test" in content
        assert "http://1.2.3.4:8080" in content

    def test_partial_test_results(self, tmp_path):
        path = str(tmp_path / "summary.md")
        generate_summary(
            project_name="test",
            stack_id="ocid1.stack.x",
            endpoints={"url": "http://x", "compute_type": "ci"},
            test_results={"total": 3, "passed": 2, "failed": 1},
            output_path=path,
        )
        with open(path) as f:
            content = f.read()
        assert "2/3 PASSED" in content


class TestReportError:
    def test_appends_error(self, tmp_path):
        path = str(tmp_path / "report.md")
        report_error("Deploy", "Connection refused", {"host": "1.2.3.4"}, path)

        with open(path) as f:
            content = f.read()
        assert "ERROR - Deploy" in content
        assert "Connection refused" in content
