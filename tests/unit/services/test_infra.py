"""InfraServiceのユニットテスト。"""

import base64
import io
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from galley.models.errors import (
    ArchitectureNotFoundError,
    CommandNotAllowedError,
    InfraOperationInProgressError,
)
from galley.models.infra import TerraformResult
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
        plan_result = TerraformResult(
            success=True,
            command="plan",
            stdout="Plan: 3 to add, 0 to change, 0 to destroy.\n",
            stderr="",
            exit_code=0,
            plan_summary="3 to add, 0 to change, 0 to destroy",
        )

        with (
            patch.object(infra_service, "_ensure_rm_stack", new_callable=AsyncMock, return_value="ocid1.stack.test"),
            patch.object(infra_service, "_run_rm_job", new_callable=AsyncMock, return_value=plan_result),
        ):
            result = await infra_service.run_terraform_plan(session_id, "/tmp/tf")

        assert result.success is True
        assert result.command == "plan"
        assert result.plan_summary == "3 to add, 0 to change, 0 to destroy"

    async def test_plan_failure(self, hearing_service: HearingService, infra_service: InfraService) -> None:
        session_id = await _create_session_with_architecture(hearing_service)
        plan_result = TerraformResult(
            success=False,
            command="plan",
            stdout="",
            stderr="Job FAILED. Job ID: ocid1.job.test",
            exit_code=1,
        )

        with (
            patch.object(infra_service, "_ensure_rm_stack", new_callable=AsyncMock, return_value="ocid1.stack.test"),
            patch.object(infra_service, "_run_rm_job", new_callable=AsyncMock, return_value=plan_result),
        ):
            result = await infra_service.run_terraform_plan(session_id, "/tmp/tf")

        assert result.success is False
        assert result.exit_code == 1

    async def test_plan_rm_exception_returns_error_result(
        self, hearing_service: HearingService, infra_service: InfraService
    ) -> None:
        """RMスタック作成失敗時にエラー結果を返す。"""
        session_id = await _create_session_with_architecture(hearing_service)

        with patch.object(
            infra_service, "_ensure_rm_stack", new_callable=AsyncMock, side_effect=Exception("Stack creation failed")
        ):
            result = await infra_service.run_terraform_plan(session_id, "/tmp/tf")

        assert result.success is False
        assert "Stack creation failed" in result.stderr

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
        apply_result = TerraformResult(success=True, command="apply", stdout="Apply complete!", stderr="", exit_code=0)

        with (
            patch.object(infra_service, "_ensure_rm_stack", new_callable=AsyncMock, return_value="ocid1.stack.test"),
            patch.object(infra_service, "_run_rm_job", new_callable=AsyncMock, return_value=apply_result) as mock_job,
        ):
            result = await infra_service.run_terraform_apply(session_id, "/tmp/tf")

        assert result.success is True
        assert result.command == "apply"
        mock_job.assert_called_once_with("ocid1.stack.test", "APPLY", "apply")

    async def test_apply_failure(self, hearing_service: HearingService, infra_service: InfraService) -> None:
        session_id = await _create_session_with_architecture(hearing_service)
        apply_result = TerraformResult(success=False, command="apply", stdout="", stderr="Job FAILED.", exit_code=1)

        with (
            patch.object(infra_service, "_ensure_rm_stack", new_callable=AsyncMock, return_value="ocid1.stack.test"),
            patch.object(infra_service, "_run_rm_job", new_callable=AsyncMock, return_value=apply_result),
        ):
            result = await infra_service.run_terraform_apply(session_id, "/tmp/tf")

        assert result.success is False
        assert result.exit_code == 1


