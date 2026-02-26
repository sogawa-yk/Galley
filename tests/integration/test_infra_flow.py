"""インフラフローのMCPプロトコル経由統合テスト。"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastmcp import Client

from galley.config import ServerConfig
from galley.server import create_server
from galley.services.infra import InfraService


@pytest.fixture
def mcp_server(tmp_path: Path) -> object:
    """テスト用MCPサーバー。"""
    config = ServerConfig(data_dir=tmp_path / "galley-test", config_dir=Path(__file__).parent.parent.parent / "config")
    return create_server(config)


def parse_tool_result(result: object) -> dict:
    """CallToolResultからJSONデータを抽出する。"""
    content = result.content  # type: ignore[union-attr]
    assert len(content) > 0
    return json.loads(content[0].text)  # type: ignore[union-attr]


async def _create_session_with_architecture_via_mcp(client: Client) -> str:  # type: ignore[type-arg]
    """MCPプロトコル経由でアーキテクチャ設定済みセッションを作成する。"""
    result = await client.call_tool("create_session", {})
    data = parse_tool_result(result)
    session_id = data["session_id"]

    await client.call_tool(
        "save_answer",
        {"session_id": session_id, "question_id": "purpose", "value": "REST API構築"},
    )
    await client.call_tool("complete_hearing", {"session_id": session_id})

    await client.call_tool(
        "save_architecture",
        {
            "session_id": session_id,
            "components": [{"service_type": "oke", "display_name": "OKE"}],
            "connections": [],
        },
    )
    return session_id


class TestInfraToolsRegistration:
    async def test_infra_tools_are_registered(self, mcp_server: object) -> None:
        """インフラ系ツールがMCPサーバーに登録されている。"""
        async with Client(mcp_server) as client:  # type: ignore[arg-type]
            tools = await client.list_tools()
            tool_names = {t.name for t in tools}
            assert "run_terraform_plan" in tool_names
            assert "run_terraform_apply" in tool_names
            assert "run_terraform_destroy" in tool_names
            assert "run_oci_cli" in tool_names
            assert "get_rm_job_status" in tool_names
            assert "update_terraform_file" in tool_names
            # 削除されたツールが存在しないこと
            assert "oci_sdk_call" not in tool_names
            assert "create_rm_stack" not in tool_names
            assert "run_rm_plan" not in tool_names
            assert "run_rm_apply" not in tool_names


class TestTerraformToolsViaMCP:
    async def test_terraform_plan_via_mcp(self, mcp_server: object) -> None:
        async with Client(mcp_server) as client:  # type: ignore[arg-type]
            session_id = await _create_session_with_architecture_via_mcp(client)

            from galley.models.infra import TerraformResult

            plan_result = TerraformResult(
                success=True,
                command="plan",
                stdout="Plan: 2 to add, 0 to change, 0 to destroy.",
                stderr="",
                exit_code=0,
                plan_summary="2 to add, 0 to change, 0 to destroy",
            )

            with (
                patch.object(InfraService, "_ensure_rm_stack", new_callable=AsyncMock, return_value="ocid1.stack"),
                patch.object(InfraService, "_run_rm_job", new_callable=AsyncMock, return_value=plan_result),
            ):
                result = await client.call_tool(
                    "run_terraform_plan",
                    {"session_id": session_id, "terraform_dir": "/tmp/tf"},
                )

            data = parse_tool_result(result)
            assert data["success"] is True
            assert data["command"] == "plan"
            assert data["plan_summary"] is not None

    async def test_terraform_apply_via_mcp(self, mcp_server: object) -> None:
        async with Client(mcp_server) as client:  # type: ignore[arg-type]
            session_id = await _create_session_with_architecture_via_mcp(client)

            from galley.models.infra import TerraformResult

            apply_result = TerraformResult(
                success=True, command="apply", stdout="Apply complete!", stderr="", exit_code=0
            )

            with (
                patch.object(InfraService, "_ensure_rm_stack", new_callable=AsyncMock, return_value="ocid1.stack"),
                patch.object(InfraService, "_run_rm_job", new_callable=AsyncMock, return_value=apply_result),
            ):
                result = await client.call_tool(
                    "run_terraform_apply",
                    {"session_id": session_id, "terraform_dir": "/tmp/tf"},
                )

            data = parse_tool_result(result)
            assert data["success"] is True
            assert data["command"] == "apply"

    async def test_terraform_destroy_via_mcp(self, mcp_server: object) -> None:
        async with Client(mcp_server) as client:  # type: ignore[arg-type]
            session_id = await _create_session_with_architecture_via_mcp(client)

            from galley.models.infra import TerraformResult

            destroy_result = TerraformResult(
                success=True, command="destroy", stdout="Destroy complete!", stderr="", exit_code=0
            )

            with (
                patch.object(InfraService, "_ensure_rm_stack", new_callable=AsyncMock, return_value="ocid1.stack"),
                patch.object(InfraService, "_run_rm_job", new_callable=AsyncMock, return_value=destroy_result),
            ):
                result = await client.call_tool(
                    "run_terraform_destroy",
                    {"session_id": session_id, "terraform_dir": "/tmp/tf"},
                )

            data = parse_tool_result(result)
            assert data["success"] is True
            assert data["command"] == "destroy"

    async def test_terraform_plan_error_returns_structured_response(self, mcp_server: object) -> None:
        """RM経由のplanエラーは構造化されたレスポンスで返される。"""
        async with Client(mcp_server) as client:  # type: ignore[arg-type]
            session_id = await _create_session_with_architecture_via_mcp(client)

            from galley.models.infra import TerraformResult

            error_result = TerraformResult(
                success=False,
                command="plan",
                stdout="Error: Invalid resource type 'oci_invalid'",
                stderr="Job FAILED. Job ID: ocid1.job.test",
                exit_code=1,
            )

            with (
                patch.object(InfraService, "_ensure_rm_stack", new_callable=AsyncMock, return_value="ocid1.stack"),
                patch.object(InfraService, "_run_rm_job", new_callable=AsyncMock, return_value=error_result),
            ):
                result = await client.call_tool(
                    "run_terraform_plan",
                    {"session_id": session_id, "terraform_dir": "/tmp/tf"},
                )

            data = parse_tool_result(result)
            assert data["success"] is False
            assert data["exit_code"] == 1

    async def test_terraform_plan_rejects_path_traversal(self, mcp_server: object) -> None:
        """terraform_dirにパストラバーサルが含まれる場合はエラーを返す。"""
        async with Client(mcp_server) as client:  # type: ignore[arg-type]
            session_id = await _create_session_with_architecture_via_mcp(client)

            result = await client.call_tool(
                "run_terraform_plan",
                {"session_id": session_id, "terraform_dir": "/tmp/../etc/passwd"},
            )

            data = parse_tool_result(result)
            assert "error" in data


class TestOciCliViaMCP:
    async def test_run_oci_cli_via_mcp(self, mcp_server: object) -> None:
        async with Client(mcp_server) as client:  # type: ignore[arg-type]
            with patch.object(InfraService, "_run_subprocess", new_callable=AsyncMock) as mock_proc:
                mock_proc.return_value = (0, '{"data": []}', "")
                result = await client.call_tool(
                    "run_oci_cli",
                    {"command": "oci compute instance list --compartment-id ocid1.test"},
                )

            data = parse_tool_result(result)
            assert data["success"] is True

    async def test_run_oci_cli_disallowed_command(self, mcp_server: object) -> None:
        async with Client(mcp_server) as client:  # type: ignore[arg-type]
            result = await client.call_tool(
                "run_oci_cli",
                {"command": "oci setup config"},
            )
            data = parse_tool_result(result)
            assert "error" in data
            assert data["error"] == "CommandNotAllowedError"


class TestInfraPromptsRegistration:
    async def test_infra_prompts_are_registered(self, mcp_server: object) -> None:
        """インフラ系プロンプトがMCPサーバーに登録されている。"""
        async with Client(mcp_server) as client:  # type: ignore[arg-type]
            prompts = await client.list_prompts()
            prompt_names = {p.name for p in prompts}
            assert "oci_resource_check" in prompt_names
            assert "infra_cleanup" in prompt_names
            assert "terraform_debug_loop" not in prompt_names

    async def test_oci_resource_check_contains_guidance(self, mcp_server: object) -> None:
        """oci_resource_checkプロンプトはOCI CLIの使い方ガイドを返す。"""
        async with Client(mcp_server) as client:  # type: ignore[arg-type]
            result = await client.get_prompt("oci_resource_check", {})
            text = result.messages[0].content.text  # type: ignore[union-attr]
            assert "run_oci_cli" in text
            assert "oci compute instance list" in text

    async def test_infra_cleanup_contains_session_id(self, mcp_server: object) -> None:
        """infra_cleanupプロンプトはsession_idを含むテキストを返す。"""
        async with Client(mcp_server) as client:  # type: ignore[arg-type]
            result = await client.get_prompt("infra_cleanup", {"session_id": "test-session-456"})
            text = result.messages[0].content.text  # type: ignore[union-attr]
            assert "test-session-456" in text
            assert "run_terraform_destroy" in text
