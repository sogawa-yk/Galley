"""AppServiceのユニットテスト。"""

import json

import pytest

from galley.models.errors import (
    AppNotScaffoldedError,
    ArchitectureNotFoundError,
    ProtectedFileError,
    TemplateNotFoundError,
)
from galley.services.app import AppService
from galley.services.hearing import HearingService


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
    async def test_scaffold_creates_project(
        self, hearing_service: HearingService, app_service: AppService
    ) -> None:
        session_id = await _create_session_with_architecture(hearing_service)
        result = await app_service.scaffold_from_template(
            session_id, "rest-api-adb", {"app_name": "test-app", "app_port": "3000"}
        )

        assert result["template_name"] == "rest-api-adb"
        assert "files" in result
        files = result["files"]
        assert isinstance(files, list)
        assert len(files) > 0

    async def test_scaffold_replaces_parameters(
        self, hearing_service: HearingService, app_service: AppService
    ) -> None:
        session_id = await _create_session_with_architecture(hearing_service)
        await app_service.scaffold_from_template(
            session_id, "rest-api-adb", {"app_name": "my-cool-app"}
        )

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
    async def test_update_app_code_success(
        self, hearing_service: HearingService, app_service: AppService
    ) -> None:
        session_id = await _create_session_with_architecture(hearing_service)
        await app_service.scaffold_from_template(session_id, "rest-api-adb", {})

        result = await app_service.update_app_code(
            session_id, "src/routes.py", "# Updated routes\n"
        )

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

        result = await app_service.update_app_code(
            session_id, "src/routes.py", "# Updated\n"
        )

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

    async def test_update_rejects_absolute_path(
        self, hearing_service: HearingService, app_service: AppService
    ) -> None:
        session_id = await _create_session_with_architecture(hearing_service)
        await app_service.scaffold_from_template(session_id, "rest-api-adb", {})

        with pytest.raises(ValueError, match="relative path"):
            await app_service.update_app_code(session_id, "/etc/passwd", "evil")


class TestBuildAndDeploy:
    async def test_build_and_deploy_returns_not_implemented(
        self, hearing_service: HearingService, app_service: AppService
    ) -> None:
        session_id = await _create_session_with_architecture(hearing_service)
        await app_service.scaffold_from_template(session_id, "rest-api-adb", {})

        result = await app_service.build_and_deploy(session_id)
        assert result.success is False
        assert "not yet implemented" in (result.reason or "")

    async def test_build_and_deploy_raises_for_unscaffolded(
        self, hearing_service: HearingService, app_service: AppService
    ) -> None:
        session_id = await _create_session_with_architecture(hearing_service)

        with pytest.raises(AppNotScaffoldedError):
            await app_service.build_and_deploy(session_id)


class TestCheckAppStatus:
    async def test_check_status_not_deployed(
        self, hearing_service: HearingService, app_service: AppService
    ) -> None:
        session_id = await _create_session_with_architecture(hearing_service)
        status = await app_service.check_app_status(session_id)
        assert status.session_id == session_id
        assert status.status == "not_deployed"

    async def test_check_status_after_scaffold(
        self, hearing_service: HearingService, app_service: AppService
    ) -> None:
        session_id = await _create_session_with_architecture(hearing_service)
        await app_service.scaffold_from_template(session_id, "rest-api-adb", {})
        status = await app_service.check_app_status(session_id)
        assert status.session_id == session_id
        assert status.status == "not_deployed"