class TestRunTerraformDestroy:
    async def test_destroy_success(self, hearing_service: HearingService, infra_service: InfraService) -> None:
        session_id = await _create_session_with_architecture(hearing_service)
        destroy_result = TerraformResult(
            success=True, command="destroy", stdout="Destroy complete!", stderr="", exit_code=0
        )

        with (
            patch.object(infra_service, "_ensure_rm_stack", new_callable=AsyncMock, return_value="ocid1.stack.test"),
            patch.object(infra_service, "_run_rm_job", new_callable=AsyncMock, return_value=destroy_result) as mock_job,
        ):
            result = await infra_service.run_terraform_destroy(session_id, "/tmp/tf")

        assert result.success is True
        assert result.command == "destroy"
        mock_job.assert_called_once_with("ocid1.stack.test", "DESTROY", "destroy")


class TestZipTerraformDir:
    def test_zip_includes_tf_files(self, tmp_path: Path) -> None:
        """Terraformファイルがzipに含まれる。"""
        (tmp_path / "main.tf").write_text("provider {}")
        (tmp_path / "variables.tf").write_text("variable {}")

        result = InfraService._zip_terraform_dir(tmp_path)
        decoded = base64.b64decode(result)
        with zipfile.ZipFile(io.BytesIO(decoded)) as zf:
            names = set(zf.namelist())
            assert "main.tf" in names
            assert "variables.tf" in names

    def test_zip_excludes_terraform_dir(self, tmp_path: Path) -> None:
        """.terraform/ ディレクトリが除外される。"""
        (tmp_path / "main.tf").write_text("provider {}")
        tf_cache = tmp_path / ".terraform" / "providers"
        tf_cache.mkdir(parents=True)
        (tf_cache / "provider.tf").write_text("cached")

        result = InfraService._zip_terraform_dir(tmp_path)
        decoded = base64.b64decode(result)
        with zipfile.ZipFile(io.BytesIO(decoded)) as zf:
            names = zf.namelist()
            assert not any(".terraform" in n for n in names)

    def test_zip_excludes_tfstate(self, tmp_path: Path) -> None:
        """*.tfstate* ファイルが除外される。"""
        (tmp_path / "main.tf").write_text("provider {}")
        (tmp_path / "terraform.tfstate").write_text("{}")
        (tmp_path / "terraform.tfstate.backup").write_text("{}")

        result = InfraService._zip_terraform_dir(tmp_path)
        decoded = base64.b64decode(result)
        with zipfile.ZipFile(io.BytesIO(decoded)) as zf:
            names = zf.namelist()
            assert not any("tfstate" in n for n in names)

    def test_zip_uses_relative_paths(self, tmp_path: Path) -> None:
        """zipアーカイブ内のパスが相対パスになる。"""
        sub = tmp_path / "modules"
        sub.mkdir()
        (tmp_path / "main.tf").write_text("provider {}")
        (sub / "network.tf").write_text("resource {}")

        result = InfraService._zip_terraform_dir(tmp_path)
        decoded = base64.b64decode(result)
        with zipfile.ZipFile(io.BytesIO(decoded)) as zf:
            names = set(zf.namelist())
            assert "main.tf" in names
            assert "modules/network.tf" in names
            # 絶対パスが含まれないこと
            assert not any(n.startswith("/") for n in names)


