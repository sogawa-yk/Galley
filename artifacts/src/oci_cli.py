"""OCI CLI Wrapper Module.

Provides Python functions to execute OCI CLI commands and parse results.
Uses instance principal authentication (no explicit auth configuration needed).
"""

import json
import os
import subprocess


def run_command(args: list[str], timeout: int = 120) -> dict:
    """Execute an OCI CLI command and return parsed JSON result.

    Args:
        args: OCI CLI arguments (without the leading 'oci').
        timeout: Command timeout in seconds.

    Returns:
        Parsed JSON response as dict.

    Raises:
        RuntimeError: If the command fails.
    """
    cmd = ["oci"] + args + ["--output", "json"]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"OCI CLI failed (exit {result.returncode}): {result.stderr.strip()}"
        )
    if not result.stdout.strip():
        return {}
    return json.loads(result.stdout)


def get_instance_metadata() -> dict:
    """Retrieve instance metadata from the metadata service.

    Returns:
        Instance metadata as dict.

    Raises:
        RuntimeError: If metadata service is unreachable.
    """
    import requests

    url = "http://169.254.169.254/opc/v2/instance/"
    headers = {"Authorization": "Bearer Oracle"}
    resp = requests.get(url, headers=headers, timeout=5)
    resp.raise_for_status()
    return resp.json()


def get_compartment_id() -> str:
    """Resolve compartment ID using fallback chain.

    Order:
        1. Instance metadata (instance principal)
        2. OCI_COMPARTMENT_ID environment variable
        3. Raises RuntimeError (caller should ask user)

    Returns:
        Compartment OCID.

    Raises:
        RuntimeError: If compartment ID cannot be resolved automatically.
    """
    # 1. Instance metadata
    try:
        metadata = get_instance_metadata()
        compartment_id = metadata.get("compartmentId")
        if compartment_id:
            return compartment_id
    except Exception:
        pass

    # 2. Environment variable
    compartment_id = os.environ.get("OCI_COMPARTMENT_ID")
    if compartment_id:
        return compartment_id

    # 3. Cannot resolve
    raise RuntimeError(
        "Could not resolve compartment ID. "
        "Set OCI_COMPARTMENT_ID environment variable or run on an OCI instance."
    )


def get_region() -> str:
    """Get the current region.

    Order:
        1. Instance metadata
        2. OCI_REGION environment variable

    Returns:
        Region identifier string.

    Raises:
        RuntimeError: If region cannot be resolved.
    """
    try:
        metadata = get_instance_metadata()
        region = metadata.get("canonicalRegionName") or metadata.get("region")
        if region:
            return region
    except Exception:
        pass

    region = os.environ.get("OCI_REGION")
    if region:
        return region

    raise RuntimeError("Could not resolve region.")


def get_tenancy_id() -> str:
    """Get tenancy OCID from instance metadata or environment.

    Returns:
        Tenancy OCID.
    """
    try:
        metadata = get_instance_metadata()
        # Tenancy is in the compartment hierarchy root
        result = run_command([
            "iam", "compartment", "get",
            "--compartment-id", metadata["compartmentId"],
        ])
        return result["data"]["compartment-id"]
    except Exception:
        pass

    tenancy_id = os.environ.get("OCI_TENANCY_ID")
    if tenancy_id:
        return tenancy_id

    raise RuntimeError("Could not resolve tenancy ID.")


def list_resources(resource_type: str, compartment_id: str) -> list[dict]:
    """List resources of given type in a compartment.

    Args:
        resource_type: OCI resource type command (e.g., 'compute instance').
        compartment_id: Compartment OCID.

    Returns:
        List of resource dicts.
    """
    args = resource_type.split() + ["list", "--compartment-id", compartment_id]
    result = run_command(args)
    return result.get("data", [])


def get_resource(resource_type: str, resource_id: str) -> dict:
    """Get details of a specific resource.

    Args:
        resource_type: OCI resource type command (e.g., 'compute instance').
        resource_id: Resource OCID.

    Returns:
        Resource details dict.
    """
    type_parts = resource_type.split()
    args = type_parts + ["get", f"--{type_parts[-1]}-id", resource_id]
    result = run_command(args)
    return result.get("data", {})
