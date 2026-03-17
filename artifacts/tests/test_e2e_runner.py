"""Tests for e2e_runner module."""

import json

from src.e2e_runner import check_endpoint, generate_report, run_test_suite


class TestGenerateReport:
    """Tests for generate_report function."""

    def test_generates_markdown_report(self, tmp_path):
        results = {
            "total": 2,
            "passed": 1,
            "failed": 1,
            "results": [
                {
                    "name": "Health Check",
                    "passed": True,
                    "response_time_ms": 50.5,
                    "error": None,
                },
                {
                    "name": "GET /api/items",
                    "passed": False,
                    "response_time_ms": 120.0,
                    "error": "Expected 200, got 500",
                },
            ],
        }
        output = str(tmp_path / "report.md")
        path = generate_report(results, output)

        with open(path) as f:
            content = f.read()

        assert "# E2E Test Report" in content
        assert "**Total**: 2" in content
        assert "**Passed**: 1" in content
        assert "**Failed**: 1" in content
        assert "PASS" in content
        assert "FAIL" in content
        assert "Health Check" in content
        assert "Expected 200, got 500" in content

    def test_empty_results(self, tmp_path):
        results = {"total": 0, "passed": 0, "failed": 0, "results": []}
        output = str(tmp_path / "report.md")
        path = generate_report(results, output)

        with open(path) as f:
            content = f.read()
        assert "**Total**: 0" in content


class TestRunTestSuite:
    """Tests for run_test_suite - only structure tests (no HTTP)."""

    def test_returns_correct_structure(self):
        # This test would require mocking requests, just verify structure
        result = run_test_suite([])
        assert result["total"] == 0
        assert result["passed"] == 0
        assert result["failed"] == 0
        assert result["results"] == []