class TestBuildRmVariables:
    def test_adds_auto_variables_from_env(self, infra_service: InfraService, monkeypatch: pytest.MonkeyPatch) -> None:
        """環境変数からregion/compartment_ocidを自動設定する。"""
        monkeypatch.setenv("GALLEY_REGION", "ap-osaka-1")
        monkeypatch.setenv("GALLEY_WORK_COMPARTMENT_ID", "ocid1.compartment.test")
        monkeypatch.delenv("OCI_RESOURCE_PRINCIPAL_VERSION", raising=False)
        with patch("galley.services.infra.oci.config.from_file", return_value={"tenancy": "ocid1.tenancy.test"}):
            result = infra_service._build_rm_variables(None)
        assert result["region"] == "ap-osaka-1"
        assert result["compartment_ocid"] == "ocid1.compartment.test"
        assert result["tenancy_ocid"] == "ocid1.tenancy.test"

    def test_user_variables_override_auto(self, infra_service: InfraService, monkeypatch: pytest.MonkeyPatch) -> None:
        """ユーザー指定値が自動設定より優先される。"""
        monkeypatch.setenv("GALLEY_REGION", "ap-osaka-1")
        monkeypatch.setenv("GALLEY_WORK_COMPARTMENT_ID", "ocid1.compartment.env")
        variables = {
            "region": "us-ashburn-1",
            "compartment_ocid": "ocid1.compartment.user",
            "tenancy_ocid": "ocid1.tenancy.user",
            "subnet_id": "ocid1.subnet",
        }
        result = infra_service._build_rm_variables(variables)
        assert result["region"] == "us-ashburn-1"
        assert result["compartment_ocid"] == "ocid1.compartment.user"
        assert result["tenancy_ocid"] == "ocid1.tenancy.user"
        assert result["subnet_id"] == "ocid1.subnet"

    def test_none_returns_auto_variables(self, infra_service: InfraService, monkeypatch: pytest.MonkeyPatch) -> None:
        """Noneの場合も自動変数が設定される。"""
        monkeypatch.setenv("GALLEY_REGION", "ap-tokyo-1")
        monkeypatch.setenv("GALLEY_WORK_COMPARTMENT_ID", "ocid1.compartment.test")
        monkeypatch.delenv("OCI_RESOURCE_PRINCIPAL_VERSION", raising=False)
        with patch("galley.services.infra.oci.config.from_file", return_value={"tenancy": "ocid1.tenancy.test"}):
            result = infra_service._build_rm_variables(None)
        assert "region" in result
        assert "compartment_ocid" in result
        assert "tenancy_ocid" in result

    def test_preserves_user_variables(self, infra_service: InfraService, monkeypatch: pytest.MonkeyPatch) -> None:
        """ユーザー指定の非自動変数が保持される。"""
        monkeypatch.setenv("GALLEY_REGION", "ap-osaka-1")
        monkeypatch.setenv("GALLEY_WORK_COMPARTMENT_ID", "ocid1.compartment.test")
        monkeypatch.delenv("OCI_RESOURCE_PRINCIPAL_VERSION", raising=False)
        variables = {"subnet_id": "ocid1.subnet", "image_id": "ocid1.image"}
        with patch("galley.services.infra.oci.config.from_file", return_value={"tenancy": "ocid1.tenancy.test"}):
            result = infra_service._build_rm_variables(variables)
        assert result["subnet_id"] == "ocid1.subnet"
        assert result["image_id"] == "ocid1.image"


class TestGetRmClient:
    def test_api_key_auth(self, infra_service: InfraService, monkeypatch: pytest.MonkeyPatch) -> None:
        """API Key認証でRMクライアントが初期化される。"""
        monkeypatch.delenv("OCI_RESOURCE_PRINCIPAL_VERSION", raising=False)
        mock_config = {"region": "ap-osaka-1"}
        with (
            patch("galley.services.infra.oci.config.from_file", return_value=mock_config) as mock_from_file,
            patch("galley.services.infra.oci.resource_manager.ResourceManagerClient") as mock_client_cls,
        ):
            client = infra_service._get_rm_client()
            mock_from_file.assert_called_once()
            mock_client_cls.assert_called_once_with(mock_config)
            assert client is mock_client_cls.return_value

    def test_resource_principal_auth(self, infra_service: InfraService, monkeypatch: pytest.MonkeyPatch) -> None:
        """ResourcePrincipal認証でRMクライアントが初期化される。"""
        monkeypatch.setenv("OCI_RESOURCE_PRINCIPAL_VERSION", "2.2")
        mock_signer = MagicMock()
        with (
            patch("galley.services.infra.oci.auth.signers.get_resource_principals_signer", return_value=mock_signer),
            patch("galley.services.infra.oci.resource_manager.ResourceManagerClient") as mock_client_cls,
        ):
            client = infra_service._get_rm_client()
            mock_client_cls.assert_called_once_with({}, signer=mock_signer)
            assert client is mock_client_cls.return_value

    def test_caches_client(self, infra_service: InfraService, monkeypatch: pytest.MonkeyPatch) -> None:
        """RMクライアントがキャッシュされる。"""
        monkeypatch.delenv("OCI_RESOURCE_PRINCIPAL_VERSION", raising=False)
        with (
            patch("galley.services.infra.oci.config.from_file", return_value={}),
            patch("galley.services.infra.oci.resource_manager.ResourceManagerClient"),
        ):
            client1 = infra_service._get_rm_client()
            client2 = infra_service._get_rm_client()
            assert client1 is client2


