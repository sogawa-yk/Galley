"""ヒアリング関連のMCPリソース定義。"""

from pathlib import Path

import yaml
from fastmcp import FastMCP


def register_hearing_resources(mcp: FastMCP, config_dir: Path) -> None:
    """ヒアリング関連のMCPリソースを登録する。"""

    @mcp.resource("galley://hearing/questions")
    async def hearing_questions() -> str:
        """ヒアリング質問定義を取得する。

        利用可能な質問ID、質問文、カテゴリ、回答タイプを含む質問定義を返します。
        """
        questions_file = config_dir / "hearing-questions.yaml"
        with open(questions_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return yaml.dump(data, allow_unicode=True, default_flow_style=False)

    @mcp.resource("galley://hearing/flow")
    async def hearing_flow() -> str:
        """ヒアリングフロー定義を取得する。

        質問の提示順序とフェーズ構成を返します。
        """
        flow_file = config_dir / "hearing-flow.yaml"
        with open(flow_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return yaml.dump(data, allow_unicode=True, default_flow_style=False)
