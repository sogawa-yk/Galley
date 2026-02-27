"""AppServiceのユニットテスト。"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from galley.config import ServerConfig
from galley.models.errors import (
    AppNotScaffoldedError,
    ArchitectureNotFoundError,
    ProtectedFileError,
    TemplateNotFoundError,
)
from galley.services.app import AppService
from galley.services.hearing import HearingService
from galley.storage.service import StorageService


async def _create_session_with_architecture(hearing_service: HearingService) -> str:
    """テスト用にアーキテクチャ設定済みのセッションを作成する。"""
    from galley.models.architecture import Architecture

    session = await hearing_service.create_session()
    await hearing_service.save_answer(session.id, "purpose", "REST API構築")
    await hearing_service.complete_hearing(session.id)
    loaded = await hearing_service._storage.load_session(session.id)
    loaded.architecture = Architecture(session_id=session.id)
    await hearing_service._storage.save_session(loaded)
    return session.id


class TestListTemplates:
    async def test_list_templates_returns_templates(self, app_service: AppService) -> None:
        templates = await app_service.list_templates()
        assert len(templates) >= 1
        rest_api = next((t for t in templates if t.name == "rest-api-adb"), None)
        assert rest_api is not None
        assert rest_api.display_name == "REST API + Autonomous Database"

    async def test_list_templates_empty_when_no_templates_dir(self, app_service: AppService) -> None:
        # テンプレートディレクトリを一時的にリネーム
        templates_dir = app_service._templates_dir
        backup_dir = templates_dir.parent / "templates_backup"
        templates_dir.rename(backup_dir)
        try:
            templates = await app_service.list_templates()
            assert templates == []
        finally:
            backup_dir.rename(templates_dir)


class TestScaffoldFromTemplate:
    async def test_scaffold_creates_project(self, hearing_service: HearingService, app_service: AppService) -> None:
        session_id = await _create_session_with_architecture(hearing_service)
        result = await app_service.scaffold_from_template(
            session_id, "rest-api-adb", {"app_name": "test-app", "app_port": "3000"}
        )

        assert result["template_name"] == "rest-api-adb"
        assert "files" in result
        files = result["files"]
        assert isinstance(files, list)
        assert len(files) > 0

    async def test_scaffold_replaces_parameters(self, hearing_service: HearingService, app_service: AppService) -> None:
        session_id = await _create_session_with_architecture(hearing_service)
        await app_service.scaffold_from_template(session_id, "rest-api-adb", {"app_name": "my-cool-app"})

        app_dir = app_service._app_dir(session_id)
        main_content = (app_dir / "main.py").read_text(encoding="utf-8")
        assert "my-cool-app" in main_content
        assert "{{app_name}}" not in main_content

    async def test_scaffold_raises_for_missing_template(
        self, hearing_service: HearingService, app_service: AppService
    ) -> None:
        session_id = await _create_session_with_architecture(hearing_service)

        with pytest.raises(TemplateNotFoundError):
            await app_service.scaffold_from_template(session_id, "nonexistent-template", {})

    async def test_scaffold_raises_for_missing_architecture(
        self, hearing_service: HearingService, app_service: AppService
    ) -> None:
        session = await hearing_service.create_session()
        await hearing_service.save_answer(session.id, "purpose", "test")
        await hearing_service.complete_hearing(session.id)

        with pytest.raises(ArchitectureNotFoundError):
            await app_service.scaffold_from_template(session.id, "rest-api-adb", {})

    async def test_scaffold_saves_template_metadata(
        self, hearing_service: HearingService, app_service: AppService
    ) -> None:
        session_id = await _create_session_with_architecture(hearing_service)
        await app_service.scaffold_from_template(session_id, "rest-api-adb", {})

        metadata_file = app_service._app_dir(session_id).parent / "template-metadata.json"
        assert metadata_file.exists()
        data = json.loads(metadata_file.read_text(encoding="utf-8"))
        assert data["name"] == "rest-api-adb"

    async def test_scaffold_rejects_path_traversal(
        self, hearing_service: HearingService, app_service: AppService
    ) -> None:
        session_id = await _create_session_with_architecture(hearing_service)

        with pytest.raises(TemplateNotFoundError):
            await app_service.scaffold_from_template(session_id, "../etc/passwd", {})


class TestUpdateAppCode:
    async def test_update_app_code_success(self, hearing_service: HearingService, app_service: AppService) -> None:
        session_id = await _create_session_with_architecture(hearing_service)
        await app_service.scaffold_from_template(session_id, "rest-api-adb", {})

        result = await app_service.update_app_code(session_id, "src/routes.py", "# Updated routes\n")

        assert result["success"] is True
        assert "snapshot_id" in result

        # ファイルが更新されたか確認
        app_dir = app_service._app_dir(session_id)
        content = (app_dir / "src" / "routes.py").read_text(encoding="utf-8")
        assert content == "# Updated routes\n"

    async def test_update_app_code_creates_snapshot(
        self, hearing_service: HearingService, app_service: AppService
    ) -> None:
        session_id = await _create_session_with_architecture(hearing_service)
        await app_service.scaffold_from_template(session_id, "rest-api-adb", {})

        result = await app_service.update_app_code(session_id, "src/routes.py", "# Updated\n")

        snapshot_id = result["snapshot_id"]
        snapshots_dir = app_service._snapshots_dir(session_id)
        snapshot_dir = snapshots_dir / str(snapshot_id)
        assert snapshot_dir.exists()

    async def test_update_rejects_protected_file(
        self, hearing_service: HearingService, app_service: AppService
    ) -> None:
        session_id = await _create_session_with_architecture(hearing_service)
        await app_service.scaffold_from_template(session_id, "rest-api-adb", {})

        with pytest.raises(ProtectedFileError):
            await app_service.update_app_code(session_id, "src/db.py", "# hacked\n")

    async def test_update_rejects_another_protected_file(
        self, hearing_service: HearingService, app_service: AppService
    ) -> None:
        session_id = await _create_session_with_architecture(hearing_service)
        await app_service.scaffold_from_template(session_id, "rest-api-adb", {})

        with pytest.raises(ProtectedFileError):
            await app_service.update_app_code(session_id, "Dockerfile", "FROM scratch\n")

    async def test_update_raises_for_unscaffolded(
        self, hearing_service: HearingService, app_service: AppService
    ) -> None:
        session_id = await _create_session_with_architecture(hearing_service)

        with pytest.raises(AppNotScaffoldedError):
            await app_service.update_app_code(session_id, "main.py", "# test\n")

    async def test_update_rejects_path_traversal(
        self, hearing_service: HearingService, app_service: AppService
    ) -> None:
        session_id = await _create_session_with_architecture(hearing_service)
        await app_service.scaffold_from_template(session_id, "rest-api-adb", {})

        with pytest.raises(ValueError, match="path contains"):
            await app_service.update_app_code(session_id, "../../../etc/passwd", "evil")

    async def test_update_rejects_absolute_path(self, hearing_service: HearingService, app_service: AppService) -> None:
        session_id = await _create_session_with_architecture(hearing_service)
        await app_service.scaffold_from_template(session_id, "rest-api-adb", {})

        with pytest.raises(ValueError, match="relative path"):
            await app_service.update_app_code(session_id, "/etc/passwd", "evil")


class TestGenerateK8sManifests:
    async def test_generates_deployment_and_service(
        self, hearing_service: HearingService, app_service: AppService
    ) -> None:
        session_id = await _create_session_with_architecture(hearing_service)
        await app_service.scaffold_from_template(session_id, "rest-api-adb", {"app_port": "3000"})

        k8s_dir = app_service._generate_k8s_manifests(session_id, "ghcr.io/test/app:latest", "default")

        assert k8s_dir.exists()
        assert (k8s_dir / "deployment.yaml").exists()
        assert (k8s_dir / "service.yaml").exists()

        deployment = (k8s_dir / "deployment.yaml").read_text(encoding="utf-8")
        assert "ghcr.io/test/app:latest" in deployment
        assert "containerPort: 3000" in deployment

        service = (k8s_dir / "service.yaml").read_text(encoding="utf-8")
        assert "targetPort: 3000" in service
        assert "type: LoadBalancer" in service

    async def test_uses_default_port_when_not_in_dockerfile(
        self, hearing_service: HearingService, app_service: AppService
    ) -> None:
        session_id = await _create_session_with_architecture(hearing_service)
        await app_service.scaffold_from_template(session_id, "rest-api-adb", {})

        # Dockerfileのポートを読み取る（テンプレートには{{app_port}}が入っている場合）
        k8s_dir = app_service._generate_k8s_manifests(session_id, "test:latest")
        deployment = (k8s_dir / "deployment.yaml").read_text(encoding="utf-8")
        # ポートが数値として設定されていることを確認（デフォルト8000 or テンプレートのEXPOSE値）
        assert "containerPort:" in deployment


class TestBuildAndDeploy:
    async def test_build_and_deploy_raises_for_unscaffolded(
        self, hearing_service: HearingService, app_service: AppService
    ) -> None:
        session_id = await _create_session_with_architecture(hearing_service)

        with pytest.raises(AppNotScaffoldedError):
            await app_service.build_and_deploy(session_id, "ocid1.cluster.oc1..xxx", "test:latest")

    async def test_build_and_deploy_returns_error_on_kubeconfig_failure(
        self, hearing_service: HearingService, app_service: AppService
    ) -> None:
        session_id = await _create_session_with_architecture(hearing_service)
        await app_service.scaffold_from_template(session_id, "rest-api-adb", {})

        with patch.object(app_service, "_run_subprocess", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = (1, "", "Could not find config file")

            result = await app_service.build_and_deploy(session_id, "ocid1.cluster.oc1..xxx", "test:latest")

        assert result.success is False
        assert "kubeconfig" in (result.reason or "").lower()
        assert result.k8s_manifests_dir is not None

    async def test_build_and_deploy_returns_error_on_kubectl_apply_failure(
        self, hearing_service: HearingService, app_service: AppService
    ) -> None:
        session_id = await _create_session_with_architecture(hearing_service)
        await app_service.scaffold_from_template(session_id, "rest-api-adb", {})

        call_count = 0

        async def mock_subprocess(args: list[str], cwd: str | None = None) -> tuple[int, str, str]:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # kubeconfig成功
                return (0, "kubeconfig created", "")
            # kubectl apply失敗
            return (1, "", "error: connection refused")

        with patch.object(app_service, "_run_subprocess", side_effect=mock_subprocess):
            result = await app_service.build_and_deploy(session_id, "ocid1.cluster.oc1..xxx", "test:latest")

        assert result.success is False
        assert "kubectl apply failed" in (result.reason or "")

    async def test_build_and_deploy_success(self, hearing_service: HearingService, app_service: AppService) -> None:
        session_id = await _create_session_with_architecture(hearing_service)
        await app_service.scaffold_from_template(session_id, "rest-api-adb", {})

        call_count = 0

        async def mock_subprocess(args: list[str], cwd: str | None = None) -> tuple[int, str, str]:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # kubeconfig成功
                return (0, "", "")
            if call_count == 2:
                # kubectl apply成功
                return (0, "deployment.apps/rest-api-adb created", "")
            if call_count == 3:
                # rollout status成功
                return (0, "deployment successfully rolled out", "")
            # get svc (endpoint)
            return (0, "10.0.1.100", "")

        with patch.object(app_service, "_run_subprocess", side_effect=mock_subprocess):
            result = await app_service.build_and_deploy(session_id, "ocid1.cluster.oc1..xxx", "ghcr.io/test/app:latest")

        assert result.success is True
        assert result.image_uri == "ghcr.io/test/app:latest"
        assert result.endpoint == "http://10.0.1.100"
        assert result.k8s_manifests_dir is not None


class TestCheckAppStatus:
    async def test_check_status_not_deployed(self, hearing_service: HearingService, app_service: AppService) -> None:
        session_id = await _create_session_with_architecture(hearing_service)
        status = await app_service.check_app_status(session_id)
        assert status.session_id == session_id
        assert status.status == "not_deployed"

    async def test_check_status_after_scaffold(self, hearing_service: HearingService, app_service: AppService) -> None:
        session_id = await _create_session_with_architecture(hearing_service)
        await app_service.scaffold_from_template(session_id, "rest-api-adb", {})
        status = await app_service.check_app_status(session_id)
        assert status.session_id == session_id
        assert status.status == "not_deployed"

    async def test_check_status_running(self, hearing_service: HearingService, app_service: AppService) -> None:
        session_id = await _create_session_with_architecture(hearing_service)
        await app_service.scaffold_from_template(session_id, "rest-api-adb", {})

        # kubeconfigを作成してデプロイ済み状態をシミュレート
        kubeconfig = app_service._kubeconfig_path(session_id)
        kubeconfig.parent.mkdir(parents=True, exist_ok=True)
        kubeconfig.write_text("dummy-kubeconfig", encoding="utf-8")

        call_count = 0

        async def mock_subprocess(args: list[str], cwd: str | None = None) -> tuple[int, str, str]:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # get deployment readyReplicas
                return (0, "1", "")
            # get svc endpoint
            return (0, "10.0.1.100", "")

        with patch.object(app_service, "_run_subprocess", side_effect=mock_subprocess):
            status = await app_service.check_app_status(session_id)

        assert status.status == "running"
        assert status.endpoint == "http://10.0.1.100"


class TestBuildAndPushImage:
    """Build Instance 経由のイメージビルドテスト。"""

    @pytest.fixture
    def app_service_with_config(self, storage: StorageService, config_dir: Path, tmp_data_dir: Path) -> AppService:
        """ビルド設定付きの AppService を作成する。"""
        config = ServerConfig(
            data_dir=tmp_data_dir,
            config_dir=config_dir,
            build_instance_id="ocid1.instance.oc1..build-test",
            ocir_endpoint="ap-osaka-1.ocir.io",
            ocir_username="namespace/user@example.com",
            ocir_auth_token="test-token-123",
            bucket_name="galley-test-bucket",
            bucket_namespace="testnamespace",
            region="ap-osaka-1",
        )
        return AppService(storage=storage, config_dir=config_dir, config=config)

    async def test_build_script_contains_required_commands(self) -> None:
        script = AppService._build_script(
            bucket_name="my-bucket",
            bucket_namespace="my-ns",
            object_name="builds/abc/app.tar.gz",
            image_uri="ap-osaka-1.ocir.io/my-ns/test-app:abc12345",
            ocir_endpoint="ap-osaka-1.ocir.io",
            ocir_username="my-ns/user@example.com",
            ocir_auth_token="secret-token",
        )
        assert "docker build" in script
        assert "docker push" in script
        assert "docker login" in script
        assert "my-bucket" in script
        assert "builds/abc/app.tar.gz" in script
        assert "ap-osaka-1.ocir.io/my-ns/test-app:abc12345" in script

    async def test_build_and_deploy_without_image_uri_fails_when_no_config(
        self, hearing_service: HearingService, app_service: AppService
    ) -> None:
        session_id = await _create_session_with_architecture(hearing_service)
        await app_service.scaffold_from_template(session_id, "rest-api-adb", {})

        result = await app_service.build_and_deploy(session_id, "ocid1.cluster.oc1..xxx")

        assert result.success is False
        assert "build" in (result.reason or "").lower()

    async def test_build_and_deploy_without_image_uri_triggers_build(
        self,
        hearing_service: HearingService,
        app_service_with_config: AppService,
    ) -> None:
        session_id = await _create_session_with_architecture(hearing_service)
        await app_service_with_config.scaffold_from_template(session_id, "rest-api-adb", {})

        call_count = 0

        async def mock_subprocess(args: list[str], cwd: str | None = None) -> tuple[int, str, str]:
            nonlocal call_count
            call_count += 1
            cmd = " ".join(args)

            # 1. upload tarball to Object Storage
            if "os" in args and "object" in args and "put" in args:
                return (0, "", "")

            # 2. instance-agent command create
            if "instance-agent" in args and "command" in args and "create" in args:
                return (
                    0,
                    json.dumps({"data": {"id": "ocid1.command.oc1..test"}}),
                    "",
                )

            # 3. instance-agent command-execution get (complete)
            if "command-execution" in args and "get" in args:
                return (
                    0,
                    json.dumps(
                        {
                            "data": {
                                "lifecycle-state": "SUCCEEDED",
                                "content": {
                                    "exit-code": 0,
                                    "output": {"text": "BUILD_SUCCESS"},
                                },
                            }
                        }
                    ),
                    "",
                )

            # 4. kubeconfig
            if "ce" in args and "cluster" in args:
                return (0, "", "")

            # 5. kubectl apply
            if "kubectl" in args and "apply" in cmd:
                return (0, "deployment created", "")

            # 6. rollout status
            if "kubectl" in args and "rollout" in cmd:
                return (0, "rolled out", "")

            # 7. get svc
            if "kubectl" in args and "get" in cmd:
                return (0, "10.0.1.200", "")

            return (0, "", "")

        with (
            patch.object(app_service_with_config, "_run_subprocess", side_effect=mock_subprocess),
            patch.dict("os.environ", {"GALLEY_WORK_COMPARTMENT_ID": "ocid1.compartment.oc1..test"}),
        ):
            result = await app_service_with_config.build_and_deploy(session_id, "ocid1.cluster.oc1..xxx")

        assert result.success is True
        assert "ap-osaka-1.ocir.io" in (result.image_uri or "")
        assert result.endpoint == "http://10.0.1.200"

    async def test_build_failure_returns_error(
        self,
        hearing_service: HearingService,
        app_service_with_config: AppService,
    ) -> None:
        session_id = await _create_session_with_architecture(hearing_service)
        await app_service_with_config.scaffold_from_template(session_id, "rest-api-adb", {})

        async def mock_subprocess(args: list[str], cwd: str | None = None) -> tuple[int, str, str]:
            # upload 成功
            if "os" in args and "put" in args:
                return (0, "", "")
            # command create 失敗
            return (1, "", "Access denied")

        with (
            patch.object(app_service_with_config, "_run_subprocess", side_effect=mock_subprocess),
            patch.dict("os.environ", {"GALLEY_WORK_COMPARTMENT_ID": "ocid1.compartment.oc1..test"}),
        ):
            result = await app_service_with_config.build_and_deploy(session_id, "ocid1.cluster.oc1..xxx")

        assert result.success is False
        assert "build" in (result.reason or "").lower()