class TestEnsureRmStack:
    async def test_creates_new_stack(
        self, hearing_service: HearingService, infra_service: InfraService, tmp_path: Path
    ) -> None:
        """スタック未作成時に新規作成する。"""
        session_id = await _create_session_with_architecture(hearing_service)
        (tmp_path / "main.tf").write_text("provider {}")

        mock_client = MagicMock()
        mock_response = SimpleNamespace(data=SimpleNamespace(id="ocid1.stack.new"))
        mock_client.create_stack.return_value = mock_response

        async def fake_to_thread(func, *args, **kwargs):
            return func(*args, **kwargs)

        with (
            patch.object(infra_service, "_get_rm_client", return_value=mock_client),
            patch("asyncio.to_thread", side_effect=fake_to_thread),
        ):
            stack_id = await infra_service._ensure_rm_stack(session_id, tmp_path)

        assert stack_id == "ocid1.stack.new"
        mock_client.create_stack.assert_called_once()
        # zip_uploadがkwargsに含まれないこと（config_source内で渡す）
        call_args = mock_client.create_stack.call_args
        assert "zip_upload" not in (call_args.kwargs or {})
        # config_sourceにzip_file_base64_encodedが設定されていること
        create_details = call_args.args[0]
        assert create_details.config_source.zip_file_base64_encoded is not None
        # セッションにstack_idが保存されている
        session = await hearing_service._storage.load_session(session_id)
        assert session.rm_stack_id == "ocid1.stack.new"

    async def test_updates_existing_stack(
        self, hearing_service: HearingService, infra_service: InfraService, tmp_path: Path
    ) -> None:
        """スタック既存時に更新する。"""
        session_id = await _create_session_with_architecture(hearing_service)
        # セッションにスタックIDを設定
        session = await hearing_service._storage.load_session(session_id)
        session.rm_stack_id = "ocid1.stack.existing"
        await hearing_service._storage.save_session(session)

        (tmp_path / "main.tf").write_text("provider {}")
        mock_client = MagicMock()

        async def fake_to_thread(func, *args, **kwargs):
            return func(*args, **kwargs)

        with (
            patch.object(infra_service, "_get_rm_client", return_value=mock_client),
            patch("asyncio.to_thread", side_effect=fake_to_thread),
        ):
            stack_id = await infra_service._ensure_rm_stack(session_id, tmp_path)

        assert stack_id == "ocid1.stack.existing"
        mock_client.update_stack.assert_called_once()
        # zip_uploadがkwargsに含まれないこと
        call_args = mock_client.update_stack.call_args
        assert "zip_upload" not in (call_args.kwargs or {})
        # config_sourceにzip_file_base64_encodedが設定されていること
        update_details = call_args.args[1]
        assert update_details.config_source.zip_file_base64_encoded is not None


