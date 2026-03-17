"""Reporter Module.

Provides functions for progress reporting and final summary generation.
"""

import json
from datetime import datetime, timezone


def report_progress(
    phase: str,
    status: str,
    details: str,
    output_path: str,
) -> None:
    """Append a progress entry to the report file.

    Args:
        phase: Current phase name.
        status: Status (started/completed/failed).
        details: Additional details.
        output_path: Path to the progress report file.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = f"\n## {phase}\n- **Status**: {status}\n- **Time**: {timestamp}\n- **Details**: {details}\n"

    with open(output_path, "a") as f:
        f.write(entry)


def generate_summary(
    project_name: str,
    stack_id: str,
    endpoints: dict,
    test_results: dict,
    output_path: str,
) -> str:
    """Generate a final summary report.

    Args:
        project_name: Project name.
        stack_id: Resource Manager Stack OCID.
        endpoints: Deployment endpoints.
        test_results: E2E test results.
        output_path: Path to write the summary.

    Returns:
        Path to the summary file.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    url = endpoints.get("url", "N/A")
    health_url = endpoints.get("health_url", "N/A")
    compute_type = endpoints.get("compute_type", "N/A")

    passed = test_results.get("passed", 0)
    total = test_results.get("total", 0)
    test_status = "ALL PASSED" if passed == total else f"{passed}/{total} PASSED"

    lines = [
        f"# Demo Environment Summary - {project_name}",
        "",
        f"**Generated**: {timestamp}",
        "",
        "## Environment Info",
        f"- **Project**: {project_name}",
        f"- **Compute Type**: {compute_type}",
        f"- **Application URL**: {url}",
        f"- **Health Check**: {health_url}",
        "",
        "## Infrastructure",
        f"- **Stack OCID**: `{stack_id}`",
        "- **Cleanup**: OCI Console > Resource Manager > Stacks > Delete (Destroy)",
        "",
        "## Test Results",
        f"- **Status**: {test_status}",
        f"- **Passed**: {passed}",
        f"- **Total**: {total}",
        "",
        "## Quick Links",
        f"- Application: {url}",
        f"- Health Check: {health_url}",
        f"- OCI Console: https://cloud.oracle.com/resourcemanager/stacks",
        "",
    ]

    with open(output_path, "w") as f:
        f.write("\n".join(lines))

    return output_path


def report_error(
    phase: str,
    error: str,
    context: dict,
    output_path: str,
) -> None:
    """Append an error entry to the report file.

    Args:
        phase: Phase where error occurred.
        error: Error message.
        context: Additional context dict.
        output_path: Path to the report file.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    ctx = json.dumps(context, indent=2, default=str)
    entry = (
        f"\n## ERROR - {phase}\n"
        f"- **Time**: {timestamp}\n"
        f"- **Error**: {error}\n"
        f"- **Context**:\n```json\n{ctx}\n```\n"
    )

    with open(output_path, "a") as f:
        f.write(entry)
