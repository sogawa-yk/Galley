"""E2E Test Runner Module.

Provides functions for health checks, API endpoint testing,
and test report generation.
"""

import json
import time
from dataclasses import dataclass, field

import requests


def health_check(
    url: str,
    timeout: int = 30,
    retries: int = 10,
    interval: int = 10,
) -> dict:
    """Perform a health check against the given URL.

    Retries until the endpoint responds or max retries reached.

    Args:
        url: Health check URL.
        timeout: HTTP request timeout in seconds.
        retries: Maximum number of retry attempts.
        interval: Wait time between retries in seconds.

    Returns:
        Dict with status, response_time, and details.
    """
    for attempt in range(1, retries + 1):
        try:
            start = time.time()
            resp = requests.get(url, timeout=timeout)
            elapsed = time.time() - start

            if resp.status_code == 200:
                return {
                    "passed": True,
                    "status_code": resp.status_code,
                    "response_time_ms": round(elapsed * 1000, 2),
                    "attempt": attempt,
                    "body": _safe_json(resp),
                }
        except requests.RequestException:
            pass

        if attempt < retries:
            time.sleep(interval)

    return {
        "passed": False,
        "status_code": None,
        "response_time_ms": None,
        "attempt": retries,
        "error": f"Health check failed after {retries} attempts",
    }


def check_endpoint(
    url: str,
    method: str = "GET",
    payload: dict | None = None,
    headers: dict | None = None,
    expected_status: int = 200,
    timeout: int = 30,
    session: requests.Session | None = None,
) -> dict:
    """Test a single API endpoint.

    Args:
        url: Endpoint URL.
        method: HTTP method.
        payload: Request body (for POST/PUT).
        headers: Request headers.
        expected_status: Expected HTTP status code.
        timeout: Request timeout in seconds.
        session: Optional requests.Session for authenticated requests.

    Returns:
        Test result dict.
    """
    try:
        requester = session if session is not None else requests
        start = time.time()
        resp = requester.request(
            method=method,
            url=url,
            json=payload,
            headers=headers,
            timeout=timeout,
        )
        elapsed = time.time() - start

        passed = resp.status_code == expected_status
        return {
            "passed": passed,
            "url": url,
            "method": method,
            "expected_status": expected_status,
            "actual_status": resp.status_code,
            "response_time_ms": round(elapsed * 1000, 2),
            "body": _safe_json(resp),
            "error": None if passed else f"Expected {expected_status}, got {resp.status_code}",
        }
    except requests.RequestException as e:
        return {
            "passed": False,
            "url": url,
            "method": method,
            "expected_status": expected_status,
            "actual_status": None,
            "response_time_ms": None,
            "body": None,
            "error": str(e),
        }


def run_test_suite(test_specs: list[dict]) -> dict:
    """Run a suite of endpoint tests.

    Args:
        test_specs: List of test spec dicts, each with:
            - url: Endpoint URL
            - method: HTTP method (default GET)
            - payload: Request body (optional)
            - expected_status: Expected status (default 200)
            - name: Test name (optional)
            - session: Optional requests.Session for authenticated requests

    Returns:
        Dict with total, passed, failed counts and detailed results.
    """
    results = []
    for spec in test_specs:
        name = spec.get("name", f"{spec.get('method', 'GET')} {spec['url']}")
        result = check_endpoint(
            url=spec["url"],
            method=spec.get("method", "GET"),
            payload=spec.get("payload"),
            headers=spec.get("headers"),
            expected_status=spec.get("expected_status", 200),
            session=spec.get("session"),
        )
        result["name"] = name
        results.append(result)

    passed = sum(1 for r in results if r["passed"])
    failed = len(results) - passed

    return {
        "total": len(results),
        "passed": passed,
        "failed": failed,
        "results": results,
    }


def generate_report(test_results: dict, output_path: str) -> str:
    """Generate a Markdown test report.

    Args:
        test_results: Results from run_test_suite or combined results.
        output_path: Path to write the report.

    Returns:
        Path to the report file.
    """
    lines = [
        "# E2E Test Report",
        "",
        f"**Total**: {test_results['total']} | "
        f"**Passed**: {test_results['passed']} | "
        f"**Failed**: {test_results['failed']}",
        "",
        "## Results",
        "",
        "| # | Test | Status | Response Time | Details |",
        "|---|---|---|---|---|",
    ]

    for i, r in enumerate(test_results["results"], 1):
        status = "PASS" if r["passed"] else "FAIL"
        rt = f"{r['response_time_ms']}ms" if r["response_time_ms"] else "N/A"
        details = r.get("error", "") or ""
        name = r.get("name", r.get("url", ""))
        lines.append(f"| {i} | {name} | {status} | {rt} | {details} |")

    lines.append("")

    with open(output_path, "w") as f:
        f.write("\n".join(lines))

    return output_path


def _safe_json(resp: requests.Response) -> dict | str | None:
    """Safely parse JSON response.

    For binary responses (images, files, etc.), returns a summary string
    with content type and size instead of garbled text.
    """
    content_type = resp.headers.get("content-type", "")
    if content_type and not content_type.startswith(("application/json", "text/")):
        return f"[binary: {content_type}, {len(resp.content)} bytes]"
    try:
        return resp.json()
    except (json.JSONDecodeError, ValueError):
        return resp.text[:500] if resp.text else None
