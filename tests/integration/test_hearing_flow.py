"""ヒアリングフローのMCPプロトコル経由統合テスト。"""

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


class TestHearingFlowViaMCP:
    async def test_create_session_via_mcp(self, mcp_server: object) -> None:
        async with Client(mcp_server) as client:  # type: ignore[arg-type]
            result = await client.call_tool("create_session", {})
            data = parse_tool_result(result)
            assert "session_id" in data

    async def test_full_hearing_flow_via_mcp(self, mcp_server: object) -> None:
        async with Client(mcp_server) as client:  # type: ignore[arg-type]
            # 1. セッション作成
            result = await client.call_tool("create_session", {})
            data = parse_tool_result(result)
            session_id = data["session_id"]
            assert data["status"] == "in_progress"

            # 2. 回答保存
            result = await client.call_tool(
                "save_answer",
                {"session_id": session_id, "question_id": "purpose", "value": "REST API構築"},
            )
            data = parse_tool_result(result)
            assert data["question_id"] == "purpose"

            # 3. バッチ回答保存
            result = await client.call_tool(
                "save_answers_batch",
                {
                    "session_id": session_id,
                    "answers": [
                        {"question_id": "users", "value": "100人"},
                        {"question_id": "workload_type", "value": "API サービス"},
                    ],
                },
            )
            data = parse_tool_result(result)
            assert data["saved_count"] == 2

            # 4. ヒアリング完了
            result = await client.call_tool("complete_hearing", {"session_id": session_id})
            data = parse_tool_result(result)
            assert data["session_id"] == session_id
            assert "summary" in data
            assert "requirements" in data

            # 5. ヒアリング結果取得
            result = await client.call_tool("get_hearing_result", {"session_id": session_id})
            data = parse_tool_result(result)
            assert data["session_id"] == session_id
            assert "REST API構築" in data["summary"]

    async def test_error_handling_via_mcp(self, mcp_server: object) -> None:
        async with Client(mcp_server) as client:  # type: ignore[arg-type]
            # 存在しないセッションへのアクセス — エラーがdict形式で返されるのでraise_on_error=False
            result = await client.call_tool(
                "save_answer",
                {"session_id": "nonexistent", "question_id": "purpose", "value": "test"},
                raise_on_error=False,
            )
            data = parse_tool_result(result)
            assert "error" in data
            assert data["error"] == "SessionNotFoundError"

    async def test_list_tools_via_mcp(self, mcp_server: object) -> None:
        async with Client(mcp_server) as client:  # type: ignore[arg-type]
            tools = await client.list_tools()
            tool_names = {t.name for t in tools}
            assert "create_session" in tool_names
            assert "save_answer" in tool_names
            assert "save_answers_batch" in tool_names
            assert "complete_hearing" in tool_names
            assert "get_hearing_result" in tool_names

    async def test_list_resources_via_mcp(self, mcp_server: object) -> None:
        async with Client(mcp_server) as client:  # type: ignore[arg-type]
            resources = await client.list_resources()
            resource_uris = {str(r.uri) for r in resources}
            assert "galley://hearing/questions" in resource_uris
            assert "galley://hearing/flow" in resource_uris

    async def test_list_prompts_via_mcp(self, mcp_server: object) -> None:
        async with Client(mcp_server) as client:  # type: ignore[arg-type]
            prompts = await client.list_prompts()
            prompt_names = {p.name for p in prompts}
            assert "start_hearing" in prompt_names
            assert "resume_hearing" in prompt_names

    async def test_start_hearing_prompt_contains_session_id_instruction(self, mcp_server: object) -> None:
        async with Client(mcp_server) as client:  # type: ignore[arg-type]
            result = await client.get_prompt("start_hearing", {})
            text = result.messages[0].content.text  # type: ignore[union-attr]
            assert "session_id" in text
            assert "利用者に必ず提示" in text
