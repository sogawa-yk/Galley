"""アプリケーション層データモデルのユニットテスト。"""

from galley.models.app import AppStatus, DeployResult, TemplateMetadata, TemplateParameter


class TestTemplateParameter:
    def test_create_string_parameter(self) -> None:
        param = TemplateParameter(
            name="app_name",
            description="Application name",
            param_type="string",
        )
        assert param.name == "app_name"
        assert param.param_type == "string"
        assert param.required is True
        assert param.default is None
        assert param.choices is None

    def test_create_choice_parameter(self) -> None:
        param = TemplateParameter(
            name="db_type",
            description="Database type",
            param_type="choice",
            choices=["adb", "mysql"],
            default="adb",
        )
        assert param.choices == ["adb", "mysql"]
        assert param.default == "adb"

    def test_optional_parameter(self) -> None:
        param = TemplateParameter(
            name="port",
            description="Port number",
            param_type="number",
            required=False,
            default=8080,
        )
        assert param.required is False
        assert param.default == 8080


class TestTemplateMetadata:
    def test_create_metadata(self) -> None:
        metadata = TemplateMetadata(
            name="rest-api-adb",
            display_name="REST API + ADB",
            description="REST API with Autonomous Database",
        )
        assert metadata.name == "rest-api-adb"
        assert metadata.parameters == []
        assert metadata.protected_paths == []

    def test_create_metadata_with_protected_paths(self) -> None:
        metadata = TemplateMetadata(
            name="rest-api-adb",
            display_name="REST API + ADB",
            description="REST API with Autonomous Database",
            protected_paths=["src/db.py", "src/auth.py"],
        )
        assert len(metadata.protected_paths) == 2

    def test_create_metadata_with_parameters(self) -> None:
        metadata = TemplateMetadata(
            name="test",
            display_name="Test",
            description="Test template",
            parameters=[
                TemplateParameter(
                    name="app_name",
                    description="App name",
                    param_type="string",
                )
            ],
        )
        assert len(metadata.parameters) == 1


class TestDeployResult:
    def test_success_result(self) -> None:
        result = DeployResult(
            success=True,
            image_uri="ocir.io/namespace/app:latest",
            endpoint="https://app.example.com",
        )
        assert result.success is True
        assert result.rolled_back is False

    def test_failure_result(self) -> None:
        result = DeployResult(
            success=False,
            reason="Build failed",
        )
        assert result.success is False
        assert result.image_uri is None

    def test_rollback_result(self) -> None:
        result = DeployResult(
            success=False,
            rolled_back=True,
            reason="Health check failed",
        )
        assert result.rolled_back is True


class TestAppStatus:
    def test_default_status(self) -> None:
        status = AppStatus(session_id="test-session")
        assert status.status == "not_deployed"
        assert status.endpoint is None
        assert status.health_check is None
        assert status.last_deployed_at is None

    def test_running_status(self) -> None:
        status = AppStatus(
            session_id="test-session",
            status="running",
            endpoint="https://app.example.com",
        )
        assert status.status == "running"
        assert status.endpoint == "https://app.example.com"
