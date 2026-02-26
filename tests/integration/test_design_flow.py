"""設計フローのMCPプロトコル経由統合テスト。"""

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


async def _create_completed_session_via_mcp(client: Client) -> str:  # type: ignore[type-arg]
    """MCPプロトコル経由でヒアリング完了済みセッションを作成する。"""
    result = await client.call_tool("create_session", {})
    data = parse_tool_result(result)
    session_id = data["session_id"]

    await client.call_tool(
        "save_answer",
        {"session_id": session_id, "question_id": "purpose", "value": "REST API構築"},
    )
    await client.call_tool("complete_hearing", {"session_id": session_id})
    return session_id


class TestDesignFlowViaMCP:
    async def test_save_architecture_via_mcp(self, mcp_server: object) -> None:
        async with Client(mcp_server) as client:  # type: ignore[arg-type]
            session_id = await _create_completed_session_via_mcp(client)

            result = await client.call_tool(
                "save_architecture",
                {
                    "session_id": session_id,
                    "components": [{"service_type": "oke", "display_name": "OKEクラスター"}],
                    "connections": [],
                },
            )
            data = parse_tool_result(result)
            assert data["session_id"] == session_id
            assert len(data["components"]) == 1

    async def test_add_component_via_mcp(self, mcp_server: object) -> None:
        async with Client(mcp_server) as client:  # type: ignore[arg-type]
            session_id = await _create_completed_session_via_mcp(client)

            result = await client.call_tool(
                "add_component",
                {"session_id": session_id, "service_type": "oke", "display_name": "本番OKE"},
            )
            data = parse_tool_result(result)
            assert data["service_type"] == "oke"
            assert "id" in data

    async def test_remove_component_via_mcp(self, mcp_server: object) -> None:
        async with Client(mcp_server) as client:  # type: ignore[arg-type]
            session_id = await _create_completed_session_via_mcp(client)

            add_result = await client.call_tool(
                "add_component",
                {"session_id": session_id, "service_type": "oke", "display_name": "OKE"},
            )
            comp_data = parse_tool_result(add_result)
            component_id = comp_data["id"]

            result = await client.call_tool(
                "remove_component",
                {"session_id": session_id, "component_id": component_id},
            )
            data = parse_tool_result(result)
            assert data["success"] is True

    async def test_configure_component_via_mcp(self, mcp_server: object) -> None:
        async with Client(mcp_server) as client:  # type: ignore[arg-type]
            session_id = await _create_completed_session_via_mcp(client)

            add_result = await client.call_tool(
                "add_component",
                {
                    "session_id": session_id,
                    "service_type": "adb",
                    "display_name": "ADB",
                    "config": {"endpoint_type": "public"},
                },
            )
            comp_data = parse_tool_result(add_result)

            result = await client.call_tool(
                "configure_component",
                {
                    "session_id": session_id,
                    "component_id": comp_data["id"],
                    "config": {"endpoint_type": "private"},
                },
            )
            data = parse_tool_result(result)
            assert data["config"]["endpoint_type"] == "private"

    async def test_validate_architecture_via_mcp(self, mcp_server: object) -> None:
        async with Client(mcp_server) as client:  # type: ignore[arg-type]
            session_id = await _create_completed_session_via_mcp(client)

            await client.call_tool(
                "save_architecture",
                {
                    "session_id": session_id,
                    "components": [
                        {"id": "oke-1", "service_type": "oke", "display_name": "OKE"},
                        {
                            "id": "adb-1",
                            "service_type": "adb",
                            "display_name": "ADB",
                            "config": {"endpoint_type": "public"},
                        },
                    ],
                    "connections": [
                        {
                            "source_id": "oke-1",
                            "target_id": "adb-1",
                            "connection_type": "public",
                            "description": "OKE to ADB",
                        }
                    ],
                },
            )

            result = await client.call_tool("validate_architecture", {"session_id": session_id})
            data = parse_tool_result(result)
            assert "results" in data
            assert data["error_count"] >= 1

    async def test_list_available_services_via_mcp(self, mcp_server: object) -> None:
        async with Client(mcp_server) as client:  # type: ignore[arg-type]
            result = await client.call_tool("list_available_services", {})
            data = parse_tool_result(result)
            assert "services" in data
            assert len(data["services"]) > 0

    async def test_export_summary_via_mcp(self, mcp_server: object) -> None:
        async with Client(mcp_server) as client:  # type: ignore[arg-type]
            session_id = await _create_completed_session_via_mcp(client)

            await client.call_tool(
                "save_architecture",
                {
                    "session_id": session_id,
                    "components": [{"service_type": "oke", "display_name": "OKEクラスター"}],
                    "connections": [],
                },
            )

            result = await client.call_tool("export_summary", {"session_id": session_id})
            data = parse_tool_result(result)
            assert "markdown" in data
            assert "OKEクラスター" in data["markdown"]

    async def test_export_mermaid_via_mcp(self, mcp_server: object) -> None:
        async with Client(mcp_server) as client:  # type: ignore[arg-type]
            session_id = await _create_completed_session_via_mcp(client)

            await client.call_tool(
                "save_architecture",
                {
                    "session_id": session_id,
                    "components": [{"service_type": "oke", "display_name": "OKE"}],
                    "connections": [],
                },
            )

            result = await client.call_tool("export_mermaid", {"session_id": session_id})
            data = parse_tool_result(result)
            assert "mermaid" in data
            assert "graph TB" in data["mermaid"]

    async def test_export_iac_via_mcp(self, mcp_server: object) -> None:
        async with Client(mcp_server) as client:  # type: ignore[arg-type]
            session_id = await _create_completed_session_via_mcp(client)

            await client.call_tool(
                "save_architecture",
                {
                    "session_id": session_id,
                    "components": [{"service_type": "oke", "display_name": "OKE"}],
                    "connections": [],
                },
            )

            result = await client.call_tool("export_iac", {"session_id": session_id})
            data = parse_tool_result(result)
            assert "terraform_files" in data
            assert "main.tf" in data["terraform_files"]

    async def test_export_all_via_mcp(self, mcp_server: object) -> None:
        async with Client(mcp_server) as client:  # type: ignore[arg-type]
            session_id = await _create_completed_session_via_mcp(client)

            await client.call_tool(
                "save_architecture",
                {
                    "session_id": session_id,
                    "components": [{"service_type": "oke", "display_name": "OKE"}],
                    "connections": [],
                },
            )

            result = await client.call_tool("export_all", {"session_id": session_id})
            data = parse_tool_result(result)
            assert "summary" in data
            assert "mermaid" in data
            assert "terraform_files" in data

    async def test_full_design_flow_via_mcp(self, mcp_server: object) -> None:
        """ヒアリング完了→設計→バリデーション→エクスポートの完全フロー。"""
        async with Client(mcp_server) as client:  # type: ignore[arg-type]
            session_id = await _create_completed_session_via_mcp(client)

            # 1. サービス一覧取得
            result = await client.call_tool("list_available_services", {})
            services_data = parse_tool_result(result)
            assert len(services_data["services"]) > 0

            # 2. コンポーネント追加
            result = await client.call_tool(
                "add_component",
                {"session_id": session_id, "service_type": "oke", "display_name": "本番OKE"},
            )
            parse_tool_result(result)

            result = await client.call_tool(
                "add_component",
                {
                    "session_id": session_id,
                    "service_type": "adb",
                    "display_name": "分析用ADB",
                    "config": {"endpoint_type": "public"},
                },
            )
            adb = parse_tool_result(result)

            # 3. バリデーション（接続なしなのでエラーは出ない）
            result = await client.call_tool("validate_architecture", {"session_id": session_id})
            val_data = parse_tool_result(result)
            assert val_data["error_count"] == 0

            # 4. 設定変更
            result = await client.call_tool(
                "configure_component",
                {
                    "session_id": session_id,
                    "component_id": adb["id"],
                    "config": {"endpoint_type": "private"},
                },
            )
            updated_adb = parse_tool_result(result)
            assert updated_adb["config"]["endpoint_type"] == "private"

            # 5. エクスポート
            result = await client.call_tool("export_all", {"session_id": session_id})
            export_data = parse_tool_result(result)
            assert "本番OKE" in export_data["summary"]
            assert "分析用ADB" in export_data["summary"]

    async def test_list_design_tools_via_mcp(self, mcp_server: object) -> None:
        async with Client(mcp_server) as client:  # type: ignore[arg-type]
            tools = await client.list_tools()
            tool_names = {t.name for t in tools}
            assert "save_architecture" in tool_names
            assert "add_component" in tool_names
            assert "remove_component" in tool_names
            assert "configure_component" in tool_names
            assert "validate_architecture" in tool_names
            assert "list_available_services" in tool_names
            assert "export_summary" in tool_names
            assert "export_mermaid" in tool_names
            assert "export_iac" in tool_names
            assert "export_all" in tool_names

    async def test_list_design_resources_via_mcp(self, mcp_server: object) -> None:
        async with Client(mcp_server) as client:  # type: ignore[arg-type]
            resources = await client.list_resources()
            resource_uris = {str(r.uri) for r in resources}
            assert "galley://design/services" in resource_uris
            assert "galley://design/validation-rules" in resource_uris

    async def test_list_design_prompts_via_mcp(self, mcp_server: object) -> None:
        async with Client(mcp_server) as client:  # type: ignore[arg-type]
            prompts = await client.list_prompts()
            prompt_names = {p.name for p in prompts}
            assert "build_infrastructure" in prompt_names
            assert "build_full_stack" in prompt_names
