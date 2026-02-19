"""アプリケーションフローのMCPプロトコル経由統合テスト。"""

import json
from pathlib import Path

import pytest
from fastmcp import Client

from galley.config import ServerConfig
from galley.server import create_server


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


class TestAppToolsRegistration:
    async def test_app_tools_are_registered(self, mcp_server: object) -> None:
        """アプリケーション系ツールがMCPサーバーに登録されている。"""
        async with Client(mcp_server) as client:  # type: ignore[arg-type]
            tools = await client.list_tools()
            tool_names = {t.name for t in tools}
            assert "list_templates" in tool_names
            assert "scaffold_from_template" in tool_names
            assert "update_app_code" in tool_names
            assert "build_and_deploy" in tool_names
            assert "check_app_status" in tool_names


class TestAppPromptsRegistration:
    async def test_app_prompts_are_registered(self, mcp_server: object) -> None:
        """アプリケーション系プロンプトがMCPサーバーに登録されている。"""
        async with Client(mcp_server) as client:  # type: ignore[arg-type]
            prompts = await client.list_prompts()
            prompt_names = {p.name for p in prompts}
            assert "template_selection" in prompt_names
            assert "app_customization" in prompt_names
            assert "app_deploy" in prompt_names


class TestListTemplatesViaMCP:
    async def test_list_templates_returns_templates(self, mcp_server: object) -> None:
        async with Client(mcp_server) as client:  # type: ignore[arg-type]
            result = await client.call_tool("list_templates", {})
            data = parse_tool_result(result)
            assert "templates" in data
            assert len(data["templates"]) >= 1
            names = [t["name"] for t in data["templates"]]
            assert "rest-api-adb" in names


class TestScaffoldFlowViaMCP:
    async def test_scaffold_from_template_via_mcp(self, mcp_server: object) -> None:
        async with Client(mcp_server) as client:  # type: ignore[arg-type]
            session_id = await _create_session_with_architecture_via_mcp(client)

            result = await client.call_tool(
                "scaffold_from_template",
                {
                    "session_id": session_id,
                    "template_name": "rest-api-adb",
                    "params": {"app_name": "test-app"},
                },
            )
            data = parse_tool_result(result)
            assert data["template_name"] == "rest-api-adb"
            assert "files" in data
            assert len(data["files"]) > 0

    async def test_scaffold_nonexistent_template_returns_error(self, mcp_server: object) -> None:
        async with Client(mcp_server) as client:  # type: ignore[arg-type]
            session_id = await _create_session_with_architecture_via_mcp(client)

            result = await client.call_tool(
                "scaffold_from_template",
                {
                    "session_id": session_id,
                    "template_name": "nonexistent",
                },
            )
            data = parse_tool_result(result)
            assert "error" in data
            assert data["error"] == "TemplateNotFoundError"


class TestUpdateAppCodeViaMCP:
    async def test_update_app_code_via_mcp(self, mcp_server: object) -> None:
        async with Client(mcp_server) as client:  # type: ignore[arg-type]
            session_id = await _create_session_with_architecture_via_mcp(client)

            await client.call_tool(
                "scaffold_from_template",
                {
                    "session_id": session_id,
                    "template_name": "rest-api-adb",
                    "params": {"app_name": "test-app"},
                },
            )

            result = await client.call_tool(
                "update_app_code",
                {
                    "session_id": session_id,
                    "file_path": "src/routes.py",
                    "new_content": "# Custom routes\n",
                },
            )
            data = parse_tool_result(result)
            assert data["success"] is True
            assert "snapshot_id" in data

    async def test_update_protected_file_returns_error(self, mcp_server: object) -> None:
        async with Client(mcp_server) as client:  # type: ignore[arg-type]
            session_id = await _create_session_with_architecture_via_mcp(client)

            await client.call_tool(
                "scaffold_from_template",
                {
                    "session_id": session_id,
                    "template_name": "rest-api-adb",
                },
            )

            result = await client.call_tool(
                "update_app_code",
                {
                    "session_id": session_id,
                    "file_path": "src/db.py",
                    "new_content": "# hacked\n",
                },
            )
            data = parse_tool_result(result)
            assert "error" in data
            assert data["error"] == "ProtectedFileError"


class TestBuildAndDeployViaMCP:
    async def test_build_and_deploy_returns_stub(self, mcp_server: object) -> None:
        async with Client(mcp_server) as client:  # type: ignore[arg-type]
            session_id = await _create_session_with_architecture_via_mcp(client)

            await client.call_tool(
                "scaffold_from_template",
                {"session_id": session_id, "template_name": "rest-api-adb"},
            )

            result = await client.call_tool(
                "build_and_deploy",
                {"session_id": session_id},
            )
            data = parse_tool_result(result)
            assert data["success"] is False
            assert "not yet implemented" in data["reason"]


class TestCheckAppStatusViaMCP:
    async def test_check_app_status_via_mcp(self, mcp_server: object) -> None:
        async with Client(mcp_server) as client:  # type: ignore[arg-type]
            session_id = await _create_session_with_architecture_via_mcp(client)

            result = await client.call_tool(
                "check_app_status",
                {"session_id": session_id},
            )
            data = parse_tool_result(result)
            assert data["session_id"] == session_id
            assert data["status"] == "not_deployed"
