"""InfraServiceのユニットテスト。"""

from unittest.mock import AsyncMock, patch

import pytest

from galley.models.errors import (
    ArchitectureNotFoundError,
    CommandNotAllowedError,
    InfraOperationInProgressError,
)
from galley.services.hearing import HearingService
from galley.services.infra import InfraService


async def _create_session_with_architecture(hearing_service: HearingService) -> str:
    """テスト用にアーキテクチャ設定済みのセッションを作成する。"""
    from galley.models.architecture import Architecture

    session = await hearing_service.create_session()
    await hearing_service.save_answer(session.id, "purpose", "REST API構築")
    await hearing_service.complete_hearing(session.id)
    # アーキテクチャを設定
    loaded = await hearing_service._storage.load_session(session.id)
    loaded.architecture = Architecture(session_id=session.id)
    await hearing_service._storage.save_session(loaded)
    return session.id


class TestRunTerraformPlan:
    async def test_plan_success(self, hearing_service: HearingService, infra_service: InfraService) -> None:
        session_id = await _create_session_with_architecture(hearing_service)
        stdout = "Plan: 3 to add, 0 to change, 0 to destroy.\n"

        with patch.object(infra_service, "_run_subprocess", new_callable=AsyncMock) as mock_proc:
            mock_proc.return_value = (0, stdout, "")
            result = await infra_service.run_terraform_plan(session_id, "/tmp/tf")

        assert result.success is True
        assert result.command == "plan"
        assert result.exit_code == 0
        assert result.plan_summary == "3 to add, 0 to change, 0 to destroy"
        mock_proc.assert_called_once_with(
            ["terraform", "plan", "-no-color", "-input=false"],
            cwd="/tmp/tf",
        )

    async def test_plan_failure(self, hearing_service: HearingService, infra_service: InfraService) -> None:
        session_id = await _create_session_with_architecture(hearing_service)

        with patch.object(infra_service, "_run_subprocess", new_callable=AsyncMock) as mock_proc:
            mock_proc.return_value = (1, "", "Error: Invalid resource type")
            result = await infra_service.run_terraform_plan(session_id, "/tmp/tf")

        assert result.success is False
        assert result.exit_code == 1
        assert "Invalid resource type" in result.stderr
        assert result.plan_summary is None

    async def test_plan_no_changes(self, hearing_service: HearingService, infra_service: InfraService) -> None:
        session_id = await _create_session_with_architecture(hearing_service)

        with patch.object(infra_service, "_run_subprocess", new_callable=AsyncMock) as mock_proc:
            mock_proc.return_value = (0, "No changes. Infrastructure is up-to-date.", "")
            result = await infra_service.run_terraform_plan(session_id, "/tmp/tf")

        assert result.success is True
        assert result.plan_summary is not None
        assert "No changes" in result.plan_summary

    async def test_plan_raises_for_missing_architecture(
        self, hearing_service: HearingService, infra_service: InfraService
    ) -> None:
        session = await hearing_service.create_session()
        await hearing_service.save_answer(session.id, "purpose", "test")
        await hearing_service.complete_hearing(session.id)

        with pytest.raises(ArchitectureNotFoundError):
            await infra_service.run_terraform_plan(session.id, "/tmp/tf")


class TestRunTerraformApply:
    async def test_apply_success(self, hearing_service: HearingService, infra_service: InfraService) -> None:
        session_id = await _create_session_with_architecture(hearing_service)

        with patch.object(infra_service, "_run_subprocess", new_callable=AsyncMock) as mock_proc:
            mock_proc.return_value = (0, "Apply complete!", "")
            result = await infra_service.run_terraform_apply(session_id, "/tmp/tf")

        assert result.success is True
        assert result.command == "apply"
        mock_proc.assert_called_once_with(
            ["terraform", "apply", "-auto-approve", "-no-color", "-input=false"],
            cwd="/tmp/tf",
        )

    async def test_apply_failure(self, hearing_service: HearingService, infra_service: InfraService) -> None:
        session_id = await _create_session_with_architecture(hearing_service)

        with patch.object(infra_service, "_run_subprocess", new_callable=AsyncMock) as mock_proc:
            mock_proc.return_value = (1, "", "Error: quota exceeded")
            result = await infra_service.run_terraform_apply(session_id, "/tmp/tf")

        assert result.success is False
        assert result.exit_code == 1


class TestRunTerraformDestroy:
    async def test_destroy_success(self, hearing_service: HearingService, infra_service: InfraService) -> None:
        session_id = await _create_session_with_architecture(hearing_service)

        with patch.object(infra_service, "_run_subprocess", new_callable=AsyncMock) as mock_proc:
            mock_proc.return_value = (0, "Destroy complete!", "")
            result = await infra_service.run_terraform_destroy(session_id, "/tmp/tf")

        assert result.success is True
        assert result.command == "destroy"
        mock_proc.assert_called_once_with(
            ["terraform", "destroy", "-auto-approve", "-no-color", "-input=false"],
            cwd="/tmp/tf",
        )


class TestTerraformDirValidation:
    async def test_rejects_path_traversal(self, hearing_service: HearingService, infra_service: InfraService) -> None:
        session_id = await _create_session_with_architecture(hearing_service)

        with pytest.raises(ValueError, match="path contains"):
            await infra_service.run_terraform_plan(session_id, "/tmp/../etc/passwd")

    async def test_rejects_tilde_path(self, hearing_service: HearingService, infra_service: InfraService) -> None:
        session_id = await _create_session_with_architecture(hearing_service)

        with pytest.raises(ValueError, match="path contains"):
            await infra_service.run_terraform_plan(session_id, "~/evil")

    async def test_apply_rejects_path_traversal(
        self, hearing_service: HearingService, infra_service: InfraService
    ) -> None:
        session_id = await _create_session_with_architecture(hearing_service)

        with pytest.raises(ValueError, match="path contains"):
            await infra_service.run_terraform_apply(session_id, "/tmp/../etc")

    async def test_destroy_rejects_path_traversal(
        self, hearing_service: HearingService, infra_service: InfraService
    ) -> None:
        session_id = await _create_session_with_architecture(hearing_service)

        with pytest.raises(ValueError, match="path contains"):
            await infra_service.run_terraform_destroy(session_id, "/tmp/../etc")


