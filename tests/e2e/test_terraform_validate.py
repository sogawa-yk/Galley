"""terraform validate E2Eテスト。

OCI接続不要。terraform init -backend=false → terraform validate を実行し、
生成されたTerraformコードが構文的に正しいことを検証する。
"""

import asyncio
from typing import Any

import pytest

from galley.services.design import DesignService
from galley.services.hearing import HearingService

from .conftest import create_session_with_component

pytestmark = pytest.mark.e2e


async def _run_subprocess(args: list[str], cwd: str) -> tuple[int, str, str]:
    """サブプロセスを非同期で実行する。"""
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
    )
    stdout_bytes, stderr_bytes = await proc.communicate()
    return (
        proc.returncode or 0,
        stdout_bytes.decode("utf-8", errors="replace"),
        stderr_bytes.decode("utf-8", errors="replace"),
    )


async def _terraform_validate(terraform_dir: str) -> tuple[int, str, str]:
    """terraform init -backend=false && terraform validate を実行する。"""
    exit_code, stdout, stderr = await _run_subprocess(
        ["terraform", "init", "-backend=false", "-no-color", "-input=false"],
        cwd=terraform_dir,
    )
    if exit_code != 0:
        return exit_code, stdout, f"terraform init failed:\n{stderr}"

    return await _run_subprocess(
        ["terraform", "validate", "-no-color"],
        cwd=terraform_dir,
    )


# 全10サービスタイプのパラメトリックテスト
@pytest.mark.parametrize(
    "service_type,display_name,config",
    [
        ("vcn", "Test VCN", {"cidr_block": "10.0.0.0/16"}),
        ("compute", "Test Compute", {}),
        ("oke", "Test OKE", {}),
        ("adb", "Test ADB", {}),
        ("apigateway", "Test API GW", {}),
        ("functions", "Test Function", {}),
        ("objectstorage", "Test Bucket", {}),
        ("loadbalancer", "Test LB", {}),
        ("streaming", "Test Stream", {}),
        ("nosql", "Test NoSQL", {}),
    ],
    ids=[
        "vcn",
        "compute",
        "oke",
        "adb",
        "apigateway",
        "functions",
        "objectstorage",
        "loadbalancer",
        "streaming",
        "nosql",
    ],
)
async def test_single_component_validates(
    hearing_service: HearingService,
    design_service: DesignService,
    service_type: str,
    display_name: str,
    config: dict[str, Any],
) -> None:
    """各サービスタイプ単体でterraform validateが成功する。"""
    components = [{"service_type": service_type, "display_name": display_name, "config": config}]
    _, terraform_dir = await create_session_with_component(hearing_service, design_service, components)

    exit_code, stdout, stderr = await _terraform_validate(terraform_dir)
    assert exit_code == 0, f"terraform validate failed for {service_type}:\nstdout: {stdout}\nstderr: {stderr}"


async def test_multi_component_validates(
    hearing_service: HearingService,
    design_service: DesignService,
) -> None:
    """複数コンポーネントの組み合わせでterraform validateが成功する。"""
    components = [
        {"service_type": "vcn", "display_name": "Main VCN", "config": {"cidr_block": "10.0.0.0/16"}},
        {"service_type": "adb", "display_name": "Analytics DB"},
        {"service_type": "streaming", "display_name": "Event Stream"},
    ]
    _, terraform_dir = await create_session_with_component(hearing_service, design_service, components)

    exit_code, stdout, stderr = await _terraform_validate(terraform_dir)
    assert exit_code == 0, f"terraform validate failed for multi-component:\nstdout: {stdout}\nstderr: {stderr}"


async def test_all_service_types_combined_validates(
    hearing_service: HearingService,
    design_service: DesignService,
) -> None:
    """全10サービスタイプを同時に含むアーキテクチャでterraform validateが成功する。"""
    components = [
        {"service_type": "vcn", "display_name": "VCN", "config": {"cidr_block": "10.0.0.0/16"}},
        {"service_type": "compute", "display_name": "Compute"},
        {"service_type": "oke", "display_name": "OKE"},
        {"service_type": "adb", "display_name": "ADB"},
        {"service_type": "apigateway", "display_name": "API GW"},
        {"service_type": "functions", "display_name": "Function"},
        {"service_type": "objectstorage", "display_name": "Bucket"},
        {"service_type": "loadbalancer", "display_name": "LB"},
        {"service_type": "streaming", "display_name": "Stream"},
        {"service_type": "nosql", "display_name": "NoSQL"},
    ]
    _, terraform_dir = await create_session_with_component(hearing_service, design_service, components)

    exit_code, stdout, stderr = await _terraform_validate(terraform_dir)
    assert exit_code == 0, f"terraform validate failed for all types:\nstdout: {stdout}\nstderr: {stderr}"
