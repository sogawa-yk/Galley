"""Deployer Module.

Provides functions for building container images, pushing to OCIR,
and deploying to OKE/Container Instances/Compute/Functions.
"""

import json
import subprocess
import time

import requests

from src.oci_cli import run_command


def login_to_ocir(
    region: str,
    tenancy_namespace: str,
    username: str,
    auth_token: str,
) -> bool:
    """Login to OCIR using docker login.

    Args:
        region: OCI region (e.g. 'ap-tokyo-1').
        tenancy_namespace: Tenancy namespace.
        username: OCI username or email.
        auth_token: Auth token for OCIR.

    Returns:
        True if login succeeded.

    Raises:
        RuntimeError: If docker login fails.
    """
    registry = f"{region}.ocir.io"
    cmd = f"docker login {registry} -u {tenancy_namespace}/{username} -p {auth_token}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"OCIR login failed: {result.stderr}")
    return True


def build_image(app_dir: str, image_name: str, tag: str = "latest") -> str:
    """Build a Docker image from the app directory.

    Args:
        app_dir: Path to directory containing Dockerfile.
        image_name: Image name.
        tag: Image tag.

    Returns:
        Full image name with tag.
    """
    full_name = f"{image_name}:{tag}"
    result = subprocess.run(
        ["docker", "build", "-t", full_name, app_dir],
        capture_output=True,
        text=True,
        timeout=600,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Docker build failed: {result.stderr}")
    return full_name


def get_tenancy_namespace() -> str:
    """Get the Object Storage namespace (used as OCIR tenancy namespace).

    Returns:
        Tenancy namespace string.
    """
    result = run_command(["os", "ns", "get"])
    return result["data"]


def push_to_ocir(
    image_name: str,
    region: str,
    tenancy_namespace: str,
    repo_name: str,
    tag: str = "latest",
) -> str:
    """Tag and push an image to OCIR.

    Args:
        image_name: Local image name (with tag).
        region: OCI region.
        tenancy_namespace: Tenancy namespace.
        repo_name: Repository name in OCIR.
        tag: Image tag.

    Returns:
        OCIR image URL.
    """
    ocir_url = f"{region}.ocir.io/{tenancy_namespace}/{repo_name}:{tag}"

    # Tag
    result = subprocess.run(
        ["docker", "tag", image_name, ocir_url],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Docker tag failed: {result.stderr}")

    # Push
    result = subprocess.run(
        ["docker", "push", ocir_url],
        capture_output=True,
        text=True,
        timeout=600,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Docker push failed: {result.stderr}")

    return ocir_url


def deploy_to_oke(kubeconfig_path: str, manifests_dir: str) -> dict:
    """Deploy to OKE using kubectl.

    Args:
        kubeconfig_path: Path to kubeconfig file.
        manifests_dir: Path to directory containing K8s manifests.

    Returns:
        Deployment result dict.
    """
    env_with_kubeconfig = {"KUBECONFIG": kubeconfig_path}
    result = subprocess.run(
        ["kubectl", "apply", "-f", manifests_dir],
        capture_output=True,
        text=True,
        timeout=120,
        env={**__import__("os").environ, **env_with_kubeconfig},
    )
    if result.returncode != 0:
        raise RuntimeError(f"kubectl apply failed: {result.stderr}")

    return {"status": "applied", "output": result.stdout}


def deploy_to_container_instances(
    compartment_id: str,
    image_url: str,
    display_name: str,
    subnet_id: str,
    shape: str = "CI.Standard.E4.Flex",
    ocpus: int = 1,
    memory_gb: int = 8,
    environment_variables: dict | None = None,
) -> dict:
    """Deploy to OCI Container Instances.

    Args:
        compartment_id: Compartment OCID.
        image_url: OCIR image URL.
        display_name: Container Instance display name.
        subnet_id: Subnet OCID.
        shape: CI shape.
        ocpus: Number of OCPUs.
        memory_gb: Memory in GB.
        environment_variables: Environment variables to pass to the container.

    Returns:
        Container Instance details.
    """
    container_spec = {
        "displayName": f"{display_name}-app",
        "imageUrl": image_url,
        "environmentVariables": environment_variables or {},
    }
    result = run_command([
        "container-instances", "container-instance", "create",
        "--compartment-id", compartment_id,
        "--display-name", display_name,
        "--shape", shape,
        "--shape-config", json.dumps({"ocpus": ocpus, "memoryInGBs": memory_gb}),
        "--containers", json.dumps([container_spec]),
        "--vnics", json.dumps([{"subnetId": subnet_id}]),
        "--container-restart-policy", "ALWAYS",
    ])
    return result.get("data", {})


def deploy_to_functions(
    app_dir: str,
    app_name: str,
    function_name: str,
) -> dict:
    """Deploy to OCI Functions.

    Args:
        app_dir: Path to function source directory.
        app_name: Functions Application name (NOT OCID).
            The ``fn`` CLI ``--app`` flag expects an application name,
            not an OCID.
        function_name: Function name (used for logging; the actual
            function name is determined by func.yaml in *app_dir*).

    Returns:
        Deploy result.
    """
    result = subprocess.run(
        ["fn", "deploy", "--app", app_name, "--local"],
        capture_output=True,
        text=True,
        timeout=300,
        cwd=app_dir,
    )
    if result.returncode != 0:
        raise RuntimeError(f"fn deploy failed: {result.stderr}")

    return {"status": "deployed", "output": result.stdout}


def wait_for_deployment(
    deploy_type: str,
    resource_id: str,
    timeout: int = 600,
    interval: int = 15,
) -> dict:
    """Wait for a deployment to be ready.

    Args:
        deploy_type: Type of deployment (oke/container_instances/compute).
        resource_id: Resource identifier.
        timeout: Timeout in seconds.
        interval: Polling interval in seconds.

    Returns:
        Final status dict.
    """
    start = time.time()
    while True:
        if deploy_type == "container_instances":
            status = _check_ci_status(resource_id)
        elif deploy_type == "oke":
            # OKE deployments are checked via kubectl
            return {"status": "applied"}
        elif deploy_type == "compute":
            return _poll_health(resource_id, timeout, interval)
        else:
            return {"status": "deployed"}

        if status.get("lifecycle_state") == "ACTIVE":
            return status

        elapsed = time.time() - start
        if elapsed >= timeout:
            raise TimeoutError(
                f"Deployment timed out after {timeout}s. State: {status}"
            )

        time.sleep(interval)


def _check_ci_status(ci_id: str) -> dict:
    """Check Container Instance status."""
    result = run_command([
        "container-instances", "container-instance", "get",
        "--container-instance-id", ci_id,
    ])
    data = result.get("data", {})
    return {
        "lifecycle_state": data.get("lifecycle-state"),
        "id": data.get("id"),
    }


def _poll_health(
    host: str,
    timeout: int = 600,
    interval: int = 15,
    port: int = 8080,
) -> dict:
    """Poll a compute instance health endpoint until it responds 200.

    Args:
        host: Hostname or IP of the compute instance.
        timeout: Maximum wait time in seconds.
        interval: Polling interval in seconds.
        port: Port the application listens on.

    Returns:
        Status dict with lifecycle_state.
    """
    url = f"http://{host}:{port}/health"
    start = time.time()
    while True:
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                return {"status": "healthy", "lifecycle_state": "RUNNING", "url": url}
        except requests.RequestException:
            pass

        elapsed = time.time() - start
        if elapsed >= timeout:
            raise TimeoutError(
                f"Compute health check timed out after {timeout}s for {url}"
            )
        time.sleep(interval)


def save_endpoints(
    url: str,
    project_name: str,
    compute_type: str,
    output_path: str,
) -> str:
    """Save deployment endpoints to JSON file.

    Args:
        url: Application base URL.
        project_name: Project name.
        compute_type: Compute type used.
        output_path: Path to write JSON file.

    Returns:
        Path to the output file.
    """
    data = {
        "url": url,
        "health_url": f"{url}/health",
        "compute_type": compute_type,
        "project_name": project_name,
    }
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    return output_path