class TestRunRmJob:
    async def test_plan_job_success(self, infra_service: InfraService) -> None:
        """Planジョブが成功する。"""
        mock_client = MagicMock()

        create_response = SimpleNamespace(data=SimpleNamespace(id="ocid1.job.test"))
        get_response = SimpleNamespace(data=SimpleNamespace(lifecycle_state="SUCCEEDED"))
        logs_response = SimpleNamespace(data=SimpleNamespace(text="Plan: 2 to add, 0 to change, 0 to destroy."))

        call_count = 0

        async def mock_to_thread(func, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            if func == mock_client.create_job:
                return create_response
            elif func == mock_client.get_job:
                return get_response
            elif func == mock_client.get_job_logs_content:
                return logs_response
            return None

        with (
            patch.object(infra_service, "_get_rm_client", return_value=mock_client),
            patch("asyncio.to_thread", side_effect=mock_to_thread),
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            result = await infra_service._run_rm_job("ocid1.stack.test", "PLAN", "plan")

        assert result.success is True
        assert result.command == "plan"
        assert result.plan_summary == "2 to add, 0 to change, 0 to destroy"

    async def test_apply_job_success(self, infra_service: InfraService) -> None:
        """Applyジョブが成功する。"""
        mock_client = MagicMock()

        create_response = SimpleNamespace(data=SimpleNamespace(id="ocid1.job.test"))
        get_response = SimpleNamespace(data=SimpleNamespace(lifecycle_state="SUCCEEDED"))
        logs_response = SimpleNamespace(data=SimpleNamespace(text="Apply complete!"))

        async def mock_to_thread(func, *args, **kwargs):
            if func == mock_client.create_job:
                return create_response
            elif func == mock_client.get_job:
                return get_response
            elif func == mock_client.get_job_logs_content:
                return logs_response
            return None

        with (
            patch.object(infra_service, "_get_rm_client", return_value=mock_client),
            patch("asyncio.to_thread", side_effect=mock_to_thread),
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            result = await infra_service._run_rm_job("ocid1.stack.test", "APPLY", "apply")

        assert result.success is True
        assert result.command == "apply"

    async def test_job_failure(self, infra_service: InfraService) -> None:
        """ジョブが失敗する。"""
        mock_client = MagicMock()

        create_response = SimpleNamespace(data=SimpleNamespace(id="ocid1.job.test"))
        get_response = SimpleNamespace(data=SimpleNamespace(lifecycle_state="FAILED"))
        logs_response = SimpleNamespace(data=SimpleNamespace(text="Error: Invalid resource type"))

        async def mock_to_thread(func, *args, **kwargs):
            if func == mock_client.create_job:
                return create_response
            elif func == mock_client.get_job:
                return get_response
            elif func == mock_client.get_job_logs_content:
                return logs_response
            return None

        with (
            patch.object(infra_service, "_get_rm_client", return_value=mock_client),
            patch("asyncio.to_thread", side_effect=mock_to_thread),
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            result = await infra_service._run_rm_job("ocid1.stack.test", "PLAN", "plan")

        assert result.success is False
        assert "FAILED" in result.stderr

    async def test_job_timeout(self, infra_service: InfraService) -> None:
        """ジョブがタイムアウトする。"""
        mock_client = MagicMock()

        create_response = SimpleNamespace(data=SimpleNamespace(id="ocid1.job.test"))
        get_response = SimpleNamespace(data=SimpleNamespace(lifecycle_state="IN_PROGRESS"))
        logs_response = SimpleNamespace(data=SimpleNamespace(text=""))

        async def mock_to_thread(func, *args, **kwargs):
            if func == mock_client.create_job:
                return create_response
            elif func == mock_client.get_job:
                return get_response
            elif func == mock_client.get_job_logs_content:
                return logs_response
            return None

        with (
            patch.object(infra_service, "_get_rm_client", return_value=mock_client),
            patch("asyncio.to_thread", side_effect=mock_to_thread),
            patch("asyncio.sleep", new_callable=AsyncMock),
            patch("galley.services.infra._JOB_TIMEOUT_PLAN", 5),
            patch("galley.services.infra._JOB_POLL_INTERVAL", 5),
        ):
            result = await infra_service._run_rm_job("ocid1.stack.test", "PLAN", "plan")

        assert result.success is False
        assert "timed out" in result.stderr


class TestGetRmJobStatus:
    async def test_returns_job_status_and_logs(self, infra_service: InfraService) -> None:
        mock_client = MagicMock()
        job_data = SimpleNamespace(
            id="ocid1.job.test",
            stack_id="ocid1.stack.test",
            operation="PLAN",
            lifecycle_state="SUCCEEDED",
        )
        job_response = SimpleNamespace(data=job_data)
        logs_response = SimpleNamespace(data=SimpleNamespace(text="Plan: 1 to add"))

        async def mock_to_thread(func, *args, **kwargs):
            if func == mock_client.get_job:
                return job_response
            elif func == mock_client.get_job_logs_content:
                return logs_response
            return None

        with (
            patch.object(infra_service, "_get_rm_client", return_value=mock_client),
            patch("asyncio.to_thread", side_effect=mock_to_thread),
        ):
            result = await infra_service.get_rm_job_status("ocid1.job.test")

        assert "job" in result
        assert result["job"]["lifecycle_state"] == "SUCCEEDED"
        assert "Plan: 1 to add" in result["logs"]

    async def test_returns_error_on_exception(self, infra_service: InfraService) -> None:
        with patch.object(infra_service, "_get_rm_client", side_effect=Exception("Connection failed")):
            result = await infra_service.get_rm_job_status("ocid1.job.test")

        assert "error" in result
        assert "Connection failed" in result["message"]


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

    async def test_run_oci_cli_adds_resource_principal_auth_when_env_set(
        self, infra_service: InfraService, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """OCI_RESOURCE_PRINCIPAL_VERSION設定時に--auth resource_principalが付与される。"""
        monkeypatch.setenv("OCI_RESOURCE_PRINCIPAL_VERSION", "2.2")
        with patch.object(infra_service, "_run_subprocess", new_callable=AsyncMock) as mock_proc:
            mock_proc.return_value = (0, '{"data": []}', "")
            await infra_service.run_oci_cli("oci compute instance list --compartment-id ocid1.test")

        called_args = mock_proc.call_args[0][0]
        assert called_args[0] == "oci"
        assert called_args[1] == "--auth"
        assert called_args[2] == "resource_principal"
        assert called_args[3] == "compute"

    async def test_run_oci_cli_no_auth_flag_when_env_not_set(
        self, infra_service: InfraService, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """OCI_RESOURCE_PRINCIPAL_VERSION未設定時に--authが付与されない。"""
        monkeypatch.delenv("OCI_RESOURCE_PRINCIPAL_VERSION", raising=False)
        with patch.object(infra_service, "_run_subprocess", new_callable=AsyncMock) as mock_proc:
            mock_proc.return_value = (0, '{"data": []}', "")
            await infra_service.run_oci_cli("oci compute instance list --compartment-id ocid1.test")

        called_args = mock_proc.call_args[0][0]
        assert called_args[0] == "oci"
        assert called_args[1] == "compute"
        assert "--auth" not in called_args


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


class TestUpdateTerraformFile:
    async def test_update_existing_file(
        self, hearing_service: HearingService, infra_service: InfraService, tmp_path: Path
    ) -> None:
        """正常系: Terraformファイルを更新できる。"""
        session_id = await _create_session_with_architecture(hearing_service)
        tf_dir = infra_service._storage.get_session_dir(session_id) / "terraform"
        tf_dir.mkdir(parents=True)
        (tf_dir / "components.tf").write_text("# old content")

        result = await infra_service.update_terraform_file(session_id, "components.tf", "# new content")

        assert "file_path" in result
        assert (tf_dir / "components.tf").read_text() == "# new content"

    async def test_rejects_path_traversal(self, hearing_service: HearingService, infra_service: InfraService) -> None:
        """パストラバーサルを拒否する。"""
        session_id = await _create_session_with_architecture(hearing_service)

        with pytest.raises(ValueError, match="relative path"):
            await infra_service.update_terraform_file(session_id, "../evil.tf", "hack")

    async def test_rejects_absolute_path(self, hearing_service: HearingService, infra_service: InfraService) -> None:
        """絶対パスを拒否する。"""
        session_id = await _create_session_with_architecture(hearing_service)

        with pytest.raises(ValueError, match="relative path"):
            await infra_service.update_terraform_file(session_id, "/etc/passwd", "hack")

    async def test_rejects_no_terraform_dir(self, hearing_service: HearingService, infra_service: InfraService) -> None:
        """terraformディレクトリが存在しない場合はエラー。"""
        session_id = await _create_session_with_architecture(hearing_service)

        with pytest.raises(ValueError, match="does not exist"):
            await infra_service.update_terraform_file(session_id, "main.tf", "content")

    async def test_raises_for_missing_architecture(
        self, hearing_service: HearingService, infra_service: InfraService
    ) -> None:
        """アーキテクチャ未設定の場合はエラー。"""
        session = await hearing_service.create_session()
        await hearing_service.save_answer(session.id, "purpose", "test")
        await hearing_service.complete_hearing(session.id)

        with pytest.raises(ArchitectureNotFoundError):
            await infra_service.update_terraform_file(session.id, "main.tf", "content")


class TestOciCliSetupHint:
    async def test_config_not_found_returns_setup_hint(self, infra_service: InfraService) -> None:
        """OCI CLI設定ファイル未検出時にsetup_hintが返る。"""
        with patch.object(infra_service, "_run_subprocess", new_callable=AsyncMock) as mock_proc:
            mock_proc.return_value = (1, "", "Could not find config file at /home/galley/.oci/config")
            result = await infra_service.run_oci_cli("oci compute instance list --compartment-id ocid1.test")

        assert result.success is False
        assert result.setup_hint is not None
        assert "oci setup config" in result.setup_hint

    async def test_normal_error_no_setup_hint(self, infra_service: InfraService) -> None:
        """通常のエラーではsetup_hintはNone。"""
        with patch.object(infra_service, "_run_subprocess", new_callable=AsyncMock) as mock_proc:
            mock_proc.return_value = (1, "", "ServiceError: NotAuthorizedOrNotFound")
            result = await infra_service.run_oci_cli("oci compute instance list --compartment-id ocid1.test")

        assert result.success is False
        assert result.setup_hint is None


class TestParseTerraformErrors:
    def test_parse_error_with_file_and_line(self, infra_service: InfraService) -> None:
        stderr = 'Error: Invalid resource type\n\n  on components.tf line 5:\n   5: resource "oci_invalid" "test" {\n'
        errors = infra_service._parse_terraform_errors(stderr)
        assert errors is not None
        assert len(errors) == 1
        assert errors[0].file == "components.tf"
        assert errors[0].line == 5
        assert "Invalid resource type" in errors[0].message

    def test_parse_error_without_file(self, infra_service: InfraService) -> None:
        stderr = "Error: No value for required variable\n"
        errors = infra_service._parse_terraform_errors(stderr)
        assert errors is not None
        assert len(errors) == 1
        assert errors[0].file is None
        assert errors[0].line is None

    def test_parse_multiple_errors(self, infra_service: InfraService) -> None:
        stderr = (
            "Error: Unsupported argument\n\n  on main.tf line 3:\n\n"
            "Error: Missing required argument\n\n  on variables.tf line 10:\n"
        )
        errors = infra_service._parse_terraform_errors(stderr)
        assert errors is not None
        assert len(errors) == 2

    def test_parse_no_errors(self, infra_service: InfraService) -> None:
        errors = infra_service._parse_terraform_errors("Warning: something happened")
        assert errors is None
