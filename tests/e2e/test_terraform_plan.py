"""terraform plan E2Eテスト。

OCI API接続が必要（リソース作成なし）。
terraform planを実行し、生成されたTerraformコードが実環境で
有効なplanを生成できることを検証する。
"""

import pytest

from galley.services.design import DesignService
from galley.services.hearing import HearingService
from galley.services.infra import InfraService

from .conftest import create_session_with_component

pytestmark = pytest.mark.e2e


async def test_vcn_plan_succeeds(
    hearing_service: HearingService,
    design_service: DesignService,
    infra_service: InfraService,
    terraform_variables: dict[str, str],
) -> None:
    """VCNコンポーネントでterraform planが成功する。"""
    components = [
        {"service_type": "vcn", "display_name": "E2E Test VCN", "config": {"cidr_block": "10.253.0.0/16"}},
    ]
    session_id, terraform_dir = await create_session_with_component(hearing_service, design_service, components)

    result = await infra_service.run_terraform_plan(session_id, terraform_dir, variables=terraform_variables)

    assert result.success, f"terraform plan failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    assert result.plan_summary is not None
    assert "to add" in result.plan_summary


async def test_adb_plan_succeeds(
    hearing_service: HearingService,
    design_service: DesignService,
    infra_service: InfraService,
    terraform_variables: dict[str, str],
) -> None:
    """ADBコンポーネントでterraform planが成功する。"""
    components = [
        {"service_type": "adb", "display_name": "E2E Test ADB"},
    ]
    session_id, terraform_dir = await create_session_with_component(hearing_service, design_service, components)

    result = await infra_service.run_terraform_plan(session_id, terraform_dir, variables=terraform_variables)

    assert result.success, f"terraform plan failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    assert result.plan_summary is not None
    assert "to add" in result.plan_summary


async def test_auto_init_on_plan(
    hearing_service: HearingService,
    design_service: DesignService,
    infra_service: InfraService,
    terraform_variables: dict[str, str],
) -> None:
    """init未実行のディレクトリでplanを実行すると自動initされる。"""
    components = [
        {"service_type": "vcn", "display_name": "Auto Init VCN", "config": {"cidr_block": "10.252.0.0/16"}},
    ]
    session_id, terraform_dir = await create_session_with_component(hearing_service, design_service, components)

    # .terraform ディレクトリが存在しないことを確認
    from pathlib import Path

    assert not (Path(terraform_dir) / ".terraform").exists()

    result = await infra_service.run_terraform_plan(session_id, terraform_dir, variables=terraform_variables)

    # auto-initが実行されplanが成功する
    assert result.success, f"terraform plan with auto-init failed:\nstderr: {result.stderr}"
    # .terraform ディレクトリが作成されている
    assert (Path(terraform_dir) / ".terraform").exists()
