"""terraform ライフサイクル E2Eテスト。

OCI API接続が必要。実際にOCIリソースを作成・削除する。
VCNは無料・高速のため、ライフサイクルテストに使用する。
"""

import pytest

from galley.services.design import DesignService
from galley.services.hearing import HearingService
from galley.services.infra import InfraService

from .conftest import create_session_with_component

pytestmark = [pytest.mark.e2e, pytest.mark.e2e_lifecycle]


async def test_vcn_full_lifecycle(
    hearing_service: HearingService,
    design_service: DesignService,
    infra_service: InfraService,
    terraform_variables: dict[str, str],
) -> None:
    """VCNのplan → apply → re-plan（冪等性）→ destroyのフルライフサイクル。"""
    components = [
        {
            "service_type": "vcn",
            "display_name": "E2E Lifecycle VCN",
            "config": {"cidr_block": "10.254.0.0/16"},
        },
    ]
    session_id, terraform_dir = await create_session_with_component(hearing_service, design_service, components)

    try:
        # 1. Plan
        plan_result = await infra_service.run_terraform_plan(session_id, terraform_dir, variables=terraform_variables)
        assert plan_result.success, f"plan failed:\nstderr: {plan_result.stderr}"
        assert plan_result.plan_summary is not None
        assert "1 to add" in plan_result.plan_summary

        # 2. Apply
        apply_result = await infra_service.run_terraform_apply(session_id, terraform_dir, variables=terraform_variables)
        assert apply_result.success, f"apply failed:\nstderr: {apply_result.stderr}"
        assert "Apply complete" in apply_result.stdout

        # 3. Re-plan（冪等性確認 — 変更なしであること）
        replan_result = await infra_service.run_terraform_plan(session_id, terraform_dir, variables=terraform_variables)
        assert replan_result.success, f"re-plan failed:\nstderr: {replan_result.stderr}"
        assert replan_result.plan_summary is not None
        assert (
            "No changes" in replan_result.plan_summary
            or "0 to add, 0 to change, 0 to destroy" in replan_result.plan_summary
        )

    finally:
        # 4. Destroy（テスト失敗時もクリーンアップ保証）
        destroy_result = await infra_service.run_terraform_destroy(
            session_id, terraform_dir, variables=terraform_variables
        )
        assert destroy_result.success, f"destroy failed:\nstderr: {destroy_result.stderr}"
        assert "Destroy complete" in destroy_result.stdout