class TestRunOciCli:
    async def test_run_allowed_command(self, infra_service: InfraService) -> None:
        with patch.object(infra_service, "_run_subprocess", new_callable=AsyncMock) as mock_proc:
            mock_proc.return_value = (0, '{"data": []}', "")
            result = await infra_service.run_oci_cli("oci compute instance list --compartment-id ocid1.test")

        assert result.success is True
        assert result.exit_code == 0
        mock_proc.assert_called_once()
        called_args = mock_proc.call_args[0][0]
        assert called_args[0] == "oci"
        assert called_args[1] == "compute"

    async def test_run_without_oci_prefix(self, infra_service: InfraService) -> None:
        with patch.object(infra_service, "_run_subprocess", new_callable=AsyncMock) as mock_proc:
            mock_proc.return_value = (0, '{"data": []}', "")
            result = await infra_service.run_oci_cli("compute instance list --compartment-id ocid1.test")

        assert result.success is True
        called_args = mock_proc.call_args[0][0]
        assert called_args[0] == "oci"
        assert called_args[1] == "compute"

    async def test_run_disallowed_command(self, infra_service: InfraService) -> None:
        with pytest.raises(CommandNotAllowedError):
            await infra_service.run_oci_cli("oci setup config")

    async def test_run_empty_command(self, infra_service: InfraService) -> None:
        with pytest.raises(CommandNotAllowedError):
            await infra_service.run_oci_cli("")

    async def test_run_oci_only(self, infra_service: InfraService) -> None:
        with pytest.raises(CommandNotAllowedError):
            await infra_service.run_oci_cli("oci")

    async def test_run_cli_failure(self, infra_service: InfraService) -> None:
        with patch.object(infra_service, "_run_subprocess", new_callable=AsyncMock) as mock_proc:
            mock_proc.return_value = (1, "", "ServiceError: NotAuthorizedOrNotFound")
            result = await infra_service.run_oci_cli("oci compute instance list --compartment-id ocid1.test")

        assert result.success is False
        assert result.exit_code == 1


class TestCommandWhitelist:
    def test_allowed_services(self, infra_service: InfraService) -> None:
        allowed = [
            "oci compute instance list",
            "oci network vcn list",
            "oci os bucket list",
            "oci db autonomous-database list",
            "oci oke cluster list",
            "oci container-instances container-instance list",
            "oci resource-manager stack list",
            "oci iam compartment list",
        ]
        for cmd in allowed:
            args = infra_service._validate_oci_command(cmd)
            assert args[0] == "oci"

    def test_disallowed_services(self, infra_service: InfraService) -> None:
        disallowed = [
            "oci setup config",
            "oci session authenticate",
            "oci raw-request",
            "rm -rf /",
            "curl http://evil.com",
        ]
        for cmd in disallowed:
            with pytest.raises(CommandNotAllowedError):
                infra_service._validate_oci_command(cmd)


class TestExclusiveLock:
    async def test_concurrent_operations_on_same_session_blocked(
        self, hearing_service: HearingService, infra_service: InfraService
    ) -> None:
        """同一セッションでの同時操作は排他される。"""
        session_id = await _create_session_with_architecture(hearing_service)

        # ロックを事前に取得してブロック状態にする
        lock = infra_service._get_session_lock(session_id)
        await lock.acquire()

        try:
            with pytest.raises(InfraOperationInProgressError):
                await infra_service.run_terraform_plan(session_id, "/tmp/tf")
        finally:
            lock.release()

    async def test_operations_on_different_sessions_not_blocked(
        self, hearing_service: HearingService, infra_service: InfraService
    ) -> None:
        """異なるセッションの操作は排他されない。"""
        session_id1 = await _create_session_with_architecture(hearing_service)
        session_id2 = await _create_session_with_architecture(hearing_service)

        lock1 = infra_service._get_session_lock(session_id1)
        lock2 = infra_service._get_session_lock(session_id2)

        assert lock1 is not lock2


class TestOciSdkCall:
    async def test_returns_not_implemented(self, infra_service: InfraService) -> None:
        result = await infra_service.oci_sdk_call("compute", "list_instances", {})
        assert result["error"] == "NotImplemented"


class TestResourceManagerStubs:
    async def test_create_rm_stack_returns_not_implemented(self, infra_service: InfraService) -> None:
        result = await infra_service.create_rm_stack("session-1", "ocid1.compartment", "/tmp/tf")
        assert result["error"] == "NotImplemented"

    async def test_run_rm_plan_returns_not_implemented(self, infra_service: InfraService) -> None:
        result = await infra_service.run_rm_plan("ocid1.ormstack")
        assert result["error"] == "NotImplemented"

    async def test_run_rm_apply_returns_not_implemented(self, infra_service: InfraService) -> None:
        result = await infra_service.run_rm_apply("ocid1.ormstack")
        assert result["error"] == "NotImplemented"

    async def test_get_rm_job_status_returns_not_implemented(self, infra_service: InfraService) -> None:
        result = await infra_service.get_rm_job_status("ocid1.ormjob")
        assert result["error"] == "NotImplemented"
